import streamlit as st
from model import SocialModel
import matplotlib.pyplot as plt
import pandas as pd

def run_model(steps, N, width, height):
    model = SocialModel(N, width, height)
    for i in range(steps):
        model.step()
    return model.datacollector.get_agent_vars_dataframe()

def main():
    st.title("Agent-Based Modeling for Social Cohesion")
    st.sidebar.title("Model Parameters")

    steps = st.sidebar.slider("Number of Steps", 1, 100, 10)
    num_agents = st.sidebar.slider("Number of Agents", 10, 100, 50)
    width = st.sidebar.slider("Grid Width", 10, 50, 20)
    height = st.sidebar.slider("Grid Height", 10, 50, 20)

    if st.sidebar.button("Run Model"):
        results = run_model(steps, num_agents, width, height)
        st.write("Simulation Results", results)

        avg_trust = results.groupby("Step")["Trust"].mean()
        st.line_chart(avg_trust)

if __name__ == "__main__":
    main()
