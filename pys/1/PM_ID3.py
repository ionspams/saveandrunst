import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

# Set page config
st.set_page_config(layout="wide", page_title="PM Dashboard")

# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=['Task', 'Start', 'End', 'Resource', 'Progress'])

def load_data(file):
    if file.name.endswith('.csv'):
        data = pd.read_csv(file)
    elif file.name.endswith('.xlsx'):
        data = pd.read_excel(file)
    elif file.name.endswith('.json'):
        data = pd.read_json(file)
    else:
        st.error("Unsupported file type. Please upload a CSV, XLSX, or JSON file.")
        return None

    required_columns = ['Task', 'Start', 'End']
    if not all(col in data.columns for col in required_columns):
        st.error(f"The file is missing one or more required columns: {', '.join(required_columns)}")
        return None

    data['Start'] = pd.to_datetime(data['Start'])
    data['End'] = pd.to_datetime(data['End'])
    
    if 'Resource' not in data.columns:
        data['Resource'] = 'Unassigned'
    if 'Progress' not in data.columns:
        data['Progress'] = 0

    return data

def save_data(data):
    return data.to_json(date_format='iso')

def create_gantt_chart(data):
    fig = px.timeline(data, x_start="Start", x_end="End", y="Task", color="Resource",
                      hover_data=["Progress"])
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        title="Project Gantt Chart",
        xaxis_title="Timeline",
        yaxis_title="Tasks",
        height=600,
        margin=dict(l=10, r=10, t=30, b=10)
    )
    return fig

def main():
    st.title("Project Management Interactive Dashboard")

    # Sidebar for navigation and file upload
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Gantt Chart", "Task Management", "Resource Management"])

    st.sidebar.title("Data Management")
    uploaded_file = st.sidebar.file_uploader("Upload Project Data", type=['csv', 'xlsx', 'json'])
    if uploaded_file is not None:
        data = load_data(uploaded_file)
        if data is not None:
            st.session_state.data = data
            st.success("Data loaded successfully!")

    if st.sidebar.button("Save Data"):
        if not st.session_state.data.empty:
            json_string = save_data(st.session_state.data)
            st.sidebar.download_button(
                label="Download JSON",
                file_name="project_data.json",
                mime="application/json",
                data=json_string
            )
        else:
            st.sidebar.warning("No data to save.")

    # Main content area
    if page == "Gantt Chart":
        st.header("Gantt Chart")
        if not st.session_state.data.empty:
            fig = create_gantt_chart(st.session_state.data)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available. Please upload a file or add tasks.")

    elif page == "Task Management":
        st.header("Task Management")
        
        # Add new task
        with st.expander("Add New Task"):
            with st.form("new_task_form"):
                task_name = st.text_input("Task Name")
                start_date = st.date_input("Start Date")
                end_date = st.date_input("End Date")
                resource = st.text_input("Resource")
                progress = st.slider("Progress", 0, 100, 0)
                
                if st.form_submit_button("Add Task"):
                    new_task = pd.DataFrame({
                        'Task': [task_name],
                        'Start': [start_date],
                        'End': [end_date],
                        'Resource': [resource],
                        'Progress': [progress]
                    })
                    st.session_state.data = pd.concat([st.session_state.data, new_task], ignore_index=True)
                    st.success("Task added successfully!")

        # Edit existing tasks
        if not st.session_state.data.empty:
            st.subheader("Edit Existing Tasks")
            task_to_edit = st.selectbox("Select Task to Edit", st.session_state.data['Task'])
            task_index = st.session_state.data[st.session_state.data['Task'] == task_to_edit].index[0]
            
            with st.form("edit_task_form"):
                edited_task = st.session_state.data.loc[task_index].copy()
                edited_task['Task'] = st.text_input("Task Name", value=edited_task['Task'])
                edited_task['Start'] = st.date_input("Start Date", value=edited_task['Start'])
                edited_task['End'] = st.date_input("End Date", value=edited_task['End'])
                edited_task['Resource'] = st.text_input("Resource", value=edited_task['Resource'])
                edited_task['Progress'] = st.slider("Progress", 0, 100, int(edited_task['Progress']))
                
                if st.form_submit_button("Update Task"):
                    st.session_state.data.loc[task_index] = edited_task
                    st.success("Task updated successfully!")

    elif page == "Resource Management":
        st.header("Resource Management")
        
        resources = st.session_state.data['Resource'].unique()
        st.subheader("Current Resources")
        st.write(", ".join(resources))

        # Add new resource
        new_resource = st.text_input("Add New Resource")
        if st.button("Add Resource"):
            if new_resource and new_resource not in resources:
                st.session_state.data.loc[st.session_state.data['Resource'] == 'Unassigned', 'Resource'] = new_resource
                st.success(f"Added new resource: {new_resource}")
            else:
                st.warning("Please enter a unique resource name.")

        # Remove resource
        resource_to_remove = st.selectbox("Select Resource to Remove", resources)
        if st.button("Remove Resource"):
            st.session_state.data.loc[st.session_state.data['Resource'] == resource_to_remove, 'Resource'] = 'Unassigned'
            st.success(f"Removed resource: {resource_to_remove}")

if __name__ == "__main__":
    main()