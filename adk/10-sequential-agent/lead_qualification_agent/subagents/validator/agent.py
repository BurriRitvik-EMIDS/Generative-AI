"""
Ground Truth Validator Agent

This agent checks if the provided claim data aligns with CMS NCCI rules,
such as appropriate CPT/ICD relationships, modifiers, POS, and clinical justifications.
"""

from google.adk.agents import LlmAgent

# --- Constants ---
GEMINI_MODEL = "gemini-2.0-flash"

# Create the validator agent
lead_validator_agent = LlmAgent(
    name="LeadValidatorAgent",
    model=GEMINI_MODEL,
    instruction="""You are a CMS Claim Ground Truth Validator.

    Your task is to validate the incoming claim data against CMS NCCI rules.
    
    Specifically check for:
    - CPT and ICD-10 alignment (procedure must be justified by diagnosis)
    - Appropriate use of Modifiers (e.g., 59, 25, 76)
    - Valid POS (Place of Service) codes for the CPT used
    - Logical consistency (e.g., age/gender appropriate procedures)

    Output ONLY 'valid' or 'invalid with a single reason if invalid.

    Example valid output: 'valid'
    Example invalid output: 'invalid: CPT code 99213 is not justified by ICD-10 code R51'
    """,
    description="Validates claim data against CMS NCCI coding logic.",
    output_key="validation_status",
)
