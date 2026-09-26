from django.db import migrations
from django.contrib.auth.hashers import make_password


def migrate_accounts(apps, schema_editor):
    Legacy = apps.get_model("search", "umTester")
    User = apps.get_model("auth", "User")
    Profile = apps.get_model("search", "Profile")
    alias = schema_editor.connection.alias
    for old in Legacy.objects.using(alias).all():
        if User.objects.using(alias).filter(username=old.username).exists():
            raise RuntimeError("Duplicate legacy username; resolve account collisions before migrating.")
        user = User.objects.using(alias).create(username=old.username, password=make_password(old.password))
        Profile.objects.using(alias).create(user=user, major=old.major)
        old.password = ""
        old.save(using=alias, update_fields=["password"])


class Migration(migrations.Migration):
    dependencies = [("search", "0006_paper_profile")]
    operations = [
        migrations.RunSQL(
            sql=[
                "CREATE VIRTUAL TABLE paper_fts USING fts5(title, summary, authors, content='search_paper', content_rowid='id', tokenize='porter unicode61')",
                "CREATE TRIGGER paper_ai AFTER INSERT ON search_paper BEGIN INSERT INTO paper_fts(rowid,title,summary,authors) VALUES(new.id,new.title,new.summary,new.authors); END",
                "CREATE TRIGGER paper_ad AFTER DELETE ON search_paper BEGIN INSERT INTO paper_fts(paper_fts,rowid,title,summary,authors) VALUES('delete',old.id,old.title,old.summary,old.authors); END",
                "CREATE TRIGGER paper_au AFTER UPDATE ON search_paper BEGIN INSERT INTO paper_fts(paper_fts,rowid,title,summary,authors) VALUES('delete',old.id,old.title,old.summary,old.authors); INSERT INTO paper_fts(rowid,title,summary,authors) VALUES(new.id,new.title,new.summary,new.authors); END",
                "INSERT INTO paper_fts(paper_fts) VALUES('rebuild')",
            ],
            reverse_sql=["DROP TRIGGER paper_ai", "DROP TRIGGER paper_ad", "DROP TRIGGER paper_au", "DROP TABLE paper_fts"],
        ),
        # One-way: restoring plaintext credentials would be unsafe.
        migrations.RunPython(migrate_accounts),
    ]
