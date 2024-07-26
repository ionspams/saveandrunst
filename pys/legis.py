import streamlit as st
import requests
from bs4 import BeautifulSoup

# Function to search and fetch data from legis.md
def search_legislation(keyword, lang='ro'):
    try:
        # Corrected the URL according to a typical search pattern
        search_url = f"https://www.legis.md/cautare/getResults?lang={lang}&search={keyword}"
        response = requests.get(search_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        results = []
        # Adjust the HTML parsing according to actual class names and structures observed on the site
        for item in soup.find_all('a', href=True):
            if 'getResults?doc_id' in item['href']:  # Ensuring only valid document links are processed
                title = item.text.strip()
                link = f"https://www.legis.md{item['href']}" if not item['href'].startswith('http') else item['href']
                results.append((title, link))
        return results
    except requests.RequestException as e:
        st.error(f"An error occurred: {e}")
        return []

# Function to fetch the content of a selected document
def fetch_document_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        content = soup.find('div', class_='document-content')
        if content:
            return content.text.strip()  # Clean any extra whitespace
        else:
            return "Content not found."
    except requests.RequestException as e:
        st.error(f"An error occurred while fetching the document: {e}")
        return "Content not found."

# Streamlit app interface with enhanced feedback and error handling
st.title('Moldova Legislative Search')
keyword = st.text_input('Enter keyword:')
language = st.selectbox('Select language:', ['ro', 'ru'])
search_button = st.button('Search')

if search_button and keyword:
    with st.spinner('Searching...'):
        results = search_legislation(keyword, language)
        if results:
            st.write(f"Found {len(results)} results.")
            for title, link in results:
                with st.expander(title):
                    doc_content = fetch_document_content(link)
                    st.write(doc_content)
        else:
            st.warning("No results found. Please try different keywords or check the language selection.")
