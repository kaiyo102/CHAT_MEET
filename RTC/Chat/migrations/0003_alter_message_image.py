# Generated by Django 4.2.19 on 2025-02-21 08:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Chat', '0002_message_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='chat_images/'),
        ),
    ]
