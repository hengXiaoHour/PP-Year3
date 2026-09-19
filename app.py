import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="EduRisk Analytics - Lab 01",
    page_icon="🎓",
    layout="centered"
)

student_df = pd.DataFrame({
    "Student Name": ["Dara", "Sophea", "Vuthy", "Malis", "Rithy"],
    "Course": ["Python", "Statistics", "Python", "Database", "Web App"],
    "Score": [85, 68, 45, 92, 58],
    "Attendance": [90, 75, 50, 95, 60],
    "Study Hours": [12, 8, 3, 15, 5]
})

total_students = len(student_df)
average_score = student_df["Score"].mean()
average_attendance = student_df["Attendance"].mean()
low_score_students = student_df[student_df["Score"] < 60].shape[0]

with st.sidebar:
    st.title("EduRisk Menu")
    selected_page = st.radio(
        "Select Page",
        ["Home", "Student Data", "About"]
    )

if selected_page == "Home":
    st.title("🎓 EduRisk Analytics")
    st.subheader("Student Risk Prediction and Monitoring System")
    st.write("Welcome to your first Streamlit web application.")
    st.success("Streamlit is working successfully!")

    if st.button("Click Me"):
        st.write("Welcome")

elif selected_page == "Student Data":
    st.title("Student Data")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Total Students", total_students)
        st.metric("Average Score", round(average_score, 2))

    with col2:
        st.metric("Average Attendance", f"{round(average_attendance, 2)}%")
        st.metric("Low Score Students", low_score_students)

    st.dataframe(student_df)

else:
    st.title("About")
    st.write("This app is part of Lab 01.")
    st.write("Course: Web App Development for Data Science")
    st.write("Project Theme: EduRisk Analytics")
