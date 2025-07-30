from rest_framework import serializers
from .models import ReceiptFile, Receipt

class ReceiptFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReceiptFile
        fields = '__all__'
        read_only_fields = ('is_valid', 'invalid_reason', 'is_processed', 'created_at', 'updated_at')

class ReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipt
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class ReceiptDetailSerializer(serializers.ModelSerializer):
    receipt_file_details = ReceiptFileSerializer(source='receipt_file', read_only=True)

    class Meta:
        model = Receipt
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')