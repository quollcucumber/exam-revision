"""Run with the optional Playwright environment against localhost:8080."""
import os
import shutil

from playwright.sync_api import sync_playwright

BASE = os.environ.get('REVISION_URL', 'http://localhost:8080')

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=shutil.which('google-chrome'),
                              headless=True, args=['--no-sandbox'])
    page = browser.new_page()
    page.goto(BASE + '/english/')
    page.locator('textarea').first.wait_for()
    page.evaluate("localStorage.setItem('english-exam-antigone-writing', JSON.stringify({marks:{'creon-women':0.5},choices:{}}))")
    page.reload()
    mark = page.locator('input[type=number]').first
    assert mark.input_value() == '0'
    for value, expected in [('0.5', '0'), ('999', '4'), ('-1', '0'), ('', '0')]:
        mark.fill(value)
        assert mark.input_value() == expected
    answer = page.locator('textarea').first
    answer.fill('Antigone\n<not HTML>')
    mark.fill('1')
    page.reload()
    assert answer.input_value() == 'Antigone\n<not HTML>'
    assert mark.input_value() == '1'
    answer.fill('')
    page.reload()
    assert answer.input_value() == ''
    print('PASS: legacy marks migrate; empty, fractional, negative and excessive marks normalize; multiline answers persist and clear')

    page.goto(BASE + '/geography/')
    page.locator('.essay-picker').wait_for()
    essay = page.locator('textarea').last
    essay.fill('First alternative')
    page.locator('.essay-picker').select_option('1')
    assert essay.input_value() == ''
    essay.fill('Second alternative')
    page.locator('#exam-picker').select_option('1')
    page.locator('textarea').first.fill('Other paper')
    page.locator('#exam-picker').select_option('0')
    assert essay.input_value() == 'Second alternative'
    page.locator('.essay-picker').select_option('0')
    assert essay.input_value() == 'First alternative'
    page.reload()
    assert essay.input_value() == 'First alternative'
    page.evaluate('localStorage.clear()')
    page.reload()
    assert all(value == '' for value in page.locator('textarea').evaluate_all('(els)=>els.map(e=>e.value)'))
    assert 'Self-mark total: 0 / 50' in page.inner_text('#practice')
    print('PASS: answers isolated by paper and essay alternative; clearing site data resets answers and marks')

    context = browser.new_context()
    context.add_init_script("Storage.prototype.setItem = () => { throw new Error('Storage unavailable') };")
    page = context.new_page()
    page.goto(BASE + '/english/')
    page.locator('textarea').first.fill('Still usable')
    page.locator('input[type=number]').first.fill('1')
    assert 'Self-mark total: 1 / 16' in page.inner_text('#practice')
    print('PASS: unavailable storage does not prevent answering or self-marking')
    browser.close()
