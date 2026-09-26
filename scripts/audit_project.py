"""Read-only corpus audit plus isolated temporary-database functional probes.
Run from the repository root with .venv/Scripts/python.exe scripts/audit_project.py.
Does not modify application code or the user's local data.
"""
import json
import os
from pathlib import Path
import statistics
import sys
import time
from collections import Counter
from html.parser import HTMLParser
from io import StringIO
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scholar_search'))
sys.dont_write_bytecode = True
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scholar_search.settings')
import django
django.setup()
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.db.models import Count, Min, Max
from django.test import Client, override_settings
from django.test.utils import setup_databases, teardown_databases
from search.models import Paper, SavedPaper
from search.services import search_papers


class Markup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.references = []
        self.links = []
    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if data.get('id'):
            self.ids.append(data['id'])
        for key in ('aria-describedby', 'aria-labelledby', 'aria-controls'):
            self.references.extend(data.get(key, '').split())
        if tag == 'a' and data.get('href'):
            self.links.append(data['href'])


report = {'checks': [], 'findings': []}
def check(name, condition, detail=None):
    report['checks'].append({'name': name, 'passed': bool(condition), 'detail': detail})


def corpus_audit():
    stats = Paper.objects.aggregate(total=Count('id'), earliest=Min('published'), latest=Max('published'))
    report['corpus'] = {key: str(value) if key != 'total' else value for key, value in stats.items()}
    duplicates = list(Paper.objects.values('url').annotate(n=Count('id')).filter(n__gt=1))
    report['corpus']['duplicate_url_groups'] = len(duplicates)
    report['corpus']['excess_duplicate_url_records'] = sum(item['n'] - 1 for item in duplicates)
    report['corpus']['unique_urls'] = Paper.objects.values('url').distinct().count()
    with connection.cursor() as cursor:
        cursor.execute('PRAGMA quick_check')
        check('SQLite quick_check', cursor.fetchone()[0] == 'ok')
    report['timings'] = []
    client = Client()
    for query in ('neural networks', 'transformer attention', 'the', 'quantum computing'):
        samples = []
        for _ in range(5):
            started = time.perf_counter()
            response = client.get('/resps/', {'q': query})
            samples.append(round((time.perf_counter() - started) * 1000, 2))
        report['timings'].append({'query': query, 'median_ms': statistics.median(samples), 'max_ms': max(samples)})
        check('Corpus query: ' + query, response.status_code == 200)
    for path in ('/', '/resps/?q=neural+networks', '/library/', '/users/login/', '/users/signup/'):
        response = client.get(path)
        markup = Markup(); markup.feed(response.content.decode())
        check('Rendered page: ' + path, response.status_code == 200)
        check('ARIA references: ' + path, not (set(markup.references) - set(markup.ids)))
        check('Unique IDs: ' + path, len(markup.ids) == len(set(markup.ids)))
        check('No placeholder links: ' + path, '#' not in markup.links)
    report['head_statuses'] = {path: client.head(path).status_code for path in ('/', '/resps/', '/library/')}


def isolated_audit():
    original = setup_databases(verbosity=0, interactive=False)
    try:
        client = Client()
        owner = User.objects.create_user('audit_reader', password='Audit-only-password-104!')
        paper = Paper.objects.create(title='Unique quantum computing paper', summary='An abstract.',
            authors='Ada Example', published='2024-01-01', url='https://arxiv.org/abs/2401.12345')
        other = Paper.objects.create(title='Quantum optics', summary='Another abstract.',
            authors='Bob Example', published='2023-01-01', url='https://arxiv.org/abs/2301.54321')
        response = client.post('/users/signup/', {'username': 'new_user', 'major': 'cs', 'password1': 'abc', 'password2': 'abc'})
        markup = Markup(); markup.feed(response.content.decode())
        report['invalid_form_markup'] = {
            'duplicate_ids': [key for key, count in Counter(markup.ids).items() if count > 1],
            'missing_aria_targets': sorted(set(markup.references) - set(markup.ids)),
        }
        response = client.post('/users/login/?next=/library/', {'username': owner.username, 'password': 'Audit-only-password-104!'})
        report['login_next_redirect'] = response.headers.get('Location')
        check('Login succeeds', response.status_code == 302 and '_auth_user_id' in client.session)
        check('Logout requires POST', client.get('/users/logout/').status_code == 405)
        for _ in range(3):
            client.post(f'/papers/{paper.pk}/save/', {'action': 'save'})
        check('Repeated saves are idempotent', SavedPaper.objects.filter(user=owner, paper=paper).count() == 1)
        for target in ('https://example.com', '//example.com', 'javascript:alert(1)'):
            response = client.post(f'/papers/{paper.pk}/save/', {'action': 'save', 'next': target})
            check('Unsafe redirect rejected: ' + target, response.headers.get('Location') == '/library/')
        before = SavedPaper.objects.count()
        response = client.post(f'/papers/{other.pk}/save/', {'action': 'typo'})
        report['invalid_save_action'] = {'status': response.status_code, 'records_added': SavedPaper.objects.count() - before}
        client.post('/users/logout/')
        check('Logout clears authentication', '_auth_user_id' not in client.session)
        check('Guest library hides private titles', paper.title.encode() not in client.get('/library/').content)
        for page in ('-1', 'invalid', '999999999999999999999999'):
            check('Pagination input: ' + page, client.get('/resps/', {'q': 'quantum', 'page': page}).status_code == 200)
        for query in ('!!!', "' OR 1=1 --", '\u4e2d\u6587', 'q' * 301):
            check('Search boundary: ' + query[:30], client.get('/resps/', {'q': query}).status_code == 200)
        for path in ('/missing/', '/papers/9999999999999999999999/'):
            check('Unknown route: ' + path, client.get(path).status_code == 404)
        with override_settings(DEBUG=False):
            response = client.get('/missing/')
            check('Branded production 404', response.status_code == 404 and b'This path ends here' in response.content)
        report['phrase_search_ids'] = list(search_papers('"quantum computing"').values_list('id', flat=True))
        report['phrase_exact_paper_id'] = paper.pk
        report['arxiv_identifier_search_ids'] = list(search_papers('2401.12345').values_list('id', flat=True))
        csrf = Client(enforce_csrf_checks=True)
        check('Signup CSRF protection', csrf.post('/users/signup/', {}).status_code == 403)
        client.force_login(owner)
        before = SavedPaper.objects.count()
        Paper.objects.filter(pk=paper.pk).delete()
        check('Deleting paper cleans saved references', SavedPaper.objects.count() == before - 1)
        check('Deleted paper removed from search index', not search_papers('unique').exists())
        with TemporaryDirectory(prefix='scholar-audit-', dir=ROOT) as folder:
            path = Path(folder) / 'partial.sql'
            rows = [f"({1000+i},'Atomic paper','Abstract','Author','2024-01-01','https://arxiv.org/abs/{1000+i}')" for i in range(251)]
            path.write_text('INSERT INTO `papers` VALUES ' + ','.join(rows) + ',(broken);', encoding='utf-8')
            count = Paper.objects.count()
            rejected = False
            try:
                call_command('import_papers', str(path), stdout=StringIO())
            except CommandError:
                rejected = True
            check('Import failure rolls back flushed batches', rejected and Paper.objects.count() == count)
    finally:
        teardown_databases(original, verbosity=0)


with override_settings(ALLOWED_HOSTS=['testserver']):
    corpus_audit()
    isolated_audit()
if report['corpus']['excess_duplicate_url_records']:
    report['findings'].append({'id': 'DATA-01', 'severity': 'medium', 'issue': 'Duplicate corpus URLs',
        'excess_records': report['corpus']['excess_duplicate_url_records']})
if report['invalid_form_markup']['duplicate_ids']:
    report['findings'].append({'id': 'UI-01', 'severity': 'medium', 'issue': 'Duplicate HTML IDs in invalid signup form'})
if report['login_next_redirect'] != '/library/':
    report['findings'].append({'id': 'AUTH-01', 'severity': 'medium', 'issue': 'Login discards the next destination'})
if report['invalid_save_action']['records_added']:
    report['findings'].append({'id': 'API-01', 'severity': 'low', 'issue': 'Unknown save actions silently create a saved record'})
if any(status != 200 for status in report['head_statuses'].values()):
    report['findings'].append({'id': 'HTTP-01', 'severity': 'low', 'issue': 'Public pages reject HEAD requests'})
report['summary'] = {'checks': len(report['checks']), 'passed': sum(item['passed'] for item in report['checks'])}
output = ROOT / 'AUDIT_RESULTS.json'
output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, indent=2))
