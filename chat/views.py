from django.shortcuts import render, redirect
from .models import GroupChatRoom, ChannelVilla, ChannelBindingIdentity, Messages, MarkAsRead
from django.contrib import messages
from accounts.models import PhoneBook
import json
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from accounts.models import CurrentlyBindedContact, Profile
from django.http import JsonResponse
import os
import base64
from django.core.files.uploadedfile import SimpleUploadedFile
from .tasks import async_mark_as_read_views
from time import sleep

# Create your views here.
@login_required
def index(request):
    connected_channels = ChannelBindingIdentity.objects.filter(connected_receiver=request.user).order_by('-created_on')
    # print(connected_channels)
    public_chat = []
    private_chat = []
    for ch in connected_channels:
        if ch.channel_name_type == 'public':
            public_chat.append(ch.channel_name)
        if ch.channel_name_type == 'private':
            private_chat.append(ch.channel_name.channel_name_main)
    public_rooms = GroupChatRoom.objects.filter(channel_name__in=public_chat)
    # print(request.user.id)
    # print(private_chat)
    # print(request.user.profile.home_channel_name)
    user_list = []
    cbc_qs = CurrentlyBindedContact.objects.filter(
        app_runner=request.user,
        channel_name__in=private_chat)
    for cbc in cbc_qs:
        profile = Profile.objects.get(home_channel_name=cbc.contact_channel)
        user_list.append(profile.user)
    private_rooms = User.objects.filter(username__in=user_list)
    # print(request.user.profile.home_channel_name)
    content = {
        'connected_channels':connected_channels,
        'public_rooms':public_rooms,
        'private_rooms':private_rooms,
        'home_channel_name':request.user.profile.home_channel_name
    }
    return render(request, 'chat/home.html', content)


@login_required
def group_room(request, room_name):
    own_user_number = User.objects.get(username=request.user).username
    try:
        channel_name = ChannelVilla.objects.get(channel_name_main=room_name)
        group_info = GroupChatRoom.objects.get(channel_name=channel_name)
    except (ChannelVilla.DoesNotExist, GroupChatRoom.DoesNotExist):
        messages.error(request, 'Chat room is unavaiable to you')
        return redirect('chat_zone:index')

    try:
        room_mates = ChannelBindingIdentity.objects.filter(channel_name=channel_name)
    except:
        messages.error(request, 'Could not get members of chatroom')
        # return redirect('chat_zone:index')
    rm_list = []
    rm_list.append('You')
    for room_mate in room_mates:
        try:
            user = User.objects.get(username=room_mate.connected_receiver)
            ph_book = PhoneBook.objects.get(number__iexact=str(user.username))
            if user != request.user:
                rm_list.append(str(ph_book.contact_name))
        except PhoneBook.DoesNotExist:
            if user != request.user:
                rm_list.append(str(room_mate.connected_receiver))
    home_channel_name = Profile.objects.get(user=request.user).home_channel_name
    group_members = str(rm_list[0:3])
    group_members = group_members.replace('[','').replace(']','').replace("'","")
    # chat_messages = Messages.objects.filter(channel_name=ch_name).order_by('created_on')[:20]
    # try:
    ph_list = PhoneBook.objects.filter(phone_owner=request.user).values().values_list('contact_name', 'number')
    print(json.dumps(list(ph_list)))

    ch_name = ChannelVilla.objects.get(channel_name_main=room_name)
    chat_messages = Messages.objects.filter(channel_name=ch_name)
    # messages = reversed(room.messages.order_by('-created_on')[:50])

    # msr = MarkAsRead.objects.filter(channel_name=ch_name, message_delivered=False, read_by=request.user)
    # for mr in msr:
    #     mr.message_unread = True
    #     mr.message_delivered = True
    #     mr.save()

    async_mark_as_read_views.delay(room_name, request.user.username)

    # except:
    #     chat_messages = ''

    if len(rm_list) > 3:
        group_members = '%s...'%group_members
    content = {
        'group_members': group_members,
        'room_name': room_name,
        'group_name': group_info,
        'own_user_number': own_user_number,
        'home_channel_name': home_channel_name,
        'chat_messages': chat_messages,
        'phonebook': json.dumps(list(ph_list))

    }
    return render(request, 'chat/public_chat_space.html', content)


@login_required
def private_room(request, room_name):
    # name_of_your_function.delay(10)
    try:
        local_storage = CurrentlyBindedContact.objects.get(app_runner=request.user, contact_channel=request.user.profile.home_channel_name, channel_name=room_name)
    except CurrentlyBindedContact.DoesNotExist:
        # local_storage = CurrentlyBindedContact.objects.get(app_runner=request.user, channel_name=room_name)
        try:
            local_storage = CurrentlyBindedContact.objects.get(app_runner=request.user, channel_name=room_name)
        except:
            messages.error(request, 'Unauthorized access to room')
            return redirect('chat_zone:index')
    profile = Profile.objects.get(home_channel_name=local_storage.contact_channel)
    personal_channel_add = Profile.objects.get(user=request.user)
    if profile.online != True:
        status = profile.last_seen_algorithm
    else:
        status = 'Online'
    if profile.contact_name is None:
        contact_name = profile.mobile
    else:
        contact_name = profile.contact_name
    own_user_number = User.objects.get(username=request.user).username
    # print(personal_channel_add.home_channel_name)
    # print(local_storage.contact_channel)
    # chat_message = chat_message[chat_message:20]
    # chat_messages = Messages.objects.filter(channel_name=ch_name).reverse().order_by('-created_on')[0:20]
    # print(json.dumps(list(ph_list)))
    ph_list = PhoneBook.objects.filter(phone_owner=request.user).values().values_list('contact_name', 'number')
    chat_messages = Messages.objects.filter(channel_name__channel_name_main=room_name)
    # messages = reversed(room.messages.order_by('-created_on')[:50])
    # print(chat_messages)
    # try:
    #     ch_name = ChannelVilla.objects.get(channel_name_main=room_name)
    #     msr = MarkAsRead.objects.filter(channel_name=ch_name, message_read=False, read_by=request.user)
    #     for mr in msr:
    #         mr.message_read = True
    #         mr.message_delivered = True
    #         mr.save()
    # except:
    #     chat_messages = ''
    # async_mark_as_read_views.delay(room_name, request.user.username)

    content = {
        'room_name': room_name,
        'status': status,
        'own_user_number': own_user_number,
        'home_channel_name': personal_channel_add.home_channel_name,
        'room_mate_home_channel_name': local_storage.contact_channel,
        'contact_name': contact_name,
        'profile_picture': profile.cover_image,
        'chat_messages': chat_messages,
        'phonebook': json.dumps(list(ph_list))
    }
    return render(request, 'chat/private_chat_space.html', content)

@login_required
def upload_voice_note(request):
    if request.is_ajax and request.method == 'POST':
        channel_name = request.POST['channel_name']
        message_id = request.POST['message_id']
        media_file = request.FILES['voice_note']
        print(type(media_file))
        print(channel_name)
        print(message_id)
        # with open("voice_note.wav", "wb") as fh:
        #     fh.write(base64.decodebytes(media_file))

        # print(fh)

        # suf = SimpleUploadedFile('uploaded_file.wav', image_output.read(), content_type='audio/wav')
        # print(suf)

        # filename, ext = os.path.splitext(self.event['media_file'].lower())
        # filename = "%s.%s" %(slugify(filename), timezone.now())
        # hs_index = hashlib.md5(filename.encode()).hexdigest()
        # message = Messages.objects.create(
        #     sent_by=request.user,
        #     media = '🎙 Voice note',
        #     media_file = text_data_json['message'],
        #     file_type = text_data_json['file_type'],
        #     channel_name = ch_name,
        #     message_id = text_data_json['message_id'],
        #     # message_state = None,
        # ).save()
        # msr = MarkAsRead.objects.create(
        #     message = message,
        #     channel_name = ch_name,
        #     read_by = self.scope['user']
        # ).save()
        # message.message_unread = msr
        # message.save()

        try:
            # message = Messages.objects.create(
            #     sent_by=request.user,
            #     media = '🎙 Voice note',
            #     file_type = media_file,
            #     channel_name = channel_name,
            #     message_id = message_id,
            # )
            pass
            content = {
                'data': True,
                'data': True,
                'data': True,
                'data': True,
            }
        except:
            pass

    return JsonResponse(content)

def message_read(request):
    # sleep(1)
    if request.method == 'POST':
        room_channel_name = request.POST['room_channel_name']
        message_delivered = request.POST['message_delivered']
        message_read = request.POST['message_read']
        file_type = request.POST['file_type']
        print(room_channel_name)
        # async_mark_as_read_views.delay(room_channel_name, request.user.username)

        mess = Messages.objects.filter(channel_name__channel_name_main=room_channel_name).last()
        content = {
            'data': False
        }
        if file_type == 'Text':
            mrk_ini = MarkAsRead.objects.get(message=mess, read_by=request.user, media_type='Text')
            mrk_ini.message_read = message_read
            mrk_ini.message_delivered = message_delivered
            mrk_ini.save()
            content = {
                'data': True
            }
        return JsonResponse(content)
