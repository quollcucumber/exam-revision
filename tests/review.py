"""Regression checks for the review fixes; invoked by verify.py."""


def check_essay_state(browser, base):
    context = browser.new_context()
    page = context.new_page()
    page.goto(base + "/geography/#practice")
    page.locator(".essay-picker").wait_for()
    earlier = page.locator("#practice textarea").first
    earlier.fill("Keep my earlier answer")
    page.locator("#practice .choices button").first.click()
    feedback = page.locator("#practice .choices").first.locator("..").locator(".status")
    message = feedback.inner_text()
    page.get_by_role("button", name="Start timer", exact=True).click()
    page.evaluate("""() => {
      window.earlierAnswer = document.querySelector('#practice textarea');
      window.timerButton = [...document.querySelectorAll('#practice button')]
        .find(b => b.textContent === 'Pause timer');
    }""")
    page.locator(".essay-picker").select_option("1")
    assert earlier.input_value() == "Keep my earlier answer"
    assert feedback.inner_text() == message
    page.get_by_role("button", name="Pause timer", exact=True).wait_for()
    assert page.evaluate("""() =>
      window.earlierAnswer === document.querySelector('#practice textarea') &&
      window.timerButton.isConnected""")
    assert "Self-mark total: 0 / 50" in page.inner_text("#practice")
    context.close()


def check_quiz_distractors(browser, base):
    words = [
        {"chinese": "不", "pinyin": "bù", "english": "not"},
        {"chinese": "不", "pinyin": "bù", "english": "no / not"},
        {"chinese": "没有", "pinyin": "méiyǒu", "english": "not"},
        {"chinese": "是", "pinyin": "shì", "english": "is"},
        {"chinese": "否", "pinyin": "fǒu", "english": "no"},
        {"chinese": "不是", "pinyin": "búshì", "english": "is not"},
    ]
    context = browser.new_context()
    page = context.new_page()
    page.route("**/chinese/list-1.json", lambda route: route.fulfill(
        json={"categories": [{"name": "Regression fixture", "words": words}]}))
    page.goto(base + "/chinese/words.html#quiz")
    page.locator(".choices").wait_for()
    for direction in ("cn", "en"):
        page.select_option("#direction", direction)
        prompt_field, answer_field = ("chinese", "english") if direction == "cn" else ("english", "chinese")
        for _ in words:
            prompt = page.locator(".panel .hanzi" if direction == "cn" else ".panel .english").inner_text()
            valid = {w[answer_field] for w in words if w[prompt_field] == prompt}
            options = page.locator(".choices button").all_text_contents()
            assert len(valid.intersection(options)) == 1, (prompt, options)
            answer = next(option for option in options if option in valid)
            page.locator(".choices").get_by_role("button", name=answer, exact=True).click()
            assert "Correct." in page.locator(".status").inner_text()
            page.get_by_role("button", name="Continue →", exact=True).click()
        page.get_by_role("button", name="Try again", exact=True).click()
    context.close()


def check_failed_list(browser, base):
    context = browser.new_context()
    page = context.new_page()
    page.goto(base + "/chinese/words.html#quiz")
    page.locator(".choices").wait_for()
    pending = []
    page.route("**/chinese/list-2.json", lambda route: pending.append(route))
    page.select_option("#list", "2")
    page.get_by_text("Loading vocabulary…", exact=True).wait_for()
    page.get_by_role("button", name="Quick quiz", exact=True).click()
    assert page.locator(".choices button").count() == 0
    assert page.locator("#study").inner_text() == "Loading vocabulary…"
    pending.pop().abort()
    page.get_by_text("Could not load this word list. Please refresh and try again.", exact=True).wait_for()
    for tab in ("Table", "Flashcards", "Quick quiz"):
        page.get_by_role("button", name=tab, exact=True).click()
        assert "Could not load" in page.locator("#study").inner_text()
        assert page.locator("#study button").count() == 0
    assert page.evaluate("Object.keys(localStorage).filter(k => k.startsWith('chinese-best-2-'))") == []
    page.select_option("#list", "1")
    page.locator(".choices").wait_for()
    page.select_option("#list", "2")
    page.get_by_text("Loading vocabulary…", exact=True).wait_for()
    page.select_option("#list", "1")
    page.locator(".choices").wait_for()
    pending.pop().abort()
    assert page.locator(".choices").is_visible()
    context.close()


def check_flashcard_names(browser, base):
    context = browser.new_context()
    page = context.new_page()
    for path in ("/english/", "/chinese/words.html#flashcards"):
        page.goto(base + path)
        card = page.locator(".card")
        card.wait_for()
        for _ in range(2):
            visible = " ".join(card.inner_text().split())
            assert visible
            page.get_by_role("button", name=visible, exact=True).wait_for()
            card.click()
    page.select_option("#direction", "en")
    card = page.locator(".card")
    for _ in range(2):
        page.get_by_role("button", name=" ".join(card.inner_text().split()), exact=True).wait_for()
        card.click()
    context.close()


def check_known_word_identity(browser, base):
    context = browser.new_context()
    page = context.new_page()
    words = [
        {"chinese": "只", "pinyin": "zhǐ", "english": "only"},
        {"chinese": "只", "pinyin": "zhī", "english": "measure word"},
        {"chinese": "只", "pinyin": "zhǐ", "english": "just"},
    ]
    page.route("**/chinese/list-1.json", lambda route: route.fulfill(
        json={"categories": [{"name": "Homographs", "words": words}]}))
    page.goto(base + "/chinese/words.html#flashcards")
    page.get_by_role("button", name="Mark as known", exact=True).click()
    for _ in range(2):
        page.get_by_role("button", name="Next →", exact=True).click()
        page.get_by_role("button", name="Mark as known", exact=True).wait_for()
    page.get_by_role("button", name="Next →", exact=True).click()
    page.get_by_role("button", name="✓ Known — undo", exact=True).wait_for()
    page.reload()
    page.get_by_role("button", name="✓ Known — undo", exact=True).wait_for()
    page.get_by_role("button", name="Next →", exact=True).click()
    page.get_by_role("button", name="Mark as known", exact=True).wait_for()
    context.close()


def check_shuffle(browser, base):
    context = browser.new_context()
    page = context.new_page()
    page.goto(base + "/")
    assert page.evaluate("""async () => {
      const {shuffled} = await import('/assets/common.js');
      const random = Math.random;
      try {
        const input = [1, 2, 3, 4];
        const draws = [0, 0.5, 0.999999];
        Math.random = () => draws.shift();
        const result = shuffled(input);
        if (JSON.stringify(result) !== '[4,3,2,1]' ||
            JSON.stringify(input) !== '[1,2,3,4]' || result === input ||
            draws.length !== 0) return false;
        return shuffled([]).length === 0 &&
          JSON.stringify(shuffled([1])) === '[1]';
      } finally { Math.random = random; }
    }""")
    context.close()


def check_timer_deadline(browser, base):
    context = browser.new_context()
    page = context.new_page()
    page.clock.install(time=1700000000000)
    page.goto(base + "/geography/#practice")
    page.get_by_role("button", name="Start timer", exact=True).click()
    timer = page.locator("#practice > div > .status").first
    assert timer.inner_text() == "Time remaining: 50:00"
    page.clock.fast_forward(125000)
    assert timer.inner_text() == "Time remaining: 47:55"
    page.locator(".essay-picker").select_option("1")
    page.clock.fast_forward(1000)
    assert timer.inner_text() == "Time remaining: 47:54"
    page.get_by_role("button", name="Pause timer", exact=True).click()
    page.clock.fast_forward(600000)
    assert timer.inner_text() == "Time remaining: 47:54"
    page.get_by_role("button", name="Resume timer", exact=True).click()
    page.clock.fast_forward(2868000)
    assert timer.inner_text() == "Time remaining: 0:06"
    page.clock.fast_forward(60000)
    assert timer.inner_text() == "Time is up. Finish your current thought, then self-mark."
    assert page.get_by_role("button", name="Pause timer", exact=True).is_disabled()
    page.select_option("#exam-picker", "1")
    page.get_by_role("button", name="Start timer", exact=True).wait_for()
    assert timer.inner_text() == "Optional timer: 50 minutes"
    context.close()


def run_review(browser, base):
    for name, check in sorted(globals().items()):
        if name.startswith("check_"):
            check(browser, base)
            print("PASS:", name)
