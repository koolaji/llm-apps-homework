"""Exercise 1 — Smart product review analysis (فروشگاه آنلاین).

Turns a free-text (Persian) product review into a structured analysis:
sentiment, approximate 1–5 score, recommendation flag, pros/cons, summary.

Prompt-engineering principles used:
  * Role            — expert review analyst in the system prompt
  * Delimiter       — review text is wrapped in <review> tags
  * Output format   — Pydantic schema enforced via with_structured_output
  * No guessing     — missing info must be empty lists, never invented
"""

from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from common.llm import get_model


class ReviewAnalysis(BaseModel):
    """Structured analysis of a single product review."""

    sentiment: Literal["positive", "negative", "neutral"] = Field(
        description="Overall customer feeling about the product."
    )
    approximate_score: int = Field(
        ge=1,
        le=5,
        description="Approximate 1..5 rating implied by the review text.",
    )
    would_recommend: bool = Field(
        description="True only if the customer clearly recommends the product."
    )
    main_positive_points: list[str] = Field(
        default_factory=list,
        description="Most important positive points; [] if none are stated.",
    )
    main_negative_points: list[str] = Field(
        default_factory=list,
        description="Most important negative points; [] if none are stated.",
    )
    summary: str = Field(
        default="",
        description="One-sentence summary of the review, in the review's language.",
    )


SYSTEM_PROMPT = """You are an expert product-review analyst for an online store.

Analyze the customer review that will be provided between <review> tags and
fill the requested schema. Rules:

1. Base every field ONLY on what is actually written in the review.
2. If the review does not mention any positive or negative points, return an
   empty list for that field — never invent or guess points.
3. If it is impossible to tell whether the customer recommends the product,
   set would_recommend to false and do not add commentary.
4. The approximate_score must reflect the overall tone (1 = terrible,
   5 = excellent) even if no explicit rating is given.
5. Write the summary in the same language as the review, max two sentences.

<review>
{review}
</review>"""


def analyze_review(review: str) -> ReviewAnalysis:
    """Analyze one product review and return a structured result."""
    prompt = ChatPromptTemplate.from_messages(
        [("system", SYSTEM_PROMPT), ("human", "{review}")]
    )
    model = get_model().with_structured_output(ReviewAnalysis)
    chain = prompt | model
    return chain.invoke({"review": review})


if __name__ == "__main__":
    from exercises.ex1_review.samples import SAMPLE_REVIEWS

    for name, review_text in SAMPLE_REVIEWS:
        print(f"\n{'=' * 60}\nReview: {name}\n{'-' * 60}")
        result = analyze_review(review_text)
        print(result.model_dump_json(indent=2))
