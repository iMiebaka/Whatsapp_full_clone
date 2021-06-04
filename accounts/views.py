from .models import Profile, PhoneBook, CurrentlyBindedContact
from mysite.config import OTP_KEY
import pyotp
import base64
from django.shortcuts import render
import re
import string
import hashlib
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.contrib.auth import (login as auth_login,  authenticate, logout)
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from accounts.models import Profile
from django.contrib.auth import update_session_auth_hash
from django.utils import timezone
from datetime import datetime
from django.utils.http import urlsafe_base64_encode
from django.contrib import messages
from chat.models import GroupChatRoom, ChannelVilla, ChannelBindingIdentity
from django.http import JsonResponse

def signup(request):
    if request.method == 'POST':
        phonenumber = request.POST['phonenumber']
        country = request.POST['country']
        username = request.POST['username']
        cover_image = request.FILES['cover_image']
        home_channel_name_token = phonenumber + str(timezone.now())
        hash_channel_name = hashlib.md5(home_channel_name_token.encode())
        home_channel_name = hash_channel_name.hexdigest()
        email_address = '%s@whatsapp.com'%phonenumber
        if phonenumber == '' or country == '':
            messages.error(request,'Please make sure phone number and country are provided')
            return render(request, 'signup.html')

        try:
            user = User.objects.get(username__iexact=phonenumber)
            if user.is_active == False:
                add_number = Profile.objects.get(user=user)
                add_number.counter += 1  # Update Counter At every Call
                add_number.isVerified=False
                if cover_image !=  None:
                    add_number.cover_image=request.FILES['cover_image']
                add_number.save()
                rt_valu = str(phonenumber) + str(datetime.date(datetime.now())) + OTP_KEY
                try:
                    key = base64.b32encode(rt_valu.encode())  # Key is generated
                    OTP = pyotp.HOTP(key)  # HOTP Model for OTP is created
                    print('Your OTP is '+OTP.at(add_number.counter))
                    messages.success(request, 'OTP has been sent to your modile device')
                    correspondent = redirect('accounts:verify_account_sms')
                    correspondent.set_cookie('whatsapp_clone', phonenumber , max_age=600)
                    return correspondent
                except:
                    messages.error(request,'Unable to complete Registration')
                    return render(request, 'signup.html')
            else:
                messages.error(request, "Username is already taken")
                return render(request, 'signup.html')
        except User.DoesNotExist:
            try:
                user = User.objects.create_user(
                    phonenumber,
                    email_address,
                    '12345'
                )
                user.first_name = username
                user.is_active = False
                user.save()
                add_number = Profile.objects.get(user=user)
                add_number.mobile = phonenumber
                add_number.location = country
                add_number.home_channel_name = home_channel_name
                add_number.counter += 1  # Update Counter At every Call
                add_number.isVerified=False
                if cover_image != None:
                    add_number.cover_image=cover_image
                add_number.save()
                rt_valu = str(phonenumber) + str(datetime.date(datetime.now())) + OTP_KEY
                try:
                    key = base64.b32encode(rt_valu.encode())  # Key is generated
                    OTP = pyotp.HOTP(key)  # HOTP Model for OTP is created
                    print('Your OTP is '+OTP.at(add_number.counter))
                    messages.success(request, 'OTP has been sent to your modile device')
                    correspondent = redirect('accounts:verify_account_sms')
                    correspondent.set_cookie('whatsapp_clone', phonenumber , max_age=600)
                    return correspondent
                except:
                    user.delete()
                    print('Unable to complete Registration')
                    messages.error(request,'Unable to complete Registration')
                    return render(request, 'signup.html')
            except:
                user.delete()
                print('Something went wrong with request')
                messages.error(request, 'Something went wrong with request')
                return render(request, 'signup.html')
    if request.method == 'GET':
        return render(request, 'signup.html')

def login(request):
    if request.user.is_authenticated:
        return redirect('chat_zone:index')
    else:
        if request.method == 'POST':
            phonenumber = request.POST['phonenumber']
            raw_password = request.POST['phonenumber']
            try:
                profile = Profile.objects.get(mobile__iexact=phonenumber).user_id
                username = User.objects.get(id=profile).username
            except Profile.DoesNotExist:
                messages.error(request, 'User does not exit')
                return render(request, 'login.html')
            user = authenticate(username=username, password='12345')
            user = User.objects.get(id=Profile.objects.get(mobile__iexact=phonenumber).user_id)

            if user is not None:
                try:
                    auth_login(request, user)
                    messages.success(request, 'Login successful')
                    return redirect('chat_zone:index')
                except:
                    messages.error(request, 'Something went wrong with the request')
                    return render(request, 'login.html')
            else:
                messages.error(request, 'User does not exist')
                return render(request, 'login.html')
    if request.method == 'GET':
        return render(request, 'login.html')

def logout_view(request):
    logout(request)
    messages.success(request, "Logged out")
    return redirect('accounts:login')

@login_required
def check_status(request):
    channel_name = request.GET['channel_name']
    try:
        data = Profile.objects.get(home_channel_name=channel_name).avaiablity
    except Profile.DoesNotExist:
        data = None
    content = {
        "data": data
    }
    # print(data)
    return JsonResponse(content)

@login_required
def add_options(request, slider):
    if request.method == 'GET':
        filtered_list = []
        pb_qs = PhoneBook.objects.filter(phone_owner=request.user)
        for user in pb_qs:
            try:
                us = User.objects.get(username__iexact=user.number)
                filtered_list.append(str(us))
            except:
                pass
        contacts = PhoneBook.objects.filter(number__in=filtered_list)
        content = {
        'contacts': contacts,
        'slider':slider
        }
        return render(request, 'add_options.html',content)

@login_required
def add_to_chat(request):
    if request.method == 'GET':
        filtered_list = []
        # chat_channel = []
        channel_name = ''
        us = ''
        pb_qs = PhoneBook.objects.filter(phone_owner=request.user)
        for user in pb_qs:
            try:
                us = User.objects.get(username__iexact=user.number)
                filtered_list.append(str(us))
                try:
                    if us:
                        cbc = CurrentlyBindedContact.objects.get(
                        added_contact_runner=User.objects.get(username=us),
                        app_runner=request.user)
                        # chat_channel.append(str(cbc.channel_name))
                except CurrentlyBindedContact.DoesNotExist:
                    channel_name_token = str(us.profile.home_channel_name) + str(timezone.now()) + str(request.user.profile.home_channel_name)
                    channel_name = hashlib.md5(channel_name_token.encode()).hexdigest()

                    cbc = CurrentlyBindedContact.objects.create(
                        app_runner = request.user,
                        added_contact_runner = User.objects.get(username=us),
                        contact_channel = Profile.objects.get(user=us).home_channel_name,
                        channel_name = channel_name)
            except User.DoesNotExist:
                pass
        # contacts = PhoneBook.objects.filter(number__in=filtered_list)
        # print(contacts)
        # contacts_channel_name = CurrentlyBindedContact.objects.filter(channel_name__in=chat_channel)
        # print(contacts_channel_name)
        contacts_details = User.objects.filter(username__in=filtered_list)
        print(contacts_details)
        content = {
            'contacts_details':contacts_details
        }
        return render(request, 'add_to_chat.html', content)


# 1111
@login_required
def add_contact(request):
    if request.method == 'POST':
        contact_name = request.POST['name']
        phonenumber = request.POST['phonenumber']
        try:
            PhoneBook.objects.get(phone_owner=request.user, number__iexact=phonenumber)
            messages.error(request, "Phone number already exists")
            return redirect('accounts:add_options', 1)
        except PhoneBook.DoesNotExist:
            pb = PhoneBook.objects.create(
                number = phonenumber,
                phone_owner = request.user,
                contact_name = contact_name
            ).save()
            messages.success(request, "%s's number has been saved"%contact_name)
            return redirect('accounts:add_options', 1)

@login_required
def create_group(request):
    if request.method == 'POST':
        group_name = request.POST['group_name']
        group_description = request.POST['group_description']
        cover_image = request.POST['group_image']
        contacts = request.POST.getlist('contact')
        if contacts is "":
            messages.error(request, 'A group is more than one bro...')
            return redirect('accounts:add_options', 2)
        try:
            raw_code = str(request.user) + str(timezone.now()) + str(group_name)
            hash_value = hashlib.md5(raw_code.encode()).hexdigest()
            channel_name_in = ChannelVilla.objects.create(
                channel_name_main = hash_value,
                created_by = request.user)
        except:
            messages.error(request, 'Unable to initiate group')
            return redirect('accounts:add_options', 2)

        try:
            create_group = GroupChatRoom.objects.create(
                chat_room_name = group_name,
                chat_room_description = group_description,
                channel_name = channel_name_in,
                room_id = hash_value).save()
            if cover_image != '':
                create_group.cover_image = request.FILES['group_image']
                create_group.save()
        except:
            channel_name_in.delete()
            messages.error(request, 'The group creation was a flop')
            return redirect('accounts:add_options', 2)

        try:
            channel_bind = ChannelBindingIdentity.objects.create(
            connected_receiver = request.user,
            channel_name = channel_name_in,
            channel_name_type = 'public'
            )
            for contact in contacts:
                registerd_user =  User.objects.get(username__iexact=contact)
                channel_bind_others = ChannelBindingIdentity.objects.create(
                connected_receiver = registerd_user,
                channel_name = channel_name_in,
                channel_name_type = 'public'
                )
            messages.success(request, '%s, has been successfully created'%group_name)
            return redirect('chat_zone:public_room', hash_value)
        except:
            channel_name_in.delete()
            create_group.delete()
            channel_bind.delete()
            if channel_bind_others != None:
                channel_bind_others.delete()
            messages.error(request, 'Unable to add people to the group')
            return redirect('accounts:add_options', 2)


@login_required
def view_profile(request):
    if request.method == 'POST':
        try:
            phonenumber = request.POST['phonenumber']
            raw_password = hashlib.md5(phonenumber.encode()).hash_number.hexdigest()
            cover_image = request.FILES.get('cover_image')
            user_ins = request.user
            changes_made = False
            if phonenumber != '':
                user_ins.username = phonenumber
                user_ins.save()
                changes_made = True

            if raw_password != '':
                user_ins.set_password(raw_password)
                user_ins.save()
                update_session_auth_hash(request, user_ins)
                changes_made = True

            if cover_image != None:
                us_profile = Profile.objects.get(user=user_ins)
                us_profile.cover_image = cover_image
                us_profile.save()
                changes_made = True

            if changes_made:
                messages.success(request,'Profile have been updated successfully!')
            else:
                messages.info(request,'Nothing to updated!')
            return redirect('chat_zone:index')
        except:
            messages.error(request,'Something when wrong')
        return render(request, 'profile.html')

    if request.method == 'GET':
        return render(request, 'profile.html')

def verify_account_sms(request):
    if request.method == 'POST':
        phonenumber = request.COOKIES.get('whatsapp_clone')
        otp = request.POST['otp'].strip()
        try:
            Mobile = Profile.objects.get(mobile__iexact=phonenumber)
        except Profile.DoesNotExist:
            messages.error(request, "User does not exist")  # False Call
            return render(request, 'otp-waiting.html')
        rt_valu = str(phonenumber) + str(datetime.date(datetime.now())) + OTP_KEY
        key = base64.b32encode(rt_valu.encode())  # Generating Key
        OTP = pyotp.HOTP(key)  # HOTP Model
        if Mobile.isVerified:
            messages.error(request, 'OTP is expired')
            return render(request, 'otp-waiting.html')

        if OTP.verify(otp, Mobile.counter):  # Verifying the OTP
            Mobile.isVerified = True
            Mobile.save()
            user = User.objects.get(id=Profile.objects.get(mobile__iexact=phonenumber).user_id)
            user.is_active = True
            user.save()
            auth_login(request, user)
            messages.success(request,'Registration Complete')
            return redirect('chat_zone:index')

    if request.method == 'GET':
        return render(request, 'otp-waiting.html')
