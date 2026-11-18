# Revision room

A no-build, plain HTML/CSS/JavaScript revision site for Year 9 in Melbourne.

## Run

From this directory, run:

```sh
python3 -m http.server 8080
```

Open http://localhost:8080. Use HTTP rather than opening files directly: the pages fetch JSON.
No dependencies, service worker or external fonts. The original Chinese revision page retains its own voice integrations (online voice needs internet and browser speech support varies).

## Content

Chinese list JSON is grouped into `categories: [{name, words: [{english, chinese, pinyin}]}]`.
Pinyin is preserved exactly from the supplied markdown, including neutral tones.
List 1 contains 478 rows (474 unique Chinese entries); list 2 contains 672.
There is no overlap between the lists. Repeated entries within list 1 are retained in their source categories.

Geography, English, Maths and Chinese Unit 1 now use the supplied school files.
English prepares for one Antigone essay and one ad analysis: drill the complete
quote/comment sheet, then write paragraphs and self-mark using source-bank reveals.
Its only teaching sources are `Antigone Quotes.pdf` and `english.odt.txt`.
Each note, flashcard and practice paper names its source. See `SOURCES.md` for
coverage gaps and adaptations. The old food-security pack has a readable,
source-checked abridgement at `geography/food-security.html`.

Edit each subject's `data.json` using this illustrative schema (not real teaching content):

```json
{
  "notes": [
    {"heading": "Heading from class", "source": "School file.txt", "body": "A paragraph.\n\n- A bullet\n- Another bullet"}
  ],
  "flashcards": [
    {"id": "stable-card-id", "term": "Term from notes", "definition": "Definition from notes", "source": "School file.txt"}
  ],
  "exams": [{
    "id": "stable-exam-id",
    "title": "Practice paper",
    "source": "School file.txt",
    "durationMinutes": 30,
    "sections": [
      {
        "title": "Section heading",
        "questions": [
          {
            "type": "multiple-choice",
            "prompt": "Question from practice sheet",
            "options": ["First option", "Second option"],
            "answer": 0,
            "explanation": "Explanation from notes",
            "marks": 1
          },
          {
            "type": "short-answer",
            "prompt": "Written question from practice sheet",
            "marks": 3,
            "modelAnswer": "Model response.\n- Marking point"
          }
        ]
      }
    ]
  }]
}
```

`answer` is a zero-based option index. Notes and model answers support plain
paragraphs separated by newlines and lines starting with `- ` as bullets;
HTML is treated as text, not executed. Stable flashcard IDs are recommended.
Use `exams` for multiple selectable papers (`practiceExam` remains supported for
older datasets). Each exam has a stable `id` for independent saved self-marks.
A section may set `"choose": 1` to offer alternative questions: only the selected
question counts toward the total. All alternatives should have equal marks.
The Geography revision paper uses this for its four choose-one essay prompts.
`notesOnly: true` hides cards/exams for a notes-only page such as Chinese Unit 1.
Notes can provide `caution` text and an optional relative `href` for a longer page.
Questions may include `stimulus` text to replace an available source caption;
unrecoverable maps/figures are omitted rather than invented.

The optional timer defaults to 30 minutes if omitted. Marks are manually entered
and clamped to each question's maximum in the self-mark total.

## Progress and privacy

Known cards, best vocabulary quiz percentages (per list/category/direction),
and subject exam self-marks and written answers are stored only in this browser's localStorage.
Clearing site data resets progress. If storage is unavailable, study still works
but progress will not persist. Timer state is not saved.

## Original revision guide

`chinese/year9-revision.html` is the supplied file with the shared subject
navigation. Its content and voice scripts are intact.
