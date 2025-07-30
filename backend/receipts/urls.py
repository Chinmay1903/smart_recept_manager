
from django.urls import path
from .views import (
    UploadReceiptView,
    ReceiptListView,
    ReceiptDetailView
)

urlpatterns = [
    path('upload/', UploadReceiptView.as_view(), name='upload_receipt'),
    path('receipts/', ReceiptListView.as_view(), name='receipt_list'),
    path('receipts/<int:id>/', ReceiptDetailView.as_view(), name='receipt_detail'),
]