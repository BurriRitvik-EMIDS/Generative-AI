from google.adk.agents import Agent
from settings import llm
from prompts import next_best_actions_prompt

next_best_actions_agent = Agent(
    name="next_best_actions_agent",
    model=llm,
    description="Analyzes the entire conversation context and suggests actionable next steps or recommendations based on the information provided.",
    instruction=next_best_actions_prompt,
)
