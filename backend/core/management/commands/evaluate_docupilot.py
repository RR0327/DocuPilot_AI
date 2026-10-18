"""Local, reversible benchmark of production retrieval and invoice code paths."""
import json
import uuid
from pathlib import Path
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from core.models import Document, DocumentPage
from core.search import rebuild_document_chunks, retrieve
from core.invoice_extraction import parse_invoice_pages
from core.evaluation_metrics import (retrieval_metrics, invoice_field_accuracy,
                                     character_error_rate, check_source_excerpt)


class Command(BaseCommand):
    help = 'Evaluate document evidence and invoice extraction on synthetic examples; rolls back all fixture records.'

    def add_arguments(self, parser):
        parser.add_argument('--fixture', default=str(Path(__file__).resolve().parents[3] / 'evaluation' / 'sample_cases.json'))
        parser.add_argument('--mode', choices=['keyword', 'semantic', 'hybrid'], default='keyword')
        parser.add_argument('--output', default=None, help='Optional local path for JSON metrics')

    def handle(self, *args, **options):
        path = Path(options['fixture'])
        try:
            fixture = json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(fixture['documents'], list) or not isinstance(fixture['queries'], list):
                raise ValueError('documents and queries must be arrays')
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise CommandError(f'Invalid evaluation fixture: {exc}') from exc
        # Never retain temporary records; a transaction rolls back even when successful.
        try:
            with transaction.atomic():
                user = get_user_model().objects.create_user(username='eval_' + uuid.uuid4().hex, password=None)
                mapping = {}
                for entry in fixture['documents']:
                    key = entry['key']
                    if key in mapping:
                        raise ValueError('Duplicate fixture document key')
                    doc = Document.objects.create(owner=user, title=key, file_type='txt', processing_status='completed')
                    for i, text in enumerate(entry['pages'], start=1):
                        DocumentPage.objects.create(document=doc, page_number=i, extracted_text=text)
                    rebuild_document_chunks(doc)
                    mapping[key] = doc
                results = []
                for entry in fixture['queries']:
                    expected = entry.get('expected')
                    if expected is not None and expected not in mapping:
                        raise ValueError('Query expects an unknown fixture document')
                    hits = retrieve(user, entry['question'], mode=options['mode'], limit=5)
                    ranked = [hit.document_title for hit in hits]
                    integrity = all(
                        mapping[hit.document_title].pages.get(page_number=hit.page_number).extracted_text.find(hit.excerpt) >= 0
                        for hit in hits
                    )
                    results.append({'expected': expected, 'ranked': ranked,
                                    'source_integrity': int(integrity)})
                invoices = []
                for entry in fixture.get('invoices', []):
                    if entry['document'] not in mapping:
                        raise ValueError('Invoice fixture document missing')
                    predicted = parse_invoice_pages(mapping[entry['document']].pages.order_by('page_number'))['fields']
                    invoices.append((entry['expected_fields'], predicted))
                metrics = {
                    'benchmark': 'local_fixture_not_production_accuracy',
                    'retrieval_mode': options['mode'],
                    'retrieval': retrieval_metrics(results),
                    'invoice': invoice_field_accuracy(invoices),
                    'ocr_samples': [
                        {'name': row['name'], 'character_error_rate': character_error_rate(row['reference'], row['recognized'])}
                        for row in fixture.get('ocr_samples', [])
                    ],
                }
                transaction.set_rollback(True)
        except Exception as exc:
            raise CommandError(f'Evaluation failed (all temporary records rolled back): {exc}') from exc
        output = json.dumps(metrics, indent=2, ensure_ascii=False)
        if options['output']:
            Path(options['output']).write_text(output + '\n', encoding='utf-8')
        self.stdout.write(output)
