from django.urls import path
from . import views

app_name='chat_zone'

urlpatterns = [
    path('', views.index, name='index'),
    path('ajax/upload-voice-note/', views.upload_voice_note, name='upload_voice_note'),
    path('ajax/message-read/', views.message_read, name='message_read'),
    path('public/<str:room_name>/', views.public_room, name='public_room'),
    path('private/<str:room_name>/', views.private_room, name='private_room'),
    path('ajax/111/', views.check_fetch, name='check_fetch')
]
