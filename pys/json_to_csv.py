import pandas as pd
import json

def is_new_row_start(content, previous_content):
    """
    Determines the start of a new row based on content analysis.

    This function should be customized based on the specific patterns
    observed in your JSON data. 

    Args:
        content (str): The current word's content.
        previous_content (str): The content of the previous word.

    Returns:
        bool: True if the content indicates the start of a new row, False otherwise.
    """
    # Example logic: Check if the content is a single digit, 
    # which might indicate a row number in your document.
    if content.isdigit() and len(content) == 1 and previous_content.isdigit() is False:
        return True
    # Add more conditions based on your data's structure
    return False

def assign_to_field(row, content, previous_content):
    """
    Assigns content to the correct field in the row.

    This function should be customized based on keywords, data types,
    and other patterns observed in your JSON data.

    Args:
        row (dict): The current row being populated.
        content (str): The current word's content.
        previous_content (str): The content of the previous word.
    """
    # Example logic:
    if "Name" in previous_content:
        row['Name'] = content
    elif "Surname" in previous_content:
        row['Surname'] = content
    elif len(content) == 10 and content.isdigit():
        row['Telephone Number'] = content
    elif "Date" in content:
        row['Date'] = content
    elif "Kit" in content:
        if "Family" in content:
            row['Family Food Kit'] = content
        elif "Baby" in content:
            row['Baby Food Kit'] = content
    # Add more conditions based on your data's structure

def extract_structured_data(json_data):
    """
    Extracts structured data from the JSON and returns a Pandas DataFrame.

    Args:
        json_data (dict): The loaded JSON data.

    Returns:
        pandas.DataFrame: The extracted data in a tabular format.
    """
    all_data = []
    for page in json_data['analyzeResult']['pages']:
        current_row = {}
        previous_content = ""
        for word in page['words']:
            content = word['content'].strip()
            if is_new_row_start(content, previous_content):
                if current_row:
                    all_data.append(current_row)
                current_row = {'Row': content}  
            assign_to_field(current_row, content, previous_content)
            previous_content = content

        if current_row:
            all_data.append(current_row)

    return pd.DataFrame(all_data)

# --- Main Execution ---
# Load your JSON file
json_file_path = 'C:\\Users\\gh\\ci\\Documents\\LaoLa\\ta\\M4P\\2024\\Dopo\\April Funds\\Apps\\my_streamlit_app\\json_to_csv.json'  # Replace with the actual path to your JSON file
with open(json_file_path, 'r') as f:
    json_data = json.load(f)

# Extract the data
df = extract_structured_data(json_data)

# Print the DataFrame to the console
print(df)

# Save the DataFrame to a CSV file (optional)
df.to_csv('extracted_data.csv', index=False) 