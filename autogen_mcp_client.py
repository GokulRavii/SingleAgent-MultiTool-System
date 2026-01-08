from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv
import os
from mcp_tools import call_mcp_tool
import asyncio
import json

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

model_client = OpenAIChatCompletionClient(
    model="gemini-2.5-flash",
    api_key=api_key
)


assistant = AssistantAgent(
    name="weather_agent",
    model_client=model_client,
    description = 'An agent which uses tools to solve tasks',
    system_message="""
You are a weather routing agent.

You MUST respond with ONLY valid JSON.
NO explanations.
NO markdown.
NO extra text.

Schema:
{
  "tool": "get_alerts" | "get_forecast" | "send_email",
  "args": { ... }
}

Rules:
- Alerts questions → get_alerts(state)
- Forecast questions → get_forecast(latitude, longitude)
- Math question -> calc(a, b, operation)
- Email requests → send_email(to, subject, body)

Examples:

User: Is there any weather alert in California?
Response:
{"tool":"get_alerts","args":{"state":"CA"}}

User: Give me the forecast for San Francisco
Response:
{"tool":"get_forecast","args":{"latitude":37.77,"longitude":-122.42}}

User: Send an email to test@gmail.com saying hello
Response:
{
  "tool": "send_email",
  "args": {
    "to": "test@gmail.com",
    "subject": "Hello",
    "body": "Hello!"
  }
}
"""
)


# user_proxy = UserProxyAgent(
#     name="user",
#     description = 'A proxy agent that represent a user',
#     input_func = input
# )

async def run(query: str):
    result = await assistant.run(task = query)
    #print("dw",result)
    reply = result.messages[-1].content
    print("\nRaw LLM output:\n", reply)

    # Parse JSON from LLM
    tool_call = json.loads(reply)
    #print(tool_call)

    tool_name = tool_call["tool"]
    args = tool_call["args"]

    print(f"\nCalling MCP tool: {tool_name} with {args}")

    result = await call_mcp_tool(tool_name, args)

    print("\nMCP RESULT:\n", result)

if __name__ == "__main__":
    asyncio.run(run("send email to gokulravi.vkp@gmail.com with the subject 'Hello Ravi' and body 'Meeting is Postponed'"))

# Is there any weather alert in California?
# Give me forecast for San Francisco
# what is 10 divide by 0?
# uv run server\Autogen_integrated\autogen_mcp_client.py

"""
User: "Is there any weather alert in Newyork?"

↓
AutoGen LLM
↓
{"tool":"get_alerts","args":{"state":"NY"}}

↓
call_mcp_tool()
↓
MCP Server
↓
weather.gov API
↓
formatted alerts

↓
User sees result
"""