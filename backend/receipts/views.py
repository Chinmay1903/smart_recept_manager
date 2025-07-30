from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
import os
from django.db import transaction
from datetime import datetime
from .models import ReceiptFile, Receipt
from .serializers import ReceiptFileSerializer, ReceiptSerializer, ReceiptDetailSerializer
from .utils import validate_pdf, extract_details_with_gemini, get_storage_path

class UploadReceiptView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        if 'file' not in request.FILES:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        uploaded_file = request.FILES['file']
        if not uploaded_file.name.lower().endswith('.pdf'):
            return Response({'error': 'Only PDF files are allowed.'}, status=status.HTTP_400_BAD_REQUEST)

        # Generate a unique file name and path
        # Sanitize filename (remove potentially problematic characters)
        file_name = "".join(x for x in uploaded_file.name if x.isalnum() or x in "._- ").strip()
        # Add a timestamp to ensure uniqueness in case of same file name uploads
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        base_name, extension = os.path.splitext(file_name)
        unique_file_name = f"{base_name}_{timestamp}{extension}"

        relative_file_path = get_storage_path(unique_file_name)
        full_file_path = os.path.join(settings.MEDIA_ROOT, relative_file_path)

        receipt_file = None # Initialize to None for error handling

        try:
            # 1. Save the file to the local directory
            with open(full_file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            # Create ReceiptFile entry with initial status
            receipt_file = ReceiptFile.objects.create(
                file_name=uploaded_file.name, # Store original name
                file_path=relative_file_path,  # Store relative path
                is_valid=False,  # Will be validated immediately
                is_processed=False # Will be processed immediately if valid
            )

            # 2. Validate the uploaded file
            is_valid, invalid_reason = validate_pdf(full_file_path)
            receipt_file.is_valid = is_valid
            receipt_file.invalid_reason = invalid_reason

            if not is_valid:
                receipt_file.save() # Save the validation result
                return Response(
                    {'message': 'File uploaded but is invalid.', 'receipt_file': ReceiptFileSerializer(receipt_file).data},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 3. Extract receipt details using Gemini (if valid)
            # --- Call Gemini for extraction ---
            parsed_data, raw_gemini_response = extract_details_with_gemini(full_file_path)

            if parsed_data is None: # If Gemini extraction failed or returned null
                receipt_file.is_processed = False
                receipt_file.invalid_reason = f"Gemini extraction failed: {raw_gemini_response}"
                receipt_file.save()
                return Response(
                    {'message': 'File is valid but AI extraction failed.', 'receipt_file': ReceiptFileSerializer(receipt_file).data},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Basic check if Gemini yielded meaningful data
            if not parsed_data.get('merchant_name') and not parsed_data.get('total_amount') and not parsed_data.get('purchased_at'):
                receipt_file.is_processed = False
                receipt_file.invalid_reason = "AI extracted text, but parsing yielded no meaningful data or key fields are missing."
                receipt_file.save()
                return Response(
                    {'message': 'AI extracted text, but parsing yielded no meaningful data.', 'receipt_file': ReceiptFileSerializer(receipt_file).data},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            print(f"DEBUG: Gemini Raw Response:\n{parsed_data}")

            with transaction.atomic():
                receipt_instance, created = Receipt.objects.update_or_create(
                    receipt_file=receipt_file,
                    defaults={
                        'purchased_at': parsed_data.get('purchased_at'),
                        'merchant_name': parsed_data.get('merchant_name'),
                        'total_amount': parsed_data.get('total_amount'),
                        'parsed_text': raw_gemini_response, # Store raw Gemini JSON response here
                    }
                )
                receipt_file.is_processed = True
                receipt_file.save()

            return Response(
                {
                    'message': 'File uploaded, validated, and processed successfully!',
                    'receipt_file': ReceiptFileSerializer(receipt_file).data,
                    'extracted_receipt': ReceiptSerializer(receipt_instance).data
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            if receipt_file:
                receipt_file.is_valid = False
                receipt_file.is_processed = False
                receipt_file.invalid_reason = f"Processing failed: {str(e)}"
                receipt_file.save()
            else:
                if os.path.exists(full_file_path):
                    os.remove(full_file_path)

            return Response(
                {'error': f'An unexpected error occurred during receipt processing: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ValidateReceiptView(APIView):
    def post(self, request, *args, **kwargs):
        receipt_file_id = request.data.get('receipt_file_id')
        if not receipt_file_id:
            return Response({'error': 'receipt_file_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            receipt_file = ReceiptFile.objects.get(id=receipt_file_id)
        except ReceiptFile.DoesNotExist:
            return Response({'error': 'ReceiptFile not found'}, status=status.HTTP_404_NOT_FOUND)

        full_file_path = os.path.join(settings.MEDIA_ROOT, receipt_file.file_path)

        is_valid, invalid_reason = validate_pdf(full_file_path)

        receipt_file.is_valid = is_valid
        receipt_file.invalid_reason = invalid_reason
        receipt_file.save()

        serializer = ReceiptFileSerializer(receipt_file)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ProcessReceiptView(APIView):
    def post(self, request, *args, **kwargs):
        receipt_file_id = request.data.get('receipt_file_id')
        if not receipt_file_id:
            return Response({'error': 'receipt_file_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            receipt_file = ReceiptFile.objects.get(id=receipt_file_id)
        except ReceiptFile.DoesNotExist:
            return Response({'error': 'ReceiptFile not found'}, status=status.HTTP_404_NOT_FOUND)

        if not receipt_file.is_valid:
            return Response({'error': f'File is not valid: {receipt_file.invalid_reason}'}, status=status.HTTP_400_BAD_REQUEST)
        if receipt_file.is_processed:
            return Response({'message': 'Receipt already processed.'}, status=status.HTTP_200_OK)

        full_file_path = os.path.join(settings.MEDIA_ROOT, receipt_file.file_path)

        try:
            parsed_data, raw_gemini_response = extract_details_with_gemini(full_file_path)

            if parsed_data is None:
                receipt_file.is_processed = False
                receipt_file.invalid_reason = f"Gemini extraction failed: {raw_gemini_response}"
                receipt_file.save()
                return Response(
                    {'message': 'AI extraction failed.', 'receipt_file': ReceiptFileSerializer(receipt_file).data},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Basic check if Gemini yielded meaningful data
            if not parsed_data.get('merchant_name') and not parsed_data.get('total_amount') and not parsed_data.get('purchased_at'):
                receipt_file.is_processed = False
                receipt_file.invalid_reason = "AI extracted text, but parsing yielded no meaningful data or key fields are missing."
                receipt_file.save()
                return Response(
                    {'message': 'AI extracted text, but parsing yielded no meaningful data.', 'receipt_file': ReceiptFileSerializer(receipt_file).data},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            with transaction.atomic():
                receipt_instance, created = Receipt.objects.update_or_create(
                    receipt_file=receipt_file,
                    defaults={
                        'purchased_at': parsed_data.get('purchased_at'),
                        'merchant_name': parsed_data.get('merchant_name'),
                        'total_amount': parsed_data.get('total_amount'),
                        'parsed_text': raw_gemini_response,
                    }
                )
                receipt_file.is_processed = True
                receipt_file.save()

            serializer = ReceiptSerializer(receipt_instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            receipt_file.is_processed = False
            receipt_file.invalid_reason = f"Processing failed: {str(e)}"
            receipt_file.save()
            return Response({'error': f'Receipt processing failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ReceiptListView(APIView):
    def get(self, request, *args, **kwargs):
        receipts = Receipt.objects.select_related('receipt_file').all() # Use select_related for optimized queries
        serializer = ReceiptDetailSerializer(receipts, many=True)
        return Response(serializer.data)

class ReceiptDetailView(APIView):
    def get(self, request, id, *args, **kwargs):
        try:
            receipt = Receipt.objects.select_related('receipt_file').get(id=id)
            serializer = ReceiptDetailSerializer(receipt)
            return Response(serializer.data)
        except Receipt.DoesNotExist:
            return Response({'error': 'Receipt not found'}, status=status.HTTP_404_NOT_FOUND)