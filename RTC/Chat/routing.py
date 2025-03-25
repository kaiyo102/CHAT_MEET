from django.urls import path
from Chat.consumers import ChatConsumer
from django.urls import re_path

websocket_urlpatterns = [
    # Định nghĩa đường dẫn WebSocket với room_name
    re_path(r'ws/chat/(?P<room_name>\w+)/$', ChatConsumer.as_asgi()),

]