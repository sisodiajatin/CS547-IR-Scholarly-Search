from datetime import date
from urllib.parse import urlencode
from django.contrib.auth.models import User
from django.test import TestCase
from .models import Paper, PaperRedirect, SavedPaper
from .services import search_papers
from .navigation import reader_return


class NavigationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        for i in range(12):
            Paper.objects.create(title=f"Neural systems {i}", authors="A", summary="Test research", published=date(2024, 1, i+1), url=f"https://arxiv.org/abs/{i}")
        Paper.objects.create(title="Neural earlier", summary="Earlier", authors="A", published=date(2023,12,31), url="https://arxiv.org/abs/earlier")
        Paper.objects.create(title="Neural later", summary="Later", authors="A", published=date(2025,1,1), url="https://arxiv.org/abs/later")
        Paper.objects.create(title="Neural undated", summary="Undated", authors="A", url="https://arxiv.org/abs/undated")

    def test_exact_chart_count_and_boundaries(self):
        response = self.client.get("/resps/?year=2024&year_mode=exact&sort=newest")
        self.assertEqual(response.context["papers"].paginator.count, 12)
        self.assertEqual(search_papers("neural",2024,year_mode="exact").count(),12)
        self.assertEqual(search_papers("neural",2024).count(),13)
        self.assertEqual(search_papers("",2024).count(),13)
        self.assertFalse(search_papers("!!!",2024))
        home = self.client.get("/")
        self.assertContains(home, "?year=2024&amp;year_mode=exact&amp;sort=newest")
        self.assertNotContains(home, 'q=research&amp;year=')

    def test_empty_and_invalid_browsing(self):
        self.assertEqual(self.client.get("/resps/").context["papers"].paginator.count,0)
        for query in ["year=invalid", "year=2024&year_mode=wrong", "year=2200"]:
            response=self.client.get("/resps/?"+query)
            self.assertTrue(response.context["form"].errors)
            self.assertEqual(response.context["papers"].paginator.count,0)

    def test_pagination_preserves_year_mode(self):
        response = self.client.get("/resps/?year=2024&year_mode=exact&page=2")
        self.assertEqual(response.context["papers"].number,2)
        self.assertIn("year_mode=exact", response.context["querystring"])
        self.assertContains(response,'name="year_mode"')

    def test_reader_context_and_alias_roundtrip(self):
        paper=Paper.objects.first()
        origin="/resps/?q=neural&year=2024&year_mode=exact&sort=newest&page=2"
        response=self.client.get(origin)
        self.assertContains(response, "return_to=%2Fresps%2F")
        url=f"/papers/{paper.pk}/?"+urlencode({"return_to":origin})
        self.assertEqual(self.client.get(url).context["return_to"],origin)
        PaperRedirect.objects.create(old_id=999,paper=paper)
        self.assertRedirects(self.client.get("/papers/999/?"+urlencode({"return_to":origin})), url, status_code=301)
        # Different origins in separate requests must not overwrite each other.
        library="/library/?q=neural&page=2"
        self.assertEqual(self.client.get(f"/papers/{paper.pk}/",{"return_to":library}).context["return_to"],library)
        self.assertEqual(self.client.get(url).context["return_to"],origin)

    def test_return_destinations_are_allowlisted(self):
        for target in ["https://example.com/resps/", "//example.com/resps/", "/users/logout/", "/papers/1/", "/resps/\\evil", "/resps/\n", "/resps/../users/logout/"]:
            self.assertEqual(reader_return(target)[0],"/resps/")

    def test_login_save_remove_preserve_reader_context(self):
        paper=Paper.objects.first()
        origin="/library/?q=neural&page=2"
        reader=f"/papers/{paper.pk}/?"+urlencode({"return_to":origin})
        response=self.client.get(reader)
        self.assertContains(response, "return_to%3D")
        user=User.objects.create_user("reader",password="Test-password-888!")
        self.assertRedirects(self.client.post("/users/login/",{"username":"reader","password":"Test-password-888!","next":reader}),reader)
        for action in ["save","remove"]:
            self.assertRedirects(self.client.post(f"/papers/{paper.pk}/save/",{"action":action,"next":reader}),reader)
        self.assertFalse(SavedPaper.objects.filter(user=user).exists())
