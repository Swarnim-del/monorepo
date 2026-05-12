import uuid

from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .models import Conversation, ConversationMember, Message


@login_required
def conversation_list(request):
    conversations = (
        Conversation.objects.filter(members__user=request.user)
        .distinct()
        .order_by("-created_at")
    )
    return render(
        request,
        "chat/conversation_list.html",
        {"conversations": conversations},
    )


@login_required
@require_http_methods(["POST"])
def conversation_create(request):
    title = (request.POST.get("title") or "New chat").strip() or "New chat"
    conv = Conversation.objects.create(title=title, created_by=request.user)
    ConversationMember.objects.create(conversation=conv, user=request.user)
    return HttpResponseRedirect(reverse("chat_room", args=[conv.pk]))


@login_required
def chat_room(request, pk):
    if not ConversationMember.objects.filter(
        conversation_id=pk, user=request.user
    ).exists():
        raise Http404()
    conversation = get_object_or_404(Conversation, pk=pk)
    chat_messages = (
        Message.objects.filter(conversation=conversation)
        .select_related("author")
        .order_by("created_at")
    )
    return render(
        request,
        "chat/room.html",
        {"conversation": conversation, "chat_messages": chat_messages},
    )


@login_required
@require_http_methods(["POST"])
def invite_regenerate(request, pk):
    if not ConversationMember.objects.filter(
        conversation_id=pk, user=request.user
    ).exists():
        raise Http404()
    conversation = get_object_or_404(Conversation, pk=pk)
    conversation.invite_token = uuid.uuid4()
    conversation.save(update_fields=["invite_token"])
    return HttpResponseRedirect(reverse("chat_room", args=[pk]))


@login_required
def join_conversation(request):
    error = None
    if request.method == "POST":
        raw = (request.POST.get("token") or "").strip()
        try:
            token = uuid.UUID(raw)
        except ValueError:
            error = "Invalid token format. Paste the full UUID."
        else:
            conversation = Conversation.objects.filter(invite_token=token).first()
            if not conversation:
                error = "No group matches this token."
            else:
                ConversationMember.objects.get_or_create(
                    conversation=conversation,
                    user=request.user,
                )
                return HttpResponseRedirect(
                    reverse("chat_room", args=[conversation.pk])
                )
    return render(request, "chat/join.html", {"error": error})
