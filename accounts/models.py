from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.dispatch import receiver
from .select_options import COUNTRY, sex
from django.db.models.signals import post_save
from rest_framework.authtoken.models import Token
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
from datetime import timedelta, datetime
from PIL import Image
import hashlib
import os
from datetime import date, datetime
from chat.models import (Messages, ChannelVilla, MarkAsRead)
# models = chat.get_model(Messages, ChannelVilla, MarkAsRead)
# Create your models here.
# def generate_media_path(self, request, filename):

def generate_media_path_private_profile_image(self, filename):
    filename, ext = os.path.splitext(filename.lower())
    filename = "%s.%s" %(filename, timezone.now())
    filename = hashlib.md5(filename.encode()).hexdigest()
    return "%s/%s" %(settings.UPLOAD_PATH_PROFILE_IMAGE, filename)


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)
    email_confirmed = models.BooleanField(default=False)
    mobile = models.CharField(max_length=15, null=True)
    mark_as_read = models.BooleanField(default=True)
    display_last_seen = models.BooleanField(null=True, default=True)
    last_seen = models.DateTimeField(default=timezone.now, null=True)
    about = models.TextField(max_length=200, default='Hey, there! I am using Whatsapp')
    location = models.CharField(max_length=20 , choices=COUNTRY, null=True, blank=True)
    cover_image = models.ImageField(default='default_image.jpg', null=True, upload_to=generate_media_path_private_profile_image)
    isVerified = models.BooleanField(null=True, default=False)
    otp_mobile = models.BooleanField(default=False)
    two_step_verification = models.BooleanField(default=False)
    counter = models.IntegerField(default=0, null=True)   # For HOTP Verification
    home_channel_name = models.CharField(max_length=29)

    def __str__(self):
        return str(self.user)

    def last_seen_cache(self):
        return cache.get('seen_%s' %self.user.username)

    @property
    def last_seen_algorithm(self):
        if self.display_last_seen:
            ls = str(self.last_seen.date())
            now = str(timezone.now().date())
            if now == ls:
                return ('last seen today at %s' %self.last_seen.strftime('%-I:%M %p'))
            if now > ls:
                return ('last seen %s' %self.last_seen.strftime('%b %-d, %-I:%M %p'))
        else:
            return None

    @property
    def online(self):
        if self.display_last_seen:
            if self.last_seen_cache():
                now = timezone.now()
                if now > self.last_seen_cache() + timedelta(seconds=settings.USER_ONLINE_TIMEOUT):
                    return False
                else:
                    return True
            else:
                return None
        else:
            return None

    @property
    def avaiablity(self):
        if self.last_seen_cache():
            now = timezone.now()
            if now > self.last_seen_cache() + timedelta(seconds=settings.USER_ONLINE_TIMEOUT):
                return False
            else:
                return True
        else:
            return False

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        img = Image.open(self.cover_image.path)
        if img.height > 2000 or img.width > 2000:
            output_size = (img.height/2, img.width/2)
            img.thumbnail(output_size)
            img.save(self.cover_image.path)

    @property
    def contact_name(self):
        try:
            return PhoneBook.objects.get(number=self.mobile, phone_owner__username=cache.get('user_ins_unread_messages')).contact_name
        except PhoneBook.DoesNotExist:
            return self.mobile

    @property
    def contact_name_typing(self):
        try:
            return PhoneBook.objects.get(number=self.mobile, phone_owner__username=cache.get('user_ins_unread_messages')).contact_name
        except PhoneBook.DoesNotExist:
            return self.mobile

    @property
    def remote_channel_name(self):
        return CurrentlyBindedContact.objects.get(added_contact_runner=self.user, app_runner__username=cache.get('user_ins_unread_messages')).channel_name

    @property
    def message_count(self):
        # ch_name = CurrentlyBindedContact.objects.get(added_contact_runner=self.user).channel_name
        ch_name = CurrentlyBindedContact.objects.get(added_contact_runner=self.user, app_runner__username=cache.get('user_ins_unread_messages')).channel_name
        print(ch_name)
        unread_messages_count = MarkAsRead.objects.filter(
            channel_name__channel_name_main=ch_name,
            read_by__username=cache.get('user_ins_unread_messages'),
            message_read=False).count()
        return unread_messages_count

    # @property
    # def message_count_indefinite(self):
    #     # print('@@@@@@@@')
    #     # ch_name = CurrentlyBindedContact.objects.get(added_contact_runner=self.user).channel_name
    #     ch_name = CurrentlyBindedContact.objects.get(added_contact_runner=self.user, app_runner__username=cache.get('user_ins_unread_messages')).channel_name
    #     print(ch_name)
    #     unread_messages =  Messages.objects.filter(
    #         channel_name__channel_name_main=ch_name).last()
    #     print(unread_messages_count)
    #     return unread_messages_count.media


    @property
    def last_message(self):
        ch_name = CurrentlyBindedContact.objects.get(added_contact_runner=self.user, app_runner__username=cache.get('user_ins_unread_messages')).channel_name
        # ch_name = CurrentlyBindedContact.objects.get(added_contact_runner=self.user).channel_name
        unread_messages =  Messages.objects.filter(
            channel_name__channel_name_main=ch_name).last()
        return unread_messages

    @property
    def last_message_time(self):
        ch_name = CurrentlyBindedContact.objects.get(added_contact_runner=self.user, app_runner__username=cache.get('user_ins_unread_messages')).channel_name
        unread_messages =  Messages.objects.filter(
            channel_name__channel_name_main=ch_name).last()
        if unread_messages is None:
            return ''
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

    def message_count_private(self, ch_name):
        # ch_name = ch_name.channel_name
        unread_messages_count = MarkAsRead.objects.filter(
            channel_name=ch_name,
            read_by=self.user,
            message_read=False).count()
        return unread_messages_count

    def message_count_public(self, ch_name, user):
        # ch_name = ch_name.channel_name
        unread_messages_count = MarkAsRead.objects.filter(
            channel_name=ch_name,
            read_by=user,
            message_read=False).count()
        return unread_messages_count


    def last_message_private(self, ch_name):
        # print(ch_name)
        unread_messages =  Messages.objects.filter(
            channel_name=ch_name).last()
        if unread_messages is None:
            return ''
        return unread_messages.media

    def last_message_time_private(self, ch_name):
        # ch_name = CurrentlyBindedContact.objects.get(added_contact_runner=self.user, app_runner__username=cache.get('user_ins_unread_messages')).channel_name
        unread_messages =  Messages.objects.filter(
            channel_name=ch_name).last()
        if unread_messages is None:
            return ''
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

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


'''
This part simulates the phone memory
'''
class PhoneBook(models.Model):
    """docstring for ContactList."""
    phone_owner =  models.ForeignKey(settings.AUTH_USER_MODEL, related_name='contact_stored_by', on_delete=models.CASCADE)
    contact_name = models.CharField(max_length=29)
    number = models.CharField(max_length=19)

    def __str__(self):
        return self.number

    class meta:
        order_by=('contact_name')


'''
This part simulates the whatsapp local memory
'''
class CurrentlyBindedContact(models.Model):
    """docstring for CurrentlyBindedContact."""
    app_runner =  models.ForeignKey(settings.AUTH_USER_MODEL, related_name='local_user_init', on_delete=models.CASCADE)
    added_contact_runner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='local_contact', on_delete=models.CASCADE)
    contact_channel = models.CharField(max_length=35, null=True)
    channel_name = models.CharField(max_length=35)
    created_on = models.DateTimeField(default=timezone.now)


    def __str__(self):
        return self.channel_name
