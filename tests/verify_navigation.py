"""Run with Playwright and Chrome against the local server: python3 tests/verify_navigation.py."""

import os
import shutil

from playwright.sync_api import sync_playwright

BASE = os.environ.get("REVISION_URL", "http://localhost:8080").rstrip("/")
SUBJECTS = {
    "Home": "/",
    "Chinese": "/chinese/",
    "Geography": "/geography/",
    "English": "/english/",
    "Maths": "/maths/",
}
PAGES = {route: subject for subject, route in SUBJECTS.items()} | {
    "/chinese/words.html": "Chinese",
    "/chinese/unit-1.html": "Chinese",
    "/chinese/year9-revision.html": "Chinese",
    "/geography/food-security.html": "Geography",
}

with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path=os.environ.get("CHROME_BINARY") or shutil.which("google-chrome"),
        headless=True, args=["--no-sandbox"],
    )
    for width in (320, 390):
        page = browser.new_page(
            viewport={"width": width, "height": 844},
            is_mobile=True, has_touch=True,
        )
        nav = page.get_by_role("navigation", name="Subjects")
        for path, current in PAGES.items():
            page.goto(BASE + path)
            assert nav.get_by_role("link").count() == len(SUBJECTS)
            expected_current = "page" if path in SUBJECTS.values() else "location"
            assert nav.locator(f'[aria-current="{expected_current}"]').inner_text() == current
            for subject, route in SUBJECTS.items():
                link = nav.get_by_role("link", name=subject, exact=True)
                assert link.evaluate("(link) => link.pathname") == route
                bounds = link.bounding_box()
                assert bounds["width"] >= 44 and bounds["height"] >= 44
                assert bounds["x"] >= 0 and bounds["x"] + bounds["width"] <= width

        page.goto(BASE + "/geography/")
        page.get_by_role("link", name="Practice exam", exact=True).tap()
        page.wait_for_url(BASE + "/geography/#practice")
        heading = page.get_by_role("heading", name="Practice exam", exact=True)
        nav_bottom = nav.bounding_box()["height"]
        assert nav.bounding_box()["y"] == 0
        assert nav_bottom <= heading.bounding_box()["y"] < 160
        nav.get_by_role("link", name="Maths").tap()
        page.wait_for_url(BASE + "/maths/")
        page.go_back()
        page.wait_for_url(BASE + "/geography/#practice")
        heading.wait_for()
        assert nav_bottom <= heading.bounding_box()["y"] < 160

        page.goto(BASE + "/chinese/year9-revision.html")
        page.get_by_role("link", name="Grammar", exact=True).tap()
        page.locator("section#grammar.on").wait_for()
        nav.get_by_role("link", name="Chinese").tap()
        page.wait_for_url(BASE + "/chinese/")
        nav.get_by_role("link", name="Home", exact=True).tap()
        page.wait_for_url(BASE + "/")
        page.close()
        print(f"PASS: subject links, anchor clearance and original guide tabs at {width}px")
    browser.close()
