# Lab 05: Visualization and Interactivity

## Project Theme

EduRisk Analytics

## Description

This Streamlit app is a student academic monitoring prototype.

This lab continues from Lab 03 and improves the Risk Checker page using Streamlit forms, input validation, and session state.

The app loads student data from `students.csv`, displays dashboard information, and allows users to check individual student risk levels with a reliable form-based workflow.

## Continued from Lab 03

This lab is built on top of the Lab 03 app, not restarted from scratch. Everything from Lab 03 is still here:

- The same `EduRiskAnalytics` project and the same virtual environment
- The sidebar menu and the Home, Dashboard, Student Data, Risk Checker and About pages
- The `Click Me` button on the Home page
- The `Low Score Students` metric (shown under "From Lab 01" on the Student Data page)
- Student Information on the About page
- The course filter, risk level filter, minimum attendance slider and minimum score slider
- The `Show Filtered Dataset` checkbox and the `Download Filtered Data` button
- The Student Scores, Risk Level Count and Course Count charts
- The signature black, white and red theme with dot-matrix depth
- `students.csv` as the data source, read with `pd.read_csv()`
- `load_student_data()` with missing-file error handling and `st.stop()`
- A Data Inspection section on the Student Data page (shape, column names, first 5 rows)
- An Ethics Reminder on the Dashboard as well as the About page

The Risk Level rule is unchanged.

## What Lab 04 adds

- A `st.form()` grouping the Student Name, Score and Attendance inputs on the Risk Checker page
- A `st.form_submit_button()` so risk is only calculated after the user confirms
- Empty-name validation that warns instead of calculating
- Supportive risk feedback messages (on track / monitor progress / may need support)
- `st.session_state["risk_history"]` storing each submitted check
- A Recent Risk Checks table rendered from session state
- A Clear History button that resets the session-state list
- An Ethics Reminder at the bottom of the Risk Checker page
- Updated Home and About pages for Lab 04

## Features

- Sidebar navigation
- Home page
- Dashboard page with filters
- Student data page
- Improved risk checker page
- About page
- Student dataset stored in students.csv
- CSV data loading with Pandas
- Missing CSV file error handling
- Risk level calculation
- Streamlit form
- Form submit button
- Empty student name validation
- Supportive risk feedback messages
- Session state risk-check history
- Recent Risk Checks table
- Clear History button
- Dashboard metrics
- Student records table
- Student score chart
- Risk level count chart
- Course count chart
- Data inspection section
- CSV download of the filtered dataset
- Ethics reminders
- Lab 01, Lab 02 and Lab 03 features retained: Click Me button, Low Score Students metric, filters, download button
- Signature black, white and red theme with dot-matrix depth

## Tools Used

- Python
- Streamlit
- Pandas
- VS Code

## Required Files

- app.py
- students.csv
- requirements.txt
- README.md

## How to Run

streamlit run app.py

Note: activate the project environment first with `source .venv/bin/activate`
(Python 3.12; created via `uv venv -p python3.12 .venv`).

## Student Information

Name: Heng Hour
Student ID: 0007307
Class: M2