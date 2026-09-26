from django.db import migrations, models
import django.db.models.deletion


def consolidate(apps, schema_editor):
    alias = schema_editor.connection.alias
    Paper = apps.get_model("search", "Paper")
    Saved = apps.get_model("search", "SavedPaper")
    Redirect = apps.get_model("search", "PaperRedirect")
    duplicates = list(Paper.objects.using(alias).values("url").annotate(total=models.Count("id")).filter(total__gt=1))
    for group in duplicates:
        ids = list(Paper.objects.using(alias).filter(url=group["url"]).order_by("id").values_list("id", flat=True))
        keeper, removed = ids[0], ids[1:]
        for saved in Saved.objects.using(alias).filter(paper_id__in=removed).order_by("created_at", "id"):
            existing = Saved.objects.using(alias).filter(user_id=saved.user_id, paper_id=keeper).first()
            if existing:
                if saved.created_at < existing.created_at:
                    Saved.objects.using(alias).filter(pk=existing.pk).update(created_at=saved.created_at)
                saved.delete(using=alias)
            else:
                Saved.objects.using(alias).filter(pk=saved.pk).update(paper_id=keeper)
        Redirect.objects.using(alias).filter(paper_id__in=removed).update(paper_id=keeper)
        Redirect.objects.using(alias).bulk_create([Redirect(old_id=pk, paper_id=keeper) for pk in removed])
        Paper.objects.using(alias).filter(pk__in=removed).delete()


class Migration(migrations.Migration):
    dependencies = [("search", "0008_savedpaper")]
    operations = [
        migrations.CreateModel(name="PaperRedirect", fields=[
            ("old_id", models.BigIntegerField(primary_key=True, serialize=False)),
            ("paper", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="search.paper")),
        ]),
        # Irreversible data consolidation; back up the database before applying.
        migrations.RunPython(consolidate),
        # Avoid SQLite's table-rebuild path: rebuilding search_paper would drop
        # the FTS maintenance triggers attached to the original table.
        migrations.SeparateDatabaseAndState(
            database_operations=[migrations.RunSQL(
                "CREATE UNIQUE INDEX unique_paper_url ON search_paper(url)",
                "DROP INDEX unique_paper_url",
            )],
            state_operations=[migrations.AddConstraint(model_name="paper",
                constraint=models.UniqueConstraint(fields=("url",), name="unique_paper_url"))],
        ),
    ]
