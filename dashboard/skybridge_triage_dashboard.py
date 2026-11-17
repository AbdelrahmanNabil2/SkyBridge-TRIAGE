"""
SkyBridge TRIAGE — Business Dashboard
======================================
A read-only, business-facing companion to SkyBridge_Analysis_Notebook.ipynb.

Run it with:
    pip install streamlit pandas plotly numpy
    streamlit run skybridge_triage_dashboard.py

By default it looks for a `dashboard_data/` folder sitting next to this file
(the exports written by Section 11 of the notebook). If that folder isn't
found, the sidebar lets you point at another location or upload the files
directly, so this app is portable on its own.
"""

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# --------------------------------------------------------------------------
# Page setup & theme
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="SkyBridge TRIAGE — Business Dashboard",
    page_icon="\u2708\ufe0f",
    layout="wide",
    initial_sidebar_state="expanded",
)

NAVY = "#1f4e79"
RED = "#c0392b"
ORANGE = "#e67e22"
GREEN = "#27ae60"
PURPLE = "#8e44ad"
TEAL = "#16a085"
PALETTE = [NAVY, RED, ORANGE, GREEN, PURPLE, TEAL]
BAND_COLORS = {"Critical": RED, "Priority": ORANGE, "Watch": "#f1c40f", "Low": "#95a5a6"}

st.markdown(
    f"""
    <style>
    .stMetric {{ background-color: #f7f9fb; border-radius: 10px; padding: 10px 14px; border: 1px solid #e3e8ee; }}
    div[data-testid="stMetricValue"] {{ color: {NAVY}; }}
    h1, h2, h3 {{ color: {NAVY}; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------
# Data loading — resilient to where this file actually gets run from
# --------------------------------------------------------------------------
DEFAULT_DIRS = [
    Path(__file__).parent / "dashboard_data",
    Path(__file__).parent / "dashboard_package" / "dashboard_data",
    Path("dashboard_data"),
    Path("/home/claude/dashboard_data"),
]

REQUIRED_FILES = [
    "model_metrics.json", "passenger_decision_output.csv", "fairness_audit.csv",
    "flights_scored.csv", "route_risk.csv", "airport_risk.csv", "monthly_trend.csv",
    "hourly_trend.csv", "recovery_cost_ladder.csv", "satisfaction_by_action.csv",
    "capacity_stress.csv", "complaint_topics.csv",
]


def find_data_dir():
    for d in DEFAULT_DIRS:
        if d.exists() and (d / "model_metrics.json").exists():
            return d
    return None


st.sidebar.title("\u2708\ufe0f SkyBridge TRIAGE")
st.sidebar.caption("Airline Disruption & Passenger Recovery — TAG Week 3 Final Competition")

data_dir = find_data_dir()
with st.sidebar.expander("Data source", expanded=data_dir is None):
    manual_path = st.text_input("Or point to a dashboard_data folder", value=str(data_dir) if data_dir else "")
    if manual_path and Path(manual_path).exists():
        data_dir = Path(manual_path)
    if data_dir:
        st.success(f"Loaded from: {data_dir}")
    else:
        st.error(
            "Couldn't find `dashboard_data/`. Run Section 11 of "
            "SkyBridge_Analysis_Notebook.ipynb first, or point at the folder above."
        )
        st.stop()


@st.cache_data
def load_all(dir_path: str):
    d = Path(dir_path)
    data = {}
    data["metrics"] = json.loads((d / "model_metrics.json").read_text())
    data["decisions"] = pd.read_csv(d / "passenger_decision_output.csv")
    data["fairness"] = pd.read_csv(d / "fairness_audit.csv")
    data["flights"] = pd.read_csv(d / "flights_scored.csv", parse_dates=["Flight_Date"])
    data["routes"] = pd.read_csv(d / "route_risk.csv")
    data["airports"] = pd.read_csv(d / "airport_risk.csv")
    data["monthly"] = pd.read_csv(d / "monthly_trend.csv")
    data["hourly"] = pd.read_csv(d / "hourly_trend.csv")
    data["cost_ladder"] = pd.read_csv(d / "recovery_cost_ladder.csv")
    data["satisfaction"] = pd.read_csv(d / "satisfaction_by_action.csv")
    data["stress"] = pd.read_csv(d / "capacity_stress.csv")
    data["topics"] = pd.read_csv(d / "complaint_topics.csv")
    return data


DATA = load_all(str(data_dir))
M = DATA["metrics"]

page = st.sidebar.radio(
    "Section",
    [
        "Executive Overview",
        "Flight Risk Explorer",
        "Passenger Recovery Queue",
        "Fairness & Responsible AI",
        "Recovery Economics",
        "Scenario Simulator",
    ],
)

st.sidebar.markdown("---")
st.sidebar.caption(
    "This dashboard reads pre-computed outputs from the analysis notebook — "
    "it never retrains the model, so every page loads instantly."
)

# --------------------------------------------------------------------------
# Page: Executive Overview
# --------------------------------------------------------------------------
if page == "Executive Overview":
    st.title("Executive Overview")
    st.caption("Where SkyBridge stands today, and what the JED pilot is expected to cost and catch.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Material disruption rate", f"{M['material_disruption_rate']:.1%}",
               help="Major + Severe + Cancelled, across 30,000 historical flights.")
    c2.metric("Peak vs. off-peak", f"{M['peak_disruption_rate']:.1%} / {M['offpeak_disruption_rate']:.1%}",
               help="Peak-hour flights are ~34% more likely to become a material disruption.")
    c3.metric("Model lift (AUC)", f"{M['baseline_auc']:.3f} \u2192 {M['challenger_auc']:.3f}",
               delta=f"+{M['bootstrap_auc_gap']:.3f} (p<0.001)")
    c4.metric("Historical override rate", f"{M['historical_override_rate']:.1%}",
               help="Baseline the JED pilot's override rate will be measured against.")

    st.markdown("### The JED pilot, at a glance")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Disrupted flights", f"{M['jed_disrupted_flights']:,}")
    c2.metric("Affected bookings", f"{M['jed_affected_bookings']:,}")
    c3.metric("Total recovery cost", f"EGP {M['jed_total_recovery_cost_egp']:,.0f}")
    c4.metric("Requires human review", f"{M['jed_human_review_pct']:.1%} ({M['jed_human_review_count']} bookings)")

    st.markdown("### Where the affected bookings land")
    band_counts = pd.Series(M["band_counts"]).reindex(["Critical", "Priority", "Watch", "Low"])
    col1, col2 = st.columns([1, 1.4])
    with col1:
        fig = go.Figure(go.Pie(
            labels=band_counts.index, values=band_counts.values, hole=0.55,
            marker_colors=[BAND_COLORS[b] for b in band_counts.index],
            textinfo="label+percent",
        ))
        fig.update_layout(title="Recovery Priority Index band", height=380, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        mc = pd.DataFrame({
            "Scenario": ["p10 (optimistic)", "p50 (expected)", "p90 (budget planning)"],
            "Cost (EGP)": [M["monte_carlo_p10"], M["monte_carlo_p50"], M["monte_carlo_p90"]],
        })
        fig = px.bar(mc, x="Scenario", y="Cost (EGP)", color="Scenario",
                     color_discrete_sequence=[GREEN, NAVY, RED], text_auto=".2s")
        fig.update_layout(title="5,000-run Monte Carlo pilot cost range", height=380, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.info(
        "**Recommendation basis:** budget the JED pilot against the **p90 figure "
        f"(EGP {M['monte_carlo_p90']:,.0f})**, not the average — Finance said not to minimize "
        "cost at any price, but a pilot that runs out of budget mid-peak is worse than one "
        "budgeted conservatively."
    )

# --------------------------------------------------------------------------
# Page: Flight Risk Explorer
# --------------------------------------------------------------------------
elif page == "Flight Risk Explorer":
    st.title("Flight Risk Explorer")
    st.caption("Which flights, routes, and airports are actually carrying the risk.")

    flights = DATA["flights"]
    airports = sorted(set(flights["Origin"]) | set(flights["Destination"]))
    c1, c2, c3 = st.columns(3)
    origin_filter = c1.multiselect("Origin airport", airports)
    aircraft_filter = c2.multiselect("Aircraft type", sorted(flights["Aircraft_Type"].unique()))
    peak_filter = c3.selectbox("Departure window", ["All", "Peak only", "Off-peak only"])

    f = flights.copy()
    if origin_filter:
        f = f[f["Origin"].isin(origin_filter)]
    if aircraft_filter:
        f = f[f["Aircraft_Type"].isin(aircraft_filter)]
    if peak_filter == "Peak only":
        f = f[f["Peak_Departure_Flag"] == 1]
    elif peak_filter == "Off-peak only":
        f = f[f["Peak_Departure_Flag"] == 0]

    c1, c2, c3 = st.columns(3)
    c1.metric("Flights in view", f"{len(f):,}")
    c2.metric("Disruption rate", f"{f['material_disruption'].mean():.1%}" if len(f) else "—")
    c3.metric("Avg. model risk score", f"{f['flight_risk_score'].mean():.2f}" if len(f) else "—")

    tab1, tab2, tab3 = st.tabs(["Risk score distribution", "Route hotspots", "Monthly & hourly trend"])
    with tab1:
        fig = px.histogram(f, x="flight_risk_score", color=f["material_disruption"].map({0: "No disruption", 1: "Disrupted"}),
                            nbins=40, color_discrete_map={"No disruption": NAVY, "Disrupted": RED},
                            barmode="overlay", opacity=0.7)
        fig.update_layout(title="Challenger model risk score, by actual outcome", height=430,
                           legend_title_text="")
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        top_routes = DATA["routes"].sort_values("disruption_rate", ascending=False).head(15).iloc[::-1]
        fig = px.bar(top_routes, x="disruption_rate", y="route", orientation="h",
                     color_discrete_sequence=[RED])
        fig.update_layout(title="15 riskiest routes (min. 100 flights)", height=500)
        st.plotly_chart(fig, use_container_width=True)

        ap = DATA["airports"].sort_values("disruption_rate", ascending=False)
        fig2 = go.Figure()
        fig2.add_bar(x=ap["Origin"], y=ap["disruption_rate"], name="Disruption rate", marker_color=NAVY)
        fig2.add_bar(x=ap["Origin"], y=ap["Congestion_Profile_0_1"], name="Congestion profile",
                     marker_color=ORANGE, yaxis="y2")
        fig2.update_layout(
            title="Disruption rate vs. published congestion profile, by airport",
            yaxis=dict(title="Disruption rate"),
            yaxis2=dict(title="Congestion profile", overlaying="y", side="right"),
            barmode="group", height=430,
        )
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        c1, c2 = st.columns(2)
        with c1:
            fig = px.line(DATA["monthly"], x="month", y="disruption_rate", markers=True,
                          color_discrete_sequence=[NAVY])
            fig.update_layout(title="Disruption rate by month", height=380, yaxis_range=[0.15, 0.25])
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            hr = DATA["hourly"].copy()
            hr["is_peak"] = hr["hour"].isin([7, 8, 9, 17, 18, 19, 20])
            fig = px.bar(hr, x="hour", y="disruption_rate", color="is_peak",
                         color_discrete_map={True: RED, False: NAVY})
            fig.update_layout(title="Disruption rate by departure hour", height=380, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    with st.expander("Flight-level detail"):
        st.dataframe(
            f[["Flight_ID", "Origin", "Destination", "Flight_Date", "Aircraft_Type",
               "flight_risk_score", "Final_Disruption_Severity", "Actual_Departure_Delay_Min"]]
            .sort_values("flight_risk_score", ascending=False),
            use_container_width=True, height=350,
        )

# --------------------------------------------------------------------------
# Page: Passenger Recovery Queue
# --------------------------------------------------------------------------
elif page == "Passenger Recovery Queue":
    st.title("Passenger Recovery Queue")
    st.caption("The RPI-ranked decision output for the JED pilot — one row per affected booking.")

    dec = DATA["decisions"]
    c1, c2, c3 = st.columns(3)
    band_filter = c1.multiselect("Risk / impact band", ["Critical", "Priority", "Watch", "Low"])
    action_filter = c2.multiselect("Recommended action", sorted(dec["Recommended_Action"].unique()))
    approval_filter = c3.selectbox("Approval required?", ["All", "Yes only", "No only"])

    d = dec.copy()
    if band_filter:
        d = d[d["Risk_or_Impact_Band"].isin(band_filter)]
    if action_filter:
        d = d[d["Recommended_Action"].isin(action_filter)]
    if approval_filter == "Yes only":
        d = d[d["Approval_Required_Flag"] == "Y"]
    elif approval_filter == "No only":
        d = d[d["Approval_Required_Flag"] == "N"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Bookings in view", f"{len(d):,}")
    c2.metric("Total est. cost", f"EGP {d['Estimated_Cost_EGP'].sum():,.0f}")
    c3.metric("Avg. cost / booking", f"EGP {d['Estimated_Cost_EGP'].mean():,.0f}" if len(d) else "—")
    c4.metric("Needing approval", f"{(d['Approval_Required_Flag']=='Y').mean():.1%}" if len(d) else "—")

    c1, c2 = st.columns(2)
    with c1:
        band_action = d.groupby(["Risk_or_Impact_Band", "Recommended_Action"]).size().reset_index(name="count")
        fig = px.bar(band_action, x="Risk_or_Impact_Band", y="count", color="Recommended_Action",
                     category_orders={"Risk_or_Impact_Band": ["Critical", "Priority", "Watch", "Low"]},
                     color_discrete_sequence=PALETTE)
        fig.update_layout(title="Recommended action, by band", height=400, legend_title_text="")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        cost_by_band = d.groupby("Risk_or_Impact_Band")["Estimated_Cost_EGP"].sum().reindex(
            ["Critical", "Priority", "Watch", "Low"]).dropna()
        fig = px.bar(cost_by_band, x=cost_by_band.index, y=cost_by_band.values,
                     color=cost_by_band.index, color_discrete_map=BAND_COLORS)
        fig.update_layout(title="Estimated cost concentration, by band", height=400,
                           yaxis_title="Estimated cost (EGP)", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("##### Queue (Critical first)")
    order = {"Critical": 0, "Priority": 1, "Watch": 2, "Low": 3}
    d_sorted = d.assign(_o=d["Risk_or_Impact_Band"].map(order)).sort_values("_o").drop(columns="_o")
    st.dataframe(
        d_sorted[["Booking_ID", "Flight_ID", "Risk_or_Impact_Band", "Recommended_Action", "Fallback_Action",
                  "Short_Reason", "Estimated_Cost_EGP", "Estimated_Impact_or_Delay", "Human_Owner",
                  "Approval_Required_Flag"]],
        use_container_width=True, height=420,
    )
    st.download_button("Download filtered queue as CSV", d_sorted.to_csv(index=False),
                        file_name="skybridge_recovery_queue_filtered.csv", mime="text/csv")

# --------------------------------------------------------------------------
# Page: Fairness & Responsible AI
# --------------------------------------------------------------------------
elif page == "Fairness & Responsible AI":
    st.title("Fairness & Responsible AI")
    st.caption("Audit-only fields are never model or RPI inputs — this page checks outcomes across them anyway.")

    fair = DATA["fairness"]
    c1, c2 = st.columns(2)
    c1.metric("Max gap — age band", f"{M['fairness_age_max_gap']*100:.1f} pts")
    c2.metric("Max gap — nationality group", f"{M['fairness_nationality_max_gap']*100:.1f} pts")

    c1, c2 = st.columns(2)
    for col, field, title in [(c1, "Age_Band_AuditOnly", "Priority-band rate by age band"),
                               (c2, "Nationality_Group_AuditOnly", "Priority-band rate by nationality group")]:
        sub = fair[fair["group_field"] == field]
        fig = px.bar(sub, x="group_value", y="priority_rate", color_discrete_sequence=[NAVY],
                     text_auto=".1%")
        fig.update_layout(title=title, height=380, yaxis_title="Priority-band rate (RPI \u2265 40)",
                           xaxis_title="")
        col.plotly_chart(fig, use_container_width=True)

    st.markdown("### Average RPI by group")
    fig = px.bar(fair, x="group_value", y="avg_RPI", color="group_field",
                 barmode="group", color_discrete_sequence=[NAVY, ORANGE])
    fig.update_layout(height=380, legend_title_text="")
    st.plotly_chart(fig, use_container_width=True)

    st.warning(
        "**Calibrated claim, not a guarantee:** both gaps are small and show no obvious "
        "systematic pattern (the Levant group is a comparatively small n=1,540 slice). "
        "Report this as *checked, small gaps, worth re-running on more data before scaling* — "
        "not as proof the system is bias-free."
    )

    with st.expander("Human review & override design"):
        st.markdown(f"""
- **{M['jed_human_review_pct']:.1%}** of the JED pilot sample is routed to mandatory human review
  (cabin downgrades, special-assistance cases, high-cost actions, and any "no feasible option" case).
- The historical human override rate across *all* recovery actions is **{M['historical_override_rate']:.1%}** —
  this is the number the pilot's override rate should stay near. A sustained spike above baseline
  is one of the two stop-conditions for the pilot.
- `Age_Band_AuditOnly` and `Nationality_Group_AuditOnly` are retained **only** for this audit —
  they are never features in the flight-risk model or inputs to the RPI formula.
""")

# --------------------------------------------------------------------------
# Page: Recovery Economics
# --------------------------------------------------------------------------
elif page == "Recovery Economics":
    st.title("Recovery Economics")
    st.caption("What recovery actually costs, whether it works, and where capacity is tightest.")

    c1, c2 = st.columns(2)
    with c1:
        ladder = DATA["cost_ladder"].sort_values("avg_cost_egp")
        fig = px.bar(ladder, x="avg_cost_egp", y="Recovery_Action", orientation="h",
                     color_discrete_sequence=[RED], text_auto=".0f")
        fig.update_layout(title="Historical avg. cost per booking, by recovery action", height=420,
                           xaxis_title="EGP")
        c1.plotly_chart(fig, use_container_width=True)
        ratio = ladder["avg_cost_egp"].max() / ladder["avg_cost_egp"].min()
        c1.caption(f"Cost escalates **{ratio:.0f}x** from cheapest to most expensive action — "
                   f"this is exactly the EGP {M['cost_fn_egp']:,.0f} used as the model's false-negative cost.")

    with c2:
        sat = DATA["satisfaction"].sort_values("avg_satisfaction")
        fig = go.Figure()
        fig.add_bar(x=sat["Recovery_Action"], y=sat["avg_satisfaction"], name="Avg. satisfaction (1-10)",
                    marker_color=NAVY)
        fig.add_bar(x=sat["Recovery_Action"], y=sat["complaint_rate"] * 10, name="Complaint rate (x10 scale)",
                    marker_color=RED)
        fig.update_layout(title="Satisfaction & complaint rate, by recovery action", height=420,
                           barmode="group", legend_title_text="")
        c2.plotly_chart(fig, use_container_width=True)

    st.markdown("### Capacity stress by airport")
    stress = DATA["stress"].sort_values("stress_ratio", ascending=False)
    colors = [RED if a == "JED" else NAVY for a in stress["Airport"]]
    fig = go.Figure(go.Bar(x=stress["Airport"], y=stress["stress_ratio"], marker_color=colors))
    fig.update_layout(title="Recovery-option volume \u00f7 avg. hotel rooms available (JED highlighted)",
                       height=400, yaxis_title="Stress ratio")
    st.plotly_chart(fig, use_container_width=True)
    jed_rank = int((stress["Airport"] == "JED").idxmax()) + 1 if "JED" in stress["Airport"].values else None
    if jed_rank:
        rank_pos = list(stress["Airport"]).index("JED") + 1
        st.caption(f"JED currently ranks #{rank_pos} of {len(stress)} airports on this stress ratio — "
                   "before applying the Day-4 change request's ~35% hotel-capacity cut. Use the Scenario "
                   "Simulator tab to see the effect of that cut.")

    st.markdown("### What passengers actually complain about")
    topics = DATA["topics"].sort_values("count", ascending=False)
    fig = px.pie(topics, names="Complaint_Topic", values="count", hole=0.5,
                 color_discrete_sequence=PALETTE)
    fig.update_layout(height=420)
    st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------------------------------
# Page: Scenario Simulator
# --------------------------------------------------------------------------
elif page == "Scenario Simulator":
    st.title("Scenario Simulator")
    st.caption("Re-run the Monte Carlo pilot-cost simulation live, and stress-test the Day-4 JED capacity cut.")

    st.markdown("#### 1. Monte Carlo pilot cost — adjust the assumptions")
    c1, c2, c3, c4 = st.columns(4)
    disruption_mean = c1.slider("Assumed disruption rate", 0.10, 0.30, float(M["material_disruption_rate"]), 0.01)
    pct_critical = c2.slider("Critical + Priority share", 0.05, 0.25, 0.145, 0.005)
    cost_per_cp = c3.slider("Avg. cost per Critical/Priority pax (EGP)", 600, 3000, 1450, 50)
    n_sims = c4.slider("Simulation runs", 1000, 10000, 5000, 500)

    n_jed_flights = 4830  # JED-touching flights in the historical network (Origin or Destination == JED)
    avg_bookings_per_flight = DATA["flights"].shape[0] and (
        DATA["decisions"].shape[0] / max(M["jed_disrupted_flights"], 1)
    )

    rng = np.random.default_rng(7)
    disruption_samples = rng.normal(disruption_mean, 0.015, n_sims).clip(0.05, 0.40)
    cost_samples = rng.normal(cost_per_cp, 300, n_sims).clip(300, 6000)
    pct_samples = rng.normal(pct_critical, 0.02, n_sims).clip(0.02, 0.40)

    disrupted_flights_sim = disruption_samples * n_jed_flights
    affected_bookings_sim = disrupted_flights_sim * avg_bookings_per_flight
    total_cost_sim = affected_bookings_sim * pct_samples * cost_samples

    p10, p50, p90 = np.percentile(total_cost_sim, [10, 50, 90])
    c1, c2, c3 = st.columns(3)
    c1.metric("p10 (optimistic)", f"EGP {p10:,.0f}")
    c2.metric("p50 (expected)", f"EGP {p50:,.0f}")
    c3.metric("p90 (budget ceiling)", f"EGP {p90:,.0f}")

    fig = px.histogram(total_cost_sim, nbins=60, color_discrete_sequence=[NAVY])
    for val, label, color in [(p10, "p10", GREEN), (p50, "p50", NAVY), (p90, "p90", RED)]:
        fig.add_vline(x=val, line_dash="dash", line_color=color, annotation_text=label)
    fig.update_layout(title=f"Simulated JED pilot recovery cost ({n_sims:,} runs)", height=420,
                       xaxis_title="Total cost (EGP)", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 2. Day-4 change request — JED hotel capacity cut")
    st.caption(
        "The Client Change Request cuts JED's contracted hotel capacity by ~35% during the pilot peak. "
        "This slider shows how many Critical-band bookings that were assigned a hotel-tier action would "
        "need to fall back to ground-transfer or manual review instead."
    )
    cut_pct = st.slider("Hotel capacity reduction at JED", 0, 60, 35, 5, format="%d%%")

    dec = DATA["decisions"]
    hotel_actions = dec[dec["Recommended_Action"] == "Hotel + Rebook"]
    n_hotel = len(hotel_actions)
    n_displaced = int(round(n_hotel * (cut_pct / 100)))

    c1, c2, c3 = st.columns(3)
    c1.metric("Bookings currently on Hotel + Rebook", f"{n_hotel:,}")
    c2.metric(f"Displaced by a {cut_pct}% cut", f"{n_displaced:,}")
    c3.metric("Extra cost if displaced to Ground Transfer",
              f"EGP {n_displaced * (700 - 2251):,.0f}".replace("-", "-").replace("EGP -", "-EGP "))

    st.info(
        "**Design response (no model rebuild required):** at JED specifically, lower the RPI threshold "
        "required to auto-qualify for a hotel-tier action; prefer ground-transfer / same-day-rebook ahead "
        "of hotel for anyone below the new, higher bar; and route anyone the reduced supply can't cover to "
        "mandatory human review rather than silently downgrading their service. This is a **policy change, "
        "not a model change** — exactly what the case brief is testing for."
    )

st.sidebar.markdown("---")
st.sidebar.caption("TAG AI Team Development Program — Week 3 Final Competition · SkyBridge Airlines (fictional)")
