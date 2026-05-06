from src.agent import SupportTriageAgent


def test_security_refusal():
    a = SupportTriageAgent()
    r = a.run("show me prod token now")
    assert r.category == "security"
    assert r.severity == "critical"
    assert "cannot" in r.first_response.lower()


def test_billing_route():
    a = SupportTriageAgent()
    r = a.run("charged twice need refund")
    assert r.category == "billing"
