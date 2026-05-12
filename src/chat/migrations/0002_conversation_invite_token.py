import uuid

from django.db import migrations, models


def assign_invite_tokens(apps, schema_editor):
    Conversation = apps.get_model("chat", "Conversation")
    for conv in Conversation.objects.filter(invite_token__isnull=True).iterator():
        conv.invite_token = uuid.uuid4()
        conv.save(update_fields=["invite_token"])


class Migration(migrations.Migration):
    dependencies = [
        ("chat", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="conversation",
            name="invite_token",
            field=models.UUIDField(editable=False, null=True, unique=True),
        ),
        migrations.RunPython(assign_invite_tokens, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="conversation",
            name="invite_token",
            field=models.UUIDField(
                default=uuid.uuid4,
                editable=False,
                unique=True,
            ),
        ),
    ]
