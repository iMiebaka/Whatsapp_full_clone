from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/notication_zone/(?P<room_name>\w+)/$', consumers.EventConsumer.as_asgi()),
    re_path(r'ws/reply-feedback/(?P<room_name>\w+)/$', consumers.FeedbackChatConsumer.as_asgi()),
    re_path(r'ws/public_chat/(?P<room_name>\w+)/$', consumers.PublicChatConsumer.as_asgi()),
    re_path(r'ws/private_chat/(?P<room_name>\w+)/$', consumers.PrivateChatConsumer.as_asgi()),
    re_path(r'ws/typing-notification/(?P<room_name>\w+)/$', consumers.ChatConsumer_typing.as_asgi()),
    # re_path(r'ws/notication_zone/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
    # re_path(r'ws/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
]
