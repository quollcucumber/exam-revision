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
    expected = {"study-guide": 50, "2023": 22, "2025": 40}[exam["id"]]
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
    for mark in page.locator("#practice input[type=number]:not([readonly])").all():
        mark.fill(mark.get_attribute("max"))
    assert "Self-mark total: 45 / 50" in page.inner_text("#practice")
    page.locator("#practice .choices").first.get_by_role("button", name="Biome", exact=True).click()
    assert "Self-mark total: 46 / 50" in page.inner_text("#practice")
    page.locator("#practice textarea").first.fill("My biome answer")
    page.reload()
    page.get_by_text("Self-mark total: 46 / 50", exact=True).wait_for()
    assert page.locator("#practice textarea").first.input_value() == "My biome answer"
    page.get_by_role("button", name="Start timer", exact=True).click()
    page.locator(".essay-picker").select_option("1")
    assert "Self-mark total: 30 / 50" in page.inner_text("#practice")
    page.get_by_role("button", name="Pause timer", exact=True).wait_for()
    assert page.locator("#practice textarea").first.input_value() == "My biome answer"
    page.locator("#practice input[type=number]").last.fill("999")
    assert page.locator("#practice input[type=number]").last.input_value() == "16"
    assert "Self-mark total: 46 / 50" in page.inner_text("#practice")
    page.locator(".essay-picker").select_option("2")
    assert "Self-mark total: 30 / 50" in page.inner_text("#practice")
    page.locator("#practice details").last.locator("summary").click()
    assert "desert" in page.locator("#practice details").last.inner_text()
    page.locator("#exam-picker").select_option("1")
    assert "Self-mark total: 0 / 22" in page.inner_text("#practice")
    page.locator("#practice .choices").first.get_by_role("button", name="False", exact=True).click()
    assert "Correct." in page.inner_text("#practice")
    assert "Self-mark total: 1 / 22" in page.inner_text("#practice")
    page.get_by_role("button", name="Try again", exact=True).click()
    assert "Self-mark total: 0 / 22" in page.inner_text("#practice")
    page.evaluate("localStorage.setItem('geography-exam-2023', JSON.stringify({marks: {'0-0': 1, '1-0': 2}}))")
    page.reload()
    page.locator("#exam-picker").select_option("1")
    assert "Self-mark total: 2 / 22" in page.inner_text("#practice")
    page.locator("#exam-picker").select_option("2")
    assert "Self-mark total: 0 / 40" in page.inner_text("#practice")
    assert "Rice seedlings in soil containing salt." in page.inner_text("#practice")
    page.get_by_role("button", name="Start timer", exact=True).click()
    page.get_by_role("button", name="Pause timer", exact=True).wait_for()
    page.get_by_role("button", name="Pause timer", exact=True).click()
    page.get_by_role("button", name="Resume timer", exact=True).wait_for()
    print("PASS: all three papers, choose-one essays, auto-marked MCQs, saved answers, correct totals, independent saved marks, clamping and timer")

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

    studio_context = browser.new_context(viewport={"width": 1280, "height": 1100})
    list1 = json.loads((ROOT / "chinese/list-1.json").read_text())
    words1 = [w for c in list1["categories"] for w in c["words"]]
    first_shi = next(i for i, w in enumerate(words1) if w["chinese"] == "是")
    studio_context.add_init_script(f"""
        let remaining = {len(words1)};
        Math.random = () => --remaining === {first_shi} ? 0 : 0.999999;
    """)
    studio = studio_context.new_page()
    studio.goto(BASE + "/chinese/")
    studio.evaluate("localStorage.setItem('chinese-known', JSON.stringify(['我', '只', '是', '爷爷', JSON.stringify(['你', 'nǐ'])]))")
    studio.goto(BASE + "/chinese/words.html#quiz")
    studio.locator(".choices").wait_for()
    assert studio.locator("#study .hanzi").inner_text() == "是"
    options = studio.locator(".choices button").all_text_contents()
    assert "yes / correct" in options and "to be" not in options
    assert len(options) == len(set(options))
    studio.get_by_role("button", name="yes / correct", exact=True).click()
    assert studio.inner_text(".status") == "Correct. Nice work!"
    assert all(b.is_disabled() for b in studio.locator(".choices button").all())
    migrated = studio.evaluate("JSON.parse(localStorage.getItem('chinese-known'))")
    assert json.dumps(["我", "wǒ", "I, me"], ensure_ascii=False, separators=(",", ":")) in migrated
    assert json.dumps(["你", "nǐ", "you"], ensure_ascii=False, separators=(",", ":")) in migrated
    assert json.dumps(["你", "nǐ"], ensure_ascii=False, separators=(",", ":")) not in migrated
    assert "我" not in migrated and "只" not in migrated and "是" not in migrated
    assert "爷爷" in migrated
    print("PASS: Chinese quiz excludes alternate valid answers; unique legacy progress migrates")

    studio.get_by_role("button", name="Flashcards", exact=True).click()
    studio.select_option("#category", "Adverbs & Function Words")
    for _ in range(48):
        if studio.locator(".card .hanzi").inner_text() == "只":
            break
        studio.get_by_role("button", name="Next →", exact=True).click()
    assert studio.locator(".card .pinyin").inner_text() == "zhǐ"
    studio.get_by_role("button", name="Mark as known", exact=True).click()
    studio.select_option("#category", "Measure Words")
    for _ in range(13):
        if studio.locator(".card .hanzi").inner_text() == "只":
            break
        studio.get_by_role("button", name="Next →", exact=True).click()
    assert studio.locator(".card .pinyin").inner_text() == "zhī"
    assert studio.get_by_role("button", name="Mark as known", exact=True).count() == 1
    studio.select_option("#list", "2")
    studio.wait_for_function("document.querySelector('#summary').textContent.startsWith('672')")
    studio.get_by_role("button", name="✓ Known — undo", exact=True).wait_for()
    studio.select_option("#category", index=1)
    category = studio.input_value("#category")
    studio.reload()
    studio.locator(".card").wait_for()
    assert studio.input_value("#list") == "2" and studio.input_value("#category") == category
    assert "Card 1 of 40" in studio.inner_text("#study")
    print("PASS: Chinese homographs stay separate; second-list legacy progress and selection persist")

    studio.locator("h1").click()
    studio.keyboard.press("ArrowRight")
    assert "Card 2 of 40" in studio.inner_text("#study")
    studio.keyboard.press("Space")
    assert "Answer · Tap to return" in studio.inner_text(".card")
    studio.keyboard.press("ArrowLeft")
    assert "Card 1 of 40" in studio.inner_text("#study")
    assert "Answer ·" not in studio.inner_text(".card")
    studio.locator("#category").focus()
    studio.locator("#category").dispatch_event("keydown", {"key": "ArrowRight", "bubbles": True})
    assert "Card 1 of 40" in studio.inner_text("#study")
    studio.get_by_role("button", name="Next →", exact=True).click()
    front = studio.locator(".card").inner_text()
    studio.get_by_role("button", name="Mark as known", exact=True).focus()
    studio.keyboard.press("Space")
    studio.get_by_role("button", name="✓ Known — undo", exact=True).wait_for()
    assert studio.locator(".card").inner_text() == front
    assert "Answer ·" not in studio.inner_text(".card")
    studio.locator(".card").focus()
    studio.keyboard.press("Space")
    assert "Answer · Tap to return" in studio.inner_text(".card")
    print("PASS: Space activates focused Chinese controls and natively flips the focused card")
    studio.get_by_role("button", name="Table", exact=True).click()
    studio.get_by_role("button", name="Flashcards", exact=True).click()
    studio.go_back()
    studio.locator("tbody").wait_for()
    studio.go_forward()
    studio.locator(".card").wait_for()
    studio.evaluate("location.hash = 'table'")
    studio.locator("tbody").wait_for()
    for column, label in enumerate(("Chinese", "Pinyin", "English"), 1):
        toggle = studio.get_by_label("Show " + label, exact=True)
        toggle.uncheck()
        assert studio.locator(f"tbody tr:first-child td:nth-child({column})").evaluate(
            "cell => getComputedStyle(cell).visibility") == "hidden"
        toggle.check()
        assert studio.locator(f"tbody tr:first-child td:nth-child({column})").is_visible()
    print("PASS: Chinese flashcard shortcuts, Back/Forward/hash navigation and three column toggles")

    studio.route("**/chinese/list-1.json", lambda route: route.abort())
    studio.select_option("#list", "1")
    error = "Could not load this word list. Please refresh and try again."
    studio.get_by_text(error, exact=True).wait_for()
    for mode in ("Flashcards", "Quick quiz", "Table"):
        studio.get_by_role("button", name=mode, exact=True).click()
        assert studio.inner_text("#study") == error
        assert studio.locator("tbody tr, .card, .choices").count() == 0
    studio.unroute("**/chinese/list-1.json")
    studio.route("**/chinese/list-1.json", lambda route: route.fulfill(json={"categories": []}))
    studio.reload()
    studio.get_by_text("No words in this selection.", exact=True).wait_for()
    studio.get_by_role("button", name="Flashcards", exact=True).click()
    studio.locator("h1").click()
    studio.keyboard.press("ArrowRight")
    studio.keyboard.press("Space")
    assert studio.inner_text("#study") == "No words in this selection."
    studio.unroute("**/chinese/list-1.json")
    print("PASS: Chinese fetch failures clear stale data and survive mode changes; empty decks are safe")

    list1 = json.loads((ROOT / "chinese/list-1.json").read_text())
    original = list1["categories"][0]["words"][:3]
    # A test-only shared gloss exercises reverse-direction ambiguity.
    fixture = {"categories": [{"name": "Quiz test", "words": [
        original[0], dict(original[1], english=original[0]["english"]), original[2]]}]}
    studio.route("**/chinese/list-1.json", lambda route: route.fulfill(json=fixture))
    studio.goto(BASE + "/chinese/")
    studio.goto(BASE + "/chinese/words.html#quiz")
    studio.locator(".choices").wait_for()
    studio.select_option("#direction", "en")
    options = studio.locator(".choices button").all_text_contents()
    assert original[0]["chinese"] in options and original[1]["chinese"] not in options
    assert len(options) == len(set(options))
    studio.get_by_role("button", name=original[0]["chinese"], exact=True).click()
    assert studio.inner_text(".status") == "Correct. Nice work!"
    studio.unroute("**/chinese/list-1.json")
    print("PASS: reverse Chinese quiz excludes entries sharing the English prompt")

    studio.set_viewport_size({"width": 390, "height": 1100})
    studio.goto(BASE + "/chinese/")
    studio.goto(BASE + "/chinese/words.html#table")
    studio.locator("tbody").wait_for()
    assert studio.locator("tbody tr").count() == 478
    assert studio.evaluate("document.documentElement.scrollWidth <= innerWidth")
    studio.goto(BASE + "/chinese/year9-revision.html#vocab")
    studio.locator("#vocab.on").wait_for()
    assert studio.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert studio.locator("#vocab .vocab-scroll > table.vocab").count() > 0
    studio.locator("#vocab th").first.click()
    assert "hidecol-1" in studio.locator("#vocab table").first.get_attribute("class")
    studio_context.close()
    print("PASS: Chinese studio and original vocabulary tables fit 390px; original column hiding works")

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
