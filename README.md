# SkyBridge TRIAGE

**Airline Disruption & Passenger Recovery Decisioning**  
TAG AI Team Development Program — Week 3 Final Competition

> Developed a dual-horizon disruption-risk model (gradient boosting, AUC 0.949 vs. 0.938 baseline, bootstrap-validated) on 30K flights / 290K bookings; designed a fairness-audited Recovery Priority Index for capacity-aware recovery, achieving 95.3% recall at the cost-optimal threshold; presented through a multi-page Streamlit dashboard.

Treat disruption recovery like an emergency room: flights arrive with different severities, OCC is the triage desk, and recovery capacity (seats, hotels, agents, budget) is always finite. A risk score is a triage score — not a verdict — and human controllers can always override.

---

## The big idea — TRIAGE

| Letter | Stands for | Decision area |
|--------|------------|---------------|
| **T** | Timing | When to decide (flight disruption) |
| **R** | Risk | Which flights disrupt |
| **I** | Impact | Which passengers are hurt |
| **A** | Allocation | Who gets what recovery action |
| **G** | Guardrails | Human review, fairness, override logging |
| **E** | Evaluation | Pilot KPIs and stop/scale rule |

### Dual-horizon decision timing (T)

- **EARLYBIRD (~T-240 / T-210):** soft prep trigger — put a flight on OCC’s radar; no hard resource commitment. Signal is already strong this early.
- **LASTCALL (~T-90 / T-60):** confirm trigger — flight formally enters the recovery queue and consumes capacity.

---

## Repository structure

```text
github_upload/
├── README.md                          ← you are here
├── requirements.txt
├── .gitignore
├── SkyBridge_Analysis_Notebook.ipynb  ← full evidence trail (EDA → model → RPI → exports)
├── dashboard/
│   ├── skybridge_triage_dashboard.py  ← Streamlit business dashboard
│   └── dashboard_data/                ← pre-computed CSV/JSON from notebook §11
├── docs/
│   ├── SkyBridge_TRIAGE_Playbook.md   ← team strategy & pitch bible
│   ├── SkyBridge_TRIAGE_Presentation.pptx
│   └── Executive_Recommendation.docx
└── outputs/
    ├── Passenger_Decision_Output.csv  ← JED pilot decision queue (~9,960 bookings)
    └── fairness_audit.csv
```

> **Note:** Raw competition data drops (`Data_Drop_01/02/03`) are **not** included in this repo. The Streamlit dashboard runs entirely from `dashboard/dashboard_data/`. Re-running the notebook requires the original TAG data pack and updating the `DATA` path in the first code cell.

---

## Quick start — business dashboard

The dashboard is the easiest way to explore results. It never retrains the model.

```bash
# from this folder
pip install -r requirements.txt
streamlit run dashboard/skybridge_triage_dashboard.py
```

Opens at [http://localhost:8501](http://localhost:8501).

### Dashboard pages

| Page | What it shows |
|------|---------------|
| **Executive Overview** | KPIs, RPI band mix, Monte Carlo pilot cost range (p10 / p50 / p90) |
| **Flight Risk Explorer** | Risk calibration, route/airport hotspots, monthly & hourly trends |
| **Passenger Recovery Queue** | Filterable RPI-ranked JED decisions + CSV download |
| **Fairness & Responsible AI** | Age / nationality gap charts; human-review design |
| **Recovery Economics** | Cost ladder, satisfaction/complaints, capacity stress, complaint topics |
| **Scenario Simulator** | Live Monte Carlo + JED hotel-capacity-cut stress test |

---

## Key findings (data-grounded)

1. **Waiting for certainty barely buys certainty.** Correlation of inbound aircraft delay with material disruption is **0.68 at T-300** and only **0.73 at T-30**. The signal is already strong five hours out.
2. **Turnaround readiness beats weather as an early warning.** `Turnaround_Readiness_Pct` correlates at **−0.65** with disruption vs. weather severity **0.31**.
3. **Peak-hour flights are ~34% more likely** to become a material disruption (**23.7%** vs **17.7%** off-peak).
4. **Long-tail allocation problem.** ~80% of bookings on a disrupted flight only need “Keep Original.” Precision in the remaining ~20% is where the money is.
5. **Cost escalates ~64×** across the action ladder: Keep Original ≈ **EGP 77**/pax vs Hotel + Rebook ≈ **EGP 4,932**/pax.
6. **Complaints cost ~2 satisfaction points** (8.4 → 6.4) and hit ~10.8% of disrupted bookings.
7. **Human override today ≈ 8.6%** — the pilot’s stop-rule benchmark.

---

## Risk model (R)

| Item | Detail |
|------|--------|
| **Target** | Binary *material disruption* = Major + Severe + Cancelled (base rate ≈ **19.8%**) |
| **Baseline** | Logistic regression on T-240 raw features |
| **Challenger** | Gradient boosting + **multi-snapshot trend features** (slope of inbound delay & turnaround readiness across the 300→30 min window) |
| **Baseline AUC** | **0.938** |
| **Challenger AUC** | **0.949** |
| **AUC gap** | **+0.0105** — bootstrap p &lt; 0.001; 95% CI **[0.007, 0.014]** (entirely above zero) |
| **Operating threshold** | Cost-weighted (~**0.055**), using FN cost ≈ EGP 4,932 and FP prep cost ≈ EGP 300 — not a default 0.5 cutoff |
| **Recall @ cost-optimal threshold** | **95.3%** |

**Decision-time discipline:** `Final_Disruption_Severity` and `Actual_Departure_Delay_Min` are labels only — never features.

---

## Passenger Recovery Priority Index (I + A)

```text
RPI = 0.40 × Connection_Fragility
    + 0.25 × Party_Feasibility_Risk
    + 0.20 × Vulnerability          (special assistance, child in party, overnight delay)
    + 0.15 × Severity_of_Flight_Risk  (from the R model)
```

**Bands:** Critical → Priority → Watch → Low (process in that order).

**Explicitly excluded from scoring:** `Age_Band_AuditOnly`, `Nationality_Group_AuditOnly` (audit-only).  
**Loyalty / customer value:** tie-breaker only — never a primary weight.

**Allocation:** cheapest feasible recovery option that satisfies party size and cabin; otherwise flag for manual handling.

**Auto-approve:** low-cost / low-sensitivity actions (Keep Original, Keep Original + Care, Rebook Same Day under cost threshold).  
**Mandatory human review:** Hotel + Rebook, Rebook Next Day, cabin downgrade, special assistance, or no feasible option.

### JED pilot decision output (summary)

| Metric | Value |
|--------|-------|
| Disrupted flights (JED-touching) | 1,004 |
| Affected bookings | 9,960 |
| Total estimated recovery cost | EGP ~4.07M (historical-scale reference) |
| Human review rate | ~1.9% (188 bookings) |
| Band mix | Critical 119 · Priority 1,325 · Watch 4,545 · Low 3,971 |

---

## Fairness & responsible AI (G)

| Group field | Priority-rate range | Max gap |
|-------------|---------------------|---------|
| Age band (18–25, 26–40, 41–60, 60+) | 14.1% – 14.8% | **0.7 pts** |
| Nationality (Egypt, GCC, Levant, Europe/Other) | 14.1% – 16.1% | **2.0 pts** |

**Calibrated claim:** checked, small gaps, worth re-running on more data before scaling — not “proven fair.”

### Accountability map

| Role | Responsibility |
|------|----------------|
| Business Owner | Customer Experience Director — churn/disruption KPI; go/no-go past JED |
| AI / Data Team | R model + RPI; fairness audit cadence |
| Operations | OCC (EARLYBIRD/LASTCALL queue); Passenger Recovery agents (RPI queue) |
| Risk / Compliance | Audit-only exclusion + fairness review before go-live |
| Management Sponsor | JED pilot budget and stop/scale decision |

---

## Pilot & evaluation (E)

**Scope:** single-airport pilot at **JED**, 4–6 weeks (covers the Client Change Request’s hotel-capacity constraint).

### Monte Carlo pilot cost (5,000 runs)

| Scenario | Affected bookings (approx.) | Estimated cost (EGP) |
|----------|-----------------------------|----------------------|
| p10 (optimistic) | ~8,564 | ~1,347,502 |
| p50 (expected) | ~9,467 | ~1,961,848 |
| **p90 (budget ceiling)** | ~10,384 | **~2,678,922** |

Ask Finance to approve against **p90**, not p50.

### Success / stop rules

- **Success:** lower severe passenger impact at comparable disruption levels; cost per avoided severe impact trending down; override rate stable or falling.
- **Stop / pause:** override rate spikes well above ~8.6% historical baseline; persistent unexplained fairness gap; any compliance/safety concern from OCC.

### Day-4 capacity shock (no model rebuild)

JED hotel capacity −35%: raise the RPI bar for hotel-tier actions at JED; prefer ground-transfer / same-day rebook below that bar; route overflow to human review. Policy change, not a model change — stress-testable in the Scenario Simulator.

---

## Analysis notebook outline

`SkyBridge_Analysis_Notebook.ipynb` (12 sections):

1. Load & business framing  
2. EDA — timing & turnaround insights  
3. Extended EDA across all data drops  
4. Feature engineering — multi-snapshot trends  
5. Baseline vs. challenger  
6. Cost-weighted operating threshold  
7. RPI + JED decision output  
8. Bootstrap hypothesis test on AUC gap  
9. Monte Carlo pilot cost range  
10. Fairness audit  
11. Export dashboard artifacts → `dashboard/dashboard_data/`  
12. Summary  

To re-run against the competition data pack, set in the first code cell:

```python
DATA = "/path/to/03_DATA/extracted"
```

Then re-run Section 11 to refresh `dashboard/dashboard_data/`.

---

## Tech stack

| Layer | Tools |
|-------|--------|
| Analysis | Python, pandas, scikit-learn (LogisticRegression, GradientBoostingClassifier), matplotlib, seaborn, networkx |
| Dashboard | Streamlit, Plotly |
| Deliverables | Jupyter notebook, Markdown playbook, PowerPoint, Word exec note, CSV decision output |

---

## Docs & deliverables

| File | Purpose |
|------|---------|
| [`docs/SkyBridge_TRIAGE_Playbook.md`](docs/SkyBridge_TRIAGE_Playbook.md) | Full team playbook: TAG curriculum mapping, pitch strategy, workload discipline |
| [`docs/SkyBridge_TRIAGE_Presentation.pptx`](docs/SkyBridge_TRIAGE_Presentation.pptx) | Competition presentation deck |
| [`docs/Executive_Recommendation.docx`](docs/Executive_Recommendation.docx) | One-page executive recommendation |
| [`outputs/Passenger_Decision_Output.csv`](outputs/Passenger_Decision_Output.csv) | Booking-level recovery recommendations for the JED pilot |
| [`outputs/fairness_audit.csv`](outputs/fairness_audit.csv) | Group-level RPI / priority-rate audit table |

### Dashboard data dictionary (`dashboard/dashboard_data/`)

| File | Contents |
|------|----------|
| `model_metrics.json` | Headline KPIs, AUCs, bootstrap, Monte Carlo, band counts |
| `flights_scored.csv` | 30,000 flights with challenger risk scores |
| `passenger_decision_output.csv` | JED affected bookings with RPI band & recommended action |
| `route_risk.csv` / `airport_risk.csv` | Route & airport disruption rates |
| `monthly_trend.csv` / `hourly_trend.csv` | Seasonality & hour-of-day disruption rates |
| `recovery_cost_ladder.csv` | Avg. EGP cost by recovery action |
| `satisfaction_by_action.csv` | Satisfaction, complaint, override rates by action |
| `capacity_stress.csv` | Airport hotel stress ratios |
| `complaint_topics.csv` | Complaint topic counts |
| `fairness_audit.csv` | Audit-only group outcomes |

---

## Executive recommendation (skeleton)

1. **Problem:** reactive disruption response; scarce recovery capacity allocated inconsistently; weak explainability of who gets priority.  
2. **Process:** TRIAGE — dual-horizon risk (EARLYBIRD / LASTCALL) → transparent, capacity-aware RPI → mandatory human review on sensitive / high-cost / infeasible cases.  
3. **Evidence:** challenger AUC 0.949 vs baseline 0.938 (significant lift); cost-optimal threshold; fairness gaps small.  
4. **Value:** precision in the top ~20% of the recovery ladder; budget JED pilot at Monte Carlo **p90**.  
5. **Controls:** audit-only fields never in scoring; overrides logged; stop if override or fairness degrades.  
6. **Pilot:** JED, 4–6 weeks; design already accounts for the −35% hotel cut via policy, not model rebuild.

---

## License / context

Built for the **TAG AI Team Development Program** Week 3 final competition (SkyBridge Airlines is a fictional client). Competition raw data packs remain with the program and are intentionally omitted from this repository.
