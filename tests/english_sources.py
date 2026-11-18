"""Verify English content against the supplied school files (pdftotext required)."""
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('REVISION_SOURCES', '/home/ubuntu/revsrc/text'))
data = json.loads((ROOT / 'english/data.json').read_text())
pdf = subprocess.check_output(['pdftotext', '-layout', str(SOURCE / 'Antigone Quotes.pdf'), '-']).decode()
ad = (SOURCE / 'english.odt.txt').read_text()
normalize = lambda text: ' '.join(text.split())
entries = re.split(r'(?m)^(?=(?:Antigone:|Ismene:|Creon:|Haemon:|Chorus:|Sentry:|Teiresias:|Sentry sent news|“))', pdf.replace('\f', ''))[1:]
entries = [normalize(entry) for entry in entries]
cards = data['flashcards']
assert len(entries) == len(cards) == 62
for entry, card in zip(entries, cards):
    assert normalize(card['term'] + ' ' + card['definition']) == entry
    assert normalize(card['term']) in normalize(pdf)
    assert normalize(card['definition']) in normalize(pdf)
    assert entry in normalize(data['notes'][0]['body'])
print('PASS: all 62 PDF entries appear in full in both the by-character note and quote/comment flashcards; every card side is verbatim source text')

headings = {'Antigone', 'Ismene', 'Creon', 'Haemon', 'Chorus', 'Sentry', 'Teiresias', 'Later scenes (no speaker given on your sheet)'}
for line in data['notes'][0]['body'].splitlines():
    if line and line not in headings:
        assert normalize(line) in normalize(pdf), line
gap = '[To fill in from the ad]'
ad_body = data['notes'][1]['body'].replace(gap, '')
assert normalize(ad_body) == normalize(ad)
assert data['notes'][1]['body'].count(gap) == 2
for exam in data['exams']:
    for section in exam['sections']:
        for question in section['questions']:
            body = question['modelAnswer'].split('\n\n', 1)[1].replace(gap, '')
            source = pdf if question['source'] == 'Antigone Quotes.pdf' else ad
            for line in body.splitlines():
                if line.strip():
                    assert normalize(line) in normalize(source), line
assert len(data['notes']) == 2
assert 'english essay.odt.txt' not in json.dumps(data)
print('PASS: all note/reveal quotations, claims and comments are verbatim PDF or Pepsi-plan text; both Pepsi gaps retained; no History content')
