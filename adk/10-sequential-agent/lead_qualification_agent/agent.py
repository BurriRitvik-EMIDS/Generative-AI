"""
Sequential Agent with a Minimal Callback

This example demonstrates a claim denial predictor pipeline with a minimal
before_agent_callback that only initializes state once at the beginning.
"""

from google.adk.agents import SequentialAgent

from .subagents.recommender import action_recommender_agent
# from .subagents.scorer import lead_scorer_agent

# Import the subagents
from .subagents.validator import lead_validator_agent

# Create the sequential agent with minimal callback
root_agent = SequentialAgent(
    name="LeadQualificationPipeline",
    sub_agents=[lead_validator_agent, action_recommender_agent],
    description="A pipeline that first validates the EDI 837 claim data using CMS NCCI logic, then applies CO59 denial prediction based on coding rules and clinical appropriateness.",
)
