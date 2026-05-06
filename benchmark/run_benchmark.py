from __future__ import annotations

import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.agent import SupportTriageAgent
from src.metrics import score_case


def main() -> None:
    root = Path(__file__).resolve().parent
    test_cases = json.loads((root / "test_cases.json").read_text())
    claude_baseline = json.loads((root / "claude_baseline_predictions.json").read_text())

    agent = SupportTriageAgent()

    custom_total = 0
    claude_total = 0

    print("Benchmark results (scale 1-10000):\n")

    for case in test_cases:
        case_id = case["id"]
        expected = case["expected"]

        start = time.perf_counter()
        result = agent.run(case["ticket"])
        elapsed_ms = int((time.perf_counter() - start) * 1000)

        custom_dict = {
            "category": result.category,
            "severity": result.severity,
            "rationale": result.rationale,
            "first_response": result.first_response,
        }

        custom_score = score_case(expected, custom_dict, elapsed_ms).total
        claude_score = score_case(expected, claude_baseline[case_id], 450).total

        custom_total += custom_score
        claude_total += claude_score

        print(f"{case_id}: custom={custom_score}, claude_baseline={claude_score}")

    n = len(test_cases)
    custom_final = round(custom_total / n)
    claude_final = round(claude_total / n)

    print("\n---\nFinal Scores")
    print(f"Custom Agent Score: {custom_final}/10000")
    print(f"Default Cursor Claude Baseline Score: {claude_final}/10000")
    print(f"Delta: {custom_final - claude_final}")


if __name__ == "__main__":
    main()
