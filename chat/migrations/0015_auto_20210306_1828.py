# Generated by Django 3.1.6 on 2021-03-06 18:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0014_auto_20210304_1847'),
    ]

    operations = [
        migrations.RenameField(
            model_name='markasread',
            old_name='message_unread',
            new_name='message_read',
        ),
    ]
