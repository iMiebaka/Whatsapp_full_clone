from django.db import models
from django.conf import settings
from django.utils import timezone
from django.conf import settings
import os
from django.core.cache import cache
from django.apps import apps
from datetime import date
# from accounts.models import PhoneBook, Profile
# Create your models here.

def generate_media_path_status_image(self, filename):
    filename, ext = os.path.splitext(filename.lower())
    filename = "%s.%s" %(slugify(filename), timezone.now())
    hs_index = hashlib.md5(filename.encode())
    filename = "%s" %hs_index.hexdigest()
    return "%s/%s" %(settings.UPLOAD_PATH_STATUS, filename)


def generate_media_path(self, filename, message_state):
    filename, ext = os.path.splitext(filename.lower())
    filename = "%s.%s" %(slugify(filename), timezone.now())
    hs_index = hashlib.md5(filename.encode())
    filename = "%s" %hs_index.hexdigest()
    if message_state == 'private':
        return "%s/%s" %(settings.UPLOAD_PRIVATE_MEDIA_PATH, filename)
    if message_state == 'public':
        return "%s/%s" %(settings.UPLOAD_PATH_GROUP_PROFILE_IMAGE, filename)


class ChannelVilla(models.Model):
    channel_name_main = models.CharField(max_length=35)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='group_member', on_delete=models.CASCADE)
    created_on =  models.DateTimeField(default=timezone.now)


class ChannelBindingIdentity(models.Model):
    """docstring for PrivateChatRoom."""
    connected_receiver =  models.ForeignKey(settings.AUTH_USER_MODEL, related_name='private_chat_reveiver', on_delete=models.CASCADE)
    channel_name = models.ForeignKey('ChannelVilla', related_name='binded_channel', on_delete=models.CASCADE)
    channel_name_type = models.CharField(max_length=8, null=True)
    created_on = models.DateTimeField(default=timezone.now)

    # def __str__(self):
    #     return '%s of the type %s'%(self.channel_name.channel_name_main, self.channel_name_type)

class Messages(models.Model):
    """Model for messages recieved."""
    sent_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='group_sender', on_delete=models.CASCADE)
    media = models.CharField(max_length=1000)
    media_file = models.FileField(upload_to=generate_media_path, null=True)
    file_type = models.CharField(max_length=6)
    message_unread = models.ForeignKey('MarkAsRead', related_name='mrk_as_read', null=True, on_delete=models.SET_NULL)
    sent_from_delete = models.BooleanField(default=False)
    sent_by_delete = models.BooleanField(default=False)
    created_on =  models.DateTimeField(default=timezone.now)
    channel_name = models.ForeignKey('ChannelVilla', related_name='group_channel_name', on_delete=models.CASCADE)
    message_id = models.CharField(max_length=35)
    message_state = models.CharField(max_length=7, null=True)

    def contact_name_typing(self):
        try:
            Profile = apps.get_model('accounts', 'Profile')
            PhoneBook = apps.get_model('accounts', 'PhoneBook')
            profile = Profile.objects.get(user=self.sent_by).mobile
            return PhoneBook.objects.get(number=profile).contact_name
        except PhoneBook.DoesNotExist:
            return profile

    def message_status(self):
        message_status = MarkAsRead.objects.get(message=self)
        msg_state = 1
        if message_status.message_delivered == True:
            msg_state = 2
        if message_status.message_read == True:
            Profile = apps.get_model('accounts', 'Profile')
            user_opt  = Profile.objects.get(user=self.sent_by).mark_as_read
            if user_opt:
                msg_state = 3
            else:
                msg_state = 2
            # print(msg_state)
        return msg_state

    class Meta:
        get_latest_by = 'created_on'


    # def __str__(self):
    #     return self.channel_name.channel_name_main

class MarkAsRead(models.Model):
    message_read = models.BooleanField(default=False)
    message_delivered = models.BooleanField(default=False)
    read_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='reader', on_delete=models.CASCADE)
    message = models.ForeignKey('Messages', related_name='message_seen', on_delete=models.CASCADE)
    channel_name = models.ForeignKey('ChannelVilla', null=True, related_name='group_channel_mark_as_read',on_delete=models.CASCADE)
    media_type = models.CharField(max_length=5, default='Text')

class GroupChatRoom(models.Model):
    """docstring for GroupChatRoom."""
    chat_room_name = models.CharField(max_length=29)
    chat_room_description = models.CharField(max_length=50)
    message_by_admin = models.BooleanField(default=False)
    admin = models.BooleanField(default=False)
    created_on =  models.DateTimeField(default=timezone.now)
    cover_image = models.ImageField(default='default_image.jpg', upload_to=generate_media_path)
    channel_name = models.ForeignKey('ChannelVilla', related_name='group_channel',on_delete=models.CASCADE)
    room_id = models.CharField(max_length=35)

    def __str__(self):
        return '%s_%s'%(self.chat_room_name,self.channel_name)

    def message_count(self):
        unread_messages_count =  MarkAsRead.objects.filter(
            channel_name=self.channel_name,
            read_by__username=cache.get('user_ins_unread_messages'),
            message_read=False).count()
        # print(unread_messages_count)
        return unread_messages_count

    def message_count(self, user):
        unread_messages_count =  MarkAsRead.objects.filter(
            channel_name=self.channel_name,
            read_by__username=user,
            message_read=False).count()
        # print(unread_messages_count)
        return unread_messages_count

    def last_message_public(self):
        unread_messages =  Messages.objects.filter(
            channel_name=self.channel_name).last()
        # print(unread_messages)
        if unread_messages is None:
            return ''
        return unread_messages.media


    def last_message(self):
        unread_messages =  Messages.objects.filter(
            channel_name=self.channel_name).last()
        # print(unread_messages)
        if unread_messages is None:
            return ''
        return unread_messages.media

    def last_message_time_value(self):
        CurrentlyBindedContact = apps.get_model('accounts', 'CurrentlyBindedContact')
        # ch_name = CurrentlyBindedContact.objects.get(added_contact_runner=self.user, app_runner__username=cache.get('user_ins_unread_messages')).channel_name
        unread_messages =  Messages.objects.filter(
            channel_name=self.channel_name).last()
        if unread_messages is None:
            now = date(
                year=timezone.now().year,
                month=timezone.now().month,
                day=timezone.now().day
            )
            then = date(
                year=self.created_on.year,
                month=self.created_on.month,
                day=self.created_on.day
            )
            date_difference = abs((now - then).days)
            if date_difference == 0:
                time_date = self.created_on.strftime('%-I:%M %p')
            elif date_difference == 1:
                time_date = 'Yesterday'
            else:
                time_date = self.created_on.strftime('%d/%m/%y')
            return "Created %s"%time_date
        now = date(
            year=timezone.now().year,
            month=timezone.now().month,
            day=timezone.now().day
        )
        then = date(
            year=unread_messages.created_on.year,
            month=unread_messages.created_on.month,
            day=unread_messages.created_on.day
        )
        date_difference = abs((now - then).days)
        if date_difference == 0:
            time_date = unread_messages.created_on.strftime('%-I:%M %p')
        elif date_difference == 1:
            time_date = 'Yesterday'
        else:
            time_date = unread_messages.created_on.strftime('%d/%m/%y')
        return time_date
