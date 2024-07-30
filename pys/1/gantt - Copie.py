import streamlit as st
import pandas as pd
import plotly.express as px
import json

# Load Gantt chart data from the .gantt file
def load_gantt_data(file):
    data = json.load(file)
    return data

# Save Gantt chart data to the .gantt file
def save_gantt_data(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

# Display the Gantt chart
def display_gantt_chart(data):
    df = pd.DataFrame(data['data'])
    df['StartDate'] = pd.to_datetime(df['StartDate'])
    df['EndDate'] = pd.to_datetime(df['EndDate'])
    fig = px.timeline(df, x_start="StartDate", x_end="EndDate", y="TaskName", color="TaskName",
                      hover_data=['Duration', 'resources', 'info'], title="Project Gantt Chart")
    fig.update_layout(
        height=600,
        width=1200,
        margin=dict(l=0, r=0, t=50, b=0)
    )
    st.plotly_chart(fig, use_container_width=True)

# Edit task details
def edit_task(task):
    st.write(f"### Editing Task: {task['TaskName']}")
    task['TaskName'] = st.text_input("Task Name", task['TaskName'])
    task['StartDate'] = st.date_input("Start Date", pd.to_datetime(task['StartDate'])).strftime('%Y-%m-%d')
    task['EndDate'] = st.date_input("End Date", pd.to_datetime(task['EndDate'])).strftime('%Y-%m-%d')
    task['Duration'] = (pd.to_datetime(task['EndDate']) - pd.to_datetime(task['StartDate'])).days + 1
    task['info'] = st.text_area("Info", task['info'])
    task['Predecessor'] = st.text_input("Predecessor", task['Predecessor'])
    return task

# Main function to run the Streamlit app
def main():
    st.title("Interactive Project Management App")
    
    gantt_file = st.file_uploader("Upload Gantt Chart File (.gantt)", type=["gantt"])
    if gantt_file is not None:
        data = load_gantt_data(gantt_file)
        display_gantt_chart(data)

        task_names = [task['TaskName'] for task in data['data']]
        selected_task_name = st.selectbox("Select Task to Edit", task_names)
        selected_task = next(task for task in data['data'] if task['TaskName'] == selected_task_name)
        
        if selected_task:
            edited_task = edit_task(selected_task)
            if st.button("Save Changes"):
                # Update the task in the data
                task_index = next(index for (index, d) in enumerate(data['data']) if d['TaskName'] == selected_task_name)
                data['data'][task_index] = edited_task
                
                # Save the updated data
                save_gantt_data(gantt_file.name, data)
                st.success("Task updated successfully!")
                
                # Reload the updated Gantt chart
                display_gantt_chart(data)
    else:
        st.info("Please upload a Gantt chart file to get started.")

if __name__ == "__main__":
    main()
