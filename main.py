import os
import asyncio
from dotenv import load_dotenv
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row

try:
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
except Exception:  # pragma: no cover - optional dependency
    AsyncPostgresSaver = None
from graph import build_graph

load_dotenv()

async def run_local_chat(graph, user_message: str, from_number: str):
    thread_id = from_number

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    result = await graph.ainvoke(
        {
        "latest_user_message": user_message,
        },
        config,
        stream_mode="custom"
    )

    return result[-1]

async def run_agent(user_message: str, from_number: str) -> str:

    async with AsyncConnectionPool(
        conninfo=f"postgres://{os.getenv('DATABASE_USER')}:{os.getenv('DATABASE_PASSWORD')}"
        f"@{os.getenv('DATABASE_HOST')}:{os.getenv('DATABASE_PORT')}/{os.getenv('DATABASE_NAME')}"
        f"?sslmode=require",
        max_size=20,
        kwargs={
            "autocommit": True,
            "prepare_threshold": None,  # Disable automatic prepared statements
            "row_factory": dict_row,
        },
    ) as pool:
        async with pool.connection() as conn:
            if AsyncPostgresSaver is not None:
                memory = AsyncPostgresSaver(conn)
                await memory.setup()
                checkpointer = memory
            else:
                checkpointer = None

            # Build and run the graph
            graph = build_graph(checkpointer=checkpointer)

            # Properly consume the async generator
            response = await run_local_chat(graph, user_message, from_number)
            print(f"Agent response: {response}")
            return response


if __name__ == "__main__":
    from_number = "12222"  # Use a fixed number for the conversation

    async def main_loop():
        while True:
            try:
                user_input = input("User: ")
                if user_input.lower() in ["quit", "exit", "q"]:
                    print("Goodbye!")
                    break

                await run_agent(user_input, from_number)
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
                import traceback

                traceback.print_exc()

    # Run the async main loop
    asyncio.run(main_loop())
