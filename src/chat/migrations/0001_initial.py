import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Conversation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(default="Chat", max_length=200)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_conversations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ConversationMember",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("joined_at", models.DateTimeField(auto_now_add=True)),
                (
                    "conversation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="members",
                        to="chat.conversation",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="conversation_memberships",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Message",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("body", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "author",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="chat_messages",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "conversation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="messages",
                        to="chat.conversation",
                    ),
                ),
            ],
            options={
                "ordering": ["created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="conversationmember",
            constraint=models.UniqueConstraint(fields=("conversation", "user"), name="uniq_conversation_member_user"),
        ),
        migrations.AddIndex(
            model_name="message",
            index=models.Index(fields=["conversation", "created_at"], name="chat_messag_convers_7d0bd9_idx"),
        ),
    ]
