import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, Message
from accounts.models import CustomUser
from django.utils import timezone

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_room_id = self.scope['url_route']['kwargs']['chat_room_id']
        self.room_group_name = f'chat_{self.chat_room_id}'

        # Verify user is part of the chat room
        if await self.is_valid_user():
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        content = data['content']
        sender_id = data['sender_id']
        receiver_id = data['receiver_id']

        # Save message to database
        message = await self.save_message(sender_id, receiver_id, content)

        # Broadcast message to group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message_id': str(message.message_id),
                'content': content,
                'sender_id': sender_id,
                'receiver_id': receiver_id,
                'created_at': message.created_at.isoformat(),
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message_id': event['message_id'],
            'content': event['content'],
            'sender_id': event['sender_id'],
            'receiver_id': event['receiver_id'],
            'created_at': event['created_at'],
        }))

    @database_sync_to_async
    def is_valid_user(self):
        try:
            chat_room = ChatRoom.objects.get(chat_room_id=self.chat_room_id)
            user = self.scope['user']
            return user in [chat_room.delivery.sender_id, chat_room.delivery.driver_id]
        except ChatRoom.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, sender_id, receiver_id, content):
        chat_room = ChatRoom.objects.get(chat_room_id=self.chat_room_id)
        sender = CustomUser.objects.get(id=sender_id)
        receiver = CustomUser.objects.get(id=receiver_id)
        message = Message.objects.create(
            chat_room=chat_room,
            sender=sender,
            receiver=receiver,
            content=content,
            created_at=timezone.now()
        )
        return message