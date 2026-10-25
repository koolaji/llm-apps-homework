"""Iterative prompt development for exercise 5 (course requirement).

Three versions are kept on purpose, with the reason for every change.
Run `python analyze_meeting.py --version v1` etc. to compare.
"""

PROMPT_V1 = """Extract the following from the meeting transcript:
summary, decisions, action_items (task, owner, deadline), open_questions,
mentioned_people, mentioned_projects, next_steps."""

PROMPT_V2 = """You are a meeting analyst. Read the technical meeting transcript
provided in the human message and extract:

- summary: short summary of the meeting.
- decisions: things that were DECIDED.
- action_items: list of {task, owner, deadline}.
- open_questions, mentioned_people, mentioned_projects, next_steps.

Rules: use only information in the transcript; if the owner or deadline of a
task is not stated, use None — do not guess."""

PROMPT_V3 = """You are a meeting analyst for an engineering team. Read the
technical meeting transcript provided in the human message (between
<transcript> tags) and fill the schema.

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
6. Write summary in the transcript's language."""


PROMPTS = {"v1": PROMPT_V1, "v2": PROMPT_V2, "v3": PROMPT_V3}

# The transcript always goes in the human message. V1 is deliberately naive
# (no delimiter — that is one of the things V2 fixes); V2+ wrap it in tags.
HUMAN_TEMPLATES = {
    "v1": "{transcript}",
    "v2": "<transcript>\n{transcript}\n</transcript>",
    "v3": "<transcript>\n{transcript}\n</transcript>",
}

CHANGELOG = {
    "v1": "First draft: no role, no delimiter, no anti-hallucination rules; "
    "output described in prose only. Weaknesses by construction: nothing "
    "stops the model from inventing an owner/deadline when none was stated, "
    "and nothing separates proposals from decisions.",
    "v2": "Added role (meeting analyst), the <transcript> delimiter, and the "
    "explicit None rule for unknown owner/deadline. Fabricated owners are no "
    "longer possible when a task has no assignee. Remaining weakness: "
    "proposals can still leak into decisions, and people/projects can mix.",
    "v3": "Added the explicit decision-vs-proposal distinction with concrete "
    "Persian cue phrases ('قرار شد' vs 'شاید'), a rule separating named "
    "people from project names, and ordered next_steps. Final version used "
    "by analyze_meeting().",
}
