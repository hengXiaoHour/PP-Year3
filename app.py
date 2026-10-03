import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="EduRisk Analytics - Lab 02",
    layout="wide"
)

# --- VISWA theme ---------------------------------------------------------
# Exactly three colours: black, white, red. Every other tone in this file is
# black or white with an alpha channel, which is how the balancing-robot UI
# creates depth instead of inventing more greys.
#   black  #000000   the field
#   white  #FFFFFF   type, rules, dot field
#   red    #CC0000   the single accent (#FF0A0A is the same hue, hover only)
# Depth comes from three stacked dot fields plus white-over-black alpha plates.
# The CSS lives inside app.py on purpose: the lab submission is exactly
# app.py, requirements.txt and README.md, so a .streamlit/config.toml could not
# ship with it.
VISWA_CSS = """
<style>
:root {
  --v-black: #000000;
  --v-white: #FFFFFF;
  --v-red:   #CC0000;
  --v-red-hot: #FF0A0A;
  --v-white-06: rgba(255, 255, 255, 0.06);
  --v-white-10: rgba(255, 255, 255, 0.10);
  --v-white-16: rgba(255, 255, 255, 0.16);
  --v-white-30: rgba(255, 255, 255, 0.30);
  --v-white-55: rgba(255, 255, 255, 0.55);
  --v-white-80: rgba(255, 255, 255, 0.80);
  --v-font-display: 'Oswald', 'Anton', 'Arial Narrow', 'DejaVu Sans Condensed', sans-serif;
  --v-font-mono: 'JetBrains Mono', 'Space Mono', 'DejaVu Sans Mono', monospace;
}
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
  background-color: var(--v-black) !important;
  color: var(--v-white);
  font-family: var(--v-font-mono);
}

/* ---- DEPTH: three stacked dot fields ---------------------------------
   far  : 66px grid, barely there, gives the void a scale
   mid  : 22px grid, the signature dot-matrix, masked so it fades downward
   near : 11px grid over the top third only, reads as the foreground plane */
.stApp::before {
  content: '';
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background-image:
    radial-gradient(var(--v-white-06) 1px, transparent 1.5px),
    radial-gradient(var(--v-white-10) 1px, transparent 1.5px),
    radial-gradient(var(--v-white-16) 1px, transparent 1.4px);
  background-size: 66px 66px, 22px 22px, 11px 11px;
  background-position: 0 0, 0 0, 0 0;
  -webkit-mask-image: radial-gradient(ellipse 130% 105% at 50% -10%, black 30%, transparent 92%);
  mask-image: radial-gradient(ellipse 130% 105% at 50% -10%, black 30%, transparent 92%);
}
/* red bloom at the top edge: pushes the field back */
.stApp::after {
  content: '';
  position: fixed;
  inset: 0 0 auto 0;
  height: 320px;
  z-index: 0;
  pointer-events: none;
  background: radial-gradient(ellipse 70% 100% at 50% 0%, rgba(204, 0, 0, 0.22), transparent 70%);
}
.block-container, [data-testid="stSidebar"] > div { position: relative; z-index: 1; }

/* ---- NEUTRALISE STREAMLIT'S OWN PALETTE ----------------------------
   Streamlit 1.65 bakes its default theme into emotion classes and exposes
   NO theme custom properties, so the defaults have to be overridden directly.
   Its palette is grey-blue #31333F, green #21C354 and blue #0068C9. These two
   rules reset every inherited colour and border; every rule further down that
   sets a specific colour uses !important and therefore wins. */
.stApp, .stApp *,
[data-testid="stSidebar"], [data-testid="stSidebar"] * {
  color: var(--v-white-80);
  border-color: var(--v-white-16);
}
[data-testid="stAlertContainer"] {
  background-color: transparent !important;
  color: var(--v-white-80) !important;
  border-color: transparent !important;
}
[data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] {
  color: var(--v-white-55) !important;
}
/* the little "**" tooltip icons beside widget labels paint with
   stroke="currentColor", so their inherited COLOUR is what leaks Streamlit's
   #31333F into the SVG stroke */
[data-testid="stHeaderActionElements"] a,
[data-testid="stWidgetLabel"] a,
[data-testid="stHeaderActionElements"] svg {
  color: var(--v-white-55) !important;
}
/* Streamlit sets stroke explicitly on those icons, so colour alone is not
   enough. Scoped to svg elements that actually have a stroke attribute, so
   icons declared stroke="none" stay invisible. */
[data-testid="stHeaderActionElements"] svg[stroke]:not([stroke="none"]) {
  stroke: var(--v-white-55) !important;
}
svg path, svg circle, svg rect, svg line, svg polyline, svg polygon {
  stroke: var(--v-white-55) !important;
}
[data-baseweb="notification"] svg { stroke: var(--v-white-80) !important; fill: var(--v-white-80) !important; }
a, a:any-link, [data-testid="stLink"] a {
  color: var(--v-red) !important;
  text-decoration-color: var(--v-red) !important;
}
input, textarea, select, button { font-family: var(--v-font-mono) !important; }

/* ---- TYPE -------------------------------------------------------------- */
h1, h2, h3, h4, h5, h6 { font-family: var(--v-font-mono) !important; }
h1 {
  color: var(--v-white) !important;
  text-transform: uppercase !important;
  letter-spacing: 0.10em !important;
  font-weight: 700 !important;
}
/* section heads: micro mono caps, white at 55%, with the red spine */
h2, h3, h4 {
  color: var(--v-white-55) !important;
  font-size: 11px !important;
  letter-spacing: 0.24em !important;
  text-transform: uppercase !important;
  font-weight: 700 !important;
  border-left: 2px solid var(--v-red) !important;
  padding-left: 12px !important;
  margin-top: 6px !important;
}
p, label, span, div, li, td { color: var(--v-white-80); }
a { color: var(--v-red) !important; }

/* ---- SIDEBAR: a recessed well, not a panel --------------------------- */
[data-testid="stSidebar"] {
  background-color: var(--v-black) !important;
  border-right: 1px solid var(--v-white-10);
}
[data-testid="stSidebar"] * { color: var(--v-white-80) !important; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
  border-left: none !important;
  padding-left: 0 !important;
  color: var(--v-white) !important;
  letter-spacing: 0.14em !important;
  font-size: 13px !important;
}
[data-testid="stSidebar"] h1 { border-bottom: 2px solid var(--v-red); padding-bottom: 6px !important; }
[data-testid="stSidebar"] label p {
  font-size: 11px !important;
  letter-spacing: 0.14em !important;
  text-transform: uppercase !important;
}

/* ---- PLATES: white-over-black alpha lift off the dot field ------------- */
[data-testid="stMetric"] {
  background-color: rgba(255, 255, 255, 0.04) !important;
  background-image:
    radial-gradient(var(--v-white-06) 1px, transparent 1.5px),
    linear-gradient(var(--v-white-30), var(--v-white-30)),
    linear-gradient(var(--v-white-30), var(--v-white-30)),
    linear-gradient(var(--v-white-30), var(--v-white-30)),
    linear-gradient(var(--v-white-30), var(--v-white-30)),
    linear-gradient(var(--v-white-30), var(--v-white-30)),
    linear-gradient(var(--v-white-30), var(--v-white-30)),
    linear-gradient(var(--v-white-30), var(--v-white-30)),
    linear-gradient(var(--v-white-30), var(--v-white-30));
  background-size: 11px 11px, 14px 2px, 2px 14px, 14px 2px, 2px 14px, 14px 2px, 2px 14px, 14px 2px, 2px 14px;
  background-position: 0 0, -1px -1px, -1px -1px, calc(100% + 1px) -1px, calc(100% + 1px) -1px,
    -1px calc(100% + 1px), -1px calc(100% + 1px), calc(100% + 1px) calc(100% + 1px), calc(100% + 1px) calc(100% + 1px);
  background-repeat: repeat, no-repeat, no-repeat, no-repeat, no-repeat, no-repeat, no-repeat, no-repeat, no-repeat;
  border: 1px solid var(--v-white-16);
  border-radius: 0 !important;
  padding: 16px 14px;
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.05) inset;
}
[data-testid="stMetricLabel"] {
  color: var(--v-white-55) !important;
  font-family: var(--v-font-mono) !important;
  font-size: 10px !important;
  letter-spacing: 0.22em !important;
  text-transform: uppercase !important;
}
[data-testid="stMetricValue"] {
  color: var(--v-white) !important;
  font-family: var(--v-font-mono) !important;
  font-weight: 700 !important;
  font-variant-numeric: tabular-nums;
}

/* ---- PRIMARY ACTION: solid red, white type (robot UI .control-btn) ---- */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
  background-color: var(--v-red) !important;
  color: var(--v-white) !important;
  border: 1px solid var(--v-red) !important;
  border-radius: 0 !important;
  font-family: var(--v-font-mono) !important;
  font-weight: 700 !important;
  font-size: 12px !important;
  letter-spacing: 0.18em !important;
  text-transform: uppercase !important;
  padding: 9px 18px !important;
}
.stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover {
  background-color: var(--v-red-hot) !important;
  border-color: var(--v-red-hot) !important;
  color: var(--v-white) !important;
}

/* ---- INPUTS: recessed (darker than the field, not lighter) ----------- */
[data-baseweb="select"] > div,
[data-baseweb="input"],
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input {
  background-color: var(--v-black) !important;
  border: 1px solid var(--v-white-16) !important;
  border-radius: 0 !important;
  color: var(--v-white) !important;
  font-family: var(--v-font-mono) !important;
}
[data-baseweb="select"] > div:hover, [data-baseweb="input"]:hover { border-color: var(--v-white-30) !important; }
[data-baseweb="base-input"] { background-color: var(--v-black) !important; }
[data-baseweb="popover"] > div, [data-baseweb="menu"] { background-color: var(--v-black) !important; }
/* the red is the focus colour, as in the robot UI */
[data-baseweb="select"] > div:focus-within, [data-baseweb="input"]:focus {
  border-color: var(--v-red) !important;
  box-shadow: none !important;
}
[data-testid="stSlider"] [role="slider"] { background-color: var(--v-red) !important; }
[data-testid="stSlider"] [data-testid="stTickBarMin"], [data-testid="stSlider"] [data-testid="stTickBarMax"] {
  color: var(--v-white-55) !important;
}
[data-testid="stCheckbox"] label, [data-testid="stRadio"] label {
  font-family: var(--v-font-mono) !important;
  font-size: 11px !important;
  letter-spacing: 0.12em !important;
  text-transform: uppercase !important;
  color: var(--v-white-80) !important;
}
[data-baseweb="checkbox"] svg, [data-baseweb="radio"] svg { color: var(--v-red) !important; }

/* ---- ALERTS: flat black plate, white type, red only for errors ------- */
[data-testid="stAlert"] {
  background-color: rgba(255, 255, 255, 0.04) !important;
  border: 1px solid var(--v-white-16) !important;
  border-left: 3px solid var(--v-white-30) !important;
  border-radius: 0 !important;
  color: var(--v-white-80) !important;
}
[data-testid="stAlert"] * { color: var(--v-white-80) !important; }
[data-baseweb="notification"] { background-color: transparent !important; }
[data-testid="stAlertContainer"] [data-testid="stMarkdownContainer"] p { color: var(--v-white-80) !important; }
div[data-baseweb="notification"][kind="error"] { border-left-color: var(--v-red) !important; }

/* ---- DATA + CHARTS: recessed wells ----------------------------------- */
[data-testid="stDataFrame"], [data-testid="stDataFrameResizable"] {
  border: 1px solid var(--v-white-16) !important;
  background-color: rgba(255, 255, 255, 0.03) !important;
  border-radius: 0 !important;
}
/* st.bar_chart renders Vega-Lite, which ships its own blue/grey theme and
   an opaque black plot background. Neither is reachable from a plain colour
   rule, so each part is overridden explicitly. The bar fill itself is set in
   Python via st.bar_chart(..., color="#CC0000"). */
.js-plotly-plot, [data-testid="stVegaChart"], [data-testid="stVegaLiteChart"] {
  background-color: rgba(255, 255, 255, 0.03) !important;
  border: 1px solid var(--v-white-16) !important;
  border-radius: 0 !important;
  padding: 10px;
}
[data-testid="stVegaLiteChart"] svg.marks,
[data-testid="stVegaLiteChart"] .background,
[data-testid="stVegaLiteChart"] rect.background {
  fill: transparent !important;
  background-color: transparent !important;
}
/* axis and value labels: Vega's default #808495 grey -> white at 55% */
[data-testid="stVegaLiteChart"] text,
[data-testid="stVegaLiteChart"] tspan {
  fill: var(--v-white-55) !important;
  font-family: var(--v-font-mono) !important;
}
/* the vega <form> wrapper carried Streamlit's #31333F */
[data-testid="stVegaLiteChart"] form,
[data-testid="stVegaLiteChart"] .vega-bindings,
[data-testid="stVegaLiteChart"] div {
  color: var(--v-white-55) !important;
  border-color: transparent !important;
}
[data-testid="stVegaLiteChart"] .vega-bindings { padding: 0 !important; }

/* ---- SCROLLBARS: thin black track, white thumb, red on hover -------- */
::-webkit-scrollbar { width: 9px; height: 9px; }
::-webkit-scrollbar-track { background: var(--v-black); }
::-webkit-scrollbar-thumb { background: var(--v-white-16); }
::-webkit-scrollbar-thumb:hover { background: var(--v-red); }
hr { border-color: var(--v-white-10) !important; }
/* Streamlit's own footer / status chrome, kept out of the way */
footer, [data-testid="stStatusWidget"] { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }
/* kill any inherited border-radius so plates stay square */
[data-testid="stAppViewContainer"] * { border-radius: 0 !important; }
</style>
"""
st.markdown(VISWA_CSS, unsafe_allow_html=True)
student_df = pd.DataFrame({
    "Student Name": ["Dara", "Sophea", "Vuthy", "Malis", "Rithy", "Sreyneang", "Chan", "Bopha"],
    "Course": ["Python", "Statistics", "Python", "Database", "Web App", "Database", "Python", "Statistics"],
    "Score": [85, 68, 45, 92, 58, 91, 72, 62],
    "Attendance": [90, 75, 50, 95, 60, 94, 80, 88],
    "Study Hours": [12, 8, 3, 15, 5, 14, 9, 7]
})

def get_risk_level(score, attendance):
    if score < 60 or attendance < 60:
        return "High Risk"
    elif score < 75 or attendance < 75:
        return "Medium Risk"
    else:
        return "Low Risk"

student_df["Risk Level"] = student_df.apply(
    lambda row: get_risk_level(row["Score"], row["Attendance"]),
    axis=1
)

# Carried over from Lab 01: the raw "score below 60" count, kept alongside the
# Lab 02 Risk Level so nothing from Lab 01 is lost.
low_score_students = student_df[student_df["Score"] < 60].shape[0]

with st.sidebar:
    st.title("EduRisk Menu")
    selected_page = st.radio(
        "Select Page",
        ["Home", "Dashboard", "Student Data", "Risk Checker", "About"]
    )

if selected_page == "Home":
    st.title("EduRisk Analytics")
    st.subheader("Interactive Student Risk Monitoring Dashboard")
    st.write("Welcome to Lab 02.")
    st.write("In this lab, you will use Streamlit widgets to explore student performance data.")
    st.success("Lab 02 app is running successfully!")

    # Carried over from Lab 01.
    if st.button("Click Me"):
        st.write("Welcome")

elif selected_page == "Dashboard":
    st.title("Interactive Dashboard")

    st.write("Use the filters below to explore student performance.")

    selected_course = st.selectbox(
        "Select Course",
        ["All"] + list(student_df["Course"].unique())
    )

    selected_risk = st.selectbox(
        "Select Risk Level",
        ["All", "Low Risk", "Medium Risk", "High Risk"]
    )

    min_attendance = st.slider(
        "Minimum Attendance",
        0,
        100,
        0
    )

    min_score = st.slider(
        "Minimum Score",
        0,
        100,
        0
    )

    filtered_df = student_df.copy()

    if selected_course != "All":
        filtered_df = filtered_df[filtered_df["Course"] == selected_course]

    if selected_risk != "All":
        filtered_df = filtered_df[filtered_df["Risk Level"] == selected_risk]

    filtered_df = filtered_df[
        filtered_df["Attendance"] >= min_attendance
    ]

    filtered_df = filtered_df[
        filtered_df["Score"] >= min_score
    ]

    total_students = len(filtered_df)

    if len(filtered_df) > 0:
        average_score = filtered_df["Score"].mean()
        average_attendance = filtered_df["Attendance"].mean()
    else:
        average_score = 0
        average_attendance = 0

    high_risk_students = filtered_df[
        filtered_df["Risk Level"] == "High Risk"
    ].shape[0]

    st.subheader("Dashboard Metrics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Students", total_students)

    with col2:
        st.metric("Average Score", round(average_score, 2))

    with col3:
        st.metric("Average Attendance", f"{round(average_attendance, 2)}%")

    with col4:
        st.metric("High Risk", high_risk_students)

    show_data = st.checkbox("Show Filtered Dataset", True)

    if show_data:
        st.subheader("Filtered Student Dataset")
        st.dataframe(filtered_df)

        csv = filtered_df.to_csv(index=False)

        st.download_button(
            label="Download Filtered Data",
            data=csv,
            file_name="filtered_student_data.csv",
            mime="text/csv"
        )
    else:
        st.info("Filtered dataset is hidden.")

    st.subheader("Charts")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.write("Student Scores")

        if len(filtered_df) > 0:
            score_chart = filtered_df.set_index("Student Name")["Score"]
            st.bar_chart(score_chart, color="#CC0000")
        else:
            st.warning("No data available for score chart.")

    with chart_col2:
        st.write("Risk Level Count")

        if len(filtered_df) > 0:
            risk_count = filtered_df["Risk Level"].value_counts()
            st.bar_chart(risk_count, color="#CC0000")
        else:
            st.warning("No data available for risk chart.")

elif selected_page == "Student Data":
    st.title("Student Data")

    total_students = len(student_df)
    average_score = student_df["Score"].mean()
    average_attendance = student_df["Attendance"].mean()
    high_risk_students = student_df[
        student_df["Risk Level"] == "High Risk"
    ].shape[0]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Students", total_students)

    with col2:
        st.metric("Average Score", round(average_score, 2))

    with col3:
        st.metric("Average Attendance", f"{round(average_attendance, 2)}%")

    with col4:
        st.metric("High Risk Students", high_risk_students)

    st.subheader("Full Student Dataset")
    st.dataframe(student_df)

    # Carried over from Lab 01, kept as its own row so the Lab 02 metric row
    # above stays exactly as the lab sheet defines it.
    st.subheader("From Lab 01")
    lab1_col1, lab1_col2 = st.columns(2)

    with lab1_col1:
        st.metric("Low Score Students", low_score_students)

    with lab1_col2:
        st.caption("Count of students scoring below 60, carried over from Lab 01.")

elif selected_page == "Risk Checker":
    st.title("Single Student Risk Checker")

    with st.form("risk_checker_form"):
        input_name = st.text_input("Student Name")
        input_score = st.number_input("Score", 0, 100, 50)
        input_attendance = st.number_input("Attendance", 0, 100, 50)
        submitted = st.form_submit_button("Check Risk")

    if submitted:
        risk_result = get_risk_level(input_score, input_attendance)

        st.write("Student Name:", input_name)
        st.write("Score:", input_score)
        st.write("Attendance:", input_attendance)

        if risk_result == "Low Risk":
            st.success("Risk Level: Low Risk")
        elif risk_result == "Medium Risk":
            st.warning("Risk Level: Medium Risk")
        else:
            st.error("Risk Level: High Risk")

else:
    st.title("About")
    st.write("This app is part of Lab 02.")
    st.write("Course: Web App Development for Data Science")
    st.write("Project Theme: EduRisk Analytics")
    st.write("Topic: Streamlit Interactive Dashboard")
    st.info("Ethics Reminder: Risk prediction should support students, not punish them.")

    st.subheader("Student Information")
    st.write("Name: Heng Hour")
    st.write("Student ID: 0007307")
    st.write("Class: M2")
