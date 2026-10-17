import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import ChatRoom, Message

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_room_id = self.scope['url_route']['kwargs']['room_uuid']
        self.room_group_name = f'chat_{self.chat_room_id}'

        logger.debug(
            f"WebSocket connect request: Room ID = {self.chat_room_id}, User = {self.scope['user']}"
        )

        if await self.is_valid_user():
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()
            logger.info(f"Connection accepted for room {self.chat_room_id}")
        else:
            logger.warning("Unauthorized user tried to connect to WebSocket.")
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        logger.debug(f"Disconnected from room {self.chat_room_id}")

    async def receive(self, text_data):
        if not text_data.strip():
            logger.debug("Empty message received — ignoring")
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON received: {text_data}")
            return

        # Handle ping/pong for keepalive
        if data.get('type') == 'ping':
            await self.send(json.dumps({'type': 'pong'}))
            return

        content = data.get('content', '').strip()
        if not content:
            await self.send(json.dumps({"error": "Missing 'content' field"}))
            return

        sender = self.scope['user']
        receiver = await self.get_receiver(sender)
        if not receiver:
            await self.send(json.dumps({"error": "Receiver not found"}))
            return

        logger.debug(f"New message from {sender.id} -> {receiver.id}: {content}")

        message = await self.save_message(sender, receiver, content)

        try:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message_id': str(message.message_id),
                    'content': content,
                    'sender_id': str(sender.id),
                    'receiver_id': str(receiver.id),
                    'created_at': message.created_at.isoformat(),
                }
            )
        except Exception as e:
            logger.error(f"Channel layer error (Redis may not be running): {e}")
            # Fall back: deliver only to the current connection
            await self.chat_message({
                'message_id': str(message.message_id),
                'content': content,
                'sender_id': str(sender.id),
                'receiver_id': str(receiver.id),
                'created_at': message.created_at.isoformat(),
            })

    async def chat_message(self, event):
        message_data = {
            'message_id': event['message_id'],
            'content': event['content'],
            'sender_id': event['sender_id'],
            'receiver_id': event['receiver_id'],
            'created_at': event['created_at'],
        }
        if event.get('image'):
            message_data['image'] = event['image']

        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message_data
        }))

    @database_sync_to_async
    def is_valid_user(self):
        try:
            user = self.scope['user']
            if user is None:
                return False

            chat_room = ChatRoom.objects.get(chat_room_id=self.chat_room_id)
            delivery = chat_room.delivery

            is_sender = user.id == delivery.sender_id.id
            is_driver_direct = delivery.driver_id and user.id == delivery.driver_id.id
            is_driver_via_post = (
                delivery.driver_post_id
                and user.id == delivery.driver_post_id.user.id
            )
            # Allow any driver if no driver is yet assigned (open deliveries)
            is_any_driver_for_open = (
                user.role == 'Driver'
                and delivery.driver_id is None
                and delivery.driver_post_id is None
            )

            return is_sender or is_driver_direct or is_driver_via_post or is_any_driver_for_open

        except ChatRoom.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"Error in is_valid_user: {e}")
            return False

    @database_sync_to_async
    def get_receiver(self, sender):
        try:
            chat_room = ChatRoom.objects.get(chat_room_id=self.chat_room_id)
            delivery = chat_room.delivery

            if sender.id == delivery.sender_id.id:
                if delivery.driver_id:
                    return delivery.driver_id
                if delivery.driver_post_id:
                    return delivery.driver_post_id.user
                return None

            if delivery.driver_id and sender.id == delivery.driver_id.id:
                return delivery.sender_id

            if delivery.driver_post_id and sender.id == delivery.driver_post_id.user.id:
                return delivery.sender_id

            # Any driver can message the sender on an open delivery
            if sender.role == 'Driver' and delivery.driver_id is None and delivery.driver_post_id is None:
                return delivery.sender_id

            return None
        except ChatRoom.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error in get_receiver: {e}")
            return None

    @database_sync_to_async
    def save_message(self, sender, receiver, content):
        chat_room = ChatRoom.objects.get(chat_room_id=self.chat_room_id)
        message = Message.objects.create(
            chat_room=chat_room,
            sender=sender,
            receiver=receiver,
            content=content,
            created_at=timezone.now()
        )
        return message