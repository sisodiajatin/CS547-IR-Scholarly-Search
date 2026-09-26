from urllib.parse import urlencode
from django.test import TestCase
from .models import Paper
from .services import search_papers


class MatchingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        for name, title, abstract in [
            ('phrase', 'Machine translation methods', 'Language'),
            ('reverse', 'Translation by machine', 'Language'),
            ('split', 'Machine methods', 'Translation'),
            ('single', 'Translation invariance', 'Images'),
            ('repeat', 'Very very small machine', 'Language'),
            ('once', 'Very small machine', 'Language'),
        ]:
            Paper.objects.create(title=title, summary=abstract, authors='A', url=name, published='2024-01-01')

    def urls(self, query, **kwargs):
        return set(search_papers(query, **kwargs).values_list('url', flat=True))

    def test_matching_semantics(self):
        self.assertEqual(self.urls('machine translation', match='all'), {'phrase','reverse','split'})
        self.assertEqual(self.urls('machine translation', match='phrase'), {'phrase'})
        self.assertEqual(self.urls('machine translation'), self.urls('machine translation', match='any'))
        self.assertEqual(len(self.urls('machine translation')), 6)
        self.assertEqual(self.urls('very very', match='phrase'), {'repeat'})
        self.assertEqual(self.urls('very very', match='all'), {'repeat','once'})

    def test_normalization_and_invalid_input(self):
        self.assertEqual(self.urls('"MACHINE, translations"', match='phrase'), {'phrase'})
        for mode in ('any','all','phrase'):
            self.assertFalse(self.urls('!!!', match=mode))
            if mode != 'any':
                self.assertFalse(self.urls('machine OR missing', match=mode))
            self.assertEqual(len(self.urls('', year=2024, year_mode='exact', match=mode)), 6)
        with self.assertRaises(ValueError):
            search_papers('machine', match='invalid')
        response = self.client.get('/resps/?q=machine&match=invalid')
        self.assertTrue(response.context['form'].errors)
        self.assertEqual(response.context['papers'].paginator.count, 0)

    def test_filters_pagination_and_reader_context(self):
        for i in range(12):
            Paper.objects.create(title='Machine translation', summary='Test', authors='A', url=f'extra-{i}', published='2023-01-01')
        origin = '/resps/?' + urlencode(dict(q='machine translation', match='phrase', year=2023, year_mode='exact', sort='newest', page=2))
        response = self.client.get(origin)
        self.assertEqual(response.context['papers'].paginator.count, 12)
        self.assertIn('match=phrase', response.context['querystring'])
        self.assertContains(response, 'name="match" value="phrase"')
        paper = response.context['papers'][0]
        detail = self.client.get(f'/papers/{paper.pk}/', {'return_to':origin})
        self.assertEqual(detail.context['return_to'], origin)
