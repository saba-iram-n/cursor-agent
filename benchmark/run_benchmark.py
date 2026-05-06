from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.agent import SupportTriageAgent
from src.metrics import score_case


def _extract_text_content(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks: list[str] = []
        for item in content:
            if hasattr(item, "text"):
                chunks.append(getattr(item, "text"))
            elif isinstance(item, dict) and "text" in item:
                chunks.append(str(item["text"]))
        return "\n".join(chunks).strip()
    return str(content)


def _parse_json_object(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"Claude response did not contain a JSON object: {text}")
    return json.loads(cleaned[start : end + 1])


def _get_live_claude_prediction(client: object, model: str, ticket_text: str) -> tuple[dict, int]:
    system_prompt = (
        "You are a support ticket triage baseline. Return ONLY JSON with keys: "
        "category, severity, rationale, first_response. "
        "category must be one of: security, reliability, billing, general. "
        "severity must be one of: critical, high, medium, low."
    )
    user_prompt = f"Ticket:\n{ticket_text}"

    start = time.perf_counter()
    response = client.messages.create(
        model=model,
        max_tokens=350,
        temperature=0,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    text = _extract_text_content(response.content)
    parsed = _parse_json_object(text)
    required = {"category", "severity", "rationale", "first_response"}
    missing = required.difference(parsed.keys())
    if missing:
        raise ValueError(f"Claude response missing keys: {sorted(missing)}")
    return parsed, elapsed_ms


def _get_cursor_prediction(
    api_key: str, api_base_url: str, model: str, ticket_text: str
) -> tuple[dict, int]:
    system_prompt = (
        "You are a support ticket triage baseline. Return ONLY JSON with keys: "
        "category, severity, rationale, first_response. "
        "category must be one of: security, reliability, billing, general. "
        "severity must be one of: critical, high, medium, low."
    )
    payload = {
        "model": model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Ticket:\n{ticket_text}"},
        ],
    }

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        api_base_url.rstrip("/") + "/chat/completions",
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Cursor API HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Cursor API connection failed: {exc}") from exc
    elapsed_ms = int((time.perf_counter() - start) * 1000)

    data = json.loads(raw)
    content = data["choices"][0]["message"]["content"]
    parsed = _parse_json_object(content)
    required = {"category", "severity", "rationale", "first_response"}
    missing = required.difference(parsed.keys())
    if missing:
        raise ValueError(f"Cursor baseline response missing keys: {sorted(missing)}")
    return parsed, elapsed_ms


def main() -> None:
    parser = argparse.ArgumentParser(description="Run support triage benchmark.")
    parser.add_argument(
        "--baseline",
        choices=["auto", "fixture", "live", "cursor"],
        default="auto",
        help="Baseline mode: auto (live if key exists), fixture, live (Anthropic), or cursor (Cursor API).",
    )
    parser.add_argument(
        "--claude-model",
        default=os.environ.get("CLAUDE_MODEL", "claude-3-5-sonnet-latest"),
        help="Claude model ID used for live baseline mode.",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    test_cases = json.loads((root / "test_cases.json").read_text())
    claude_baseline = json.loads((root / "claude_baseline_predictions.json").read_text())
    live_baseline_outputs: dict[str, dict] = {}

    agent = SupportTriageAgent()
    use_live = False
    use_cursor = False
    anth_client = None
    cursor_api_key = os.environ.get("CURSOR_API_KEY")
    cursor_api_base_url = os.environ.get("CURSOR_API_BASE_URL", "https://api.cursor.com/v1")
    cursor_model = os.environ.get("CURSOR_MODEL", "claude-3-5-sonnet-latest")

    if args.baseline == "cursor":
        if not cursor_api_key:
            raise RuntimeError(
                "CURSOR_API_KEY is required for --baseline cursor.\n"
                "Set CURSOR_API_KEY and (optionally) CURSOR_API_BASE_URL/CURSOR_MODEL."
            )
        use_cursor = True

    if args.baseline in {"auto", "live"}:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            if importlib.util.find_spec("anthropic") is None:
                if args.baseline == "live":
                    raise RuntimeError(
                        "Live baseline requires the 'anthropic' package, but it is not installed.\n"
                        "Run:\n"
                        "  python3 -m pip install -r requirements.txt\n"
                        "or:\n"
                        "  python3 -m pip install anthropic\n"
                    )
            else:
                try:
                    from anthropic import Anthropic

                    anth_client = Anthropic(api_key=api_key)
                    use_live = True
                except Exception as exc:  # pragma: no cover
                    if args.baseline == "live":
                        raise RuntimeError(
                            "Failed to initialize Anthropic client. Verify key and package install.\n"
                            f"Original error: {exc}"
                        ) from exc
        elif args.baseline == "live":
            raise RuntimeError("ANTHROPIC_API_KEY is required for --baseline live")

    custom_total = 0
    claude_total = 0

    if use_cursor:
        baseline_label = "cursor_live"
    elif use_live:
        baseline_label = "live_claude"
    else:
        baseline_label = "fixture_claude"
    print(f"Benchmark results (scale 1-10000) using {baseline_label}:\n")

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
        if use_cursor:
            baseline_prediction, baseline_latency_ms = _get_cursor_prediction(
                cursor_api_key, cursor_api_base_url, cursor_model, case["ticket"]
            )
            live_baseline_outputs[case_id] = baseline_prediction
            claude_score = score_case(expected, baseline_prediction, baseline_latency_ms).total
        elif use_live:
            assert anth_client is not None
            baseline_prediction, baseline_latency_ms = _get_live_claude_prediction(
                anth_client, args.claude_model, case["ticket"]
            )
            live_baseline_outputs[case_id] = baseline_prediction
            claude_score = score_case(expected, baseline_prediction, baseline_latency_ms).total
        else:
            claude_score = score_case(expected, claude_baseline[case_id], 450).total

        custom_total += custom_score
        claude_total += claude_score

        print(f"{case_id}: custom={custom_score}, {baseline_label}={claude_score}")

    n = len(test_cases)
    custom_final = round(custom_total / n)
    claude_final = round(claude_total / n)

    if use_live or use_cursor:
        output_name = "live_cursor_predictions.latest.json" if use_cursor else "live_claude_predictions.latest.json"
        output_path = root / output_name
        output_path.write_text(json.dumps(live_baseline_outputs, indent=2))
        print(f"\nSaved live baseline outputs to: {output_path}")

    print("\n---\nFinal Scores")
    print(f"Custom Agent Score: {custom_final}/10000")
    print(f"Default Cursor Claude Baseline Score ({baseline_label}): {claude_final}/10000")
    print(f"Delta: {custom_final - claude_final}")


if __name__ == "__main__":
    main()
