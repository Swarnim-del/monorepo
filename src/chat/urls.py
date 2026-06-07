from django.urls import path

from . import views

urlpatterns = [
    path("", views.conversation_list, name="conversation_list"),
    path("conversations/new/", views.conversation_create, name="conversation_create"),
    path(
        "conversations/<int:pk>/invite/regenerate/",
        views.invite_regenerate,
        name="invite_regenerate",
    ),
    path("join/", views.join_conversation, name="join_conversation"),
    path("chat/<int:pk>/", views.chat_room, name="chat_room"),
    path("accounts/signup/", views.signup, name="signup"),
]
