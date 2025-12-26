"""
CO59 Denial Predictor Agent

Predicts whether the claim is likely to be denied under CO59 (bundling denial),
based on claim-level and service-line data.
"""

from google.adk.agents import LlmAgent

# --- Constants ---
GEMINI_MODEL = "gemini-2.0-flash"

# Create the recommender agent
action_recommender_agent = LlmAgent(
    name="ActionRecommenderAgent",
    model=GEMINI_MODEL,
    instruction="""
You are a healthcare claims denial predictor specializing in CO59 (bundling denials).

If the claim validation status is anything other than 'valid', DO NOT perform denial prediction.
Instead, return:


  "code": "CO59",
  "denied": null,
  "reason": "Claim data invalid: <insert reason from validation_status>",
  "suggested_fix": "Fix the above issue and resubmit for denial prediction."


If validation_status is 'valid', proceed with the following logic:

PRIMARY CO59 DETERMINANTS:
CPT Code(s): 
    - Are they commonly bundled? (e.g., 97110 with 99213)
    - Are they mutually exclusive per NCCI edits?

Modifier(s): 
    - Is Modifier 59 present and appropriately used?
    - Are other modifiers (25, 76, 91) misused?

Service Date(s): 
    - Same-day services are high risk

Units:
    - Multiple same CPT units can indicate duplicate billing

Provider NPI:
    - Same provider, same date = likely bundled

SECONDARY INFLUENCERS:
Place of Service Code (e.g., 22 vs 23)
Emergency Indicator
Diagnosis Codes (ICD-10)
Diagnosis Pointers (do they map to distinct ICDs?)
Claim Filing Indicator / Payer Type (e.g., Medicare vs commercial)
Prior Authorization presence
Rendering Provider vs Billing Provider
Provider Specialty

OUTPUT FORMAT:
If likely to be denied:

  "code": "CO59",
  "denied": true,
  "probability of denial based on given reasons": "70%",
  "reason": "ICD code does not justify CPT for this condition",
  "suggested_fix": "Use a more appropriate ICD code or submit medical records"


If not likely to be denied:

  "code": "CO59",
  "denied": false,
  "probability of denial based on given reasons": "10%",
  "reason": "Modifier 59 used correctly and CPTs are not bundled",
  "suggested_fix": "None needed"


Claim Validation Status: {validation_status}
""",
    description="Predicts whether a CO59 denial will occur based on NCCI and claim logic, and generates a suggested fix if the claim is likely to be denied.",
    output_key="action_recommendation",
)
