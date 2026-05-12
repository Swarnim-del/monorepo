from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.conversation_id = int(self.scope["url_route"]["kwargs"]["conversation_id"])
        user = self.scope["user"]
        if isinstance(user, AnonymousUser) or not user.is_authenticated:
            await self.close(code=4401)
            return
        if not await self.is_member():
            await self.close(code=4403)
            return
        self.room_group_name = f"chat_{self.conversation_id}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    @database_sync_to_async
    def is_member(self):
        from .models import ConversationMember

        return ConversationMember.objects.filter(
            conversation_id=self.conversation_id,
            user_id=self.scope["user"].id,
        ).exists()

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

    async def receive_json(self, content, **kwargs):
        body = (content.get("message") or "").strip()
        if not body:
            return
        saved = await self.persist_message(body)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat.event",
                "id": saved["id"],
                "author": saved["author"],
                "body": saved["body"],
                "created_at": saved["created_at"],
            },
        )

    @database_sync_to_async
    def persist_message(self, body):
        from django.contrib.auth import get_user_model
        from .models import Message

        msg = Message.objects.create(
            conversation_id=self.conversation_id,
            author_id=self.scope["user"].id,
            body=body,
        )
        author = get_user_model().objects.get(pk=self.scope["user"].id)
        return {
            "id": msg.id,
            "author": author.get_username(),
            "body": msg.body,
            "created_at": msg.created_at.isoformat(),
        }

    async def chat_event(self, event):
        await self.send_json(
            {
                "type": "message",
                "id": event["id"],
                "author": event["author"],
                "body": event["body"],
                "created_at": event["created_at"],
            }
        )
