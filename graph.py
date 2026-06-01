
from langgraph.graph import START, StateGraph

from agents.chat_bot import agent
from typing import Annotated, List
from pydantic_ai.exceptions import UsageLimitExceeded
from typing_extensions import TypedDict
from langgraph.types import StreamWriter
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
from pydantic_ai.usage import UsageLimits

max_history= 5

class chatbotstate(TypedDict):
    latest_user_message: str
    messages: Annotated[List[bytes], lambda x ,y: x+y]

async def main_bot(state: chatbotstate, writer: StreamWriter):
    messages_history: List[ModelMessage] = []
    recent_user_message = state['messages'][-max_history:]

    for message in recent_user_message:
        messages_history.extend(ModelMessagesTypeAdapter.validate_json(message))

    result = await agent.run(
        state['latest_user_message'],
        message_history= messages_history,
        usage_limits= UsageLimits(total_tokens_limit=10000, request_limit=5)
    )
    writer(result.output)

    return {
        "messages": [result.new_messages_json()]
    }

def build_graph(checkpointer= None):
    
    graph_builder = StateGraph(chatbotstate)
    graph_builder.add_node("chatbot", main_bot)
    graph_builder.add_edge(START, "chatbot")

    graph = graph_builder.compile(checkpointer=checkpointer)
    return graph