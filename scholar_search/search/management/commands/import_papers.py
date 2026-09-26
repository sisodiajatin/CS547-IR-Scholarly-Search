"""Import the bundled MySQL dump as data, without executing SQL."""
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from search.models import Paper

# MySQL quoted strings support backslash escapes and doubled apostrophes.
VALUE = r"(?:NULL|\d+|'(?:[^'\\]|\\.|'')*')"
ROW = re.compile(r"\((" + VALUE + r"),(" + VALUE + r"),(" + VALUE + r"),(" + VALUE + r"),(" + VALUE + r"),(" + VALUE + r")\)")
ESCAPES = {"0": "\0", "n": "\n", "r": "\r", "t": "\t", "b": "\b", "Z": "\x1a"}


def decode(value):
    if value == "NULL":
        return None
    if not value.startswith("'"):
        return int(value)
    return re.sub(r"\\(.)|''", lambda m: ESCAPES.get(m[1], m[1]) if m[1] else "'", value[1:-1])


def parse_rows(text):
    position = 0
    for match in ROW.finditer(text):
        if text[position:match.start()].strip(" ,\r\n"):
            raise ValueError("Unsupported data in papers INSERT")
        yield [decode(v) for v in match.groups()]
        position = match.end()
    if text[position:].strip(" ;\r\n"):
        raise ValueError("Malformed papers INSERT")


class Command(BaseCommand):
    help = "Import papers from the bundled MySQL dump (safe to rerun)."

    def add_arguments(self, parser):
        parser.add_argument("path", type=Path)

    @transaction.atomic
    def handle(self, *args, **options):
        count = 0
        try:
            with options["path"].open(encoding="utf-8") as source:
                for line in source:
                    if not line.startswith("INSERT INTO `papers` VALUES "):
                        continue
                    batch = []
                    for pk, title, summary, authors, published, url in parse_rows(line.split(" VALUES ", 1)[1]):
                        if not url or urlsplit(url).scheme not in ("http", "https"):
                            raise ValueError("Paper URL must use HTTP or HTTPS")
                        batch.append(Paper(id=pk, title=title or "Untitled", summary=summary or "",
                            authors=authors or "Unknown authors", published=date.fromisoformat(published) if published else None,
                            url=url))
                        count += 1
                        if len(batch) == 250:
                            self.save_batch(batch)
                            batch = []
                    self.save_batch(batch)
            if not count:
                raise ValueError("No papers found in this dump")
        except (OSError, ValueError) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(
            f"Processed {count:,} source rows; {Paper.objects.count():,} unique papers in the corpus. Search index updated."
        ))

    def save_batch(self, batch):
        # URL is the paper identity. Preserve the existing primary key and any
        # saved references when a duplicate source row has a different ID.
        Paper.objects.bulk_create(batch, update_conflicts=True, unique_fields=["url"],
            update_fields=["title", "summary", "authors", "published", "url"])
