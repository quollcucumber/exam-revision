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

Geography, English and Maths intentionally have no teaching content yet.
Edit each subject's `data.json` using this illustrative schema (not real teaching content):

```json
{
  "notes": [
    {"heading": "Heading from class", "body": "A paragraph.\n\n- A bullet\n- Another bullet"}
  ],
  "flashcards": [
    {"id": "stable-card-id", "term": "Term from notes", "definition": "Definition from notes"}
  ],
  "practiceExam": {
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
  }
}
```

`answer` is a zero-based option index. Notes and model answers support plain
paragraphs separated by newlines and lines starting with `- ` as bullets;
HTML is treated as text, not executed. Stable flashcard IDs are recommended.
The optional timer defaults to 30 minutes if omitted. Marks are manually entered
and clamped to each question's maximum in the self-mark total.

## Progress and privacy

Known cards, best vocabulary quiz percentages (per list/category/direction),
and subject exam self-marks are stored only in this browser's localStorage.
Clearing site data resets progress. If storage is unavailable, study still works
but progress will not persist. Typed exam responses and timer state are not saved.

## Original revision guide

`chinese/year9-revision.html` is the supplied file, unchanged except for a small
home link inserted at the top and a request-changes footer. Its content and voice scripts are intact.
