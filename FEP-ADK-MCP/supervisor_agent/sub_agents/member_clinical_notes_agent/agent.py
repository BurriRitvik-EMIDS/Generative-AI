from google.adk.agents import Agent
from settings import llm
from prompts import member_clinical_notes_prompt
from google.adk.tools.mcp_tool import MCPToolset, StdioConnectionParams
import os as _os


child_env = dict(_os.environ)


member_clinical_notes_agent = Agent(
    name="member_clinical_notes_agent",
    model=llm,
    description="Retrieves information about clinical notes and medical history and clinical visits related information.",
    instruction=member_clinical_notes_prompt,
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
