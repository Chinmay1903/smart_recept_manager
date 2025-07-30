import os
import fitz  # PyMuPDF
from django.conf import settings
from datetime import datetime
import re
import decimal
import json
import google.generativeai as genai

# Configure Google Gemini API
genai.configure(api_key=settings.GEMINI_API_KEY)

# Define the model to use
GEMINI_MODEL_NAME = 'gemini-2.5-flash' 
GEMINI_MODEL = genai.GenerativeModel(GEMINI_MODEL_NAME)

def validate_pdf(file_path):
    """
    Validates if a file is a valid PDF.
    Returns (is_valid, reason_if_invalid)
    """
    try:
        doc = fitz.open(file_path)
        if doc.page_count == 0:
            return False, "PDF contains no pages."
        doc.close()
        return True, None
    except fitz.EmptyFileError:
        return False, "File is empty or corrupted."
    except fitz.FileDataError:
        return False, "Invalid PDF file structure or format."
    except Exception as e:
        return False, f"An unexpected error occurred during PDF validation: {str(e)}"

def extract_details_with_gemini(pdf_path):
    """
    Extracts receipt details from a PDF using Google Gemini (native PDF input).
    Returns parsed data and the raw Gemini response text.
    """
    try:
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()

        # Create an inline_data part for the PDF file
        pdf_part = {
            "inline_data": {
                "mime_type": "application/pdf",
                "data": pdf_bytes # Pass raw bytes directly
            }
        }

        # Optimized Prompt for Receipt Extraction:
        prompt_text = """
        Analyze this receipt document. Extract the following details:
        - **Merchant Name**: The name of the store or business.
        - **Purchase Date**: The date of the transaction in YYYY-MM-DD format.
        - **Total Amount**: The grand total amount of the purchase, including tax, add the currency symbol (e.g., "$").
        - **Items**: A list of items purchased. For each item, include:
            - **Description**: The name of the item.
            - **Price**: The price of the individual item.

        Output the information strictly as a JSON object. If a specific detail is not found, use `null` for its value.
        Ensure the JSON is well-formed and can be directly parsed.
        Example JSON structure:
        ```json
        {
          "merchant_name": "Example Store",
          "purchase_date": "2023-10-26",
          "total_amount": "$123.45",
          "items": [
            {"description": "Product A", "price": "$10.00"},
            {"description": "Product B", "price": "$5.50"}
          ]
        }
        ```
        """
        # The contents list now includes the PDF part and the text prompt part
        contents = [
            pdf_part,
            {"text": prompt_text} # Text is also sent as a part
        ]

        response = GEMINI_MODEL.generate_content(contents)
        response.resolve() # Ensure content is fully available

        gemini_text_response = response.text.strip()
        print(f"DEBUG: Gemini Raw Response:\n{gemini_text_response}")

        # Attempt to parse the JSON output from Gemini
        json_match = re.search(r'```json\n(.*?)\n```', gemini_text_response, re.DOTALL)
        if json_match:
            json_string = json_match.group(1)
        else:
            json_string = gemini_text_response # Assume it's direct JSON if no markdown block

        parsed_data = json.loads(json_string)

        merchant_name = parsed_data.get('merchant_name')
        total_amount = None
        if parsed_data.get('total_amount') is not None:
            try:
                total_amount = parsed_data['total_amount']
            except (decimal.InvalidOperation, TypeError):
                total_amount = None

        purchased_at = None
        date_str = parsed_data.get('purchase_date')
        if date_str:
            try:
                purchased_at = datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                purchased_at = None

        extracted_info = {
            'merchant_name': merchant_name,
            'total_amount': total_amount,
            'purchased_at': purchased_at,
            # 'items_details': parsed_data.get('items') # If you add a JSONField for items
        }

        return extracted_info, gemini_text_response
    except json.JSONDecodeError as jde:
        # Include the raw response in the error message for debugging
        return None, f"Failed to parse Gemini's JSON response: {jde}. Raw response from Gemini: {gemini_text_response}"
    except Exception as e:
        print(f"Error during Gemini extraction: {e}")
        # More robust error handling for API issues
        error_message = f"Extraction failed: {str(e)}"
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            try:
                api_error_details = e.response.json()
                error_message += f". API details: {api_error_details.get('error', {}).get('message', 'No specific message')}"
            except json.JSONDecodeError:
                error_message += f". Raw API response: {e.response.text}"
        return None, error_message

def get_storage_path(filename):
    """
    Generates a storage path based on the current year.
    Example: media/receipts/2025/filename.pdf
    """
    current_year = datetime.now().year
    year_directory = os.path.join('receipts', str(current_year))
    full_directory_path = os.path.join(settings.MEDIA_ROOT, year_directory)
    os.makedirs(full_directory_path, exist_ok=True)
    return os.path.join(year_directory, filename)