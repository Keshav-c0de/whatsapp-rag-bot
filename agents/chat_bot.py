import os
import logfire
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.github import GitHubProvider
from dotenv import load_dotenv
from database.pg_vector import SupabaseVectorDB
from pydantic_ai.exceptions import UsageLimitExceeded


load_dotenv()

github_api_key = os.getenv("GITHUB_API_KEY") or os.getenv("OPENAI_API_KEY")
if not github_api_key:
    raise RuntimeError("Set GITHUB_API_KEY (or OPENAI_API_KEY for compatibility) to use GitHub Models.")

github_provider = GitHubProvider(api_key=github_api_key)

agent = Agent(
    OpenAIModel("gpt-4o-mini", provider=github_provider),
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