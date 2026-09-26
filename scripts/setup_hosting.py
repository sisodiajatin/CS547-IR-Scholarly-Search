"""Prepare a persistent, HTTPS-only Django deployment without copying local users."""
import argparse
import json
import os
from pathlib import Path
import re
import secrets
import sys

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = Path.home() / ".config" / "scholarly" / "hosting.json"


def configure(path=DEFAULT_CONFIG):
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    os.environ.update(config)
    sys.path.insert(0, str(ROOT / "scholar_search"))
    os.environ["DJANGO_SETTINGS_MODULE"] = "scholar_search.settings"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hostname", required=True, help="Your exact public hostname, without https://")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--skip-import", action="store_true", help="Use only on updates when the corpus is already imported")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?", args.hostname):
        parser.error("Use a hostname such as username.pythonanywhere.com, without a path or scheme")
    args.config = args.config.expanduser().resolve()
    args.config.parent.mkdir(parents=True, exist_ok=True)
    if args.config.exists():
        config = json.loads(args.config.read_text(encoding="utf-8"))
        if config["DJANGO_ALLOWED_HOSTS"] != args.hostname:
            parser.error("Existing configuration uses a different hostname; edit it explicitly before continuing")
    else:
        config = {
            "DJANGO_DEBUG": "false",
            "DJANGO_SECRET_KEY": secrets.token_urlsafe(64),
            "DJANGO_ALLOWED_HOSTS": args.hostname,
            "DJANGO_DB_PATH": str(args.config.parent / "scholarly.sqlite3"),
        }
        with args.config.open("x", encoding="utf-8") as target:
            json.dump(config, target, indent=2)
        args.config.chmod(0o600)
    configure(args.config)
    import django
    django.setup()
    from django.core.management import call_command
    from django.db import connection

    # Fail early if the host's SQLite cannot run this project's search engine.
    with connection.cursor() as cursor:
        cursor.execute("CREATE VIRTUAL TABLE temp.hosting_fts_check USING fts5(text)")
        cursor.execute("DROP TABLE temp.hosting_fts_check")
    call_command("migrate", interactive=False)
    if not args.skip_import:
        call_command("import_papers", ROOT / "arxiv_papers.sql")
    call_command("collectstatic", interactive=False)
    call_command("check", deploy=True)
    print("Hosting data prepared. Configure the Web tab and reload to publish.")
    print(f"Private configuration: {args.config}")
    print(f"Static directory: {ROOT / 'scholar_search' / 'staticfiles'}")


if __name__ == "__main__":
    main()
