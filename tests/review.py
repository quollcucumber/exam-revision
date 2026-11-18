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


def run_review(browser, base):
    for name, check in sorted(globals().items()):
        if name.startswith("check_"):
            check(browser, base)
            print("PASS:", name)
