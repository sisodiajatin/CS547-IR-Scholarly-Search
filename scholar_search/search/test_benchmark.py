import csv
import json
import math
import tempfile
from pathlib import Path
from unittest.mock import patch
from django.test import TestCase, SimpleTestCase
from .benchmark import prepare, evaluate, metric_at_10, FIELDS
from .models import Paper
from .services import search_papers


class MetricTests(SimpleTestCase):
    def test_hand_calculated_metrics(self):
        result = metric_at_10(['a', 'b', 'c'], {'a':0, 'b':2, 'c':1, 'd':2})
        self.assertEqual(result['precision@10'], .2)
        self.assertEqual(result['MRR@10'], .5)
        self.assertAlmostEqual(result['pooled_recall@10'], 2/3)
        self.assertAlmostEqual(result['nDCG@10'], (3/math.log2(3)+.5)/(3+3/math.log2(3)+.5))

    def test_empty_and_zero_relevance(self):
        result = metric_at_10([], {'a':0})
        self.assertEqual(result['precision@10'], 0)
        self.assertEqual(result['MRR@10'], 0)
        self.assertIsNone(result['nDCG@10'])
        self.assertIsNone(result['pooled_recall@10'])
        self.assertEqual(metric_at_10([], {'a':2})['nDCG@10'], 0)


class BenchmarkTests(TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.packet = self.root/'packet'
        for i in range(12):
            Paper.objects.create(title=f'Neural method {i}', summary='network learning', authors='A', url=f'https://example.org/{i}', published='2024-01-01')
        self.queries = [{'id':'Q01','query':'neural','intent':'Neural methods'}]
        with patch('search.benchmark.QUERIES', self.queries):
            prepare(self.packet)
        self.sheet = self.packet/'judgments.csv'
        with self.sheet.open(encoding='utf-8-sig', newline='') as handle:
            self.rows = list(csv.DictReader(handle))

    def write_rows(self, rows):
        with self.sheet.open('w', encoding='utf-8-sig', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader(); writer.writerows(rows)

    def test_frozen_blinded_packet_and_deterministic_ties(self):
        self.assertTrue(all(not row['grade'] and not row['reviewer'] for row in self.rows))
        self.assertNotIn('ranker', self.rows[0])
        for name in ('weighted','uniform'):
            self.assertEqual(list(search_papers('neural', ranker=name).values_list('id', flat=True)), list(Paper.objects.order_by('id').values_list('id', flat=True)))
        with patch('search.benchmark.QUERIES', self.queries):
            prepare(self.root/'second')
        first = json.loads((self.packet/'manifest.json').read_text())
        second = json.loads((self.root/'second'/'manifest.json').read_text())
        for field in ('corpus_sha256','runs','pool'):
            self.assertEqual(first[field], second[field])
        with self.assertRaises(ValueError):
            prepare(self.packet)

    def test_reject_incomplete_duplicate_and_invalid_judgments(self):
        with self.assertRaisesRegex(ValueError, 'human review'):
            evaluate(self.packet,self.sheet,self.root/'report')
        self.assertFalse((self.root/'report').exists())
        for row in self.rows:
            row.update(grade='2', reviewer='Synthetic test fixture')
        for rows in (self.rows[:-1], self.rows+[self.rows[0]], [dict(r, grade='3') for r in self.rows], [dict(r, reviewer='') for r in self.rows]):
            self.write_rows(rows)
            with self.assertRaises(ValueError):
                evaluate(self.packet,self.sheet,self.root/'report')

    def test_frozen_evaluation_and_zero_relevance(self):
        for row in self.rows:
            row.update(grade='0', reviewer='Synthetic test fixture')
        self.write_rows(self.rows)
        # Evaluation must not depend on the current corpus or re-run either ranker.
        with patch('search.benchmark.search_papers', side_effect=AssertionError('Not frozen')):
            report = evaluate(self.packet,self.sheet,self.root/'report')
        self.assertEqual(report['zero_relevance_queries'], ['Q01'])
        self.assertIsNone(report['macro']['weighted']['nDCG@10']['value'])
        self.assertEqual(report['macro']['weighted']['precision@10']['value'], 0)
        with self.assertRaises(ValueError):
            evaluate(self.packet,self.sheet,self.root/'report')

    def test_reject_missing_ranker(self):
        manifest = json.loads((self.packet/'manifest.json').read_text())
        del manifest['runs']['Q01']['uniform']
        (self.packet/'manifest.json').write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, 'both declared rankers'):
            evaluate(self.packet,self.sheet,self.root/'report')

    def test_ai_reports_are_explicitly_labeled(self):
        for row in self.rows:
            row.update(grade='2', reviewer='AI: Synthetic test fixture')
        self.write_rows(self.rows)
        with self.assertRaisesRegex(ValueError, 'judgment-source ai'):
            evaluate(self.packet,self.sheet,self.root/'human-report')
        report = evaluate(self.packet,self.sheet,self.root/'ai-report', judgment_source='ai')
        self.assertEqual(report['judgment_source'], 'ai')
        self.assertIn('not human ground truth', report['limitations'])
        self.assertTrue((self.root/'ai-report'/'REPORT.md').read_text().startswith('# AI-reviewed'))
        self.assertEqual(report['macro']['weighted']['precision@10']['value'], 1)

    def test_reject_unknown_judgment_source(self):
        with self.assertRaisesRegex(ValueError, 'source must be'):
            evaluate(self.packet,self.sheet,self.root/'report', judgment_source='unknown')
