from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.agent import SupportTriageAgent


def run_benchmark(baseline: str) -> tuple[bool, str]:
    cmd = [sys.executable, str(PROJECT_ROOT / "benchmark" / "run_benchmark.py"), "--baseline", baseline]
    proc = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
    output = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
    return proc.returncode == 0, output.strip()


def load_case_file() -> list[dict]:
    path = PROJECT_ROOT / "benchmark" / "test_cases.json"
    return json.loads(path.read_text())


def parse_benchmark_output(output: str) -> tuple[list[dict], dict]:
    rows: list[dict] = []
    summary = {"custom": None, "baseline": None, "delta": None}
    for line in output.splitlines():
        case_match = re.match(r"^(case_[a-z_]+): custom=(\d+), [a-z_]+=(\d+)$", line.strip())
        if case_match:
            rows.append(
                {
                    "case_id": case_match.group(1),
                    "custom_score": int(case_match.group(2)),
                    "baseline_score": int(case_match.group(3)),
                    "delta": int(case_match.group(2)) - int(case_match.group(3)),
                }
            )
            continue

        custom_match = re.match(r"^Custom Agent Score: (\d+)/10000$", line.strip())
        if custom_match:
            summary["custom"] = int(custom_match.group(1))
            continue
        baseline_match = re.match(r"^Default Cursor Claude Baseline Score .*: (\d+)/10000$", line.strip())
        if baseline_match:
            summary["baseline"] = int(baseline_match.group(1))
            continue
        delta_match = re.match(r"^Delta: (-?\d+)$", line.strip())
        if delta_match:
            summary["delta"] = int(delta_match.group(1))
    return rows, summary


def severity_badge(severity: str) -> str:
    palette = {
        "critical": "#8B0000",
        "high": "#D97706",
        "medium": "#1D4ED8",
        "low": "#047857",
    }
    color = palette.get(severity.lower(), "#374151")
    return (
        f"<span style='background:{color};color:white;padding:4px 10px;"
        "border-radius:999px;font-size:12px;font-weight:600;'>"
        f"{severity.upper()}</span>"
    )


st.set_page_config(page_title="Support Triage Execution UI", layout="wide")
st.markdown(
    """
<style>
.card {
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 16px;
  background: #ffffff;
}
.kpi {
  border-radius: 12px;
  padding: 14px;
  background: #f8fafc;
  border: 1px solid #e5e7eb;
}
.kpi-label {
  color: #64748b;
  font-size: 12px;
  margin-bottom: 6px;
}
.kpi-value {
  color: #0f172a;
  font-size: 26px;
  font-weight: 700;
}
</style>
""",
    unsafe_allow_html=True,
)
st.title("Support Triage Agent - Execution Screen")
st.caption("Run ticket triage and benchmark comparison from a UI.")

agent = SupportTriageAgent()
if "last_triage" not in st.session_state:
    st.session_state.last_triage = None
if "benchmark_output" not in st.session_state:
    st.session_state.benchmark_output = ""

left, right = st.columns(2)

with left:
    st.subheader("1) Single Ticket Execution")
    sample_cases = load_case_file()
    case_options = {"Custom input": ""}
    for c in sample_cases:
        case_options[c["id"]] = c["ticket"]

    selected = st.selectbox("Sample ticket", list(case_options.keys()))
    default_text = case_options[selected]
    ticket_text = st.text_area("Ticket text", value=default_text, height=180)

    if st.button("Run Agent", type="primary"):
        if not ticket_text.strip():
            st.error("Please provide ticket text.")
        else:
            result = agent.run(ticket_text)
            st.session_state.last_triage = result
            st.success("Execution complete")

    triage = st.session_state.last_triage
    if triage:
        c1, c2, c3 = st.columns(3)
        c1.markdown(
            f"<div class='kpi'><div class='kpi-label'>Category</div><div class='kpi-value'>{triage.category.title()}</div></div>",
            unsafe_allow_html=True,
        )
        c2.markdown(
            f"<div class='kpi'><div class='kpi-label'>Severity</div><div>{severity_badge(triage.severity)}</div></div>",
            unsafe_allow_html=True,
        )
        c3.markdown(
            f"<div class='kpi'><div class='kpi-label'>Confidence</div><div class='kpi-value'>{triage.confidence:.2f}</div></div>",
            unsafe_allow_html=True,
        )
        st.markdown("#### Rationale")
        st.markdown(f"<div class='card'>{triage.rationale}</div>", unsafe_allow_html=True)
        st.markdown("#### First Response")
        st.markdown(f"<div class='card'>{triage.first_response}</div>", unsafe_allow_html=True)

with right:
    st.subheader("2) Benchmark Execution")
    baseline = st.selectbox(
        "Baseline mode",
        ["fixture", "auto", "live", "cursor"],
        help="Use fixture if you do not have API keys.",
    )
    st.markdown(
        "- `fixture`: no API key required\n"
        "- `auto`: uses Anthropic if available, otherwise fixture\n"
        "- `live`: requires `ANTHROPIC_API_KEY`\n"
        "- `cursor`: requires `CURSOR_API_KEY` and API access"
    )

    if st.button("Run Benchmark"):
        with st.spinner("Running benchmark..."):
            ok, output = run_benchmark(baseline)
            st.session_state.benchmark_output = output
        if ok:
            st.success("Benchmark completed")
        else:
            st.error("Benchmark failed")

    benchmark_output = st.session_state.benchmark_output
    if benchmark_output:
        table_rows, summary = parse_benchmark_output(benchmark_output)
        k1, k2, k3 = st.columns(3)
        k1.metric("Custom Score", summary["custom"])
        k2.metric("Baseline Score", summary["baseline"])
        k3.metric("Delta", summary["delta"])
        if table_rows:
            st.markdown("#### Benchmark Results Table")
            st.dataframe(table_rows, use_container_width=True, hide_index=True)
        st.markdown("#### Raw Benchmark Logs")
        st.code(benchmark_output, language="text")

st.divider()
st.subheader("Environment Keys (optional)")
env_cols = st.columns(5)
env_cols[0].metric("Anthropic Key", "Set" if os.environ.get("ANTHROPIC_API_KEY") else "Not Set")
env_cols[1].metric("Cursor Key", "Set" if os.environ.get("CURSOR_API_KEY") else "Not Set")
env_cols[2].metric("Cursor Base URL", os.environ.get("CURSOR_API_BASE_URL", "https://api.cursor.com/v1"))
env_cols[3].metric("Cursor Model", os.environ.get("CURSOR_MODEL", "claude-3-5-sonnet-latest"))
env_cols[4].metric("Claude Model", os.environ.get("CLAUDE_MODEL", "claude-3-5-sonnet-latest"))
