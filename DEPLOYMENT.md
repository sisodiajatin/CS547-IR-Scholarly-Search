# Free recruiter demo on PythonAnywhere

This deployment serves the complete Django app, including the UI, FTS5 search,
registration, login and saved libraries. SQLite stays in your account's persistent
home directory. No local accounts or passwords are uploaded.

PythonAnywhere's free tier currently provides one web app/worker, 512 MiB storage
and a one-month web-app expiry. Renew it from the Web tab before its expiry date.
Use the supplied free domain; a custom domain is not required. This is a small
portfolio demo, not a high-traffic service. Hosting availability and limits are
controlled by PythonAnywhere.

## 1. Prepare the account

Create a free account at https://www.pythonanywhere.com/ (or its EU service).
Open a Bash console. Choose a Python version **3.10 or newer** that is also
available in your Web tab; use the same version for the virtualenv and web app.
The commands below use Python 3.13; substitute an available version if necessary.

```bash
git clone --depth 1 https://github.com/sisodiajatin/CS547-IR-Scholarly-Search.git
cd CS547-IR-Scholarly-Search
python3.13 -m venv .venv
source .venv/bin/activate
pip install --no-cache-dir -r requirements.txt
python scripts/setup_hosting.py --hostname YOUR_USERNAME.pythonanywhere.com
```

Replace the hostname with the exact free hostname offered by your account. EU
accounts use `YOUR_USERNAME.eu.pythonanywhere.com`. Do not install development
requirements or browser engines on the host.

The setup creates a random secret and database under `~/.config/scholarly/`,
runs migrations, checks FTS5 support, imports the 14,748-paper corpus and collects
CSS/JavaScript. It is safe to rerun: the secret and existing accounts are preserved,
and papers are updated by URL. Keep `hosting.json` private; never commit it.
The local reference database is about 42 MiB and the SQL source about 19 MiB;
check actual total usage with `du -sh ~` after installing dependencies.

The deployment check may report `security.W005` and `security.W021`: this project
does not enable HSTS for child subdomains or opt into browser HSTS preloading.
HTTPS redirects, secure cookies and one-year HSTS for the app hostname remain
enabled. These warnings do not prevent serving the free HTTPS domain.

## 2. Configure the Web tab

Add a web app using **Manual configuration**, with the same Python version.

| Setting | Value (replace YOUR_USERNAME) |
| --- | --- |
| Source code / working directory | `/home/YOUR_USERNAME/CS547-IR-Scholarly-Search` |
| Virtualenv | `/home/YOUR_USERNAME/CS547-IR-Scholarly-Search/.venv` |
| Static URL | `/static/` |
| Static directory | `/home/YOUR_USERNAME/CS547-IR-Scholarly-Search/scholar_search/staticfiles` |

Open the WSGI configuration file **linked on the Web tab** and replace its contents
with the following (the project must be cloned to the directory shown above):

```python
from pathlib import Path
import runpy

application = runpy.run_path(str(
    Path.home() / "CS547-IR-Scholarly-Search" / "deploy" / "pythonanywhere_wsgi.py"
))["application"]
```

Enable **Force HTTPS**, then click **Reload**. Open the free HTTPS URL shown in
the Web tab. Do not run `manage.py runserver` on the host. PythonAnywhere serves
static files and runs the WSGI application for you.

## 3. Verify before sharing

- Home page shows **Scholarly**, styled correctly, and 14,748 papers.
- Search `neural networks`; open a paper and return to the same results.
- Apply a year and change Any words / All words / Exact phrase.
- Create a test account, save a paper, log out/in and check My Library.
- Reload the web app and verify the account and saved paper still exist.
- Check the public URL at mobile width and confirm HTTP redirects to HTTPS.

Check the Web tab error log if startup fails. An FTS5 setup failure means the
selected Python/SQLite build is incompatible; use another available Python build
with FTS5, and recreate the virtualenv using that version. Do not disable HTTPS or
enable DEBUG on the public site to work around deployment errors.

## Updates and maintenance

Before applying migrations to an existing deployment, create a consistent SQLite
backup using the SQLite backup API (not a raw copy during writes), download it
privately, and keep within the account's disk quota.

```bash
cd ~/CS547-IR-Scholarly-Search
source .venv/bin/activate
git pull --ff-only
pip install --no-cache-dir -r requirements.txt
python scripts/setup_hosting.py --hostname YOUR_USERNAME.pythonanywhere.com --skip-import
```

Reload from the Web tab after updates. Omit `--skip-import` if updating the paper
corpus. Renew the free web app before the displayed expiry date. Never share a
real password in the recruiter demo; public search works without an account.
Account abuse throttling and password recovery are future hardening work; this
deployment does not add them.

Official references: [free limits](https://help.pythonanywhere.com/pages/FreeAccountsFeatures),
[Django deployment](https://help.pythonanywhere.com/pages/DeployExistingDjangoProject),
[static files](https://help.pythonanywhere.com/pages/DjangoStaticFiles),
[HTTPS](https://help.pythonanywhere.com/pages/ForcingHTTPS).
