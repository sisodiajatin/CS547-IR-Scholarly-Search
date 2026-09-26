import csv
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from django.test import TestCase
from .benchmark import prepare, evaluate, FIELDS, MODE_QUERIES, QUERIES
from .models import Paper
from .services import search_papers


class MatchingBenchmarkTests(TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.packet = self.root/'packet'
        Paper.objects.create(title='solar forecasting', summary='flare', authors='A', url='split')
        Paper.objects.create(title='solar energy', summary='test', authors='A', url='solar')
        self.queries = [
            {'id':'M01','query':'solar flare','intent':'Solar flares'},
            {'id':'M02','query':'xyzunmatched','intent':'Absent topic'},
        ]
        with patch('search.benchmark.MODE_QUERIES', self.queries):
            prepare(self.packet, experiment='matching')
        self.manifest = json.loads((self.packet/'manifest.json').read_text())
        with (self.packet/'judgments.csv').open(encoding='utf-8-sig',newline='') as f:
            self.rows = list(csv.DictReader(f))
        self.sheet = self.root/'ai.csv'
        with self.sheet.open('w',encoding='utf-8-sig',newline='') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(dict(row, grade='2' if row['paper_url']=='split' else '0', reviewer='AI: Synthetic test fixture') for row in self.rows)

    def test_modes_frozen_and_new_query_set(self):
        self.assertFalse({q['query'] for q in MODE_QUERIES} & {q['query'] for q in QUERIES})
        for query in self.queries:
            for mode in ('any','all','phrase'):
                papers = search_papers(query['query'],match=mode)
                self.assertEqual(self.manifest['result_counts'][query['id']][mode], papers.count())
                self.assertEqual(self.manifest['runs'][query['id']][mode], list(papers.values_list('url',flat=True)[:10]))
        self.assertEqual(self.manifest['pool']['M02'], [])
        self.assertEqual(len(self.rows), 2)

    def test_empty_modes_and_empty_query_stay_in_coverage(self):
        with patch('search.benchmark.search_papers',side_effect=AssertionError('Must use frozen runs')):
            report = evaluate(self.packet,self.sheet,self.root/'results',judgment_source='ai')
        self.assertEqual(report['coverage']['phrase']['zero_result_rate'], 1)
        self.assertEqual(report['coverage']['all']['zero_result_rate'], .5)
        self.assertEqual(report['coverage']['any']['mean_returned_at_10'], 1)
        self.assertEqual(report['macro']['all']['precision@10']['value'], .05)
        self.assertEqual(report['macro']['phrase']['nDCG@10']['value'], 0)
        self.assertEqual(report['macro']['phrase']['nDCG@10']['queries'], 1)
        self.assertEqual(report['zero_relevance_queries'], ['M02'])

    def test_reject_inconsistent_count_and_missing_mode(self):
        self.manifest['result_counts']['M01']['all'] = 2
        (self.packet/'manifest.json').write_text(json.dumps(self.manifest))
        with self.assertRaisesRegex(ValueError, 'result count'):
            evaluate(self.packet,self.sheet,self.root/'results',judgment_source='ai')
        del self.manifest['runs']['M01']['phrase']
        (self.packet/'manifest.json').write_text(json.dumps(self.manifest))
        with self.assertRaisesRegex(ValueError, 'three matching modes'):
            evaluate(self.packet,self.sheet,self.root/'results',judgment_source='ai')

    def test_blank_grades_and_overwrite_still_rejected(self):
        with self.assertRaisesRegex(ValueError, 'invalid grade'):
            evaluate(self.packet,self.packet/'judgments.csv',self.root/'results',judgment_source='ai')
        with self.assertRaisesRegex(ValueError, 'already exists'):
            prepare(self.packet,experiment='matching')
