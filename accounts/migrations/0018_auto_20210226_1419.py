# Generated by Django 3.1.6 on 2021-02-26 14:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0017_currentlybindedcontact_contact_channel'),
    ]

    operations = [
        migrations.AlterField(
            model_name='currentlybindedcontact',
            name='contact_channel',
            field=models.CharField(max_length=35, null=True),
        ),
    ]
