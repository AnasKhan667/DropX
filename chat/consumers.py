import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import ChatRoom, Message


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_room_id = self.scope['url_route']['kwargs']['room_uuid']
        self.room_group_name = f'chat_{self.chat_room_id}'

        print(f"🔹 WebSocket connect request: Room ID = {self.chat_room_id}, User = {self.scope['user']}")

        if await self.is_valid_user():
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()

            print(f"Connection accepted for room {self.chat_room_id}")
        else:
            print("Unauthorized user tried to connect")
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        print(f"Disconnected from room {self.chat_room_id}")

    async def receive(self, text_data):
        if not text_data.strip():
            print("Empty message received — ignoring")
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            print(f"Invalid JSON: {text_data}")
            return

        content = data.get('content', '').strip()
        if not content:
            await self.send(json.dumps({"error": "Missing 'content' field"}))
            print("Missing 'content' field in received data")
            return

        sender = self.scope['user']
        receiver = await self.get_receiver(sender)
        if not receiver:
            await self.send(json.dumps({"error": "Receiver not found"}))
            print("Receiver not found for this chat room")
            return

        print(f"New message from {sender.id} → {receiver.id}: {content}")

        message = await self.save_message(sender, receiver, content)

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

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message_id': event['message_id'],
            'content': event['content'],
            'sender_id': event['sender_id'],
            'receiver_id': event['receiver_id'],
            'created_at': event['created_at'],
        }))
        print(f"Broadcasted: {event['content']}")

    @database_sync_to_async
    def is_valid_user(self):
        try:
            user = self.scope['user']
            if user is None:
                print("User is None - authentication failed")
                return False
            
            chat_room = ChatRoom.objects.get(chat_room_id=self.chat_room_id)
            delivery = chat_room.delivery
            
            # Check if user is the sender
            is_sender = user.id == delivery.sender_id.id
            
            # Check if user is the driver (via driver_id field)
            is_driver_direct = delivery.driver_id and user.id == delivery.driver_id.id
            
            # Check if user is the driver (via driver_post_id)
            is_driver_via_post = delivery.driver_post_id and user.id == delivery.driver_post_id.user.id
            
            # Allow any driver if no driver assigned yet (for open deliveries)
            is_any_driver_for_open = (
                user.role == 'driver' and 
                delivery.driver_id is None and 
                delivery.driver_post_id is None
            )
            
            valid = is_sender or is_driver_direct or is_driver_via_post or is_any_driver_for_open
            
            print(f"User validation for {user}: {valid}")
            print(f"  - is_sender: {is_sender}, is_driver_direct: {is_driver_direct}, is_driver_via_post: {is_driver_via_post}, is_any_driver_for_open: {is_any_driver_for_open}")
            return valid
        except ChatRoom.DoesNotExist:
            print("ChatRoom not found")
            return False
        except Exception as e:
            print(f"Error in is_valid_user: {e}")
            return False

    @database_sync_to_async
    def get_receiver(self, sender):
        try:
            chat_room = ChatRoom.objects.get(chat_room_id=self.chat_room_id)
            delivery = chat_room.delivery

            # If sender is the package sender, receiver is the driver
            if sender.id == delivery.sender_id.id:
                # First check driver_id (direct driver assignment)
                if delivery.driver_id:
                    return delivery.driver_id
                # Then check driver_post_id
                if delivery.driver_post_id:
                    return delivery.driver_post_id.user
                return None
            
            # If sender is the driver (via driver_id)
            if delivery.driver_id and sender.id == delivery.driver_id.id:
                return delivery.sender_id
            
            # If sender is the driver (via driver_post_id)
            if delivery.driver_post_id and sender.id == delivery.driver_post_id.user.id:
                return delivery.sender_id

            # If sender is any driver and delivery is open
            if sender.role == 'driver' and delivery.driver_id is None and delivery.driver_post_id is None:
                return delivery.sender_id

            return None
        except ChatRoom.DoesNotExist:
            return None
        except Exception as e:
            print(f"Error in get_receiver: {e}")
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
        print(f"Saved message: {message.content}")
        return message






















# import json
# from channels.generic.websocket import AsyncWebsocketConsumer
# from channels.db import database_sync_to_async
# from .models import ChatRoom, Message
# from accounts.models import CustomUser
# from django.utils import timezone

# class ChatConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.chat_room_id = self.scope['url_route']['kwargs']['room_uuid']
#         self.room_group_name = f'chat_{self.chat_room_id}'

#         # Verify user is part of the chat room
#         if await self.is_valid_user():
#             await self.channel_layer.group_add(self.room_group_name, self.channel_name)
#             await self.accept()
#         else:
#             await self.close()

#     async def disconnect(self, close_code):
#         await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

#     async def receive(self, text_data):
#         if not text_data:
#             print("⚠️ Empty message received — ignoring")
#             return

#         try:
#             data = json.loads(text_data)
#         except json.JSONDecodeError:
#             print("❌ Invalid JSON:", text_data)
#             return

#         content = data.get('content')
#         sender_id = data.get('sender_id')
#         receiver_id = data.get('receiver_id')

#         if not all([content, sender_id, receiver_id]):
#             print("⚠️ Missing required fields:", data)
#             return

#         message = await self.save_message(sender_id, receiver_id, content)

#         await self.channel_layer.group_send(
#             self.room_group_name,
#             {
#                 'type': 'chat_message',
#                 'message_id': str(message.message_id),
#                 'content': content,
#                 'sender_id': sender_id,
#                 'receiver_id': receiver_id,
#                 'created_at': message.created_at.isoformat(),
#             }
#         )


#     async def chat_message(self, event):
#         await self.send(text_data=json.dumps({
#             'message_id': event['message_id'],
#             'content': event['content'],
#             'sender_id': event['sender_id'],
#             'receiver_id': event['receiver_id'],
#             'created_at': event['created_at'],
#         }))

#     @database_sync_to_async
#     def is_valid_user(self):
#         try:
#             chat_room = ChatRoom.objects.get(chat_room_id=self.chat_room_id)
#             user = self.scope['user']
#             return user in [chat_room.delivery.sender_id, chat_room.delivery.driver_id]
#         except ChatRoom.DoesNotExist:
#             return False

#     @database_sync_to_async
#     def save_message(self, sender_id, receiver_id, content):
#         chat_room = ChatRoom.objects.get(chat_room_id=self.chat_room_id)
#         sender = CustomUser.objects.get(id=sender_id)
#         receiver = CustomUser.objects.get(id=receiver_id)
#         message = Message.objects.create(
#             chat_room=chat_room,
#             sender=sender,
#             receiver=receiver,
#             content=content,
#             created_at=timezone.now()
#         )
#         return message