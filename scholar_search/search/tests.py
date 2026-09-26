from datetime import date
from importlib import import_module
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test import Client, TestCase
from django.urls import reverse
from .models import Paper, Profile, umTester
from .services import search_papers


class SearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.title_match = Paper.objects.create(title="Neural ranking", summary="Models for discovery",
            authors="Alice Example", published=date(2020, 1, 1), url="https://arxiv.org/abs/1")
        cls.abstract_match = Paper.objects.create(title="Other research", summary="Neural ranking",
            authors="Bob Example", published=date(2024, 1, 1), url="https://arxiv.org/abs/2")
        cls.unrelated = Paper.objects.create(title="Topology", summary="Manifolds", authors="Carol Example",
            published=date(2025, 1, 1), url="https://arxiv.org/abs/3")

    def test_title_weight_and_no_unrelated_results(self):
        self.assertEqual(list(search_papers("NEURAL")), [self.title_match, self.abstract_match])

    def test_stemming_authors_and_punctuation(self):
        self.assertIn(self.title_match, search_papers("rankings"))
        self.assertEqual(list(search_papers("Alice")), [self.title_match])
        self.assertFalse(search_papers('" OR * : --'))
        self.assertFalse(search_papers("!!!"))

    def test_year_is_inclusive_and_newest_sort(self):
        self.assertEqual(list(search_papers("neural", 2024)), [self.abstract_match])
        self.assertEqual(list(search_papers("neural", sort="newest")), [self.abstract_match, self.title_match])

    def test_index_tracks_updates_and_deletes(self):
        Paper.objects.filter(pk=self.title_match.pk).update(title="Banana research")
        self.assertEqual(list(search_papers("banana")), [Paper.objects.get(pk=self.title_match.pk)])
        self.title_match.delete()
        self.assertFalse(search_papers("banana"))

    def test_empty_and_invalid_searches(self):
        for params in ({}, {"q": "!!!"}, {"q": "neural", "year": "bad"}, {"q": "neural", "sort": "bad"}, {"q": "a" * 301}):
            response = self.client.get(reverse("resps"), params)
            self.assertEqual(response.status_code, 200)
        self.assertContains(self.client.get(reverse("resps"), {"year": "bad"}), "Check your search filters")

    def test_pagination_is_stateless_and_keeps_filters(self):
        for i in range(12):
            Paper.objects.create(title=f"Neural {i}", summary="Methods", authors="A",
                published=date(2024, 1, 1), url=f"https://arxiv.org/abs/extra-{i}")
        response = Client().get(reverse("resps"), {"q": "neural", "year": 2024, "sort": "newest", "page": 2})
        self.assertEqual(response.context["papers"].number, 2)
        self.assertEqual(response.context["papers"].paginator.count, 13)
        self.assertContains(response, "q=neural&amp;year=2024&amp;sort=newest")
        self.assertEqual(self.client.get(reverse("resps"), {"q": "neural", "page": "bad"}).status_code, 200)

    def test_queries_and_titles_are_escaped(self):
        response = self.client.get(reverse("resps"), {"q": "<script>alert(1)</script>"})
        self.assertNotContains(response, "<script>alert(1)</script>")

    def test_pages_and_legacy_search_redirect(self):
        for name in ("home", "search", "login", "signup"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)
        self.assertRedirects(self.client.post(reverse("search"), {"query": "neural"}), "/resps/?q=neural")


class AccountTests(TestCase):
    def test_signup_hashes_password_creates_profile_and_logs_in(self):
        response = self.client.post(reverse("signup"), {"username": "researcher", "major": "cs",
            "password1": "A-research-password-942!", "password2": "A-research-password-942!"})
        self.assertRedirects(response, reverse("profile"))
        user = User.objects.get(username="researcher")
        self.assertTrue(user.check_password("A-research-password-942!"))
        self.assertNotEqual(user.password, "A-research-password-942!")
        self.assertEqual(Profile.objects.get(user=user).major, "cs")
        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)
        self.client.post(reverse("logout"))
        self.assertEqual(self.client.get(reverse("profile")).status_code, 302)
        self.assertRedirects(self.client.post(reverse("login"), {"username": "researcher", "password": "A-research-password-942!"}), reverse("search"))

    def test_invalid_registration_and_login(self):
        response = self.client.post(reverse("signup"), {"username": "x", "major": "bad", "password1": "1", "password2": "2"})
        self.assertTrue(response.context["form"].errors)
        self.assertFalse(User.objects.exists())
        response = self.client.post(reverse("login"), {"username": "missing", "password": "wrong"})
        self.assertTrue(response.context["form"].errors)

    def test_csrf_and_profile_protection(self):
        self.assertEqual(Client(enforce_csrf_checks=True).post(reverse("signup"), {}).status_code, 403)
        self.assertEqual(Client(enforce_csrf_checks=True).post(reverse("logout"), {}).status_code, 403)
        self.assertEqual(self.client.get(reverse("profile")).status_code, 302)

    def test_legacy_account_conversion(self):
        from django.apps import apps
        umTester.objects.create(username="legacy", password="old-password", major="ds")
        migration = import_module("search.migrations.0007_search_index_and_accounts")
        from types import SimpleNamespace
        migration.migrate_accounts(apps, SimpleNamespace(connection=connection))
        self.assertTrue(User.objects.get(username="legacy").check_password("old-password"))
        self.assertEqual(umTester.objects.get().password, "")


class ImportTests(TestCase):
    def test_escapes_rerun_and_index(self):
        from .management.commands.import_papers import parse_rows
        row = r"(1,'Researcher\'s title','line\nnext','RenÃ©','2020-01-01','https://arxiv.org/abs/1');"
        self.assertEqual(list(parse_rows(row))[0][1], "Researcher's title")
        self.assertEqual(list(parse_rows(row))[0][2], "line\nnext")
        with TemporaryDirectory() as folder:
            path = Path(folder) / "papers.sql"
            path.write_text("INSERT INTO `papers` VALUES " + row, encoding="utf-8")
            for _ in range(2):
                call_command("import_papers", str(path), stdout=StringIO())
            self.assertEqual(Paper.objects.count(), 1)
            self.assertTrue(search_papers("researcher"))
            path.write_text("INSERT INTO `papers` VALUES (broken);", encoding="utf-8")
            with self.assertRaises(CommandError):
                call_command("import_papers", str(path), stdout=StringIO())
            self.assertEqual(Paper.objects.count(), 1)


class LibraryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.paper = Paper.objects.create(title="Attention & discovery", summary="An abstract with <script>text</script>.",
            authors="Ada Example, Ben Researcher", published=date(2024, 1, 2), url="https://arxiv.org/abs/2401.12345")
        cls.owner = User.objects.create_user(username="reader", password="test-only-reader-password")
        cls.other = User.objects.create_user(username="another", password="test-only-other-password")

    def test_guest_reader_and_citation(self):
        response = self.client.get(reverse("paper_detail", args=[self.paper.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "&lt;script&gt;text&lt;/script&gt;")
        self.assertContains(response, "Log in to save this paper")
        response = self.client.get(reverse("paper_citation", args=[self.paper.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertIn(r"Attention \& discovery", response.content.decode())
        self.assertIn("Ada Example and Ben Researcher", response.content.decode())

    def test_save_is_idempotent_and_scoped_to_owner(self):
        from .models import SavedPaper
        self.client.force_login(self.owner)
        url = reverse("save_paper", args=[self.paper.pk])
        for _ in range(2):
            self.assertRedirects(self.client.post(url, {"action": "save"}), reverse("library"))
        self.assertEqual(SavedPaper.objects.filter(user=self.owner).count(), 1)
        self.assertContains(self.client.get(reverse("library")), self.paper.title.replace("&", "&amp;"))
        self.client.force_login(self.other)
        self.assertNotContains(self.client.get(reverse("library")), "Attention &amp; discovery")
        self.client.post(url, {"action": "remove"})
        self.assertTrue(SavedPaper.objects.filter(user=self.owner, paper=self.paper).exists())
        self.client.force_login(self.owner)
        self.client.post(url, {"action": "remove"})
        self.assertFalse(SavedPaper.objects.filter(user=self.owner).exists())

    def test_save_requires_auth_post_csrf_and_safe_redirect(self):
        url = reverse("save_paper", args=[self.paper.pk])
        self.assertEqual(self.client.post(url).status_code, 302)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(url).status_code, 405)
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.owner)
        self.assertEqual(csrf_client.post(url).status_code, 403)
        self.assertRedirects(self.client.post(url, {"action": "save", "next": "https://example.com"}), reverse("library"))

    def test_library_filter_and_guest_state(self):
        from .models import SavedPaper
        self.assertContains(self.client.get(reverse("library")), "Log in to your library")
        SavedPaper.objects.create(user=self.owner, paper=self.paper)
        self.client.force_login(self.owner)
        self.assertContains(self.client.get(reverse("library"), {"q": "Ada"}), "Attention &amp; discovery")
        self.assertNotContains(self.client.get(reverse("library"), {"q": "missing"}), "Attention &amp; discovery")

    def test_missing_papers_return_not_found(self):
        self.assertEqual(self.client.get(reverse("paper_detail", args=[9999])).status_code, 404)
        self.assertEqual(self.client.get(reverse("paper_citation", args=[9999])).status_code, 404)
