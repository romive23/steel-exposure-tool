import streamlit as st

st.set_page_config(page_title="Exposure Estimation & Reasoning Tool", layout="centered")

st.title("Exposure Estimation & Reasoning Tool: Communities Near Steel Facilities")
st.write("""
This tool estimates daily exposure to NO₂ or PM2.5 for someone living near a steel facility. 
Users enter outdoor concentration, time outdoors, indoor infiltration, and activity level. 
The tool estimates indoor concentration, 24-hour exposure, inhaled dose, and compares results to EPA benchmarks. 
Results support exposure reasoning, not medical or regulatory decisions.
""")

st.divider()

# ----------------------------
# Sidebar inputs
# ----------------------------
st.sidebar.header("A) Choose a steel facility profile (example anchor)")
profile = st.sidebar.selectbox(
    "My situation is most similar to…",
    [
        "High impact example: U.S. Steel Clairton Coke Works (PA) – coke/steel supply chain",
        "Medium impact example: Cleveland-Cliffs Burns Harbor (IN) – large steel mill",
        "Lower impact example: Nucor (EAF-based mini-mill archetype) – scrap/EAF steelmaking",
    ],
    help=(
        "These are example anchors to help set assumptions. "
        "You can always override concentrations with monitoring data or a different assumption."
    )
)

st.sidebar.header("B) Pollutant")
pollutant = st.sidebar.selectbox("Pollutant", ["NO₂ (ppb)", "PM2.5 (µg/m³)"])

# Default outdoor concentration assumptions by profile (simple, adjustable)
# NOTE: These are illustrative starting points for reasoning, not measured values.
defaults = {
    "NO₂ (ppb)": {
        "High": 60.0,
        "Medium": 35.0,
        "Lower": 20.0,
    },
    "PM2.5 (µg/m³)": {
        "High": 20.0,
        "Medium": 12.0,
        "Lower": 8.0,
    },
}

if profile.startswith("High"):
    tier = "High"
elif profile.startswith("Medium"):
    tier = "Medium"
else:
    tier = "Lower"

default_outdoor = defaults[pollutant][tier]
unit = "ppb" if "NO₂" in pollutant else "µg/m³"

st.sidebar.header("C) Outdoor concentration assumption")
use_default = st.sidebar.checkbox(f"Use default for this profile ({default_outdoor:.0f} {unit})", value=True)

if use_default:
    c_outdoor = default_outdoor
    st.sidebar.caption(f"Using default: {c_outdoor:.0f} {unit}")
else:
    c_outdoor = st.sidebar.number_input(
        f"Outdoor concentration ({unit})",
        min_value=0.0,
        value=float(default_outdoor),
        step=1.0,
        help="Use a measured value (monitor/report) or your own assumption."
    )

st.sidebar.header("D) Time Outdoors + Indoor Infiltration")
hours_out = st.sidebar.slider("Hours outdoors per day", 0, 24, 2)
hours_in = 24 - hours_out

infiltration = st.sidebar.slider(
    "Indoor infiltration factor (0–1)",
    0.0, 1.0, 0.6, 0.05,
    help="0.2=sealed/filtered; 0.6=typical; 0.9=windows open"
)

activity = st.sidebar.selectbox("Activity level (breathing rate)", ["Resting", "Light activity", "Moderate activity"])

# Very simplified ventilation rates (m³/hr) for exposure reasoning
vent_m3_per_hr = {"Resting": 0.5, "Light activity": 1.0, "Moderate activity": 1.6}[activity]
vent_m3_per_day = vent_m3_per_hr * 24

# ----------------------------
# Exposure calculations
# ----------------------------
c_indoor = c_outdoor * infiltration
c_twa_24h = (c_outdoor * hours_out + c_indoor * hours_in) / 24.0

# Inhaled dose estimate
if "PM2.5" in pollutant:
    dose_ug_per_day = c_twa_24h * vent_m3_per_day  # (µg/m³)*(m³/day)=µg/day
else:
    # For NO2, keep dose-like metric in ppb·hours/day (mass conversion depends on T/P)
    dose_ppb_hours = c_twa_24h * 24.0

# ----------------------------
# Benchmarks (EPA ambient NAAQS for interpretation)
# ----------------------------
NO2_1hr_ppb = 100.0
NO2_ann_ppb = 53.0
PM25_24hr_ug = 35.0
PM25_ann_ug = 9.0

# ----------------------------
# Main outputs
# ----------------------------
st.subheader("Results (Exposure Estimates)")

col1, col2, col3 = st.columns(3)
col1.metric("Outdoor concentration", f"{c_outdoor:.1f} {unit}")
col2.metric("Estimated indoor concentration", f"{c_indoor:.1f} {unit}")
col3.metric("24-hr time-weighted exposure", f"{c_twa_24h:.1f} {unit}")

st.subheader("Estimated inhaled dose (simple reasoning)")
if "PM2.5" in pollutant:
    st.write(f"Assuming ventilation ≈ **{vent_m3_per_day:.1f} m³/day** ({activity.lower()}):")
    st.write(f"**{dose_ug_per_day:,.0f} µg/day** of PM2.5 (approx.)")
else:
    st.write(f"Activity category: **{activity}**")
    st.write(f"Integrated exposure: **{dose_ppb_hours:,.0f} ppb·hours/day** (NO₂)")

st.divider()

# ----------------------------
# Interpretation vs EPA benchmarks + health meaning + recommendations
# ----------------------------
st.subheader("Interpretation (EPA ambient benchmarks)")

if "NO₂" in pollutant:
    pct_1hr = 100.0 * c_outdoor / NO2_1hr_ppb
    pct_ann = 100.0 * c_twa_24h / NO2_ann_ppb

    st.write("Benchmarks used for comparison: NO₂ **1-hour 100 ppb** and **annual 53 ppb** (ambient standards).")
    st.write(f"- Outdoor vs 1-hour benchmark: **{pct_1hr:.0f}%**")
    st.write(f"- 24-hr exposure vs annual benchmark: **{pct_ann:.0f}%**")

    st.subheader("What this could mean for health (simplified)")
    st.write(
        "EPA notes that higher NO₂ concentrations can irritate airways and aggravate asthma, "
        "with short-term exposure associated with coughing, wheezing, and increased ER visits/hospital admissions. "
        "Longer exposures may contribute to asthma development or increased susceptibility to respiratory infections."
    )

    # Recommendations based on relative level (simple tiering)
    st.subheader("Practical exposure-reduction steps (not medical advice)")
    if pct_1hr >= 100 or pct_ann >= 100:
        st.warning("Higher relative concern (near/above benchmark). Consider stronger exposure-reduction actions today.")
        recs = [
            "Reduce outdoor exertion/time near the facility during peak hours.",
            "Keep windows closed; use HVAC on recirculation if available.",
            "Run a HEPA air purifier indoors (or upgrade HVAC filter if compatible).",
            "Check local AQI/alerts and shift outdoor activities to cleaner times."
        ]
    elif pct_1hr >= 50 or pct_ann >= 50:
        st.info("Moderate relative concern (approaching benchmark). Small behavior/indoor changes can matter.")
        recs = [
            "Limit prolonged outdoor activity if you notice symptoms or air smells/looks hazy.",
            "Keep indoor air cleaner: close windows during poor air periods; consider filtration.",
            "If possible, choose walking routes/activities farther from busy roads and facility perimeter."
        ]
    else:
        st.success("Lower relative concern (well below benchmark). Use this tool to see what variables matter most.")
        recs = [
            "Maintain good indoor ventilation/filtration habits and monitor conditions during stagnant/low-wind days.",
            "Use this tool to test: time outdoors vs infiltration vs activity level."
        ]

else:
    pct_24 = 100.0 * c_twa_24h / PM25_24hr_ug
    pct_ann = 100.0 * c_twa_24h / PM25_ann_ug

    st.write("Benchmarks used for comparison: PM2.5 **24-hour 35 µg/m³** and **annual 9 µg/m³** (ambient standards).")
    st.write(f"- 24-hr exposure vs 24-hr benchmark: **{pct_24:.0f}%**")
    st.write(f"- 24-hr exposure vs annual benchmark: **{pct_ann:.0f}%**")

    st.subheader("What this could mean for health (simplified)")
    st.write(
        "EPA lists PM2.5 health effects including aggravated asthma, decreased lung function, "
        "irregular heartbeat, and nonfatal heart attacks—especially for people with heart or lung disease."
    )

    st.subheader("Practical exposure-reduction steps (not medical advice)")
    if pct_24 >= 100 or pct_ann >= 100:
        st.warning("Higher relative concern (near/above benchmark). Consider stronger exposure-reduction actions today.")
        recs = [
            "Reduce outdoor exertion/time when air is smoky/hazy or during alerts.",
            "Keep windows closed during poor air periods; run a HEPA purifier indoors.",
            "If you must be outdoors, take breaks indoors and avoid heavy exertion."
        ]
    elif pct_24 >= 50 or pct_ann >= 50:
        st.info("Moderate relative concern (approaching benchmark). Indoor filtration can meaningfully reduce exposure.")
        recs = [
            "Use a HEPA purifier or improve HVAC filtration if possible.",
            "Shift outdoor exercise to times with cleaner air (after wind picks up / after a front)."
        ]
    else:
        st.success("Lower relative concern (well below benchmark). Use this tool to explore what matters most.")
        recs = [
            "Monitor conditions on stagnant days; indoor filtration remains a strong lever.",
            "Use this tool to compare: time outdoors vs infiltration vs activity level."
        ]

st.markdown("**Recommendations:**")
for r in recs:
    st.write(f"- {r}")

st.caption(
    "Note: Benchmarks are EPA ambient standards used here for interpretation; this tool supports exposure reasoning and comparison, not medical advice."
)