"""
Guardrails Pattern Example
--------------------------
This script demonstrates the Guardrails & Safety pattern:
Input -> Validate -> Process -> Validate -> Output

It simulates PII redaction and toxic content filtering.
"""

import asyncio
import re


class Guardrails:
    def __init__(self):
        self.banned_words = ["violence", "illegal", "hack"]

    def validate_input(self, text: str) -> bool:
        # Check for banned concepts
        for word in self.banned_words:
            if word in text.lower():
                print(f"🛑 Blocked Input: Contains banned word '{word}'")
                return False
        return True

    def sanitize_output(self, text: str) -> str:
        # Redact PII (Email)
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        redacted_text = re.sub(email_pattern, "[REDACTED_EMAIL]", text)

        if redacted_text != text:
            print("🛡️  Output Sanitized: PII redacted.")

        return redacted_text


async def safe_agent(prompt: str, guard: Guardrails):
    print(f"\nUser: {prompt}")

    # 1. Input Guardrail
    if not guard.validate_input(prompt):
        print("🤖 AI: I cannot process that request.")
        return

    # 2. Process (Simulated)
    response = f"Here is the info you asked for regarding {prompt}. Contact admin@example.com for more."

    # 3. Output Guardrail
    safe_response = guard.sanitize_output(response)
    print(f"🤖 AI: {safe_response}")


async def main():
    guard = Guardrails()

    # Safe interaction
    await safe_agent("marketing strategy", guard)

    # Unsafe interaction (Blocked input)
    await safe_agent("how to hack a bank", guard)

    # Unsafe interaction (PII in output)
    await safe_agent("contact details", guard)


if __name__ == "__main__":
    asyncio.run(main())
