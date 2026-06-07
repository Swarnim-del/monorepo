import uuid
from asgiref.sync import async_to_sync
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import AnonymousUser, User
from django.db.utils import IntegrityError
from django.test import TestCase, TransactionTestCase
from django.urls import reverse

from .consumers import ChatConsumer
from .models import Conversation, ConversationMember, Message


class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password123")

    def test_conversation_creation(self):
        conv = Conversation.objects.create(title="General Chat", created_by=self.user)
        self.assertEqual(conv.title, "General Chat")
        self.assertEqual(conv.created_by, self.user)
        self.assertIsNotNone(conv.invite_token)
        self.assertIsInstance(conv.invite_token, uuid.UUID)
        self.assertEqual(str(conv), "General Chat")

    def test_conversation_member_creation(self):
        conv = Conversation.objects.create(title="General Chat")
        member = ConversationMember.objects.create(conversation=conv, user=self.user)
        self.assertEqual(member.conversation, conv)
        self.assertEqual(member.user, self.user)

    def test_conversation_member_uniqueness(self):
        conv = Conversation.objects.create(title="General Chat")
        ConversationMember.objects.create(conversation=conv, user=self.user)
        with self.assertRaises(IntegrityError):
            ConversationMember.objects.create(conversation=conv, user=self.user)

    def test_message_creation_and_ordering(self):
        conv = Conversation.objects.create(title="General Chat")
        msg1 = Message.objects.create(conversation=conv, author=self.user, body="Hello first!")
        msg2 = Message.objects.create(conversation=conv, author=self.user, body="Hello second!")

        self.assertEqual(msg1.conversation, conv)
        self.assertEqual(msg1.author, self.user)
        self.assertEqual(msg1.body, "Hello first!")

        # Verify default ordering is by created_at ascending
        messages = list(Message.objects.filter(conversation=conv))
        self.assertEqual(messages, [msg1, msg2])


class ViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password123")
        self.other_user = User.objects.create_user(username="otheruser", password="password123")
        self.conv = Conversation.objects.create(title="Public Room", created_by=self.user)
        # Add creator as a member
        self.member = ConversationMember.objects.create(conversation=self.conv, user=self.user)

    def test_signup_view_get(self):
        response = self.client.get(reverse("signup"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/signup.html")

    def test_signup_view_post_valid(self):
        response = self.client.post(
            reverse("signup"),
            {"username": "newuser", "password1": "testpass123", "password2": "testpass123"},
        )
        self.assertEqual(response.status_code, 302)  # Should redirect to conversation_list
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_signup_view_post_invalid(self):
        response = self.client.post(
            reverse("signup"),
            {"username": "newuser", "password1": "pass1", "password2": "pass2"},
        )
        self.assertEqual(response.status_code, 200)  # Validation fails, stays on signup
        self.assertFalse(User.objects.filter(username="newuser").exists())

    def test_conversation_list_view_authenticated(self):
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("conversation_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chat/conversation_list.html")
        self.assertIn(self.conv, response.context["conversations"])

    def test_conversation_list_view_unauthenticated(self):
        response = self.client.get(reverse("conversation_list"))
        self.assertEqual(response.status_code, 302)  # Redirects to login

    def test_conversation_create_view_post(self):
        self.client.login(username="testuser", password="password123")
        response = self.client.post(reverse("conversation_create"), {"title": "New Room"})
        new_conv = Conversation.objects.filter(title="New Room").first()
        self.assertIsNotNone(new_conv)
        self.assertEqual(new_conv.created_by, self.user)
        # Check redirect to the new chat room
        self.assertRedirects(response, reverse("chat_room", args=[new_conv.pk]))

    def test_chat_room_view_member(self):
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("chat_room", args=[self.conv.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chat/room.html")

    def test_chat_room_view_non_member(self):
        self.client.login(username="otheruser", password="password123")
        response = self.client.get(reverse("chat_room", args=[self.conv.pk]))
        self.assertEqual(response.status_code, 404)  # Blocked

    def test_invite_regenerate_view_member(self):
        self.client.login(username="testuser", password="password123")
        old_token = self.conv.invite_token
        response = self.client.post(reverse("invite_regenerate", args=[self.conv.pk]))
        self.conv.refresh_from_db()
        self.assertNotEqual(self.conv.invite_token, old_token)
        self.assertRedirects(response, reverse("chat_room", args=[self.conv.pk]))

    def test_invite_regenerate_view_non_member(self):
        self.client.login(username="otheruser", password="password123")
        response = self.client.post(reverse("invite_regenerate", args=[self.conv.pk]))
        self.assertEqual(response.status_code, 404)

    def test_join_conversation_view_get(self):
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("join_conversation"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chat/join.html")

    def test_join_conversation_view_post_valid_token(self):
        self.client.login(username="otheruser", password="password123")
        response = self.client.post(reverse("join_conversation"), {"token": str(self.conv.invite_token)})
        self.assertRedirects(response, reverse("chat_room", args=[self.conv.pk]))
        # Verify otheruser is now a member
        self.assertTrue(
            ConversationMember.objects.filter(conversation=self.conv, user=self.other_user).exists()
        )

    def test_join_conversation_view_post_invalid_uuid(self):
        self.client.login(username="otheruser", password="password123")
        response = self.client.post(reverse("join_conversation"), {"token": "not-a-uuid-token"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["error"], "Invalid token format. Paste the full UUID.")

    def test_join_conversation_view_post_nonexistent_token(self):
        self.client.login(username="otheruser", password="password123")
        random_token = uuid.uuid4()
        response = self.client.post(reverse("join_conversation"), {"token": str(random_token)})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["error"], "No group matches this token.")


class ConsumerTests(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="chatuser", password="password")
        self.other_user = User.objects.create_user(username="otheruser", password="password")
        self.conv = Conversation.objects.create(title="Chat Room")
        ConversationMember.objects.create(conversation=self.conv, user=self.user)

    @async_to_sync
    async def test_connect_authenticated_member(self):
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), f"/ws/chat/{self.conv.id}/")
        communicator.scope["user"] = self.user
        communicator.scope["url_route"] = {"kwargs": {"conversation_id": str(self.conv.id)}}
        
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Test sending/receiving message
        await communicator.send_json_to({"message": "Hello WebSocket"})
        response = await communicator.receive_json_from()
        
        self.assertEqual(response["type"], "message")
        self.assertEqual(response["author"], "chatuser")
        self.assertEqual(response["body"], "Hello WebSocket")
        
        await communicator.disconnect()

    @async_to_sync
    async def test_connect_anonymous(self):
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), f"/ws/chat/{self.conv.id}/")
        communicator.scope["user"] = AnonymousUser()
        communicator.scope["url_route"] = {"kwargs": {"conversation_id": str(self.conv.id)}}
        
        connected, code = await communicator.connect()
        self.assertFalse(connected)
        self.assertEqual(code, 4401)

    @async_to_sync
    async def test_connect_non_member(self):
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), f"/ws/chat/{self.conv.id}/")
        communicator.scope["user"] = self.other_user
        communicator.scope["url_route"] = {"kwargs": {"conversation_id": str(self.conv.id)}}
        
        connected, code = await communicator.connect()
        self.assertFalse(connected)
        self.assertEqual(code, 4403)
