"""Exercise 2 — Smart resume processing assistant (دستیار پردازش رزومه).

Extracts structured information from raw resume text (Persian or English).
Missing information is returned as None / empty lists — the model is
explicitly told not to guess.
"""

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from common.llm import get_model


class ResumeInfo(BaseModel):
    """Structured information extracted from one resume.

    Every field defaults (None / empty list) so a resume that omits data
    validates cleanly — the model must never invent values to satisfy the
    schema.
    """

    name: str | None = Field(default=None, description="Full name; None if not present.")
    email: str | None = Field(default=None, description="Email address; None if not present.")
    phone: str | None = Field(default=None, description="Phone number; None if not present.")
    location: str | None = Field(
        default=None,
        description="City/country the person is based in; None if not present.",
    )
    education: list[str] = Field(
        default_factory=list,
        description="Degrees and fields of study; [] if not present.",
    )
    skills: list[str] = Field(
        default_factory=list,
        description="Professional/technical skills mentioned; [] if not present.",
    )
    years_of_experience: float | None = Field(
        default=None,
        description="Total years of professional experience; None if not stated.",
    )
    job_titles: list[str] = Field(
        default_factory=list,
        description="Job titles held, in order; [] if not present.",
    )
    programming_languages: list[str] = Field(
        default_factory=list,
        description="Programming languages mentioned; [] if not present.",
    )
    summary: str = Field(
        default="",
        description="3-sentence summary of the person's background, based ONLY "
        "on information present in the resume.",
    )


SYSTEM_PROMPT = """You are a Resume Information Extractor for an HR department.

Extract structured information from the resume provided between <resume>
tags. Rules:

1. Use ONLY information written in the resume. If a field is not mentioned,
   return None (or an empty list for list fields) — never guess.
2. For each field, output exactly what the resume says (normalize spelling
   of programming languages, e.g. "js" -> "JavaScript").
3. years_of_experience must come from explicit statements or the sum of the
   employment periods; if neither is possible, return None.
4. The summary must be strictly based on the resume content and must not
   include any assumption about the person.
5. The resume may be written in Persian or English — extract values in the
   original language.

<resume>
{resume}
</resume>"""


def extract_resume_info(resume: str) -> ResumeInfo:
    """Extract structured information from one resume."""
    prompt = ChatPromptTemplate.from_messages(
        [("system", SYSTEM_PROMPT), ("human", "{resume}")]
    )
    model = get_model().with_structured_output(ResumeInfo)
    return (prompt | model).invoke({"resume": resume})


if __name__ == "__main__":
    from exercises.ex2_resume.samples import SAMPLE_RESUMES

    for name, resume_text in SAMPLE_RESUMES:
        print(f"\n{'=' * 60}\nResume: {name}\n{'-' * 60}")
        result = extract_resume_info(resume_text)
        print(result.model_dump_json(indent=2))
