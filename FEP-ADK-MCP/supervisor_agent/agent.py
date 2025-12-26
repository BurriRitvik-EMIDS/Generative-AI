from google.adk.agents import Agent
from settings import llm
from prompts import supervisor_prompt
from supervisor_agent.sub_agents.member_clinical_notes_agent.agent import member_clinical_notes_agent

from .sub_agents.member_agent.agent import member_agent
from .sub_agents.next_best_actions_agent.agent import next_best_actions_agent
from .sub_agents.graph_agent.agent import graph_agent
from .sub_agents.member_claims_agent.agent import member_claims_agent
from .sub_agents.member_clinical_notes_agent.agent import member_clinical_notes_agent


root_agent = Agent(
    name="supervisor_agent",
    model=llm,
    description="Routes the query to the appropriate sub-agent based on intent.",
    instruction=supervisor_prompt,
    sub_agents=[member_agent, next_best_actions_agent,
                graph_agent, member_claims_agent, member_clinical_notes_agent],
)
