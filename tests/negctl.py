"""Negative-control harness for tests/test_lab02.py.

A test suite that has only ever printed PASS proves nothing. This script
mutates app.py in a series of realistic ways and asserts the suite CATCHES each
one. A mutant that survives means the suite has a blind spot.

    .venv/bin/python tests/negctl.py

Safety: app.py is always restored from an in-memory copy in a finally block,
and the restore is verified by SHA-256 -- including when a mutant crashes the
runner. Each mutation is counted BEFORE it is applied, so a mutant whose anchor
never existed is reported as BROKEN rather than silently recorded as survived.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app.py"
SUITE = ROOT / "tests" / "test_lab02.py"
PY = ROOT / ".venv" / "bin" / "python"

# (name, old, new, expected_occurrences)
MUTANTS: list[tuple[str, str, str, int]] = [
    (
        "risk rule: High Risk threshold 60 -> 50",
        "if score < 60 or attendance < 60:",
        "if score < 50 or attendance < 50:",
        1,
    ),
    (
        "risk rule: Medium branch dropped (everything not High is Low)",
        '    elif score < 75 or attendance < 75:\n        return "Medium Risk"\n',
        "",
        1,
    ),
    (
        "risk rule: or -> and (both conditions must be low)",
        "if score < 60 or attendance < 60:",
        "if score < 60 and attendance < 60:",
        1,
    ),
    (
        "filter: minimum score >= becomes > (boundary)",
        'filtered_df["Score"] >= min_score',
        'filtered_df["Score"] > min_score',
        1,
    ),
    (
        "filter: minimum attendance >= becomes > (boundary)",
        'filtered_df["Attendance"] >= min_attendance',
        'filtered_df["Attendance"] > min_attendance',
        1,
    ),
    (
        "filter: minimum attendance comparison inverted",
        'filtered_df["Attendance"] >= min_attendance',
        'filtered_df["Attendance"] <= min_attendance',
        1,
    ),
    (
        "page config: set_page_config moved below the first command",
        'st.set_page_config(\n    page_title="EduRisk Analytics - Lab 02",\n    layout="wide"\n)\n\n',
        "",
        1,
    ),
    (
        "sidebar: Risk Checker page removed",
        '["Home", "Dashboard", "Student Data", "Risk Checker", "About"]',
        '["Home", "Dashboard", "Student Data", "About"]',
        1,
    ),
    (
        "metrics: Dashboard Average Score rounding dropped",
        'st.metric("Average Score", round(average_score, 2))\n\n    with col3:'
        '\n        st.metric("Average Attendance", f"{round(average_attendance, 2)}%")\n\n'
        '    with col4:\n        st.metric("High Risk", high_risk_students)',
        'st.metric("Average Score", average_score)\n\n    with col3:'
        '\n        st.metric("Average Attendance", f"{round(average_attendance, 2)}%")\n\n'
        '    with col4:\n        st.metric("High Risk", high_risk_students)',
        1,
    ),
    (
        "metrics: Student Data Average Score rounding dropped",
        'st.metric("Average Score", round(average_score, 2))\n\n    with col3:'
        '\n        st.metric("Average Attendance", f"{round(average_attendance, 2)}%")\n\n'
        '    with col4:\n        st.metric("High Risk Students", high_risk_students)',
        'st.metric("Average Score", average_score)\n\n    with col3:'
        '\n        st.metric("Average Attendance", f"{round(average_attendance, 2)}%")\n\n'
        '    with col4:\n        st.metric("High Risk Students", high_risk_students)',
        1,
    ),
    (
        "download: wrong CSV filename",
        'file_name="filtered_student_data.csv"',
        'file_name="data.csv"',
        1,
    ),
    (
        "student data: one student removed from the dataset",
        '"Dara", "Sophea", "Vuthy", "Malis", "Rithy", "Sreyneang", "Chan", "Bopha"',
        '"Dara", "Sophea", "Vuthy", "Malis", "Rithy", "Sreyneang", "Chan"',
        1,
    ),
    (
        "risk checker: success/warning/error branches swapped",
        'if risk_result == "Low Risk":\n            st.success("Risk Level: Low Risk")',
        'if risk_result == "Low Risk":\n            st.error("Risk Level: Low Risk")',
        1,
    ),
    (
        "about page: student information removed",
        '    st.subheader("Student Information")\n    st.write("Name: Heng Hour")\n'
        '    st.write("Student ID: 0007307")\n    st.write("Class: M2")\n',
        "",
        1,
    ),
    (
        "checkbox: filtered dataset hidden by default",
        'show_data = st.checkbox("Show Filtered Dataset", True)',
        'show_data = st.checkbox("Show Filtered Dataset", False)',
        1,
    ),
    (
        "risk column: apply axis=1 -> axis=0",
        "    lambda row: get_risk_level(row[\"Score\"], row[\"Attendance\"]),\n    axis=1",
        "    lambda row: get_risk_level(row[\"Score\"], row[\"Attendance\"]),\n    axis=0",
        1,
    ),
    (
        "lab01 continuity: the 'Click Me' button is deleted again",
        "    # Carried over from Lab 01.\n    if st.button(\"Click Me\"):\n        st.write(\"Welcome\")\n",
        "",
        1,
    ),
    (
        "lab01 continuity: the 'Low Score Students' metric is deleted again",
        '    # Carried over from Lab 01, kept as its own row so the Lab 02 metric row\n'
        '    # above stays exactly as the lab sheet defines it.\n'
        '    st.subheader("From Lab 01")\n    lab1_col1, lab1_col2 = st.columns(2)\n\n'
        '    with lab1_col1:\n        st.metric("Low Score Students", low_score_students)\n\n'
        '    with lab1_col2:\n'
        '        st.caption("Count of students scoring below 60, carried over from Lab 01.")\n',
        "",
        1,
    ),
    (
        "lab01 continuity: the low-score threshold changes from 60 to 50",
        'low_score_students = student_df[student_df["Score"] < 60].shape[0]',
        'low_score_students = student_df[student_df["Score"] < 50].shape[0]',
        1,
    ),
    (
        "theme: an emoji is put back into the app",
        'st.title("EduRisk Analytics")',
        'st.title("\U0001f393 EduRisk Analytics")',
        1,
        "app",
    ),
    (
        "theme: charts go back to Streamlit's default blue",
        'st.bar_chart(score_chart, color="#CC0000")',
        "st.bar_chart(score_chart)",
        1,
        "theme",
    ),
    (
        "theme: the dot field is removed from the backdrop",
        "  background-image:\n    radial-gradient(var(--v-white-06) 1px, transparent 1.5px),\n"
        "    radial-gradient(var(--v-white-10) 1px, transparent 1.5px),\n"
        "    radial-gradient(var(--v-white-16) 1px, transparent 1.4px);\n"
        "  background-size: 66px 66px, 22px 22px, 11px 11px;",
        "  background-image: none;\n  background-size: auto;",
        1,
        "theme",
    ),
    (
        "empty-guard removed: metrics report NaN instead of 0 on an empty result",
        "    if len(filtered_df) > 0:\n        average_score = filtered_df[\"Score\"].mean()",
        "    if True:\n        average_score = filtered_df[\"Score\"].mean()",
        1,
    ),
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_suite() -> tuple[int, str]:
    p = subprocess.run(
        [str(PY), str(SUITE)],
        capture_output=True, text=True, timeout=600, cwd=str(ROOT),
    )
    return p.returncode, (p.stdout + p.stderr)


# --- theme mutants -------------------------------------------------------
# CSS and the Vega-Lite spec do not exist in AppTest at all, so theme mutants
# have to be judged by a real browser against a real Streamlit server. The
# server is started once and relies on Streamlit's own file watcher to reload
# after each mutation, which is what makes this affordable.
PORT = 8791
SERVER: subprocess.Popen | None = None


def start_server() -> subprocess.Popen:
    global SERVER
    SERVER = subprocess.Popen(
        [str(ROOT / ".venv" / "bin" / "streamlit"), "run", "app.py",
         "--server.headless", "true", "--server.port", str(PORT),
         "--browser.gatherUsageStats", "false"],
        cwd=str(ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    for _ in range(60):
        time.sleep(1)
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/_stcore/health", timeout=2) as r:
                if r.read().strip() == b"ok":
                    return SERVER
        except Exception:
            continue
    raise SystemExit("theme server did not come up")


def stop_server() -> None:
    global SERVER
    if SERVER is not None:
        SERVER.terminate()
        try:
            SERVER.wait(timeout=15)
        except subprocess.TimeoutExpired:
            SERVER.kill()
        SERVER = None


def run_theme_suite() -> tuple[int, str]:
    time.sleep(6)  # let Streamlit's file watcher reload the mutated app
    env = dict(os.environ)
    env["NODE_PATH"] = subprocess.run(
        ["npm", "root", "-g"], capture_output=True, text=True
    ).stdout.strip()
    p = subprocess.run(
        ["node", str(ROOT / "tests" / "verify_theme.js"),
         f"http://127.0.0.1:{PORT}", "/tmp/opencode/negctl-shots"],
        capture_output=True, text=True, timeout=600, cwd=str(ROOT), env=env,
    )
    return p.returncode, (p.stdout + p.stderr)


def main() -> int:
    original_text = APP.read_text(encoding="utf-8")
    original_sha = sha(APP)

    # baseline: the unmutated app must pass, otherwise every result is noise
    rc, out = run_suite()
    if rc != 0:
        print("BASELINE FAILED -- refusing to mutation-test a broken suite")
        print(out[-3000:])
        return 2
    print(f"baseline: PASS ({original_sha[:12]})")

    results: list[tuple[str, str]] = []
    theme_needed = any(len(m) > 4 and m[4] == "theme" for m in MUTANTS)
    server_up = False
    try:
        if theme_needed:
            start_server()
            server_up = True
            rc, out = run_theme_suite()
            if rc != 0:
                print("THEME BASELINE FAILED -- refusing to mutation-test a broken theme")
                print(out[-3000:])
                return 2
            print("theme baseline: PASS")

        for mutant_spec in MUTANTS:
            name, old, new, expected = mutant_spec[:4]
            kind = mutant_spec[4] if len(mutant_spec) > 4 else "app"
            runner = run_theme_suite if kind == "theme" else run_suite

            found = original_text.count(old)
            if found != expected:
                results.append((name, f"BROKEN anchor (found {found}, expected {expected})"))
                print(f"[BROKEN] {name} -- anchor found {found}x, expected {expected}")
                continue

            mutant = original_text.replace(old, new)
            if mutant == original_text:
                results.append((name, "BROKEN mutation was a no-op"))
                print(f"[BROKEN] {name} -- mutation produced no change")
                continue

            APP.write_text(mutant, encoding="utf-8")
            if sha(APP) == original_sha:
                results.append((name, "BROKEN mutant was not written"))
                print(f"[BROKEN] {name} -- file checksum unchanged, mutant never landed")
                continue

            try:
                rc, out = runner()
            finally:
                APP.write_text(original_text, encoding="utf-8")
                if sha(APP) != original_sha:
                    raise SystemExit(f"FATAL: app.py not restored after {name!r}")

            if rc == 0:
                results.append((name, "SURVIVED"))
                print(f"[SURVIVED] {name}  <-- the suite did NOT catch this")
            else:
                fails = [ln for ln in out.splitlines() if ln.startswith("[FAIL]")]
                crashed = "Traceback (most recent call last)" in out
                how = f"crashed" if crashed and not fails else \
                      f"{len(fails)} failing checks" if fails else \
                      f"exited {rc} with no FAIL lines"
                results.append((name, f"caught ({how})"))
                print(f"[caught]   {name}  ({how})")
                for ln in fails[:3]:
                    print(f"             {ln}")
    finally:
        APP.write_text(original_text, encoding="utf-8")
        if sha(APP) != original_sha:
            raise SystemExit("FATAL: app.py was not restored")
        if server_up:
            stop_server()

    print()
    survived = [n for n, v in results if v == "SURVIVED"]
    broken = [n for n, v in results if v.startswith("BROKEN")]
    caught = [n for n, v in results if v.startswith("caught")]
    print(f"caught {len(caught)}/{len(MUTANTS)}  |  survived {len(survived)}  |  broken {len(broken)}")
    for n in survived:
        print(f"  SURVIVED: {n}")
    for n in broken:
        print(f"  BROKEN:   {n}")
    if survived or broken:
        return 1
    print("every mutant was caught")
    return 0


if __name__ == "__main__":
    sys.exit(main())