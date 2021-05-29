import json
from channels.generic.websocket import AsyncWebsocketConsumer
import channels
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from time import sleep
import threading
from chat.models import ChannelBindingIdentity, ChannelVilla, Messages, MarkAsRead, GroupChatRoom
from accounts.models import Profile, CurrentlyBindedContact, PhoneBook
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from django.conf import settings
import hashlib
from .tasks import send_message_task, send_message_task_group, async_mark_as_read_views
from channels.generic.websocket import WebsocketConsumer
from celery import shared_task
from django.utils import timezone


class PrivateChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'private_%s_room' % self.room_name
        await self.channel_layer.group_add(
        self.room_group_name,
        self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
        self.room_group_name,
        self.channel_name
        )

    @database_sync_to_async
    def check_create_chanel(self, event):
        try:
            # Check if the channel is registerd generally
            ChannelVilla.objects.get(channel_name_main=event['room_channel_name'])
        except ChannelVilla.DoesNotExist:

            # If no, register it    #This only runs once#
            #Register the channel as a private one
            new_chan = ChannelVilla.objects.create(
                channel_name_main=event['room_channel_name'],
                created_by = self.scope['user'])

            # Get room mate user instance
            profile = Profile.objects.get(home_channel_name=event['room_mate_home_channel_name']).user
            # user = User.objects.get(username=profile)

            #Create a notification binding for both room mates
            users = [profile, self.scope['user']]
            for u in users:
                ChannelBindingIdentity.objects.create(
                connected_receiver = u,
                channel_name=new_chan,
                channel_name_type = 'private')

            #This is same as the previous but emulates local storage:
            CurrentlyBindedContact.objects.create(
                app_runner=profile,
                channel_name=event['room_channel_name'],
                added_contact_runner=self.scope['user'],
                contact_channel = self.scope['user'].profile.home_channel_name)
            # print('Room created')


            # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        message_id = text_data_json['message_id']
        time_stamp = text_data_json['time_stamp']
        file_type = text_data_json['file_type']
        own_user_number = text_data_json['own_user_number']
        room_mate_home_channel_name = text_data_json['room_mate_home_channel_name']
        room_channel_name = text_data_json['room_channel_name']

        await self.check_create_chanel(text_data_json)
        send_message_task.delay(text_data_json)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
            'type': 'chat.message',
            'file_type': file_type,
            'message': message,
            'message_id': message_id,
            'time_stamp': time_stamp,
            'room_mate_home_channel_name': room_mate_home_channel_name,
            'own_user_number': own_user_number,
            'room_channel_name': room_channel_name,
            # 'home_channel_name': home_channel_name,
            # 'pre_generated_channel_name': pre_generated_channel_name
            }
        )
        await self.other_channels(text_data_json)

    @database_sync_to_async
    def other_channels(self, text_data_json):
        # print('@@@@')
        auth_user = Profile.objects.get(mobile__iexact=text_data_json['own_user_number'])
        ch_name = ChannelVilla.objects.get(channel_name_main=text_data_json['room_channel_name'])
        channel_bind = ChannelBindingIdentity.objects.filter(channel_name=ch_name)
        for ch_b in channel_bind:
            if ch_b.connected_receiver != auth_user.user:
                profile = Profile.objects.get(user=ch_b.connected_receiver)
                try:
                    contact_name = PhoneBook.objects.get(phone_owner=ch_b.connected_receiver, number=text_data_json['own_user_number']).contact_name
                except PhoneBook.DoesNotExist:
                    contact_name = profile.mobile
                # print(profile.home_channel_name)
                message_count = profile.message_count_private(ch_name)
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    profile.home_channel_name,{
                        'type': 'send_notification_to_frontend',
                        'channel_room_name': ch_b.channel_name.channel_name_main,
                        'room_name_image': auth_user.cover_image.url,
                        'room_name': contact_name,
                        'message': text_data_json['message'],
                        'message_count': message_count,
                        'message_type': 'Message',
                        'message_time': timezone.now().strftime('%-I:%M %p')
                    })
                print('Message sent to home channel')

        # Receive message from room group
        #This is sent according to the number of connect consumers
    async def chat_message(self, event):
        message = event['message']
        message_id = event['message_id']
        time_stamp = event['time_stamp']
        file_type = event['file_type']
        room_mate_home_channel_name = event['room_mate_home_channel_name']
        own_user_number = event['own_user_number']
        room_channel_name = event['room_channel_name']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'message_id': message_id,
            'time_stamp': time_stamp,
            'room_mate_home_channel_name': room_mate_home_channel_name,
            'file_type': file_type,
            'own_user_number': own_user_number,
            'room_channel_name': room_channel_name,
        }))


#When the input box is activated
class ChatConsumer_typing(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'typing_%s' % self.room_name
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        status = text_data_json['status']
        file_type = text_data_json['file_type']
        own_user_number = text_data_json['own_user_number']
        home_channel_name = text_data_json['home_channel_name']
        room_channel_name = text_data_json['room_channel_name']

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'send.typing.message',
                'file_type': file_type,
                'status': status,
                'own_user_number': own_user_number,
                'home_channel_name': home_channel_name,
                'room_channel_name': room_channel_name
            }
        )
        if text_data_json['scope'] == 'private':
            await self.other_channels_private(text_data_json)
        if text_data_json['scope'] == 'public':
            await self.other_channels_public(text_data_json)

    @database_sync_to_async
    def other_channels_private(self, text_data_json):
        auth_user = Profile.objects.get(mobile__iexact=text_data_json['own_user_number'])
        try:
            ch_name = ChannelVilla.objects.get(channel_name_main=text_data_json['room_channel_name'])
            channel_bind = ChannelBindingIdentity.objects.filter(channel_name=ch_name)
            for ch_b in channel_bind:
                if ch_b.connected_receiver != auth_user.user:
                    profile = Profile.objects.get(user=ch_b.connected_receiver)
                    try:
                        contact_name = PhoneBook.objects.get(phone_owner=ch_b.connected_receiver, number=text_data_json['own_user_number']).contact_name
                    except PhoneBook.DoesNotExist:
                        contact_name = profile.mobile
                    message_count = profile.message_count_private(ch_name)
                    if text_data_json['status'] is True:
                        message = 'typing'
                    else:
                        message = profile.last_message_private(ch_name)
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        profile.home_channel_name,{
                            'type': 'send_notification_to_home',
                            'message': message,
                            'message_type': 'Notification',
                            'channel_room_name': text_data_json['room_channel_name'],
                            'own_user_number': text_data_json['own_user_number'],
                        })
        except ChannelVilla.DoesNotExist:
            pass

    @database_sync_to_async
    def other_channels_public(self, text_data_json):
        auth_user = Profile.objects.get(mobile__iexact=text_data_json['own_user_number'])
        ch_name = ChannelVilla.objects.get(channel_name_main=text_data_json['room_channel_name'])
        try:
            channel_bind = ChannelBindingIdentity.objects.filter(channel_name=ch_name)
            for ch_b in channel_bind:
                if ch_b.connected_receiver != auth_user.user:
                    profile = Profile.objects.get(user=ch_b.connected_receiver)
                    try:
                        contact_name = PhoneBook.objects.get(phone_owner=ch_b.connected_receiver, number=text_data_json['own_user_number']).contact_name
                    except PhoneBook.DoesNotExist:
                        contact_name = profile.mobile
                    message_count = profile.message_count_public(ch_name, profile.user)
                    print(message_count)
                    if text_data_json['status'] is True:
                        message = '%s is typing'%contact_name
                    else:
                        message = profile.last_message_private(ch_name)
                        message = '%s : %s'%(contact_name, message)
                    # print(message)
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        profile.home_channel_name,{
                            'type': 'send_notification_to_home',
                            'message': message,
                            'message_type': 'Notification',
                            'channel_room_name': text_data_json['room_channel_name'],
                            'own_user_number': text_data_json['own_user_number'],
                        })
        except ChannelVilla.DoesNotExist:
            pass

    # Receive message from room group
    #This is sent according to the number of connect consumers
    async def send_typing_message(self, event):
        status = event['status']
        file_type = event['file_type']
        home_channel_name = event['home_channel_name']
        own_user_number = event['own_user_number']
        # room_channel_name = event['room_channel_name']

        await self.send(text_data=json.dumps({
            'file_type': file_type,
            'status': status,
            'own_user_number': own_user_number,
            'home_channel_name': home_channel_name
            # 'room_channel_name': room_channel_name,
        }))


class FeedbackChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'feedback_%s' % self.room_name
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        await self.reply_instance()

    @database_sync_to_async
    def reply_instance(self):
        ch_name = ChannelBindingIdentity.objects.filter(channel_name__channel_name_main=self.room_name).exclude(connected_receiver=self.scope['user'])
        own_user_number = ''
        for ch in ch_name:
            room_mate_number = ch.connected_receiver.username
        msr = MarkAsRead.objects.filter(channel_name__channel_name_main=self.room_name, message_read=False, read_by=self.scope['user']).count()
        if msr > 0:
            channel_layer = get_channel_layer()
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'send.feedback',
                    'own_user_number': room_mate_number,
                    'file_type': 'Text',
                    'feedback_state': 'read',
                    'room_channel_name': self.room_name
                }
            )
            async_mark_as_read_views.delay(self.room_name, self.scope['user'].username)


    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        own_user_number = text_data_json['own_user_number']
        file_type = text_data_json['file_type']
        feedback_state = text_data_json['feedback_state']
        room_channel_name = text_data_json['room_channel_name']
        # message_id = text_data_json['message_id']
        print('@@@@@')
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'send.feedback',
                'own_user_number': own_user_number,
                'file_type': file_type,
                'feedback_state': feedback_state,
                'room_channel_name': room_channel_name
            }
        )
        # async_mark_as_read.delay(room_channel_name, file_type)

    async def send_feedback(self, event):
        own_user_number = event['own_user_number']
        file_type = event['file_type']
        feedback_state = event['feedback_state']
        # message_id = event['message_id']
        # room_channel_name = event['room_channel_name']

        await self.send(text_data=json.dumps({
            'own_user_number': own_user_number,
            'feedback_state': feedback_state,
            'file_type': file_type,
            # 'message_id': message_id,
            # 'room_channel_name': room_channel_name,
        }))


class PublicChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s_public' % self.room_name
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        file_type = text_data_json['file_type']
        message = text_data_json['message']
        message_id = text_data_json['message_id']
        time_stamp = text_data_json['time_stamp']
        room_channel_name = text_data_json['room_channel_name']
        home_channel_name = text_data_json['home_channel_name']
        own_user_number = text_data_json['own_user_number']

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat.message',
                'file_type': file_type,
                'message': message,
                'message_id': message_id,
                'room_channel_name': room_channel_name,
                'time_stamp': time_stamp,
                'home_channel_name': home_channel_name,
                'own_user_number': own_user_number,
            }
        )
        send_message_task.delay(text_data_json)
        await self.other_channels(text_data_json)

    @database_sync_to_async
    def other_channels(self, text_data_json):
        # print('@@@@')
        auth_user = Profile.objects.get(mobile__iexact=text_data_json['own_user_number'])
        ch_name = ChannelVilla.objects.get(channel_name_main=text_data_json['room_channel_name'])
        channel_bind = ChannelBindingIdentity.objects.filter(channel_name=ch_name)
        for ch_b in channel_bind:
            if ch_b.connected_receiver != auth_user.user:
                profile = Profile.objects.get(user=ch_b.connected_receiver)
                try:
                    contact_name = PhoneBook.objects.get(phone_owner=ch_b.connected_receiver, number=text_data_json['own_user_number']).contact_name
                except PhoneBook.DoesNotExist:
                    contact_name = profile.mobile
                # print(profile.home_channel_name)
                grp = GroupChatRoom.objects.get(channel_name=ch_name)
                message_count = grp.message_count(profile.user)
                message = '%s : %s'%(contact_name, text_data_json['message'])
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    profile.home_channel_name,{
                        'type': 'send_notification_to_frontend',
                        'channel_room_name': ch_b.channel_name.channel_name_main,
                        'room_name_image': grp.cover_image.url,
                        'room_name': grp.chat_room_name,
                        'message': message,
                        'message_count': message_count,
                        'message_type': 'Message',
                        'message_time': timezone.now().strftime('%-I:%M %p')
                    })


    # Receive message from room group
    #This is sent according to the number of connect consumers
    async def chat_message(self, event):
        file_type = event['file_type']
        message = event['message']
        message_id = event['message_id']
        time_stamp = event['time_stamp']
        room_channel_name = event['room_channel_name']
        home_channel_name = event['home_channel_name']
        own_user_number = event['own_user_number']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'home_channel_name': home_channel_name,
            'message_id': message_id,
            'room_channel_name': room_channel_name,
            'time_stamp': time_stamp,
            'file_type': file_type,
            'own_user_number': own_user_number,
        }))


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = self.room_name
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'message': message,
            }
        )

    # Receive message from room group
    #This is sent according to the number of connect consumers
    async def chat_message(self, event):
        message = event['message']

        # print('@@@@')
        await self.send(text_data=json.dumps({
            'message': message,
        }))

    async def send_message_to_frontend(self, event):
        message = event['message']

        await self.send(text_data=json.dumps({
            'message': message,
            # 'message_id': message_id
        }))

class EventConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = self.room_name
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )
        # print("DISCONNECED CODE: ",code)

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        own_user_number = text_data_json['own_user_number']
        channel_room_name = text_data_json['channel_room_name']
        feedback = text_data_json['feedback']
        feedback_state = text_data_json['feedback_state']

        # print('@@@@')

        # async_to_sync(self.channel_layer.group_send)(
        #     self.room_group_name,{
        #         "type": 'send_message_to_frontend',
        #         "message": message
        #     }
        # )

        # channel_layer = get_channel_layer()
        # async_to_sync(channel_layer.group_send)(
        #         'feedback_%s' %channel_room_name,
        #     {
        #           'type': 'send_feedback',
        #           'feedback_state': feedback_state,
        #           'file_type': file_type,
        #           'own_user_number': own_user_number,
        #           # 'channel_room_name': data.channel_room_name,
        #     }
        # )

    def send_feedback(self, event):
        # message_id = event['message_id']
        # room_channel_name = event['room_channel_name']
        own_user_number = event['own_user_number']
        file_type = event['file_type']
        feedback_state = event['feedback_state']

        self.send(text_data=json.dumps({
            'own_user_number': own_user_number,
            'feedback_state': feedback_state,
            'file_type': file_type,
            # 'message_id': message_id,
            # 'room_channel_name': room_channel_name,
        }))

    def send_notification_to_frontend(self,event):
        # Receive message from room group
        message = event['message']
        room_name = event['room_name']
        room_name_image = event['room_name_image']
        message_count = event['message_count']
        channel_room_name = event['channel_room_name']
        message_time = event['message_time']
        message_type = event['message_type']

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'room_name_image': room_name_image,
            'room_name': room_name,
            'message': message,
            'channel_room_name': channel_room_name,
            'message_count': message_count,
            'message_time': message_time,
            'message_type': message_type,
        }))

    def send_notification_to_home(self,event):
        own_user_number = event['own_user_number']
        message = event['message']
        channel_room_name = event['channel_room_name']
        message_type = event['message_type']
        own_user_number = event['own_user_number']

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'message': message,
            'message_type': message_type,
            'channel_room_name': channel_room_name,
            'own_user_number': own_user_number,
        }))

def event_triger(value):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'event_sharif',
        {
            'type': 'send_message_to_frontend',
            'message': "event_trigered_from_views"
        }
    )


# threading.Thread(target=event_triger, args=('value',)).start()
