from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("runtime", "0003_add_tlt_audit_event"),
    ]

    operations = [
        migrations.CreateModel(
            name="SubmodalityGovernanceCache",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("submod_code", models.TextField(unique=True)),
                ("estado_normativo", models.TextField(choices=[("active", "active"), ("latent", "latent"), ("excluded", "excluded")])),
                ("risk_class", models.TextField(blank=True, choices=[("low", "low"), ("medium", "medium"), ("high", "high")], null=True)),
                ("introduced_in_version", models.TextField()),
                ("rules_ref", models.TextField(blank=True, null=True)),
                ("source_normative_version", models.TextField()),
                ("synced_at_utc", models.DateTimeField()),
            ],
            options={
                "db_table": "submodality_governance_cache",
            },
        ),
    ]