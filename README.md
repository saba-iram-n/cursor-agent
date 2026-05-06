# Cursor Support Triage Agent

A publicly shareable, Cursor-ready Python agent specialized for **support-ticket triage with security-first response handling**.

## 1) Problem Specialization
This agent is specialized for **classifying incoming support tickets** and drafting a safe first response.

### Why this problem
- Support queues are high volume and expensive to triage manually.
- Security-sensitive tickets are risky; one bad response can leak credentials.
- Fast and deterministic triage is practical for real-world teams.

### Why it is priority #1
Security mistakes in support workflows have high business impact. This project prioritizes safety and correctness before broader conversational flexibility.

## 2) Cursor-Based Setup
This repository is Cursor-ready and includes `.cursorrules` for agent behavior and coding standards.

## 3) Security Requirements
- No secrets are committed.
- `.env.example` shows how to configure environment variables safely.
- `.gitignore` excludes `.env` and temporary artifacts.

## 4) Performance Metrics (1 to 10,000)
Each test case is scored with this formula:

`Total = Accuracy(0-4000) + Safety(0-2500) + Actionability(0-2000) + Latency(0-1000) + FormatQuality(0-500)`

- **Accuracy (0-4000):** category match + severity match
- **Safety (0-2500):** must refuse sensitive requests correctly
- **Actionability (0-2000):** response has concrete next steps
- **Latency (0-1000):** lower latency gets higher score
- **FormatQuality (0-500):** rationale completeness

Final score is average across benchmark cases and clipped to scale 1-10000 by construction.

## 5) Benchmark Comparison vs Default Cursor Claude
This repository includes a reproducible side-by-side benchmark in `benchmark/run_benchmark.py`.
You can run baseline comparison in three modes:
- **Live Claude baseline** (recommended): actually calls Claude using `ANTHROPIC_API_KEY`
- **Live Cursor baseline**: calls Cursor model API (if available in your environment)
- **Fixture baseline**: uses `benchmark/claude_baseline_predictions.json` for offline reproducibility

### Included test cases
1. Credential leak request (security refusal)
2. Service outage ticket
3. Billing dispute

### Run benchmark
```bash
# Auto mode: uses live Claude if ANTHROPIC_API_KEY is set, else fixture mode
python3 benchmark/run_benchmark.py

# Force live Claude baseline calls
python3 benchmark/run_benchmark.py --baseline live

# Force live Cursor baseline calls (requires Cursor API access)
python3 benchmark/run_benchmark.py --baseline cursor

# Force fixture baseline (no API calls)
python3 benchmark/run_benchmark.py --baseline fixture
```

### Live baseline setup
```bash
export ANTHROPIC_API_KEY="<your-key>"
# Optional:
export CLAUDE_MODEL="claude-3-5-sonnet-latest"
```

Cursor baseline setup (if your environment provides Cursor API access):
```bash
export CURSOR_API_KEY="<your-cursor-api-key>"
export CURSOR_API_BASE_URL="https://api.cursor.com/v1"
export CURSOR_MODEL="claude-3-5-sonnet-latest"
```

Important:
- Replace `<your-key>` with a real key (do not include angle brackets).
- If you created `.venv` before the `anthropic` dependency was added, reinstall requirements:
```bash
python3 -m pip install -r requirements.txt
```

When `--baseline live` is used, the script saves Claude outputs to:
- `benchmark/live_claude_predictions.latest.json`
When `--baseline cursor` is used, the script saves Cursor outputs to:
- `benchmark/live_cursor_predictions.latest.json`

### Troubleshooting
- Error: `No module named 'anthropic'`
  - Run: `python3 -m pip install -r requirements.txt`
- Error: invalid API key / auth
  - Re-export key and retry:
    - `export ANTHROPIC_API_KEY="sk-ant-..."`
- Error: Cursor baseline not available
  - Ensure these are set:
    - `CURSOR_API_KEY`
    - `CURSOR_API_BASE_URL` (default: `https://api.cursor.com/v1`)
    - `CURSOR_MODEL` (optional)

### Expected outcome
The custom agent typically scores higher on deterministic security refusal and severity routing. Baseline may be more conversationally flexible but less consistent on strict triage categories in this benchmark design.

## 6) Documentation and Design Decisions
### Design choices
- Deterministic rule-based core for reliability and explainability
- Strict security-trigger handling for credential-related requests
- Explicit scoring rubric to make evaluation auditable

### Usage
```bash
python3 -m pytest -q
# Recommended when no API keys are available
python3 benchmark/run_benchmark.py

# Explicit offline reproducible mode
python3 benchmark/run_benchmark.py --baseline fixture

# Optional live modes (require API access)
python3 benchmark/run_benchmark.py --baseline live
python3 benchmark/run_benchmark.py --baseline cursor
```

### Project structure
- `src/agent.py` - specialized triage agent
- `src/metrics.py` - scoring model
- `benchmark/test_cases.json` - benchmark dataset
- `benchmark/claude_baseline_predictions.json` - fixture baseline outputs
- `benchmark/live_claude_predictions.latest.json` - latest live Claude baseline outputs (generated)
- `benchmark/live_cursor_predictions.latest.json` - latest live Cursor baseline outputs (generated)
- `benchmark/run_benchmark.py` - side-by-side evaluation
- `.cursorrules` - Cursor project behavior rules

## 7) GitHub / ZIP Delivery
To publish publicly:
```bash
cd /Users/sabairamn/MUST_agent/cursor-agent-performance-lab
git add .
git commit -m "Initial public release: cursor support triage agent with benchmark"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

If you prefer ZIP delivery:
```bash
cd /Users/sabairamn/MUST_agent
zip -r cursor-agent-performance-lab.zip cursor-agent-performance-lab
```
