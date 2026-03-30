from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0003_rename_users_trust_user_id_ebf8aa_idx_users_trust_user_id_48e2ed_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="emailverificationtoken",
            name="target_email",
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AlterField(
            model_name="emailverificationtoken",
            name="purpose",
            field=models.CharField(
                choices=[
                    ("verify_email", "Verify Email"),
                    ("login_security", "Login Security"),
                    ("email_change", "Email Change"),
                ],
                default="verify_email",
                max_length=30,
            ),
        ),
        migrations.AddIndex(
            model_name="emailverificationtoken",
            index=models.Index(
                fields=["user", "purpose", "target_email", "created_at"],
                name="users_evt_uptc_idx",
            ),
        ),
    ]
