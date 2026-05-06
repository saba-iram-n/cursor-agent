from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass
class TriageResult:
    category: str
    severity: str
    confidence: float
    rationale: str
    first_response: str


class SupportTriageAgent:
    """Specialized agent for support-ticket triage and safe first response drafting."""

    SECURITY_PATTERNS = [r"api key", r"token", r"password", r"credential", r"private key"]

    def run(self, ticket_text: str) -> TriageResult:
        text = ticket_text.lower()

        if self._looks_sensitive_request(text):
            return TriageResult(
                category="security",
                severity="critical",
                confidence=0.99,
                rationale="Ticket requests or reveals sensitive credential material.",
                first_response=(
                    "I cannot help expose or share secrets. Please rotate impacted credentials "
                    "immediately, revoke tokens, and use your secure secret manager."
                ),
            )

        if any(k in text for k in ["down", "outage", "500", "cannot login", "can\'t login"]):
            return TriageResult(
                category="reliability",
                severity="high",
                confidence=0.9,
                rationale="Service reliability indicators detected.",
                first_response="Acknowledged. We are escalating to on-call and collecting logs for immediate mitigation.",
            )

        if any(k in text for k in ["invoice", "billing", "refund", "charged"]):
            return TriageResult(
                category="billing",
                severity="medium",
                confidence=0.88,
                rationale="Billing-related terms detected.",
                first_response="Thanks for flagging this. Please share invoice ID and charge date; billing ops will review today.",
            )

        return TriageResult(
            category="general",
            severity="low",
            confidence=0.72,
            rationale="No high-risk patterns found; routed to general support.",
            first_response="Thanks for reaching out. We've logged your request and will respond with next steps shortly.",
        )

    def _looks_sensitive_request(self, text: str) -> bool:
        pattern_hit = any(re.search(p, text) for p in self.SECURITY_PATTERNS)
        dangerous_intent = any(x in text for x in ["show me", "send me", "dump", "leak", "bypass"])
        return pattern_hit and dangerous_intent
