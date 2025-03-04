# Generated by Django 5.1.4 on 2025-02-15 15:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='member',
            name='primary_account',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='members', to='accounts.primaryaccount'),
        ),
        migrations.AlterField(
            model_name='member',
            name='relationship',
            field=models.CharField(choices=[('WIFE', 'wife'), ('CHILD', 'Child'), ('PARENT', 'Parent'), ('OTHER', 'Other')], max_length=20),
        ),
    ]
