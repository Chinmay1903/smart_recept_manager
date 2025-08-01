# Generated by Django 5.2.4 on 2025-07-30 07:58

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ReceiptFile',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('file_name', models.CharField(max_length=255)),
                ('file_path', models.CharField(max_length=500)),
                ('is_valid', models.BooleanField(default=False)),
                ('invalid_reason', models.TextField(blank=True, null=True)),
                ('is_processed', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Receipt',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('purchased_at', models.DateTimeField(blank=True, null=True)),
                ('merchant_name', models.CharField(blank=True, max_length=255, null=True)),
                ('total_amount', models.CharField(blank=True, max_length=10, null=True)),
                ('parsed_text', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('receipt_file', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='extracted_receipt', to='receipts.receiptfile')),
            ],
        ),
    ]
