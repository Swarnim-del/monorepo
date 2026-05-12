from django.contrib import admin

from .models import Conversation, ConversationMember, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "invite_token", "created_at", "created_by")
    search_fields = ("title",)
    readonly_fields = ("invite_token",)


@admin.register(ConversationMember)
class ConversationMemberAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "user", "joined_at")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "author", "created_at")
    list_filter = ("conversation",)
