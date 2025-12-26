from google.adk.agents import Agent
from settings import llm
from prompts import member_claims_agent_prompt
from google.adk.tools.mcp_tool import MCPToolset, StdioConnectionParams
import os as _os


child_env = dict(_os.environ)

member_claims_agent = Agent(
    name="member_claims_agent",
    model=llm,
    description="Handles queries & retrieves information related to claims data stored in a CSV file.",
    instruction=member_claims_agent_prompt,
    tools=[MCPToolset(
        connection_params=StdioConnectionParams(
            server_params={
                "command": "python",
                "args": ["mcp_server.py"],
                "env": child_env,
            }
        )
    )],
)
