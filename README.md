# Lab 03: Data Loading, Layout, and Frontend Prototype

## Project Theme

EduRisk Analytics

## Description

This Streamlit app is a frontend prototype for student academic monitoring.

This lab continues from Lab 02 and moves the student dataset out of app.py into students.csv.

The app loads CSV data using Pandas and displays it in a cleaner Streamlit dashboard layout.

## Continued from Lab 02

This lab is built on top of the Lab 02 app, not restarted from scratch. Everything from Lab 02 is still here:

- The same `EduRiskAnalytics` project and the same virtual environment
- The sidebar menu and the Home, Dashboard, Student Data, Risk Checker and About pages
- The `Click Me` button on the Home page
- The `Low Score Students` metric (shown under "From Lab 01" on the Student Data page)
- Student Information on the About page
- The course filter, risk level filter, minimum attendance slider and minimum score slider
- The `Show Filtered Dataset` checkbox and the `Download Filtered Data` button
- The Student Scores and Risk Level Count charts
- The signature black, white and red theme with dot-matrix depth

Lab 03 changes the data source and adds to the layout. The Risk Level rule is unchanged.

## What Lab 03 adds

- `students.csv` as the data source, read with `pd.read_csv()`
- `load_student_data()` with missing-file error handling and `st.stop()`
- A Data Inspection section on the Student Data page (shape, column names, first 5 rows)
- A Course Count chart on the Dashboard
- An Ethics Reminder on the Dashboard as well as the About page

## Features

- Sidebar navigation
- Home page
- Dashboard page with filters
- Student data page
- Risk checker page
- About page
- Student dataset stored in students.csv
- CSV data loading with Pandas
- Missing CSV file error handling
- Risk level calculation
- Dashboard metrics
- Student records table
- Student score chart
- Risk level count chart
- Course count chart
- Data inspection section
- CSV download of the filtered dataset
- Ethics reminder
- Lab 01 and Lab 02 features retained: Click Me button, Low Score Students metric, filters, download button
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

## Student Information

Name: Heng Hour
Student ID: 0007307
Class: M2