# SkyBridge TRIAGE — Team Playbook
### A five-day plan for the Airline Disruption & Passenger Recovery competition

---

## The big idea

Every team in this competition will build "a model that predicts delays and a rule that prioritizes passengers." Yours should be the team that walks in with a single, memorable mental model the judges haven't seen five times already that day:

**Treat disruption recovery like an emergency room.**

Flights are patients arriving with different severities. OCC is the triage desk. Recovery capacity (seats, hotel rooms, agents, budget) is hospital capacity — always finite. A risk score is a triage score, not a verdict. Doctors (human controllers) can always override the triage nurse. And just like an ER, the system's whole job is to get scarce attention to the right people first, explain why, and never quietly let a vulnerable patient wait unnoticed.

This isn't just a metaphor for the pitch — it maps directly onto the rubric and the case's four decision areas:

| Letter | Stands for | Case decision area |
|---|---|---|
| **T** | Timing | When to decide (flight disruption) |
| **R** | Risk | Which flights disrupt (flight disruption) |
| **I** | Impact | Which passengers are hurt (passenger impact) |
| **A** | Allocation | Who gets what recovery action (recovery decision) |
| **G** | Guardrails | Human review, fairness, override logging (responsible AI) |
| **E** | Evaluation | Pilot KPIs, stop/scale rule (learning & value) |

Name it **TRIAGE** in your deck. Open with a 30-second story of one passenger moving through the six letters. Judges remember stories, not slide 7.

---

## Grounded in the TAG curriculum, not generic AI

This is the single biggest lever you have that other teams probably won't use: the case brief and rubric come from the same program that taught you Sessions 1-6, in the same vocabulary. Speaking that vocabulary back, correctly applied, is a strong signal that you understood the *method*, not just the case.

| Session | Framework / tool | Where it shows up in TRIAGE |
|---|---|---|
| 1 | TAG AI Thinking Flow (Client -> Pain Point -> Goal+KPI -> Data -> AI Method -> Output -> Action) | The whole playbook follows this order, end to end |
| 1 | Entity / Features / Target / Output / Action / KPI | Flight = entity for R; Booking = entity for I/A; see the KPI hierarchy in Day 1 |
| 1 | Data leakage warning | `Final_Disruption_Severity` and `Actual_Departure_Delay_Min` are used only as the label, never as a feature (see notebook, "decision-time discipline" note) |
| 2 | Prediction -> actual -> error -> cost -> gradient -> update | This *is* the baseline-vs-challenger training loop in the notebook |
| 2 | Cost function tied to business risk, not accuracy alone | The cost-weighted operating threshold (Day 2-3) is exactly Session 2's "technical error vs. business cost" idea, with SkyBridge's own EGP figures as weights |
| 3 | Probability is risk, not certainty | Executive recommendation deliberately says "estimated risk," never "will churn/will be disrupted" |
| 3 | Hypothesis testing / p-value: is the change real? | Added: a bootstrap significance test on the baseline-vs-challenger AUC gap (below) -- most teams will report two AUC numbers and stop there |
| 3 | Monte Carlo simulation: planning multiple futures | Added: a Monte Carlo range (p10/p50/p90) on the JED pilot's cost and affected-booking count, instead of one point estimate |
| 3 | Decision threshold as a joint business/data decision | The cost-optimal threshold is presented as a recommendation to approve, not a fact the model dictates |
| 4-5 | Regression vs. classification vs. clustering vs. PCA, matched to the question | R is classification (material disruption yes/no); explicitly *not* using PCA, and the reasoning why (see "workload discipline") |
| 4-5 | Precision / Recall / F1 tied to false-positive vs. false-negative cost | Framed exactly as Session 4's telecom retention-call example, translated into SkyBridge's recovery-cost figures |
| 6 | Choose the simplest model that fits the data type and question | Flight risk is a structured-table problem -> traditional ML (logistic + GBM), not deep learning, and the notebook says why |
| 6 | Practical fairness evaluation (compare coverage and outcomes by group, never use the group as an input) | Added: a real fairness audit comparing RPI and priority rate across `Age_Band_AuditOnly` and `Nationality_Group_AuditOnly` (below) |
| 6 | Accountability map + ethical audit checklist | Added, filled in for this specific solution (Day 4 / Guardrails, below) |
| 6 | TAG delivery framework (10 steps, client context through monitoring) | The playbook's Day 1-5 structure *is* this 10-step sequence, compressed to a 5-day cadence |

If you only add three things from this table to your actual submission, make them the hypothesis test, the Monte Carlo range, and the fairness audit -- they're the parts of Sessions 3 and 6 most teams skip because they take extra work, and they're exactly what the rubric's "responsible AI" and "evidence" categories are built to reward.

---

## Data-grounded insights to build the pitch around

I pulled these directly from the data drops — use them as your "aha" moments, not generic case-study language:

1. **Waiting for certainty barely buys you certainty.** The correlation between inbound aircraft delay and eventual "material disruption" is 0.68 at 300 minutes before departure and only rises to 0.73 by 30 minutes. The signal is already strong five hours out — the client's instinct to "wait for a clearer picture" costs recovery time without meaningfully improving confidence. This directly answers OCC's stated dilemma in Client Meeting 02 and is a genuinely counter-intuitive, defensible headline finding.
2. **Turnaround readiness is your best early warning, not weather.** `Turnaround_Readiness_Pct` correlates at -0.65 with disruption — stronger than weather severity (0.31). Most teams will lead with weather because it's the intuitive villain; leading with turnaround readiness instead is a differentiator.
3. **Peak-hour flights are ~34% more likely to become a material disruption** (23.7% vs 17.7% for off-peak). This justifies peak-aware thresholds instead of one flat cutoff — which is exactly what the OCC Director asked you to think about instead of assuming.
4. **This is a long-tail allocation problem, not a mass-classification problem.** 80% of bookings on a disrupted flight just need "keep original." Your real job is getting the remaining ~20% right — reframe the pitch around triage of the tail, not prediction of everyone.
5. **Cost escalates ~64x across the action ladder** (Keep Original ≈ EGP 77/pax vs Hotel+Rebook ≈ EGP 4,932/pax). This is your ROI story: precision in the top 20% is where the money is, which is exactly why Finance said "don't minimize cost at any price" — you can show the trade-off numerically.
6. **Complaints cost ~2 satisfaction points** (8.4 → 6.4 average score) and hit 10.8% of disrupted bookings. Translate this into an "avoided complaint value" line in your executive recommendation — it converts a soft passenger-experience concern into a number Finance will respect.
7. **Human override today runs at 8.6%.** Use this as your benchmark: if your system's proposed auto-approval rate produces a wildly different override rate in testing, that's a signal your thresholds are miscalibrated — a nice responsible-AI talking point.

---

## Day 1 — Business framing (T + G groundwork)

**Deliverable:** internal working note (business problem, current process, stakeholders, KPI hierarchy, decision owners, first AI opportunities, open questions).

**Creative device — the "conflict compass":** plot each stakeholder on two axes: *Speed vs. Fairness* and *Cost vs. Experience*. COO wants speed + explainability; OCC wants a manageable queue, not alarms; Passenger Experience wants fairness over pure customer value; Finance wants capacity-matched spend. Drawing this once in your deck (even as a simple 2x2) visually proves you *heard* the tension in Client Meeting 01 rather than just extracting bullet points.

**KPI hierarchy (draft, adapt as your team confirms it):**
- Management: severe passenger impact rate, avoidable recovery cost, pilot go/no-go confidence
- Operations (OCC): lead time to actionable alert, alert-to-noise ratio (queue size vs. total flights), override rate
- Passenger Recovery: % of high-impact passengers reached before departure, party-feasibility rate
- Finance: cost per avoided severe impact, budget adherence
- Data/AI: model precision/recall at chosen threshold, fairness parity across audit-only groups (monitoring only)

**Open questions to flag for Client Meeting 02:** confirm which snapshot horizon(s) to commit to; confirm whether OCC wants a hard alert or a ranked queue; confirm how loyalty/customer value should (and shouldn't) factor into passenger priority.

---

## Day 2–3 — Risk model (R)

**Decision timing — don't pick one horizon, pick two ("dual-horizon" design):**
- **EARLYBIRD (prep trigger, ~T-240/T-210):** soft, no resource commitment — puts a flight on OCC's radar and lets Passenger Recovery pre-stage options. Justified by insight #1: the signal is already ~90% of its final strength this early.
- **LASTCALL (confirm trigger, ~T-90/T-60):** the point at which a flight formally enters the recovery queue and consumes capacity. This is about confirming operational reality (crew, gate, turnaround), not fundamentally new risk information.

This two-stage design directly answers the OCC Director's "trade-off" prompt instead of picking one arbitrary snapshot like most teams will.

**Target:** binary "material disruption" = Major + Severe + Cancelled severity (base rate ≈ 19.8% in the historical data — good enough for baseline modeling, not so rare that you need heavy resampling tricks).

**A genuinely differentiating feature idea:** most teams will only use the single latest snapshot per flight. You have **nine snapshots per flight** — use them. Engineer *trend* features: the slope of `Inbound_Aircraft_Delay_Min` and `Turnaround_Readiness_Pct` across the 300→30 minute window. A flight that's *stable but bad* is a different operational story than one that's *rapidly deteriorating* — and a slope feature captures that in a way a single cross-section can't. Mention this explicitly as your differentiator in the "data & AI framing" section of the rubric.

**Baseline vs. challenger (keep to two models — the brief explicitly penalizes overbuilding):**
- Baseline: logistic regression on the T-240 snapshot's raw features.
- Challenger: gradient boosting (e.g. `sklearn.GradientBoostingClassifier` or LightGBM) using the raw T-240 features *plus* the trend features above, evaluated against the T-90 confirm point.

**Business-error framing:** false negatives (missed disruption) cost more than false positives (unnecessary prep) — but not infinitely more, since prep isn't free either. Rather than defaulting to a 0.5 probability cutoff, derive an operating threshold that minimizes *expected business cost*, using the EGP figures Finance gave you as rough weights for a missed severe disruption vs. wasted prep effort. This turns "we picked 0.5" into "we picked the threshold that minimizes expected cost," which is a much stronger rubric answer for "evaluation metrics linked to business risk, not accuracy alone."

**Is the challenger's improvement real, or noise? (Session 3 move most teams skip.)** A paired bootstrap significance test on the held-out set shows the AUC gap (baseline 0.938 vs. challenger 0.949, a 0.0105 gap) is statistically significant — p < 0.001, 95% bootstrap CI for the gap is [0.007, 0.014], entirely above zero. Say this plainly in the pitch: "the lift isn't a lucky train/test split — we tested it." This is the exact Session 3 move of not stopping at one observed number.

---

## Day 4 — Impact, Allocation, Guardrails (I + A + G)

**Passenger impact — replace the binary connection flag with a continuous "Connection Fragility" score.** The data shows connection buffers ranging from 35 to 210 minutes (mean ≈122, std ≈50) — treating this as a single flag throws away most of the signal. A simple piecewise or linear fragility score (e.g., fragility rises sharply below ~75 minutes of buffer) is more nuanced and easy to defend in five minutes of Q&A.

**Recovery Priority Index (RPI) — a transparent, explainable weighted score**, e.g.:

```
RPI = 0.40 × Connection_Fragility
    + 0.25 × Party_Feasibility_Risk   (party size vs. available seats together)
    + 0.20 × Vulnerability            (special assistance, child in party, overnight delay)
    + 0.15 × Severity_of_Flight_Risk  (from the R model)
```

Deliberately **exclude** `Age_Band_AuditOnly` and `Nationality_Group_AuditOnly` from the formula entirely (they're audit-only for a reason, and the Client Change Request makes this explicit). Use `Loyalty_Tier` / `Customer_Value_12m_EGP` only as a **tie-breaker between passengers who are otherwise equally prioritized** — never as a primary weight. This directly answers Passenger Experience's stated concern ("I do not want a system that simply says the highest spender always goes first") and gives you a clean, quotable line for the presentation.

**Allocation logic:** process bookings in RPI order; assign the cheapest feasible recovery option from `recovery_options.csv` that satisfies party size and cabin constraints; fall back to manual handling when nothing feasible exists — and say so explicitly in the output rather than forcing a bad match.

**Guardrails (tie to the observed data):** auto-approve only low-cost, low-sensitivity actions (Keep Original, Keep Original + Care, Rebook Same Day under a cost threshold — these make up the vast majority of real actions in the historical data). Route everything else — Hotel+Rebook, Rebook Next Day, any cabin downgrade, any special-assistance case, or any "no feasible option" case — to mandatory human review. That's a direct implementation of the Client Change Request's human-review rule, and it's grounded in the actual action-mix you found in `recovery_outcomes.csv`.

**Responding to the Client Change Request (Day 4 twist), without rebuilding your model:**
- **JED hotel capacity −35%:** lower the RPI threshold required to auto-qualify for a hotel-tier action at JED specifically; prefer ground-transfer/same-day-rebook fallback ahead of hotel for anyone below the new, higher bar; explicitly flag when demand exceeds the reduced supply so it routes to human override rather than silently degrading service. (This is exactly what the demo widget above shows in action.)
- **Frozen budget:** add cost-effectiveness (impact avoided per EGP spent) as an explicit secondary ranking criterion once RPI ties are broken, so the fixed budget stretches further without lowering the priority ceiling for the most vulnerable cases.
- **30-minute refresh, not continuous:** this *validates* the dual-horizon design — you don't need continuous scoring if your two checkpoints are already timed around when new information actually changes the picture.
- **Fairness constraint:** run a simple audit report — average RPI and auto-approval rate compared across the audit-only groups, *without* those fields ever entering the scoring formula. Present it as a one-slide "here's the check we ran," not a promise that bias is impossible.

**The actual fairness audit (run on real data, Session 6's method exactly):** compare average RPI and the priority-band rate (RPI ≥ 40, i.e. Critical or Priority) across `Age_Band_AuditOnly` and `Nationality_Group_AuditOnly` — fields that were never inputs to the model or the RPI formula.

| Group field | Range across groups (priority rate) | Max gap |
|---|---|---|
| Age band (18-25, 26-40, 41-60, 60+) | 14.1% - 14.8% | 0.7 points |
| Nationality group (Egypt, GCC, Levant, Europe/Other) | 14.1% - 16.1% | 2.0 points |

Both gaps are small and don't show an obvious systematic pattern (the highest group, Levant, is a relatively small n=1,540 slice). Report this honestly as "checked, small gaps, worth re-running on more data before scaling" rather than "proven fair" — that's the calibrated claim Session 6 is actually asking for.

**Accountability map (Session 6 format, filled in for TRIAGE):**

| Role | Responsibility here |
|---|---|
| Business Owner | Customer Experience Director — owns churn/disruption KPI and the go/no-go on scaling past JED |
| AI / Data Team | Builds and monitors the R model and the RPI formula; owns the fairness audit cadence |
| Operations / Users | OCC controllers (EARLYBIRD/LASTCALL queue) and Passenger Recovery agents (act on RPI queue) |
| Risk / Compliance / Legal | Reviews the audit-only field exclusion and the fairness audit before go-live |
| Management Sponsor | Approves the JED pilot budget and the stop/scale decision |

**Ethical audit checklist (Session 6, answered for this solution):** Purpose — reduce severe passenger impact and recovery cost inconsistency, not surveillance. Data — flight and booking fields already collected for operations; audit-only fields retained for oversight only. Fairness — audited above, gaps small. Explainability — RPI is a transparent weighted sum, not a black box. Owner — see accountability map. Human validation — mandatory review on Critical band and high-cost actions. Monitoring — override rate vs. the 8.6% baseline, fairness gap trend, cost per avoided severe impact.

---

## Day 5 — Evaluation & the pitch (E)

**Narrative arc (reuse the case's suggested order, but tell it as the ER story):** client context → current reactive process → the TRIAGE decision journey (T→R→I→A→G) → data/AI evidence → passenger/recovery decision in action → value & controls → pilot/monitoring → final recommendation.

**Pilot design:** propose a single-airport pilot at JED (deliberately the airport named in the Client Change Request — it shows you're designing around their specific constraint, not a generic rollout) for a defined window (e.g. 4–6 weeks covering at least a few peak-disruption days).

**Plan for a range of futures, not one number (Session 3's Monte Carlo idea).** A 5,000-run simulation varying the disruption rate, the Critical+Priority share, and cost per passenger gives a pilot cost range rather than a single guess:

| | Affected bookings | Estimated pilot cost (EGP) |
|---|---|---|
| p10 (optimistic) | ~8,564 | ~1,347,502 |
| p50 (expected) | ~9,467 | ~1,961,848 |
| p90 (pessimistic) | ~10,384 | ~2,678,922 |

Use the p90 figure, not the p50, when asking Finance to approve a budget ceiling — that's the "prepare for the higher end" lesson from Session 3's confidence-interval material, applied to the pilot ask.

**Suggested success / stop rules:**
- Success: measurable reduction in severe passenger impact rate at comparable disruption levels; cost per avoided severe impact trending down; override rate stable or falling (not rising, which would suggest the model is being routinely distrusted).
- Stop / pause: override rate spikes well above the ~8.6% historical baseline; fairness audit shows a persistent, unexplained gap; any compliance or safety concern flagged by OCC.

**Presentation opener idea:** walk the judges through one flight (SB117, CAI→JED, the one in the demo) from EARLYBIRD alert through LASTCALL confirmation to a family of four getting a hotel room ahead of a solo Silver-tier traveler who gets a fast rebook instead — then show the same flight under the Day-4 capacity shock, and how the recommendation changes without a single line of new model code. That one worked example does more for "presentation & defense" than ten summary slides.

---

## Executive recommendation — filled skeleton (finish this on Day 5)

1. **Business problem:** SkyBridge's disruption response is reactive; recovery capacity is limited and allocated inconsistently; management lacks visibility into why one passenger is prioritized over another.
2. **Recommended operating decision process:** TRIAGE — dual-horizon flight risk detection (EARLYBIRD/LASTCALL) feeding a transparent, capacity-aware Recovery Priority Index with mandatory human review on sensitive/high-cost/infeasible cases.
3. **Key data / AI evidence:** [fill in your baseline vs. challenger metrics and the trend-feature lift once you've run Day 2–3].
4. **Expected business value and capacity implications:** [fill in — frame as cost per avoided severe impact + avoided-complaint value, and show it holds under the JED capacity shock].
5. **Responsible AI / human controls:** audit-only fields never used as model inputs; mandatory review for downgrades, special assistance, high cost, and infeasible cases; all overrides logged.
6. **Pilot and success / stop rule:** single-airport pilot at JED, 4–6 weeks; stop if override rate or fairness audit degrades meaningfully from baseline.

---

## Workload discipline (the brief means it)

The case explicitly penalizes overbuilding. Resist the urge to add a third model, a dashboard nobody asked for, or an optimization solver — the rubric gives 25 of 100 points to the *clarity and defensibility of the recovery rule*, only 15 to model evidence. Spend your creative energy on the story and the policy logic, not extra code.

---

## Appendix — extended EDA highlights (notebook Section 3)

The analysis notebook now includes a much deeper pass across every file in all three data drops, done *before* the modeling section and kept honest about null results. Use these only where they genuinely strengthen an answer in Q&A — don't force them into the 10-slide deck, which should stay lean per the workload-discipline note above.

- **Seasonality is a non-finding, and that's useful.** Month and weekday disruption rates are flat (19–21% either way). Hour-of-day is not: two departure windows (roughly 7–9 and 17–20) run visibly hotter, which independently confirms `Peak_Departure_Flag` is a real signal rather than an arbitrary label.
- **Network hot-spots cluster around connecting hubs**, not randomly — Doha, Cairo, and Istanbul routes dominate the riskiest-15 list. Airport-level disruption only correlates moderately with the airport's *published* congestion profile, which is a caution against trusting a static airport attribute over the live operational snapshot.
- **Fleet mix is a deliberately checked non-finding.** Disruption rate spread across all 5 aircraft types is under 1 point — not worth a feature, and a good example of the brief's "don't overbuild" principle in action.
- **An independent weather join confirms Finding 2 a second way.** Joining `weather_atc_events.csv` directly (nearest event per origin airport, 6-hour window) shows almost no severity gap between disrupted and non-disrupted flights (36.2 vs. 36.4 on a 0–100 scale) — using a completely different table from the one the model features come from.
- **The ~64x cost-ladder headline is now validated exactly against historical data**, not just asserted: Keep Original averages EGP 77/booking, Hotel + Rebook averages EGP 4,932/booking, in `recovery_outcomes.csv`. That EGP 4,932 figure is the literal `COST_FN` used in the cost-weighted threshold calculation — it's not a round number, it's the data.
- **Expensive actions don't buy better outcomes on their own.** Hotel+Rebook and Rebook Next Day show *lower* average satisfaction and *higher* complaint rates than cheaper actions — because today those actions are reserved for the worst cases. The lesson: the RPI has to route the *right* bookings to expensive actions, not just spend more broadly. Human override rate is flat (~8–9%) across every action type, which is the clean baseline the pilot's stop-rule leans on.
- **Two honest negative results on the passenger side:** a customer's prior-disruption count does not predict their prior-complaint count (correlation ≈ 0.00), and average 12-month customer value is essentially flat across loyalty tiers. Both *support* the decision to keep loyalty as a tie-breaker only — it isn't secretly carrying the value signal Passenger Experience worried it might.
- **JED's capacity stress ranks mid-pack today** (recovery-option volume ÷ average hotel rooms available) — which is exactly why the Day-4 change request's ~35% hotel-capacity cut there is a meaningful, not token, constraint.

All of the above ships as pre-computed CSV/JSON exports (`/dashboard_data/`) alongside a companion **Streamlit business dashboard** (`skybridge_triage_dashboard.py`) with six pages — Executive Overview, Flight Risk Explorer, Passenger Recovery Queue, Fairness & Responsible AI, Recovery Economics, and a live Scenario Simulator (re-runs the Monte Carlo and the JED hotel-cut stress test on sliders). It's meant for a non-technical stakeholder to click through after the pitch, not to replace the 10-slide story.
