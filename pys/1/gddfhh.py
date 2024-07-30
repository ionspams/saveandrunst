import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread

# Define the layout structure
st.set_page_config(layout="wide")
st.title("Link Collector")

# Input area
st.markdown("""
    <style>
        .input-section {
            display: flex;
            justify-content: center;
            align-items: center;
            flex-direction: column;
            margin-bottom: 20px;
        }
        .category-section {
            display: flex;
            justify-content: space-between;
        }
        .category {
            flex: 1;
            margin: 0 10px;
        }
    </style>
""", unsafe_allow_html=True)

# Input fields
with st.container():
    st.write("## Add Link")
    link_input = st.text_input("Enter link or content")
    title_input = st.text_input("Enter title or short description")
    category = st.selectbox("Select category", [
        "For Development", "Useful Information", "Tools", "Tasks", "Ideas & Proposals", "Courses", "News Reel", "Any Other"])
    if st.button("Add Link"):
        if link_input and title_input:
            st.success("Link added successfully!")

# Example links for display
examples = [
    {"title": "Example Title 1", "link": "https://example.com", "category": "Useful Information"},
    {"title": "Example Title 2", "link": "https://example.com", "category": "Tools"},
    {"title": "Example Title 3", "link": "https://example.com", "category": "Ideas & Proposals"},
    {"title": "Example Title 4", "link": "https://example.com", "category": "For Development"},
    {"title": "Example Title 5", "link": "https://example.com", "category": "Tasks"},
    {"title": "Example Title 6", "link": "https://example.com", "category": "Courses"},
    {"title": "Example Title 7", "link": "https://example.com", "category": "News Reel"},
    {"title": "Example Title 8", "link": "https://example.com", "category": "Any Other"},
]

# Define the sections
categories = {
    "For Development": [],
    "Useful Information": [],
    "Tools": [],
    "Tasks": [],
    "Ideas & Proposals": [],
    "Courses": [],
    "News Reel": [],
    "Any Other": [],
}

# Add example links to respective categories
for example in examples:
    categories[example["category"]].append(example)

# Display sections
for idx, (category_name, links) in enumerate(categories.items()):
    with st.container():
        st.markdown(f"### {category_name}")
        for link in links:
            st.markdown(f"- **{link['title']}**: [Link]({link['link']})")