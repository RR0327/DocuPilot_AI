"""Inspect or recover stale extraction jobs without automatic destructive changes."""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from core.models import ProcessingJob
from core.processing import classify_stale_job, recover_job, BrokerUnavailable


class Command(BaseCommand):
    help = "Inspect stale queued/running jobs; --apply to recover, dry-run by default."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--queued-minutes", type=int, default=30)
        parser.add_argument("--running-minutes", type=int, default=120)
        parser.add_argument("--max-requeues", type=int, default=2)

    def handle(self, *args, **opts):
        for name in ("queued_minutes", "running_minutes", "max_requeues"):
            if opts[name] < 1:
                raise CommandError(f"{name} must be positive")
        now = timezone.now()
        counts = {"queued": 0, "running": 0, "requeued": 0, "marked_failed": 0, "recovery_exhausted": 0, "broker_unavailable": 0}
        for job in ProcessingJob.objects.filter(state__in=["queued", "running"]).iterator():
            category = classify_stale_job(job, now, opts["queued_minutes"], opts["running_minutes"])
            if not category:
                continue
            counts[category] += 1
            if not opts["apply"]:
                continue
            try:
                action = recover_job(job, now=now, queued_minutes=opts["queued_minutes"], running_minutes=opts["running_minutes"], max_requeues=opts["max_requeues"])
                if action in counts:
                    counts[action] += 1
            except BrokerUnavailable:
                counts["broker_unavailable"] += 1
        self.stdout.write(("APPLIED" if opts["apply"] else "DRY RUN") + " " + ", ".join(f"{k}={v}" for k, v in counts.items()))
        if opts["apply"] and counts["broker_unavailable"]:
            raise CommandError("Some jobs could not be requeued; check Redis and retry")
