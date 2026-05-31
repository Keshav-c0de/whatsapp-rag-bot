
from agents.chat_bot import agent
from typing import Annotated
from pydantic_ai.exceptions import UsageLimitExceeded

from langgraph.types import StreamWriter

class chatbotstate():
    query: str
    response: str