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


def run_review(browser, base):
    for name, check in sorted(globals().items()):
        if name.startswith("check_"):
            check(browser, base)
            print("PASS:", name)
