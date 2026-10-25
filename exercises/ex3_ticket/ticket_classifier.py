"""Exercise 3 — Turn raw customer chat text into a structured support ticket.

Uses SystemMessage / HumanMessage explicitly, defines a precise priority
rubric, and forces the model to decide based on evidence in the text.
"""

from typing import Literal

from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from pydantic import BaseModel, Field

from common.llm import get_model


class SupportTicket(BaseModel):
    """A structured support ticket derived from a customer message."""

    category: Literal["authentication", "payment", "technical", "account", "other"] = (
        Field(description="Ticket category.")
    )
    priority: Literal["low", "medium", "high", "critical"] = Field(
        description="Urgency, decided strictly by the rubric in the instructions."
    )
    sentiment: Literal["calm", "worried", "frustrated", "angry"] = Field(
        description="Customer's emotional state."
    )
    summary: str = Field(description="One-sentence summary of the ticket.")
    customer_problem: str = Field(
        description="The customer's problem in one or two sentences, in their own words (paraphrased)."
    )
    suggested_action: str = Field(
        description="Concrete next step for the support team."
    )
    needs_human_agent: bool = Field(
        description="True if the ticket cannot be resolved by self-service/automation."
    )


# Message objects are constructed explicitly (course requirement: SystemMessage/HumanMessage).
SYSTEM_MESSAGE = SystemMessage(content="""You are a Support Ticket Classifier for a SaaS company.

Convert the customer message between <message> tags into a structured ticket.

Priority rubric (apply strictly, in this order):
- critical: total loss of service AND an explicit hard deadline today (e.g. "I must send my report today").
- high: cannot use the account/service now (login failure, failed payment) OR strong frustration/anger.
- medium: partial malfunction or a how-to question the user cannot solve alone.
- low: general questions, feedback, feature requests, anything with no urgency expressed.

Rules:
1. Decide the category only from evidence in the message text — not from guesses.
2. If the message mixes several problems, pick the category of the most blocking one.
3. needs_human_agent is true for payment disputes, account lockouts with no recovery
   path, and angry customers; otherwise false.
4. suggested_action must be a concrete instruction the support team can execute.""")

# HumanMessagePromptTemplate keeps the human side a real message object too,
# and carries the <message> delimiter the system prompt refers to.
HUMAN_MESSAGE_TEMPLATE = HumanMessagePromptTemplate.from_template(
    "<message>\n{message}\n</message>"
)


def classify_support_ticket(message: str) -> SupportTicket:
    """Classify one raw customer message into a structured ticket."""
    prompt = ChatPromptTemplate.from_messages([SYSTEM_MESSAGE, HUMAN_MESSAGE_TEMPLATE])
    model = get_model().with_structured_output(SupportTicket)
    return (prompt | model).invoke({"message": message})


if __name__ == "__main__":
    from exercises.ex3_ticket.samples import SAMPLE_MESSAGES

    for name, text in SAMPLE_MESSAGES:
        print(f"\n{'=' * 60}\nMessage: {name}\n{'-' * 60}")
        result = classify_support_ticket(text)
        print(result.model_dump_json(indent=2))
