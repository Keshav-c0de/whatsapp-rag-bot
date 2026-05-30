import os
import logfire
from pydantic_ai import Agent
from dotenv import load_dotenv
from database.pg_vector import SupabaseVectorDB
from pydantic_ai.exceptions import UsageLimitExceeded

load_dotenv()

agent = Agent(
    "openai-chat:gpt-4o-mini",
    system_prompt="You are a helpful assistant that answers questions based on the provided context. return the answer in plan text format. If you don't have the proper information needed, say you don't know.",
    model_settings={
        "temperature": 0.1,
        "max_tokens": 500,
    },
)

@agent.tool_plain
def get_solution(query: str) -> str:
    """return relevant technical information from the database based on the query"""

    db = SupabaseVectorDB()

    try:
        results = db.similarity_search(query, top_k=3)
        if not results:
            return "I don't know the answer to that question based on the provided context."
        
        # Combine the retrieved documents into a single context string
        context = "\n\n".join([result['text_content'] for result in results])
        return context
    
    except UsageLimitExceeded as e:
            logfire.error(f"Usage limit exceeded: {e}")
            return "You have exceeded the usage limit for this service. Please try again later."

    except Exception as e:
        logfire.error(f"Error during similarity search: {e}")
        return "encountered an error while retrieving information. Please try again later."