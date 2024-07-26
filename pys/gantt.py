import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta

# Initializing session state for storing tasks
if 'tasks' not in st.session_state:
    st.session_state.tasks = []

def add_task(task_name, start_date, end_date, resources, objective, indicator):
    new_task = {
        'Task ID': len(st.session_state.tasks) + 1,
        'Task Name': task_name,
        'Start Date': start_date,
        'End Date': end_date,
        'Duration': (end_date - start_date).days + 1,
        'Resources': resources,
        'Progress': 0,
        'Objective': objective,
        'Indicator': indicator
    }
    st.session_state.tasks.append(new_task)

def edit_task(task_id, new_name, new_start, new_end, new_resources, new_objective, new_indicator):
    for task in st.session_state.tasks:
        if task['Task ID'] == task_id:
            task['Task Name'] = new_name
            task['Start Date'] = new_start
            task['End Date'] = new_end
            task['Duration'] = (new_end - new_start).days + 1
            task['Resources'] = new_resources.split(",")
            task['Objective'] = new_objective
            task['Indicator'] = new_indicator

def delete_task(task_id):
    st.session_state.tasks = [task for task in st.session_state.tasks if task['Task ID'] != task_id]

def display_tasks():
    if st.session_state.tasks:
        df = pd.DataFrame(st.session_state.tasks)
        st.dataframe(df)
    else:
        st.write("No tasks added yet.")

def generate_gantt_chart():
    if st.session_state.tasks:
        df = pd.DataFrame(st.session_state.tasks)
        fig = px.timeline(df, x_start="Start Date", x_end="End Date", y="Task Name", color="Objective",
                          hover_data=["Resources", "Indicator"])
        fig.update_yaxes(categoryorder="total ascending")
        st.plotly_chart(fig)
    else:
        st.write("No tasks to display in Gantt chart.")

def download_gantt_file():
    if st.session_state.tasks:
        df = pd.DataFrame(st.session_state.tasks)
        gantt_data = {
            "data": [],
            "resources": [],
            "advanced": {"workWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}
        }

        resource_set = set()
        for i, task in df.iterrows():
            resources = [{"resourceId": res, "resourceName": res, "unit": 100} for res in task['Resources']]
            resource_set.update(task['Resources'])
            gantt_data["data"].append({
                "TaskID": task["Task ID"],
                "TaskName": task["Task Name"],
                "StartDate": task["Start Date"].strftime("%Y-%m-%d"),
                "EndDate": task["End Date"].strftime("%Y-%m-%d"),
                "Duration": task["Duration"],
                "Progress": task["Progress"],
                "color": "",
                "Predecessor": "",
                "resources": resources,
                "info": "",
                "DurationUnit": "day"
            })

        for res in resource_set:
            gantt_data["resources"].append({"resourceId": res, "resourceName": res})

        import json
        gantt_json = json.dumps(gantt_data, indent=2)
        st.download_button("Download Gantt Chart", gantt_json, "gantt_chart.json", "application/json")

def main():
    st.title("Agile Project Management Tool")

    st.sidebar.title("Add/Edit Task")

    task_id = st.sidebar.number_input("Task ID (for editing)", min_value=0, step=1)
    task_name = st.sidebar.text_input("Task Name")
    start_date = st.sidebar.date_input("Start Date", date.today())
    end_date = st.sidebar.date_input("End Date", date.today() + timedelta(days=1))
    resources = st.sidebar.text_input("Resources (comma-separated)")
    objective = st.sidebar.text_input("Objective")
    indicator = st.sidebar.text_input("Indicator")

    if st.sidebar.button("Add Task"):
        if task_name and start_date and end_date and resources and objective and indicator:
            if task_id == 0:
                add_task(task_name, start_date, end_date, resources.split(","), objective, indicator)
                st.sidebar.success("Task added successfully!")
            else:
                edit_task(task_id, task_name, start_date, end_date, resources, objective, indicator)
                st.sidebar.success("Task edited successfully!")
        else:
            st.sidebar.error("Please fill out all fields.")

    if st.sidebar.button("Delete Task"):
        delete_task(task_id)
        st.sidebar.success("Task deleted successfully!")

    st.header("Task List")
    display_tasks()

    st.header("Gantt Chart")
    generate_gantt_chart()

    st.header("Download Gantt Chart")
    download_gantt_file()

if __name__ == "__main__":
    main()
