"""Offline evaluation: two independent reviewers and final adjudication required."""
import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from core.adjudication import evaluate_adjudicated_path

class Command(BaseCommand):
    help = 'Evaluate separately adjudicated labeled data; default report excludes source text and sample identifiers.'
    def add_arguments(self, parser):
        parser.add_argument('--dataset', required=True, help='Local JSON dataset path')
        parser.add_argument('--output', required=True, help='JSON report path')
        parser.add_argument('--include-case-details', action='store_true', help='Opt in to case identifiers in report')
    def handle(self, *args, **options):
        path=Path(options['dataset'])
        if not path.is_file(): raise CommandError('Dataset file not found')
        try:
            report=evaluate_adjudicated_path(path,options['include_case_details'])
        except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
            raise CommandError(f'Invalid adjudicated dataset: {exc}') from exc
        target=Path(options['output'])
        if target.resolve() == path.resolve(): raise CommandError('Output must not overwrite input dataset')
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        self.stdout.write(self.style.SUCCESS(f'Evaluated {report["sample_count"]} adjudicated cases; report: {target}'))
