from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from search.benchmark import prepare, evaluate


class Command(BaseCommand):
    help = "Prepare a blinded human-judging pilot or score its completed judgments."
    def add_arguments(self, parser):
        sub = parser.add_subparsers(dest="operation", required=True)
        prep = sub.add_parser("prepare")
        prep.add_argument("--output", type=Path, required=True)
        prep.add_argument("--experiment", choices=["ranking", "matching"], default="ranking")
        score = sub.add_parser("evaluate")
        score.add_argument("packet", type=Path)
        score.add_argument("--judgments", type=Path, required=True)
        score.add_argument("--output", type=Path, required=True)
        score.add_argument("--judgment-source", choices=["human", "ai"], default="human")
    def handle(self, *args, **options):
        try:
            if options["operation"] == "prepare":
                count = prepare(options["output"], experiment=options["experiment"])
                self.stdout.write(self.style.SUCCESS(f"Prepared {count} judgments for the selected experiment. Grades are blank."))
            else:
                evaluate(options["packet"], options["judgments"], options["output"], judgment_source=options["judgment_source"])
                self.stdout.write(self.style.SUCCESS(f"Saved {options['judgment_source']}-reviewed metrics and report."))
        except (ValueError, OSError, KeyError, TypeError) as exc:
            raise CommandError(str(exc)) from exc
