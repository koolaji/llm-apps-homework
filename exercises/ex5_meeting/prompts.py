"""Iterative prompt development for exercise 5 (course requirement).

Three versions are kept on purpose, with the reason for every change.
Run `python analyze_meeting.py --version v1` etc. to reproduce the
improvement step by step.
"""

PROMPT_V1 = """Extract the following from the meeting transcript:
summary, decisions, action_items (task, owner, deadline), open_questions,
mentioned_people, mentioned_projects, next_steps.

Transcript:
{transcript}"""


PROMPT_V2 = """You are a meeting analyst. Read the technical meeting transcript
between <transcript> tags and extract:

- summary: short summary of the meeting.
- decisions: things that were DECIDED.
- action_items: list of {task, owner, deadline}.
- open_questions, mentioned_people, mentioned_projects, next_steps.

Rules: use only information in the transcript; if the owner or deadline of a
task is not stated, use None — do not guess.

<transcript>
{transcript}
</transcript>"""


PROMPT_V3 = """You are a meeting analyst for an engineering team. Read the
technical meeting transcript between <transcript> tags and fill the schema.

Extraction rules:
1. Use only what is actually said in the transcript. Never guess.
2. owner / deadline of an action item: if nobody explicitly accepted the task
   or no date was stated, use None.
3. Separate DECISIONS from PROPOSALS: a decision is only when the group or the
   decision-maker clearly agrees ("قرار شد", "OK, let's go with"). Ideas that
   were only suggested ("شاید بهتر باشه", "می‌شه اینطوری هم کرد") belong to
   open_questions or are simply not decisions.
4. mentioned_people: only real people named in the discussion, not companies
   or project names.
5. next_steps: ordered list of what the team will do after the meeting,
   derived from decisions and action items.
6. Write summary in the transcript's language.

<transcript>
{transcript}
</transcript>"""


PROMPTS = {"v1": PROMPT_V1, "v2": PROMPT_V2, "v3": PROMPT_V3}

CHANGELOG = {
    "v1": "First draft: single paragraph, no role, no delimiter, no "
    "anti-hallucination rule. Problem 1: model invented owners for tasks "
    "where nobody was assigned. Problem 2: it listed 'proposals' as decisions.",
    "v2": "Added role (meeting analyst), <transcript> delimiter, and the "
    "explicit 'use None, do not guess' rule. Fixed invented owners. Remaining "
    "problem: proposals still leaked into decisions, and people/projects were "
    "sometimes mixed.",
    "v3": "Added the decision-vs-proposal distinction with concrete Persian "
    "cue phrases, a rule separating people from projects, and ordered "
    "next_steps. This is the final version used by analyze_meeting().",
}
