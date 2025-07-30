
from django.urls import path
from .views import (
    UploadReceiptView,
    ValidateReceiptView,
    ProcessReceiptView,
    ReceiptListView,
    ReceiptDetailView
)

urlpatterns = [
    path('upload/', UploadReceiptView.as_view(), name='upload_receipt'),
    path('validate/', ValidateReceiptView.as_view(), name='validate_receipt'),
    path('process/', ProcessReceiptView.as_view(), name='process_receipt'),
    path('receipts/', ReceiptListView.as_view(), name='receipt_list'),
    path('receipts/<int:id>/', ReceiptDetailView.as_view(), name='receipt_detail'),
]