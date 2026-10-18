"""Local classification regression report (synthetic cases)."""
import json
from django.core.management.base import BaseCommand
from core.classification_evaluation import run_fixture


class Command(BaseCommand):
    help = "Evaluate classification rules on the bundled synthetic labeled cases"

    def add_arguments(self, parser):
        parser.add_argument("--output", help="Optional report path")

    def handle(self, *args, **options):
        report = run_fixture()
        text = json.dumps(report, indent=2, ensure_ascii=False)
        if options.get('output'):
            from pathlib import Path
            Path(options['output']).write_text(text + "\n", encoding="utf-8")
            self.stdout.write(self.style.SUCCESS("Classification report saved"))
        else:
            self.stdout.write(text)
