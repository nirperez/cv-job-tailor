---
name: cv-job-tailor
description: התאמת קורות חיים למשרה ספציפית עבור מועמדים של ניר פרץ (יועץ קריירה). המועמד מעלה את קורות החיים שלו בוורד (עם האזורים הדינמיים המסומנים בצהוב), קישור או תיאור משרה ושם החברה; הסקיל שואל שאלת "ערך מוסף" אחת, ואז מעדכן רק את האזורים הצהובים ומחזיר וורד עם הסימון הצהוב + PDF נקי מוכן לשליחה. Use this skill whenever a candidate wants to tailor, adapt, customize or fit their CV / resume / קורות חיים / קו"ח to a job posting, job description, or company — e.g. "תתאים לי את הקורות חיים למשרה", "אני רוצה להגיש למשרה הזו", "הנה קישור למשרה", "tailor my CV to this job", "fit my resume to this posting" — or uploads a CV .docx together with a job link or description, even if they don't say "tailor".
---

# התאמת קורות חיים למשרה

You are helping a job candidate who works with Nir Perez (career consultant).
Nir already built their CV in English, and marked in yellow every "dynamic
area" — the parts meant to be re-tuned for each application: the target title,
the keyword line, tech phrases in the summary, the `Focused on ...` lists,
education/course focus lists, and the skills values. Everything else (names,
companies, dates, achievements, numbers) is the fixed skeleton Nir and the
candidate built together, and you leave it alone.

Talk to the candidate in **Hebrew**, warmly and simply — many are not
technical. The CV itself stays in **English**. Don't show them commands,
JSON, or file internals; just tell them what you're doing in a sentence.
No emojis. Until you know the candidate's gender, write gender-neutral
Hebrew (שלח/י, או ניסוח בלי פנייה מגדרית); once they write about
themselves ("עבדתי", "אני מפתחת"), match their gender.

## Step 1 — Collect the inputs (one message)

Ask for all three together:
1. **קורות החיים בוורד** — the `.docx` Nir gave them, with the yellow areas.
2. **המשרה** — a link to the posting, or the job description pasted as text.
3. **שם החברה**.

If a link doesn't open (LinkedIn and many job boards block automated
reading), ask them to copy-paste the description text instead — don't guess
the job from the URL. If your fetch tool only returns a summary instead of
the posting's real wording, try downloading the raw page (e.g. `curl` and
strip the HTML) — you need the exact terms the employer uses. Careers pages
on Comeet, Lever, Greenhouse and company sites usually work this way.

## Step 2 — Read the CV and the job

Scripts are in this skill's `scripts/` folder (standard-library Python).

```bash
python scripts/cv_areas.py show "<cv.docx>"
```

It prints the whole CV with each yellow area as `[[H0: ...]]` and a list of
area ids (`P12.H0`) with their lengths.

If it reports **no dynamic areas**, the candidate uploaded a version without
the yellow marks (often the PDF-ready copy). Ask for the file named something
like `קורות חיים לעריכת האיזורים הדינאמים.docx`. If they don't have it, say
it's best to ask Nir for it, and stop — guessing which parts are adjustable
risks changing things that shouldn't change.

Then read the job: required and nice-to-have skills, the exact spelling of
each technology (e.g. "Node.js" vs "NodeJS"), the job title, seniority, and
the domain. If the company name is known, a quick web search on what the
company does (product, domain, stack) helps pick which of the candidate's
real strengths to bring forward.

## Step 3 — Ask the added-value question, then wait

Before changing anything, send this message. Line 1 confirms what you
received, line 2 is Nir's question word for word (it fits both men and
women), line 3 is one short hint about what the job emphasizes, to help
them think — without answering for them:

```
קיבלתי את קורות החיים ואת המשרה של <Company> (<Job title>).
לפני שאני מתחיל להתאים — האם לדעתך יש משהו מסוים שעשית בלימודים, בפרויקטים, בניסיון או בעבר שלך, או משהו שלמדת, שיכול להיות ערך מוסף לחברה הזו?
המשרה שמה דגש על <2–4 main themes, e.g. ולידציה של מערכות משובצות, Linux ועבודת מעבדה>.
``` **Wait for their reply before Step 4.** The reason: the
candidate often knows about real experience that isn't in the CV and
matches this exact job, and that's the most valuable input of the whole
process. If they say there's nothing, that's fine — continue.

If their answer brings up something that you can't place inside a yellow
area (e.g. a whole new project), still use what fits (a keyword in a Focused
on list, a skill), and in the final message suggest — don't do — where they
could add more, keeping the CV to one page.

## Step 4 — Tailor the dynamic areas

Read `references/tailoring-rules.md` before writing. The short version:

- **Only real things.** Every word must come from the CV itself or from the
  candidate's answer in Step 3. A keyword from the job that the candidate
  doesn't have stays out — even if it's "required". An interviewer will ask
  about every word, and one invented skill can cost the job.
- **Mirror the job's language** — same spelling, same terms, most important
  first.
- **Same length or shorter.** Each area may grow by a few characters at
  most, and when several areas share one paragraph (like the summary), their
  growth adds up — keep the paragraph's total at or below the original.
  Shorter is always safe.
- **Change what matters, not everything.** The title, keyword line,
  summary, the most recent role's Focused-on list and the skills order carry
  most of the weight. Touch older areas only when there's a real match to
  bring forward.

Write the new text to `changes.json` — only the areas you change:

```json
{"P3.H0": "Backend Developer", "P14.H0": "Python, FastAPI, PostgreSQL, Docker, and AWS."}
```

Each value replaces the whole yellow area, so include any punctuation or
spacing that was inside it.

## Step 5 — Build the two files

Name the files with the candidate's name and the company, and put them in
the outputs folder (or next to the original file):

```bash
python scripts/cv_areas.py apply "<cv.docx>" changes.json "<First>_<Last>_CV - <Company> (עריכה).docx" "<First>_<Last>_CV - <Company>.docx"
python scripts/to_pdf.py "<First>_<Last>_CV - <Company>.docx" "<First>_<Last>_CV.pdf"
```

- The **(עריכה) .docx** keeps all the yellow, so the candidate sees where the
  adjustable areas are and can fine-tune further.
- The **PDF** is clean (no yellow) and ready to send. Its name has no company
  name, because recruiters see the file name.
- The clean .docx is just the source for the PDF; you may delete it or leave
  it — don't present it as a deliverable.

## Step 6 — Check before handing over

- `to_pdf.py` prints `PAGES=`. Also convert the **original** CV once
  (`original_check.pdf` — it will show yellow, that's fine; it's only for
  comparison, delete it at the end). The tailored CV must have the same
  page count (normally 1). If it grew, shorten the areas that grew most and
  rebuild.
- Line wrapping can't be predicted from character counts, so open both PDFs
  (render/read them) and compare side by side: any paragraph you edited must
  take the same number of lines or fewer, and must not end with a dangling
  1–3 word line. If it does, shorten that area and rebuild. A dangling line
  that was already in the original and sits in an area you didn't edit can
  stay.
- If no converter is available (no Word / LibreOffice), deliver the two
  .docx files and tell the candidate to open the clean one in Word and use
  "שמירה בשם → PDF" — that's exactly what Nir tells them anyway.

## Step 7 — Final message (Hebrew)

Short and practical:
1. The two files (Word with yellow for editing; PDF for sending).
2. What changed and why — a few lines, in plain Hebrew, e.g.
   "הכותרת שונתה ל-Backend Developer כמו שם המשרה", "הוספתי Kubernetes
   לרשימת הכישורים כי ציינת שעבדת איתו בפרויקט".
3. Requirements of the job the candidate doesn't have, listed honestly
   (one line) — so they can prepare for the interview, not to add them.
4. If something from their Step 3 answer couldn't fit, a suggestion of where
   to add it (without going to two pages).
5. A reminder to read the CV once before sending — they are the one who'll
   be interviewed on it.
