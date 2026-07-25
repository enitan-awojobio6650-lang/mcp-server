"""
MCP client for the Library Server, using OpenRouter as the LLM provider.

Connects to app.py over stdio using the OpenAI Agents SDK, sends a request
that requires at least two tool calls in one conversation
(search_books -> borrow_book), and prints the final agent response.
"""

import asyncio
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, Runner, OpenAIChatCompletionsModel, set_tracing_disabled
from agents.mcp import MCPServerStdio

load_dotenv()
set_tracing_disabled(True)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# OpenRouter exposes an OpenAI-compatible endpoint
client = AsyncOpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
)

# Pick any free/available OpenRouter model you've used before in this bootcamp
MODEL_NAME = "nvidia/nemotron-3-ultra-550b-a55b:free"


async def main() -> None:
    async with MCPServerStdio(
        name="Library Server",
        params={
            "command": "uv",
            "args": ["run", "python", "app.py"],
        },
        client_session_timeout_seconds=30,
    ) as server:
        agent = Agent(
            name="Librarian Assistant",
            instructions=(
                "You are a helpful library assistant. Use the available tools "
                "to search for books and manage borrowing/returning. When the "
                "user's request implies multiple steps (e.g. 'find X, then "
                "borrow one'), complete ALL steps yourself without pausing to "
                "ask which option to pick — choose a reasonable one and act. "
                "Only ask a clarifying question if the request is truly "
                "ambiguous and cannot be resolved on your own. Always confirm "
                "to the user what you did at the end."
            ),
            model=OpenAIChatCompletionsModel(model="nvidia/nemotron-3-ultra-550b-a55b:free", openai_client=client),
            mcp_servers=[server],
        )

        result = await Runner.run(
            agent,
            "Find me books about space, then borrow one for member M001.",
        )

        print("\n=== Final Agent Response ===")
        print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
