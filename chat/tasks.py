from celery import shared_task
# from .models import ChannelVilla, ChannelBindingIdentity, MarkAsRead, Messages
from accounts.models import Profile, CurrentlyBindedContact, PhoneBook
import os
import hashlib
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.auth.models import User
import json
from django.contrib import messages
from time import sleep
from django.apps import apps
# from .consumers import event_triger

ChannelVilla = apps.get_model('chat', 'ChannelVilla')
ChannelBindingIdentity = apps.get_model('chat', 'ChannelBindingIdentity')
MarkAsRead = apps.get_model('chat', 'MarkAsRead')
Messages = apps.get_model('chat', 'Messages')


@shared_task
def send_message_task(text_data_json):
    try:
        ch_name = ChannelVilla.objects.get(channel_name_main=text_data_json['room_channel_name'])
    except:
        print('Channel name does not exist')

    try:
        auth_user = Profile.objects.get(mobile__iexact=text_data_json['own_user_number'])
        message = Messages.objects.create(
            sent_by=auth_user.user,
            media = text_data_json['message'],
            file_type = text_data_json['file_type'],
            channel_name = ch_name,
            message_id = text_data_json['message_id'],
        )
        print('message saved')
    except Exception as e:
        raise

    channel_bind = ChannelBindingIdentity.objects.filter(channel_name=ch_name)
    for ch_b in channel_bind:
        if ch_b.connected_receiver != auth_user.user:
            MarkAsRead.objects.create(
                message = message,
                channel_name = ch_name,
                read_by = ch_b.connected_receiver,
            )
    print('Messages saved')
    return None


@shared_task
def check_for_unread_messages(room_name, user):
    try:
        ch_name = ChannelVilla.objects.get(channel_name_main=room_name)
        user = User.objects.get(username=user)
        msr = MarkAsRead.objects.filter(channel_name=ch_name, message_read=False, read_by=user).count()
        if msr > 0:
            print('>> unread messages are %s'%msr)
            return True
        else:
            print('<< unread messages are %s'%msr)
            return False
    except:
        print('Mark as read check task incompleted')
    return None



@shared_task
def async_mark_as_read_views(room_name, user):
    try:
        ch_name = ChannelVilla.objects.get(channel_name_main=room_name)
        user = User.objects.get(username=user)
        msr = MarkAsRead.objects.filter(channel_name=ch_name, message_read=False, read_by=user)
        for mr in msr:
            mr.message_read = True
            mr.message_delivered = True
            mr.save()
            print('Mark as read task finished')
    except:
        print('Mark as read task incompleted')
    return None


@shared_task
def send_message_task_group(text_data_json):
    try:
        ch_name = ChannelVilla.objects.get(channel_name_main=text_data_json['room_channel_name'])
    except:
        print('Channel name does not exist')

    try:
        auth_user = Profile.objects.get(mobile__iexact=text_data_json['own_user_number']).user
        message = Messages.objects.create(
            sent_by=auth_user,
            media = text_data_json['message'],
            file_type = text_data_json['file_type'],
            channel_name = ch_name,
            message_id = text_data_json['message_id'],
        )
        print('Group messaged saved')
    except Exception as e:
        pass


    try:
        channel_bind = ChannelBindingIdentity.objects.filter(channel_name=ch_name)
        for ch_b in channel_bind:
            if ch_b.connected_receiver != auth_user:
                msr = MarkAsRead.objects.create(
                    message = message,
                    channel_name = ch_name,
                    read_by = ch_b.connected_receiver
                )

        print('mark as read saved')
    except Exception as e:
        print('mark as read unsaved')
        pass


'''
Start the celery using :
celery -A mysite worker -l INFO
'''
