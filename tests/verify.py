"""Run against the existing server: python3 tests/verify.py.

Browser checks need the optional Python playwright package and installed Chrome.
There are no runtime dependencies for the website.
"""
import json
import os
from pathlib import Path
import shutil
import urllib.request

from playwright.sync_api import sync_playwright
from review import run_review

ROOT = Path(__file__).resolve().parents[1]
BASE = os.environ.get("REVISION_URL", "http://localhost:8080")
SHOTS = Path("/home/ubuntu/shots")
subjects = {}

print("SUBJECT COUNTS")
for name in ("geography", "english", "maths", "chinese"):
    data = json.loads((ROOT / name / "data.json").read_text())
    subjects[name] = data
    bank = sum(len(s["questions"]) for e in data["exams"] for s in e["sections"])
    print(f'{name}: {len(data["notes"])} notes, {len(data["flashcards"])} flashcards, '
          f'{len(data["exams"])} exams, {bank} bank questions')
    for item in data["notes"] + data["flashcards"]:
        assert item["source"]
    for exam in data["exams"]:
        assert exam["source"]
        for section in exam["sections"]:
            if section.get("choose") == 1:
                assert len({q["marks"] for q in section["questions"]}) == 1
            for question in section["questions"]:
                assert question["source"] and question["marks"] > 0
                if question["type"] == "multiple-choice":
                    assert 0 <= question["answer"] < len(question["options"])
                else:
                    assert question["modelAnswer"]

print("GEOGRAPHY PAPERS")
for exam in subjects["geography"]["exams"]:
    attempted = sum(1 if s.get("choose") == 1 else len(s["questions"])
                    for s in exam["sections"])
    bank = sum(len(s["questions"]) for s in exam["sections"])
    marks = [s["questions"][0]["marks"] if s.get("choose") == 1
             else sum(q["marks"] for q in s["questions"]) for s in exam["sections"]]
    expected = {"study-guide": 50, "2023": 20, "2025": 40}[exam["id"]]
    assert sum(marks) == expected
    print(f'{exam["title"]}: {attempted} attempted / {bank} bank questions; '
          f'section marks {marks}; total {sum(marks)}; {exam["durationMinutes"]} minutes')

print("NOTES AND SOURCES")
for name, data in subjects.items():
    for note in data["notes"]:
        print(f'{name}: {note["heading"]} — {note["source"]}')

print("HTTP STATUS")
pages = sorted(ROOT.rglob("*.html"))
resources = pages + sorted(ROOT.rglob("*.json"))
for path in resources:
    relative = path.relative_to(ROOT).as_posix()
    status = urllib.request.urlopen(BASE + "/" + relative).status
    assert status == 200
    print(status, relative)

with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path=os.environ.get("CHROME_BINARY") or shutil.which("google-chrome"),
        headless=True, args=["--no-sandbox"])
    page = browser.new_page(viewport={"width": 390, "height": 1100})
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("console", lambda message: errors.append(message.text)
            if message.type == "error" else None)
    for path in pages:
        relative = path.relative_to(ROOT).as_posix()
        page.goto(BASE + "/" + relative)
        page.wait_for_load_state("networkidle")
        if path.name == "index.html" and path.parent.name in ("geography", "english", "maths"):
            page.locator("#notes").wait_for()
        if path.name == "unit-1.html":
            page.locator("#notes").wait_for()
        print("CHROME OK", relative)
    assert not errors, errors
    print("PASS: every HTML page loaded; zero JavaScript exceptions or console errors")

    page.goto(BASE + "/geography/#practice")
    page.locator("#exam-picker").wait_for()
    assert len(page.locator("#exam-picker option").all()) == 3
    assert "Self-mark total: 0 / 50" in page.inner_text("#practice")
    for mark in page.locator("#practice input[type=number]").all():
        mark.fill(mark.get_attribute("max"))
    assert "Self-mark total: 50 / 50" in page.inner_text("#practice")
    page.reload()
    page.get_by_text("Self-mark total: 50 / 50", exact=True).wait_for()
    page.locator(".essay-picker").select_option("1")
    assert "Self-mark total: 34 / 50" in page.inner_text("#practice")
    page.locator("#practice input[type=number]").last.fill("999")
    assert "Self-mark total: 50 / 50" in page.inner_text("#practice")
    page.locator(".essay-picker").select_option("2")
    assert "Self-mark total: 34 / 50" in page.inner_text("#practice")
    page.locator("#practice details").last.locator("summary").click()
    assert "desert" in page.locator("#practice details").last.inner_text()
    page.locator("#exam-picker").select_option("1")
    assert "Self-mark total: 0 / 20" in page.inner_text("#practice")
    page.locator("#practice .choices").first.get_by_role("button", name="True", exact=True).click()
    assert "Correct." in page.inner_text("#practice")
    page.locator("#practice input[type=number]").first.fill("1")
    page.locator("#exam-picker").select_option("2")
    assert "Self-mark total: 0 / 40" in page.inner_text("#practice")
    assert "Rice seedlings in soil containing salt." in page.inner_text("#practice")
    page.get_by_role("button", name="Start timer", exact=True).click()
    page.get_by_role("button", name="Pause timer", exact=True).wait_for()
    page.get_by_role("button", name="Pause timer", exact=True).click()
    page.get_by_role("button", name="Resume timer", exact=True).wait_for()
    print("PASS: all three papers, choose-one essays, correct totals, independent saved marks, clamping and timer")

    page.goto(BASE + "/english/")
    page.locator(".card").wait_for()
    first = page.locator(".card").inner_text()
    page.locator(".card").click()
    assert first != page.locator(".card").inner_text()
    assert page.locator(".card").inner_text() == subjects["english"]["flashcards"][0]["definition"]
    page.get_by_role("button", name="Mark as known", exact=True).click()
    page.reload()
    page.get_by_role("button", name="✓ Known — undo", exact=True).wait_for()
    page.goto(BASE + "/chinese/unit-1.html")
    page.locator(".note").first.locator("summary").click()
    assert "亲戚" in page.locator(".note").first.inner_text()
    assert page.locator("#practice").count() == 0
    print("PASS: English source flashcards/persistence and Chinese Unit 1 notes")

    page.goto(BASE + "/maths/")
    page.locator("#exam-picker").wait_for()
    for i, exam in enumerate(subjects["maths"]["exams"][:3]):
        assert exam["id"] == f"tech-active-{i + 1}"
        assert [sum(q["marks"] for q in s["questions"])
                for s in exam["sections"]] == [20, 15, 25]
        assert len(exam["sections"][1]["questions"]) == 15
        assert exam["durationMinutes"] == 70
        page.select_option("#exam-picker", str(i))
        assert page.locator("#practice .question").count() == 35
        assert "Self-mark total: 0 / 60" in page.inner_text("#practice")
        assert "Could not load" not in page.inner_text("body")
        question = exam["sections"][1]["questions"][0]
        page.locator("#practice .choices").first.get_by_role(
            "button", name=question["options"][question["answer"]], exact=True).click()
        assert "Correct." in page.locator("#practice .choices").first.locator("..").inner_text()
        page.locator("#practice details").first.locator("summary").click()
        assert "Final answer:" in page.locator("#practice details").first.inner_text()
    print("PASS: three 60-mark tech-active papers, 105 rendered questions, MC feedback and worked solutions")
    gauss_index = next(i for i, exam in enumerate(subjects["maths"]["exams"])
                       if exam["id"] == "gauss-examples")
    page.select_option("#exam-picker", str(gauss_index))
    page.locator("#practice details").first.locator("summary").click()
    assert "298" in page.locator("#practice details").first.inner_text()
    page.locator(".note").nth(1).locator("summary").click()
    assert "Source:" in page.locator(".note").nth(1).inner_text()
    print("PASS: Maths sourced notes and worked-example answer reveal")

    # Fixture responses exercise generic empty/error states without adding content.
    page.route("**/maths/data.json", lambda route: route.fulfill(
        json={"notes": [], "flashcards": [], "exams": []}))
    page.goto(BASE + "/maths/")
    page.get_by_text("No source-backed material available in this section yet.",
                     exact=True).first.wait_for()
    assert page.get_by_text("No source-backed material available in this section yet.",
                            exact=True).count() == 3
    page.unroute("**/maths/data.json")
    page.route("**/maths/data.json", lambda route: route.abort())
    page.goto(BASE + "/maths/")
    page.get_by_text("Could not load your revision material.", exact=False).wait_for()
    page.unroute("**/maths/data.json")
    print("PASS: empty and fetch-error states")

    # Fresh storage for screenshots, not the self-mark test state.
    page.close()
    context = browser.new_context(viewport={"width": 390, "height": 1100})
    page = context.new_page()
    page.goto(BASE + "/geography/#practice")
    page.locator("#exam-picker").wait_for()
    page.locator("#practice").scroll_into_view_if_needed()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.screenshot(path=str(SHOTS / "geography-practice-390.png"))
    page.goto(BASE + "/maths/")
    page.locator("#notes").wait_for()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.screenshot(path=str(SHOTS / "maths-hub-390.png"))
    print("PASS: 390px screenshots, no horizontal overflow")
    print(SHOTS / "geography-practice-390.png")
    print(SHOTS / "maths-hub-390.png")
    run_review(browser, BASE)
    browser.close()
