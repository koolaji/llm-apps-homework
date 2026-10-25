"""Exercise 5 — Meeting analysis assistant (دستیار تحلیل جلسه).

Converts a raw technical-meeting transcript into a structured team report.
Action items with unknown owner/deadline are returned as None — never guessed.

The iterative prompt-development requirement (V1/V2/V3 + changelog) lives in
prompts.py; run with --version v1|v2|v3 to compare behavior.
"""

from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from common.llm import get_model
from exercises.ex5_meeting.prompts import CHANGELOG, PROMPTS


class ActionItem(BaseModel):
    """One task assigned in the meeting."""

    task: str = Field(description="What needs to be done.")
    owner: str | None = Field(
        default=None,
        description="Person responsible; None if nobody explicitly accepted it.",
    )
    deadline: str | None = Field(
        default=None,
        description="Deadline as stated; None if none was mentioned.",
    )


class MeetingAnalysis(BaseModel):
    """Structured report of one meeting."""

    summary: str = Field(default="", description="Short summary of the meeting.")
    decisions: list[str] = Field(
        default_factory=list,
        description="Things clearly DECIDED — not ideas that were merely proposed.",
    )
    action_items: list[ActionItem] = Field(
        default_factory=list, description="Tasks with owner/deadline."
    )
    open_questions: list[str] = Field(
        default_factory=list, description="Unresolved questions."
    )
    mentioned_people: list[str] = Field(
        default_factory=list, description="People named in the discussion."
    )
    mentioned_projects: list[str] = Field(
        default_factory=list, description="Projects/products discussed."
    )
    next_steps: list[str] = Field(
        default_factory=list,
        description="Ordered list of what happens after the meeting.",
    )


def analyze_meeting(transcript: str, version: Literal["v1", "v2", "v3"] = "v3"):
    """Analyze a meeting transcript with the selected prompt version."""
    prompt = ChatPromptTemplate.from_messages(
        [("system", PROMPTS[version]), ("human", "{transcript}")]
    )
    model = get_model().with_structured_output(MeetingAnalysis)
    return (prompt | model).invoke({"transcript": transcript})


if __name__ == "__main__":
    import argparse

    from exercises.ex5_meeting.samples import SAMPLE_TRANSCRIPT

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--version",
        choices=["v1", "v2", "v3"],
        default="v3",
        help="Prompt version to use (see prompts.py for the changelog).",
    )
    args = parser.parse_args()

    print(f"Prompt version: {args.version}")
    print(f"Why: {CHANGELOG[args.version]}\n{'=' * 60}")
    result = analyze_meeting(SAMPLE_TRANSCRIPT, version=args.version)
    print(result.model_dump_json(indent=2))
