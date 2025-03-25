import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, Message, UserChat
from asgiref.sync import sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Kết nối WebSocket"""
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f"chat_{self.room_name}"
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
    # khi có client ngắt kết nối
    async def disconnect(self, close_code):
        """Ngắt kết nối WebSocket"""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    # khi nhận được tín hiệu gửi đến từ client
    async def receive(self, text_data):
        """Nhận tin nhắn hoặc tín hiệu cuộc gọi"""
        try:
            # lấy dữ liệu nhận được
            data = json.loads(text_data)
            event_type = data.get("type")
            sender_value = data.get("sender")
            # néu ko nhận được username của người gửi thì sẽ báo lỗi
            if not sender_value:
                await self.send(text_data=json.dumps({
                    "type": "error",
                    "message": "Không có sender trong dữ liệu."
                }))
                return
            # nếu kiểu sự kiện là chat_message thì thực hiện lấy dữ liệu từ data và lấy object dựa trên dữ liệu
            if event_type == "chat_message":   
                # Xử lý tin nhắn chat thông thường
                message_content = data.get("message", "")
                image_data = data.get("image")
                file_data = data.get("file")
                sender_username = sender_value
                room_name = self.scope['url_route']['kwargs']['room_name']

                room = await database_sync_to_async(ChatRoom.objects.get)(name=room_name)
                sender_user = await database_sync_to_async(UserChat.objects.get)(username=sender_username)
                receiver_user = await database_sync_to_async(
                    lambda: room.users.exclude(id=sender_user.id).first()
                )()

                if not receiver_user:
                    await self.send(text_data=json.dumps({
                        "type": "error",
                        "message": "Không tìm thấy người nhận trong phòng."
                    }))
                    return
                # lưu tin nhắn vào cơ sở dữ liệu
                await self.save_message(room, sender_user, receiver_user, message_content, image_data, file_data)
                # gửi tin nhắn đến người nhận
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message_content,
                        "image": image_data,
                        "file": file_data,
                        'sender': sender_user.username,
                    }
                )
            elif event_type == "call_offer":
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "send_call_offer",
                        "offer": data.get("offer"),
                        "sender": sender_value
                    }
                )
            elif event_type == "share_offer":
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "send_share_offer",
                        "offer": data.get("offer"),
                        "sender": sender_value
                    }
                )
            elif event_type == "call_answer":
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "send_call_answer",
                        "answer": data.get("answer"),
                        "sender": sender_value
                    }
                )
            elif event_type == "ice_candidate":
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "send_ice_candidate",
                        "candidate": data.get("candidate"),
                        "sender": sender_value
                    }
                )
            elif event_type == "end_connection":
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "send_end_connection",
                        "sender": sender_value,
                        "receiver": data.get("receiver")
                    }
                )
            
        except ChatRoom.DoesNotExist:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": f"Phòng '{room_name}' không tồn tại."
            }))
        except UserChat.DoesNotExist:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": f"Người dùng '{sender_username}' không tồn tại."
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": f"Lỗi xử lý: {str(e)}"
            }))

    async def send_call_offer(self, event):
        """Gửi lời mời gọi đến user khác"""
        await self.send(text_data=json.dumps({
            "type": "call_offer",
            "offer": event.get("offer"),
            "sender": event.get("sender")
        }))

    async def send_share_offer(self, event):
        """Gửi lời mời gọi đến user khác"""
        await self.send(text_data=json.dumps({
            "type": "share_offer",
            "offer": event.get("offer"),
            "sender": event.get("sender")
        }))

    async def send_call_answer(self, event):
        """Gửi câu trả lời cho cuộc gọi"""
        await self.send(text_data=json.dumps({
            "type": "call_answer",
            "answer": event.get("answer"),
            "sender": event.get("sender")
        }))

    async def send_end_connection(self, event):
        """Gửi yêu cầu kết thúc cho cuộc gọi"""
        await self.send(text_data=json.dumps({
            "type": "end_connection",
            "sender": event.get("sender"),
            "receiver": event.get("receiver")
        }))

    async def send_ice_candidate(self, event):
        """Gửi ICE candidate để hỗ trợ kết nối WebRTC"""
        await self.send(text_data=json.dumps({
            "type": "ice_candidate",
            "candidate": event.get("candidate"),
            "sender": event.get("sender")
        }))

    async def chat_message(self, event):
        """Gửi tin nhắn chat đến tất cả thành viên trong phòng"""
        message = event['message']
        sender_username = event['sender']
        image = event.get("image", None)
        file = event.get("file", None)
        try:
            sender_user = await sync_to_async(UserChat.objects.get)(username=sender_username)
            await self.send(text_data=json.dumps({
                'message': message,
                'type' : "chat_message",
                'sender': sender_user.username,
                "image": image,
                "file": file,
                'avatar': sender_user.profile_picture.url if sender_user.profile_picture else "",
            }))
        except UserChat.DoesNotExist:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": f"Người dùng '{sender_username}' không tồn tại."
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": f"Lỗi gửi tin nhắn: {str(e)}"
            }))

    @sync_to_async
    def save_message(self, room, sender, receiver, message, image, file):
        try:
            Message.objects.create(
                room_name=room,
                sender=sender,
                receiver=receiver,
                content=message,
                image=image,
                file=file
            )
        except Exception as e:
            print(f"Error saving message: {e}")
            raise