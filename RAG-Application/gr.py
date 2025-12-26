# gr.py

import re
import logging

class Guard:
    def __init__(self):
        self.health_focus_keywords = ["tuberculosis", "diabetes"]
        self.forbidden_input_keywords = [
            "suicide", "kill", "die", "murder", "abuse", "violence", "self-harm"
        ]
        self.min_question_length = 5
        self.min_answer_length = 30

        logging.basicConfig(
            filename="guardrails.log",
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )

    # ✅ Input Validation
    def validate_input(self, q: str) -> str | None:
        q = q.strip().lower()

        if len(q) < self.min_question_length:
            return "❌ Question is too short. Please be more specific."

        if any(bad in q for bad in self.forbidden_input_keywords):
            return "⚠️ Your question contains sensitive or unsafe content. Please ask something else."

        return None  # ✅ Input OK

    # ✅ Output Validation
    def validate_response(self, a: str) -> str | None:
        a = a.strip().lower()

        if len(a) < self.min_answer_length:
            return "⚠️ The response seems too short. Try asking a more detailed question."

        # Just a gentle check: Should ideally be about health/TB/diabetes
        if not any(k in a for k in self.health_focus_keywords):
            return "⚠️ The response may not be sufficiently focused on tuberculosis or diabetes."

        return None  # ✅ Output OK

    # ✅ Optional: Flag medical safety risks
    def check_medical_safety_flags(self, text: str) -> list[str]:
        flags = []

        if re.search(r"\b(take|prescribe|dosage|mg|ml|tablet|capsule|medicine|drug)\b", text.lower()):
            flags.append("⚠️ Do not follow dosage or medical advice from the chatbot. Always consult a doctor.")

        return flags
