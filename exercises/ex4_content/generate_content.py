"""Exercise 4 — Technical content generation with a parameterized prompt.

Key requirement: the prompt is NOT one static template with variables
substituted in. The instructions explain *how* each parameter changes the
output (difficulty -> depth, content_type -> structure/tone), and two
few-shot examples teach the model the difference.
"""

from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from common.llm import get_model


class TechnicalContent(BaseModel):
    """Structured generated content."""

    title: str = Field(description="Catchy title for the content.")
    content: str = Field(description="The full generated content body.")
    key_points: list[str] = Field(description="3-5 key takeaways covered.")
    target_audience: str = Field(description="Who this content is for.")
    suggested_hashtags: list[str] = Field(description="4-8 relevant hashtags.")


FEW_SHOT_EXAMPLES = """Here are two examples of the expected behavior:

EXAMPLE INPUT:
topic="Docker", audience="backend developers", difficulty="beginner",
language="English", content_type="Short explanation"

EXAMPLE OUTPUT (abbreviated): a ~120-word friendly explanation that defines
a container by analogy ("a lunchbox that packs your app with everything it
needs"), avoids any orchestration detail, ends with one actionable first
command (docker run hello-world), casual tone.

EXAMPLE INPUT:
topic="Docker", audience="backend developers", difficulty="intermediate",
language="English", content_type="Tutorial"

EXAMPLE OUTPUT (abbreviated): a ~500-word step-by-step tutorial with
numbered sections (install -> Dockerfile -> build -> run -> volumes),
code blocks for every step, an explanation of WHY layers matter for
rebuild speed, assumes the reader knows the terminal, professional tone.

Notice how difficulty changed the depth and vocabulary, and content_type
changed the structure and length. Apply the same behavior."""

SYSTEM_PROMPT = """You are a senior technical content writer for developer audiences.

Write a piece of technical content using the parameters below.

How the parameters must shape the output:
- difficulty: "beginner" -> define every term, use analogies, no prior
  knowledge assumed; "intermediate" -> assume working knowledge, focus on
  practical patterns and common pitfalls.
- content_type: "LinkedIn post" -> <= 150 words, hook in the first line,
  line breaks between ideas, ends with a question; "Tutorial" -> numbered
  steps with code blocks; "Short explanation" -> one tight paragraph;
  "Cheat sheet" -> command/table reference, minimal prose.
- language: write the content, title, key_points and target_audience in
  the requested language. Hashtags in English unless the topic is
  language-specific.

{few_shot_examples}

Now produce the content for the parameter set provided by the user, and
fill the output schema exactly."""


def generate_technical_content(
    topic: str,
    audience: str,
    difficulty: Literal["beginner", "intermediate"],
    language: str,
    content_type: Literal["LinkedIn post", "Tutorial", "Short explanation", "Cheat sheet"],
):
    """Generate technical content tailored to audience, difficulty and format."""
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            (
                "human",
                "topic={topic}\naudience={audience}\ndifficulty={difficulty}\n"
                "language={language}\ncontent_type={content_type}",
            ),
        ]
    )
    model = get_model().with_structured_output(TechnicalContent)
    return (prompt | model).invoke(
        {
            "few_shot_examples": FEW_SHOT_EXAMPLES,
            "topic": topic,
            "audience": audience,
            "difficulty": difficulty,
            "language": language,
            "content_type": content_type,
        }
    )


if __name__ == "__main__":
    # The brief's own example, plus two more to show the prompt adapts.
    requests_ = [
        dict(
            topic="RAG",
            audience="Python developers",
            difficulty="intermediate",
            language="Persian",
            content_type="LinkedIn post",
        ),
        dict(
            topic="Docker",
            audience="backend developers",
            difficulty="beginner",
            language="English",
            content_type="Short explanation",
        ),
        dict(
            topic="Git rebase",
            audience="junior developers",
            difficulty="intermediate",
            language="English",
            content_type="Cheat sheet",
        ),
    ]
    for i, kwargs in enumerate(requests_, 1):
        print(f"\n{'=' * 60}\nRequest {i}: {kwargs}\n{'-' * 60}")
        result = generate_technical_content(**kwargs)
        print(result.model_dump_json(indent=2))
