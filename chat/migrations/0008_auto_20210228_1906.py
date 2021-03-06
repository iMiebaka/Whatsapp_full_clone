# Generated by Django 3.1.6 on 2021-02-28 19:06

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('chat', '0007_channelbindingidentity_created_on'),
    ]

    operations = [
        migrations.CreateModel(
            name='MarkAsRead',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message_unread', models.BooleanField(default=False)),
                ('channel_name', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_channel_mark_as_read', to='chat.channelvilla')),
                ('message', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='message_seen', to='chat.messages')),
                ('read_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reader', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterField(
            model_name='messages',
            name='message_unread',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mrk_as_read', to='chat.markasread'),
        ),
    ]
