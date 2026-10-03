"""Lab 02 verification suite for the EduRisk Analytics Streamlit app.

Runs the REAL app script through Streamlit's own AppTest harness, so every
assertion exercises the code that will be submitted -- not a copy of it.

Run:
    .venv/bin/python tests/test_lab02.py

Exits non-zero if any check fails. Every expected value is either taken from
the Lab 02 instruction sheet (and marked as such) or recomputed here from the
risk rule, so the two must agree.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parent.parent / "app.py"
TIMEOUT = 60

RESULTS: list[tuple[str, bool, str]] = []
SOURCE = APP.read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def check(name: str, cond: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(cond), detail))


def eq(name: str, got, want) -> None:
    check(name, got == want, f"got={got!r} want={want!r}")


# --- reporting + crash handler, defined BEFORE any check runs, because the
# excepthook must already be installed when an early block blows up.
def report() -> int:
    print()
    width = max((len(n) for n, _, _ in RESULTS), default=10)
    failed = 0
    for name, ok, detail in RESULTS:
        if not ok:
            failed += 1
        mark = "PASS" if ok else "FAIL"
        line = f"[{mark}] {name.ljust(width)}"
        if not ok and detail:
            line += f"   {detail}"
        print(line)
    print()
    print(f"{len(RESULTS) - failed}/{len(RESULTS)} checks passed")
    if failed:
        print(f"FAILED: {failed}")
    return 1 if failed else 0


def _crash(exc_type, exc, tb) -> None:  # noqa: ANN001
    """If a check block blows up, still print everything that did run.

    A bare traceback with no report is a much weaker signal than "these N checks
    passed, then this widget was missing".
    """
    import traceback
    check(f"suite aborted with {exc_type.__name__}", False, str(exc))
    traceback.print_exception(exc_type, exc, tb)
    report()
    raise SystemExit(1)


sys.excepthook = _crash


# ---------------------------------------------------------------- oracle
# The dataset as written in app.py, plus an independent implementation of the
# risk rule. If app.py ever diverges from the rule, these disagree loudly.
DATA = {
    "Student Name": ["Dara", "Sophea", "Vuthy", "Malis", "Rithy", "Sreyneang", "Chan", "Bopha"],
    "Course": ["Python", "Statistics", "Python", "Database", "Web App", "Database", "Python", "Statistics"],
    "Score": [85, 68, 45, 92, 58, 91, 72, 62],
    "Attendance": [90, 75, 50, 95, 60, 94, 80, 88],
    "Study Hours": [12, 8, 3, 15, 5, 14, 9, 7],
}


def oracle_risk(score: float, attendance: float) -> str:
    if score < 60 or attendance < 60:
        return "High Risk"
    if score < 75 or attendance < 75:
        return "Medium Risk"
    return "Low Risk"


ORACLE = pd.DataFrame(DATA)
ORACLE["Risk Level"] = ORACLE.apply(
    lambda r: oracle_risk(r["Score"], r["Attendance"]), axis=1
)

# Risk levels exactly as printed in Lab 02 Step 10 (instruction sheet).
SHEET_RISK_TABLE = [
    ("Dara", 85, 90, "Low Risk"),
    ("Sophea", 68, 75, "Medium Risk"),
    ("Vuthy", 45, 50, "High Risk"),
    ("Malis", 92, 95, "Low Risk"),
    ("Rithy", 58, 60, "High Risk"),
    ("Sreyneang", 91, 94, "Low Risk"),
    ("Chan", 72, 80, "Medium Risk"),
    ("Bopha", 62, 88, "Medium Risk"),
]


# ---------------------------------------------------------------- helpers
def fresh(page: str) -> AppTest:
    """Load the app and navigate to `page`.

    A navigation failure is recorded as a FAIL and the returned AppTest is left
    on whatever page it reached, so one missing page does not abort the whole
    suite and hide the checks that come after it.
    """
    at = AppTest.from_file(str(APP), default_timeout=TIMEOUT)
    at.run()
    if at.exception:
        check(f"app boots without exception (while opening {page!r})", False,
              str(at.exception))
        return at
    radio = at.sidebar.radio[0]
    if page not in radio.options:
        check(f"page {page!r} exists in the sidebar", False, f"options={radio.options}")
        return at
    radio.set_value(page).run()
    if at.exception:
        check(f"page {page!r} renders without exception", False, str(at.exception))
    return at


def metric_map(at: AppTest) -> dict[str, str]:
    return {m.label: str(m.value) for m in at.metric}


def frame(at: AppTest) -> pd.DataFrame | None:
    return at.dataframe[0].value if at.dataframe else None


def names(at: AppTest) -> list[str]:
    f = frame(at)
    return [] if f is None else list(f["Student Name"])


def msgs(kind: str, at: AppTest) -> list[str]:
    return [getattr(e, "value", "") for e in getattr(at, kind)]


def section(name: str, fn) -> None:
    """Run a group of checks; an exception inside becomes one FAIL.

    Without this, a single missing widget aborts the whole suite and the report
    hides every check that would have run afterwards.
    """
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 - deliberately broad
        check(f"section '{name}' ran to completion", False,
              f"{type(exc).__name__}: {exc}")


def st_calls() -> list[ast.Call]:
    """Every st.<something>(...) call, in source order."""
    out: list[ast.Call] = []
    for node in ast.walk(TREE):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            base = node.func.value
            if isinstance(base, ast.Name) and base.id == "st":
                out.append(node)
    return out


def kwargs_of(call: ast.Call) -> dict[str, ast.AST]:
    return {kw.arg: kw.value for kw in call.keywords if kw.arg}


def literal(node: ast.AST):
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


def body_of(at: AppTest) -> str:
    """All rendered text of the current page (st.write lands as Markdown)."""
    parts = [str(m.value) for m in at.markdown]
    parts += [str(t.value) for t in at.title]
    parts += [str(s.value) for s in at.subheader]
    parts += msgs("success", at) + msgs("info", at) + msgs("warning", at) + msgs("error", at)
    return " ".join(parts)


# ---------------------------------------------------------------- 1. boot
at = AppTest.from_file(str(APP), default_timeout=TIMEOUT)
at.run()
check("app boots with no exception", not at.exception, str(at.exception))
eq("Home page shows the Lab 02 success banner",
   any("Lab 02 app is running successfully!" in v for v in msgs("success", at)), True)
eq("sidebar has the 5 Lab 02 pages in order",
   at.sidebar.radio[0].options,
   ["Home", "Dashboard", "Student Data", "Risk Checker", "About"])
eq("sidebar defaults to Home", at.sidebar.radio[0].value, "Home")

# set_page_config cannot be observed through AppTest (Streamlit does not put it
# in the element tree), so assert it against the AST: it must be the FIRST
# Streamlit call in the file, with the Lab 02 title and a wide layout.
calls = st_calls()
first_st = calls[0].func.attr if calls else "<none>"
eq("set_page_config is the first Streamlit command", first_st, "set_page_config")
cfg = kwargs_of(calls[0]) if calls else {}
eq("page_title is the Lab 02 title", literal(cfg.get("page_title")), "EduRisk Analytics - Lab 02")
eq("page_icon removed - no emoji in the page config", "page_icon" in cfg, False)
eq("layout is wide", literal(cfg.get("layout")), "wide")

# No emoji anywhere in app.py: the theme brief requires the signature
# black/white/red look with no pictographs.
EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF⬀-⯿]"
)
found = sorted(set(EMOJI.findall(SOURCE)))
eq("app.py contains no emoji", found, [])
eq("page_icon kwarg is absent from the source", "page_icon" in SOURCE, False)

# ---- Lab 01 continuity -------------------------------------------------
# The teacher requires Lab 02 to BUILD ON Lab 01, so the two Lab 01 features
# that the sheet's "replace your old ..." wording would have dropped must still
# be present. These checks exist so they cannot silently disappear again.
at2 = AppTest.from_file(str(APP), default_timeout=TIMEOUT)
at2.run()
check("Lab 01: 'Click Me' button still on the Home page",
      any(b.label == "Click Me" for b in at2.button),
      f"buttons={[b.label for b in at2.button]}")
# exact match, not substring: the Home page always contains "Welcome to Lab 02."
check("Lab 01: button shows nothing before it is clicked",
      not any(str(m.value).strip() == "Welcome" for m in at2.markdown),
      f"markdown={[str(m.value) for m in at2.markdown]}")
at2.button[0].click().run()
check("Lab 01: 'Click Me' still writes Welcome when clicked",
      any(str(m.value).strip() == "Welcome" for m in at2.markdown),
      f"markdown={[str(m.value) for m in at2.markdown]}")

at2 = fresh("Student Data")
mm2 = metric_map(at2)
eq("Lab 01: 'Low Score Students' metric still present",
   mm2.get("Low Score Students"),
   str(int((ORACLE["Score"] < 60).sum())))
check("Lab 01: the Lab 02 metric row is untouched (4 tiles)",
      mm2.get("Total Students") == "8" and mm2.get("High Risk Students") == "2")
check("Lab 01: 'From Lab 01' section header present",
      any(s.value == "From Lab 01" for s in at2.subheader),
      f"subheaders={[s.value for s in at2.subheader]}")

# ---------------------------------------------------------------- 2. Student Data
at = fresh("Student Data")
mm = metric_map(at)
# Lab 02 Step 31 states these four expected metrics.
eq("Student Data: Total Students (sheet)", mm.get("Total Students"), "8")
eq("Student Data: Average Score (sheet)", mm.get("Average Score"), "71.62")
eq("Student Data: Average Attendance (sheet)", mm.get("Average Attendance"), "79.0%")
eq("Student Data: High Risk Students (sheet)", mm.get("High Risk Students"), "2")
f = frame(at)
check("Student Data: full dataset rendered", f is not None)
eq("Student Data: 8 rows", 0 if f is None else len(f), 8)
eq("Student Data: Risk Level column present", None if f is None else "Risk Level" in f.columns, True)
eq("Student Data: metric values match oracle",
   (mm.get("Total Students"), mm.get("High Risk Students")),
   (str(len(ORACLE)), str(int((ORACLE["Risk Level"] == "High Risk").sum()))))

# risk column must equal the Step 10 table from the instruction sheet
got_risk = list(zip(f["Student Name"], f["Score"], f["Attendance"], f["Risk Level"]))
eq("Risk Level column matches Lab 02 Step 10 table", got_risk, SHEET_RISK_TABLE)

# ---------------------------------------------------------------- 3. Dashboard defaults
at = fresh("Dashboard")
mm = metric_map(at)
eq("Dashboard: metrics use the Students/High Risk labels",
   (mm.get("Students"), mm.get("High Risk")), ("8", "2"))
eq("Dashboard: Average Score (sheet)", mm.get("Average Score"), "71.62")
eq("Dashboard: Average Attendance (sheet)", mm.get("Average Attendance"), "79.0%")
eq("Dashboard: default table shows all 8", len(frame(at)), 8)
eq("Dashboard: course filter options",
   at.selectbox[0].options, ["All", "Python", "Statistics", "Database", "Web App"])
eq("Dashboard: risk filter options",
   at.selectbox[1].options, ["All", "Low Risk", "Medium Risk", "High Risk"])
eq("Dashboard: filters default to All / 0 / 0",
   (at.selectbox[0].value, at.selectbox[1].value, at.slider[0].value, at.slider[1].value),
   ("All", "All", 0, 0))
eq("Dashboard: attendance slider range", (at.slider[0].min, at.slider[0].max), (0, 100))
eq("Dashboard: score slider range", (at.slider[1].min, at.slider[1].max), (0, 100))
eq("Dashboard: renders 2 bar charts", len(at.get("vega_lite_chart")), 2)
eq("Dashboard: no warnings on the default view", msgs("warning", at), [])
eq("Dashboard: dataset checkbox defaults to checked", at.checkbox[0].value, True)

# ---------------------------------------------------------------- 4. filters
at = fresh("Dashboard")
at.selectbox[0].set_value("Python").run()
eq("filter Course=Python", names(at), list(ORACLE[ORACLE.Course == "Python"]["Student Name"]))
eq("filter Course=Python updates Students metric", metric_map(at).get("Students"), "3")

at.selectbox[0].set_value("Statistics").run()
eq("filter Course=Statistics", names(at), list(ORACLE[ORACLE.Course == "Statistics"]["Student Name"]))

at = fresh("Dashboard")
at.selectbox[1].set_value("Low Risk").run()
eq("filter Risk=Low Risk", names(at), list(ORACLE[ORACLE["Risk Level"] == "Low Risk"]["Student Name"]))
at.selectbox[1].set_value("High Risk").run()
eq("filter Risk=High Risk", names(at), list(ORACLE[ORACLE["Risk Level"] == "High Risk"]["Student Name"]))

at = fresh("Dashboard")
at.slider[0].set_value(80).run()
eq("filter Minimum Attendance >= 80", names(at),
   list(ORACLE[ORACLE.Attendance >= 80]["Student Name"]))

at = fresh("Dashboard")
at.slider[1].set_value(75).run()
eq("filter Minimum Score >= 75", names(at),
   list(ORACLE[ORACLE.Score >= 75]["Student Name"]))

# BOUNDARY tests. >= vs > is invisible at round numbers, because no student
# scores exactly 75. These two pin the comparison operator using values that DO
# occur in the data: Chan scores exactly 72, Sophea attends exactly 75.
at = fresh("Dashboard")
at.slider[1].set_value(72).run()
eq("boundary: Minimum Score >= 72 keeps the student who scored exactly 72",
   names(at), list(ORACLE[ORACLE.Score >= 72]["Student Name"]))
check("boundary: Chan's score of 72 is present in the data (guard for the test above)",
      "Chan" in list(ORACLE[ORACLE.Score == 72]["Student Name"]))

at = fresh("Dashboard")
at.slider[0].set_value(75).run()
eq("boundary: Minimum Attendance >= 75 keeps the student at exactly 75",
   names(at), list(ORACLE[ORACLE.Attendance >= 75]["Student Name"]))
check("boundary: Sophea's attendance of 75 is present in the data (guard for the test above)",
      "Sophea" in list(ORACLE[ORACLE.Attendance == 75]["Student Name"]))

# Lab 02 Step 30 official manual test
at = fresh("Dashboard")
at.selectbox[0].set_value("Python").run()
at.selectbox[1].set_value("High Risk").run()
eq("Step 30 official test: Python + High Risk", names(at), ["Vuthy"])
f = frame(at)
eq("Step 30: single row is Vuthy 45/50",
   (len(f), int(f.iloc[0]["Score"]), int(f.iloc[0]["Attendance"]), f.iloc[0]["Risk Level"]),
   (1, 45, 50, "High Risk"))
eq("Step 30: Students metric is 1", metric_map(at).get("Students"), "1")

at = fresh("Dashboard")
at.selectbox[0].set_value("Python").run()
at.slider[1].set_value(75).run()
eq("combined filter: Python + Score>=75", names(at), ["Dara"])

# ---------------------------------------------------------------- 5. empty-result path
at = fresh("Dashboard")
at.selectbox[0].set_value("Database").run()
at.selectbox[1].set_value("High Risk").run()
check("empty filter result raises no exception", not at.exception, str(at.exception))
eq("empty filter result: Students metric is 0", metric_map(at).get("Students"), "0")
eq("empty filter result: Average Score is 0", metric_map(at).get("Average Score"), "0")
# The lab sheet's else-branch assigns the INTEGER 0, and round(0, 2) stays int,
# so the attendance metric renders "0%" while the normal case renders "79.0%".
# This is the sheet's own behaviour, pinned here so a change to it is deliberate.
eq("empty filter result: Average Attendance renders 0% (int zero, per sheet)",
   metric_map(at).get("Average Attendance"), "0%")
eq("empty filter result: High Risk is 0", metric_map(at).get("High Risk"), "0")
eq("empty filter result: both charts warn", len(msgs("warning", at)), 2)

# ---------------------------------------------------------------- 6. download + checkbox
at = fresh("Dashboard")
dl = at.get("download_button")
eq("download button exists", len(dl), 1)
eq("download button label", dl[0].label, "Download Filtered Data")
# AppTest serves the payload from a mocked media URL and does not expose
# file_name/mime/data, so the CSV wiring is asserted against the AST instead.
check("download button serves a .csv payload",
      ".csv" in str(dl[0].proto), str(dl[0].proto)[:120])
dl_call = next((c for c in st_calls() if c.func.attr == "download_button"), None)
check("app.py declares a download_button", dl_call is not None)
if dl_call is not None:
    k = kwargs_of(dl_call)
    eq("download file_name", literal(k.get("file_name")), "filtered_student_data.csv")
    eq("download mime", literal(k.get("mime")), "text/csv")
    eq("download data comes from a variable", type(k.get("data")).__name__, "Name")
    data_name = k.get("data").id if isinstance(k.get("data"), ast.Name) else None
    binds_csv = any(
        isinstance(n, ast.Assign) and isinstance(n.value, ast.Call)
        and isinstance(n.value.func, ast.Attribute) and n.value.func.attr == "to_csv"
        and any(isinstance(t, ast.Name) and t.id == data_name for t in n.targets)
        for n in ast.walk(TREE)
    )
    check(f"download data variable {data_name!r} is bound to .to_csv(index=False)", binds_csv)
# the CSV that would be downloaded must match the table actually on screen
check("visible table round-trips to the CSV the button serves",
      frame(at).to_csv(index=False).splitlines()[0].strip()
      == "Student Name,Course,Score,Attendance,Study Hours,Risk Level")

at = fresh("Dashboard")
at.checkbox[0].set_value(False).run()
check("unticking checkbox hides the table", not at.dataframe)
eq("unticking checkbox shows the info message",
   any("hidden" in v for v in msgs("info", at)), True)
eq("unticking checkbox hides the download button", len(at.get("download_button")), 0)
check("unticking checkbox keeps the metrics", len(at.metric) == 4)

# ---------------------------------------------------------------- 7. Risk Checker
# Lab 02 Step 32 official test cases
CASES = [
    ("Student A", 90, 95, "Low Risk", "success"),
    ("Student B", 70, 80, "Medium Risk", "warning"),
    ("Student C", 50, 85, "High Risk", "error"),
    ("Student D", 80, 55, "High Risk", "error"),
]
for who, score, att, want, kind in CASES:
    eq(f"oracle agrees on {who}", oracle_risk(score, att), want)
    at = fresh("Risk Checker")
    eq(f"{who}: no result before submit", msgs("success", at) + msgs("warning", at) + msgs("error", at), [])
    at.text_input[0].set_value(who)
    at.number_input[0].set_value(score)
    at.number_input[1].set_value(att)
    at.button[0].click().run()
    check(f"{who}: submit raises no exception", not at.exception, str(at.exception))
    got = [v for k in ("success", "warning", "error") for v in msgs(k, at)]
    eq(f"{who}: shows exactly one risk message", len(got), 1)
    eq(f"{who}: message text", got, [f"Risk Level: {want}"])
    eq(f"{who}: uses the {kind} element", len(msgs(kind, at)), 1)
    eq(f"{who}: echoes the entered name", who in body_of(at), True)

at = fresh("Risk Checker")
eq("Risk Checker form has 1 text + 2 number inputs",
   (len(at.text_input), len(at.number_input)), (1, 2))
eq("Risk Checker score input range", (at.number_input[0].min, at.number_input[0].max), (0, 100))
eq("Risk Checker attendance input range", (at.number_input[1].min, at.number_input[1].max), (0, 100))
eq("Risk Checker defaults are 50/50",
   (at.number_input[0].value, at.number_input[1].value), (50, 50))

# ---------------------------------------------------------------- 8. About
at = fresh("About")
eq("About: ethics reminder present",
   any("support students, not punish" in v for v in msgs("info", at)), True)
body = body_of(at)
for needle in ("Lab 02", "Web App Development for Data Science", "EduRisk Analytics"):
    check(f"About: mentions {needle}", needle in body)
for needle in ("Heng Hour", "0007307", "M2"):
    check(f"About: student info kept from Lab 01 ({needle})", needle in body)

# ---------------------------------------------------------------- report
raise SystemExit(report())