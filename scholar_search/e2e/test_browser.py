"""Run explicitly: manage.py test e2e. Uses a disposable Django database."""
import os
from pathlib import Path
from urllib.parse import urlencode
from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from playwright.sync_api import sync_playwright, expect
from search.models import Paper, PaperRedirect, SavedPaper

ARTIFACTS = Path(__file__).resolve().parents[2] / "qa-artifacts"


class BrowserTests(StaticLiveServerTestCase):
    def setUp(self):
        self.user = User.objects.create_user("browser-reader", password="Browser-test-password-42!")
        for i in range(13):
            paper = Paper.objects.create(title=f"Neural research {i}: " + "Long scientific title " * 4,
                summary="This study examines neural systems and reproducible research. " * 30,
                authors="Ada Researcher, Bob Researcher, " * 8, published=f"2024-01-{i+1:02}", url=f"https://arxiv.org/abs/test-{i}")
            SavedPaper.objects.create(user=self.user, paper=paper)
        self.paper_id = paper.pk
        PaperRedirect.objects.create(old_id=99999, paper=paper)
        ARTIFACTS.mkdir(exist_ok=True)
        self.pw = sync_playwright().start()
        channel = os.environ.get("E2E_CHROMIUM_CHANNEL", "chrome")
        self.browser = self.pw.chromium.launch(channel=channel if channel else None, headless=True)
        self.context = self.browser.new_context(base_url=self.live_server_url, viewport={"width":1440,"height":1000})
        self.context.tracing.start(screenshots=True, snapshots=True, sources=True)
        self.page = self.context.new_page()
        self.errors = []
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))
        self.page.on("response", lambda response: self.errors.append(f"HTTP {response.status}: {response.url}") if response.status >= 500 else None)
        self.page.on("requestfailed", lambda request: self.errors.append(request.url) if request.resource_type in ("script", "stylesheet", "image") else None)

    def tearDown(self):
        self.context.tracing.stop(path=str(ARTIFACTS / (self._testMethodName + ".zip")))
        self.context.close(); self.browser.close(); self.pw.stop()
        self.assertEqual(self.errors, [])
        super().tearDown()

    def login(self):
        self.page.get_by_label("Username").fill("browser-reader")
        self.page.get_by_label("Password").fill("Browser-test-password-42!")
        self.page.get_by_role("button", name="Log in to workspace").click()

    def test_chart_and_result_roundtrip(self):
        self.page.goto(self.live_server_url)
        self.page.get_by_role("link", name="Browse 13 papers published in 2024").click()
        expect(self.page.locator('.results-meta')).to_contain_text('13 results in 2024')
        expect(self.page.locator('#year-mode')).to_have_value('exact')
        self.page.get_by_role('link',name='Next',exact=False).click()
        origin=self.page.url
        self.page.locator('[data-paper-link]').first.click()
        self.page.locator('[data-reader-back]').click()
        expect(self.page).to_have_url(origin)
        self.page.locator('[data-paper-link]').first.click()
        self.page.get_by_role('link',name='Log in to save this paper').click()
        self.login()
        self.page.get_by_role('button',name='Remove from library',exact=True).click()
        self.page.get_by_role('button',name='Save to library',exact=True).click()
        self.page.locator('[data-reader-back]').click()
        expect(self.page).to_have_url(origin)
        self.page.goto('/papers/99999/?'+urlencode({'return_to':'/library/?q=Neural&page=2'}))
        self.page.locator('[data-reader-back]').click()
        expect(self.page).to_have_url(self.live_server_url+'/library/?q=Neural&page=2')
        origin=self.page.url
        self.page.locator('[data-paper-link]').first.click()
        self.page.locator('[data-reader-back]').click()
        expect(self.page).to_have_url(origin)

    def test_responsive_layouts_and_navigation(self):
        for width in (360,390,768,1024,1440):
            self.page.set_viewport_size({'width':width,'height':900})
            for route,name in [('/', 'home'),('/resps/?q=neural','results'),(f'/papers/{self.paper_id}/','reader'),('/library/','library'),('/users/login/','login'),('/users/signup/','signup')]:
                self.page.goto(route)
                self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1'), f'Horizontal overflow: {width}, {route}')
                self.page.screenshot(path=str(ARTIFACTS/f'{name}-{width}.png'),full_page=True)
            if width<1024:
                self.page.get_by_role('button',name='Toggle navigation').click()
                expect(self.page.locator('#sidebar')).not_to_have_attribute('inert','')
                self.page.keyboard.press('Escape')
                expect(self.page.locator('[data-menu]')).to_be_focused()
                expect(self.page.locator('#sidebar')).to_have_attribute('inert','')
        self.page.goto('/users/login/')
        self.login()
        for width in (360,390,768,1024,1440):
            self.page.set_viewport_size({'width':width,'height':900})
            self.page.goto('/library/')
            expect(self.page.locator('[data-paper-link]').first).to_be_visible()
            self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth <= window.innerWidth+1'))
            self.page.screenshot(path=str(ARTIFACTS/f'library-signed-in-{width}.png'),full_page=True)

    def test_keyboard_errors_download_and_clipboard(self):
        self.page.goto('/resps/?q=neural')
        self.page.keyboard.press('/')
        expect(self.page.locator('#query')).to_be_focused()
        self.page.keyboard.press('Escape')
        self.page.keyboard.press('j')
        expect(self.page.locator('[data-paper-link]').nth(0)).to_be_focused()
        self.page.keyboard.press('j')
        expect(self.page.locator('[data-paper-link]').nth(1)).to_be_focused()
        self.page.keyboard.press('k')
        expect(self.page.locator('[data-paper-link]').nth(0)).to_be_focused()
        self.page.keyboard.press('Enter')
        expect(self.page.locator('.reading-pane')).to_be_visible()
        self.context.grant_permissions(['clipboard-read','clipboard-write'])
        self.page.get_by_role('button',name='Copy',exact=True).click()
        expect(self.page.locator('[data-toast]')).to_have_text('BibTeX citation copied.')
        self.assertIn('@misc',self.page.evaluate('navigator.clipboard.readText()'))
        self.page.evaluate("Object.defineProperty(navigator.clipboard, 'writeText', {value: () => Promise.reject(new Error('Denied'))})")
        self.page.get_by_role('button',name='Copy',exact=True).click()
        expect(self.page.locator('[data-toast]')).to_contain_text('Citation selected')
        with self.page.expect_download() as download:
            self.page.get_by_role('link',name='Export BibTeX').click()
        self.assertTrue(download.value.suggested_filename.endswith('.bib'))
        self.page.goto('/users/signup/')
        self.page.get_by_label('Username').fill('newreader')
        self.page.locator('#id_password1').fill('abc');self.page.locator('#id_password2').fill('abc')
        self.page.get_by_role('button',name='Create workspace').click()
        expect(self.page.locator('.field-error').first).to_be_visible()
        self.assertTrue(self.page.evaluate("(() => {const ids=[...document.querySelectorAll('[id]')].map(e=>e.id);return ids.length===new Set(ids).size})()"))
        self.page.screenshot(path=str(ARTIFACTS/'signup-errors.png'),full_page=True)
        self.page.goto('/resps/?q=zzzzzzzzzzzzzzz')
        expect(self.page.locator('.empty-state')).to_be_visible()
        self.page.goto('/resps/?q=neural')
        self.page.locator('#query').fill('research')
        self.page.locator('.execute').click()
        self.page.go_back()
        expect(self.page.locator('.execute')).to_contain_text('EXECUTE')

    def test_desktop_zoom(self):
        # Emulate the layout viewport of a 1440px display at 200% browser zoom.
        # This tests reflow, not the browser chrome's zoom control.
        self.page.set_viewport_size({'width':720,'height':500})
        for route in ('/resps/?q=neural', f'/papers/{self.paper_id}/'):
            self.page.goto(route)
            self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth <= window.innerWidth+1'))
        self.page.screenshot(path=str(ARTIFACTS/'reflow-200.png'),full_page=True)

    def test_matching_modes(self):
        self.page.goto('/resps/?q=neural+research')
        for mode in ('all', 'phrase'):
            self.page.get_by_label('MATCH WORDS', exact=True).select_option(mode)
            self.page.get_by_role('button', name='Apply filters').click()
            expect(self.page.locator('.results-meta')).to_contain_text('13 results')
            expect(self.page.locator('#match-mode')).to_have_value(mode)
            self.page.get_by_role('link', name='Next', exact=False).click()
            origin = self.page.url
            self.page.locator('[data-paper-link]').first.click()
            self.page.locator('[data-reader-back]').click()
            expect(self.page).to_have_url(origin)
            self.page.locator('#query').fill('research neural')
            self.page.locator('.execute').click()
            expect(self.page.locator('#match-mode')).to_have_value(mode)
            expect(self.page.locator('.results-meta')).to_contain_text('0 results' if mode == 'phrase' else '13 results')
            self.page.locator('#query').fill('neural research')
            self.page.locator('.execute').click()

    def test_other_engines_smoke(self):
        for engine in ('firefox','webkit'):
            with self.subTest(engine=engine):
                browser=getattr(self.pw,engine).launch(headless=True, timeout=30000)
                page=browser.new_page(viewport={'width':1440,'height':900})
                engine_errors = []
                page.on('pageerror', lambda error: engine_errors.append(str(error)))
                try:
                    page.goto(self.live_server_url+'/resps/?year=2024&year_mode=exact')
                    expect(page.locator('.results-meta')).to_contain_text('13 results in 2024')
                    origin=page.url
                    page.locator('[data-paper-link]').first.click()
                    page.locator('[data-reader-back]').click()
                    expect(page).to_have_url(origin)
                    page.screenshot(path=str(ARTIFACTS/f'{engine}-results.png'),full_page=True)
                    page.goto(self.live_server_url+'/resps/?q=neural+research')
                    page.locator('#match-mode').select_option('phrase')
                    with page.expect_navigation(wait_until='load'):
                        page.get_by_role('button',name='Apply filters').click()
                    expect(page.locator('.results-meta')).to_contain_text('13 results')
                    expect(page.locator('#match-mode')).to_have_value('phrase')
                    page.set_viewport_size({'width':390,'height':900})
                    self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= window.innerWidth+1'))
                    page.get_by_role('button',name='Toggle navigation').click()
                    page.keyboard.press('Escape')
                    expect(page.locator('[data-menu]')).to_be_focused()
                    page.screenshot(path=str(ARTIFACTS/f'{engine}-mobile.png'),full_page=True)
                    self.assertEqual(engine_errors, [])
                finally:
                    browser.close()
