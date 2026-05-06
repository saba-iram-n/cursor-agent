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
This repository includes a reproducible side-by-side benchmark in `benchmark/run_benchmark.py` with fixture predictions for a baseline labeled `default Cursor Claude`.

### Included test cases
1. Credential leak request (security refusal)
2. Service outage ticket
3. Billing dispute

### Run benchmark
```bash
python3 benchmark/run_benchmark.py
```

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
python3 benchmark/run_benchmark.py
```

### Project structure
- `src/agent.py` - specialized triage agent
- `src/metrics.py` - scoring model
- `benchmark/test_cases.json` - benchmark dataset
- `benchmark/claude_baseline_predictions.json` - baseline outputs
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
