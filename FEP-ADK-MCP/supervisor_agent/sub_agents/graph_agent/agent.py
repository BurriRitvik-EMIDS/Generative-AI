from google.adk.agents import Agent
from settings import llm
from prompts import graph_agent_prompt
from google.adk.tools.mcp_tool import MCPToolset, StdioConnectionParams
import os as _os


child_env = dict(_os.environ)

graph_agent = Agent(
    name="graph_agent",
    model=llm,
    description="Generates graphs and visualizations.",
    instruction=graph_agent_prompt,
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
