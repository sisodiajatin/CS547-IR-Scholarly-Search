from collections import Counter
from datetime import date, timedelta
from html.parser import HTMLParser
from importlib import import_module
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from django.apps import apps
from django.contrib.auth.models import User
from django.core.management import call_command
from django.db import connection, IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone
from .models import Paper, PaperRedirect, SavedPaper
from .services import search_papers


class Markup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.refs = [], []
    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if "id" in data:
            self.ids.append(data["id"])
        self.refs.extend(data.get("aria-describedby", "").split())


class AuditFixTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("audit", password="A-real-test-password-93!")
        cls.paper = Paper.objects.create(title="Neural paper", summary="Discovery", authors="A",
            published=date(2024, 1, 1), url="https://arxiv.org/abs/1")

    def test_login_returns_to_safe_destination_after_invalid_attempt(self):
        response = self.client.post("/users/login/?next=/library/?q=neural", {"username": "audit", "password": "wrong"})
        self.assertContains(response, 'name="next" value="/library/?q=neural"')
        response = self.client.post("/users/login/", {"username": "audit", "password": "A-real-test-password-93!", "next": "/library/?q=neural"})
        self.assertRedirects(response, "/library/?q=neural")

    def test_login_rejects_external_return_destinations(self):
        for target in ["https://example.com", "//example.com", "javascript:alert(1)"]:
            self.client.logout()
            response = self.client.post("/users/login/", {"username": "audit", "password": "A-real-test-password-93!", "next": target})
            self.assertRedirects(response, "/search/")

    def test_guest_save_link_returns_to_paper(self):
        response = self.client.get(f"/papers/{self.paper.pk}/")
        self.assertContains(response, f'/users/login/?next=/papers/{self.paper.pk}/')

    def test_invalid_form_errors_have_unique_linked_ids(self):
        response = self.client.post("/users/signup/", {"username": "new", "major": "cs", "password1": "abc", "password2": "abc"})
        parser = Markup(); parser.feed(response.content.decode())
        self.assertTrue(response.context["form"].errors)
        self.assertFalse([key for key, count in Counter(parser.ids).items() if count > 1])
        self.assertFalse(set(parser.refs) - set(parser.ids))
        self.assertIn("id_password2_error", parser.refs)

    def test_missing_and_invalid_actions_do_not_change_library(self):
        self.client.force_login(self.user)
        for payload in [{}, {"action": "typo"}, {"action": "SAVE"}]:
            response = self.client.post(f"/papers/{self.paper.pk}/save/", payload)
            self.assertEqual(response.status_code, 400)
        self.assertFalse(SavedPaper.objects.exists())

    def test_head_succeeds_and_has_no_body(self):
        self.client.force_login(self.user)
        for path in ["/", "/search/", "/resps/", "/library/", "/users/profile/", f"/papers/{self.paper.pk}/", f"/papers/{self.paper.pk}/citation/"]:
            response = self.client.head(path)
            self.assertEqual(response.status_code, 200, path)
            self.assertEqual(response.content, b"")

    def test_consolidation_preserves_bookmarks_aliases_and_index_triggers(self):
        with connection.cursor() as cursor:
            cursor.execute("DROP INDEX unique_paper_url")
        try:
            duplicate = Paper.objects.create(title="Neural paper", summary="Discovery", authors="A", url=self.paper.url)
            other_user = User.objects.create_user("another")
            keeper_saved = SavedPaper.objects.create(user=self.user, paper=self.paper)
            duplicate_saved = SavedPaper.objects.create(user=self.user, paper=duplicate)
            older = timezone.now() - timedelta(days=5)
            SavedPaper.objects.filter(pk=duplicate_saved.pk).update(created_at=older)
            SavedPaper.objects.create(user=other_user, paper=duplicate)
            migration = import_module("search.migrations.0009_paperredirect_paper_unique_paper_url_and_more")
            migration.consolidate(apps, SimpleNamespace(connection=connection))
            self.assertEqual(Paper.objects.count(), 1)
            self.assertEqual(SavedPaper.objects.count(), 2)
            self.assertEqual(SavedPaper.objects.get(user=self.user).created_at, older)
            self.assertEqual(SavedPaper.objects.get(user=other_user).paper_id, self.paper.pk)
            self.assertEqual(PaperRedirect.objects.get(old_id=duplicate.pk).paper_id, self.paper.pk)
            self.assertRedirects(self.client.get(f"/papers/{duplicate.pk}/"), f"/papers/{self.paper.pk}/", status_code=301)
            self.assertEqual(list(search_papers("neural").values_list("id", flat=True)), [self.paper.pk])
            Paper.objects.filter(pk=self.paper.pk).update(title="Updated title")
            self.assertTrue(search_papers("updated").exists())
        finally:
            with connection.cursor() as cursor:
                cursor.execute("CREATE UNIQUE INDEX unique_paper_url ON search_paper(url)")

    def test_import_duplicates_preserves_identity_and_saved_papers(self):
        SavedPaper.objects.create(user=self.user, paper=self.paper)
        with TemporaryDirectory() as folder:
            path = Path(folder) / "papers.sql"
            path.write_text("INSERT INTO `papers` VALUES (99,'Updated neural paper','Discovery','A','2024-01-01','https://arxiv.org/abs/1');", encoding="utf-8")
            for _ in range(2):
                call_command("import_papers", str(path), stdout=StringIO())
        self.assertEqual(Paper.objects.count(), 1)
        self.assertEqual(Paper.objects.get().pk, self.paper.pk)
        self.assertEqual(SavedPaper.objects.get().paper_id, self.paper.pk)
        self.assertTrue(search_papers("updated").exists())
        with self.assertRaises(IntegrityError), transaction.atomic():
            Paper.objects.create(title="Duplicate", summary="X", authors="A", url=self.paper.url)
