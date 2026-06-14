import logging
import uuid

from django.contrib.auth.decorators import login_required
from django.core.cache import caches
from django.db import connections
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .models import Conversation, ConversationMember, Message

logger = logging.getLogger(__name__)


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


def signup(request):
    from django.contrib.auth import login
    from django.contrib.auth.forms import UserCreationForm
    from django.shortcuts import redirect

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("conversation_list")
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})


@require_http_methods(["GET"])
def health_check(request):
    db_ok = True
    cache_ok = True
    errors = {}

    # Check Database
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1;")
            row = cursor.fetchone()
            if row is None or row[0] != 1:
                db_ok = False
                errors["database"] = "Invalid query result"
    except Exception as e:
        db_ok = False
        errors["database"] = str(e)
        logger.exception("Health check: Database connection failed")

    # Check Cache (Redis)
    try:
        cache = caches["default"]
        cache.set("health_check_key", "ok", timeout=5)
        if cache.get("health_check_key") != "ok":
            cache_ok = False
            errors["cache"] = "Cache read/write verification failed"
    except Exception as e:
        cache_ok = False
        errors["cache"] = str(e)
        logger.exception("Health check: Cache connection failed")

    status_code = 200 if (db_ok and cache_ok) else 503
    response_data = {
        "status": "healthy" if status_code == 200 else "unhealthy",
        "database": "healthy" if db_ok else "unhealthy",
        "cache": "healthy" if cache_ok else "unhealthy",
    }
    if errors:
        response_data["errors"] = errors

    return JsonResponse(response_data, status=status_code)

