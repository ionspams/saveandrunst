import pytesseract
from pdf2image import convert_from_path
import pandas as pd
import os

# Set the Tesseract-OCR executable path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

print("Tesseract path set")

# Path to the PDF file
pdf_path = r"C:\Users\ghici\Documents\Laolaltă\M4P\2024\Dopo\April Funds\Apps\my_streamlit_app\distribution_list.pdf"
print(f"PDF path set to: {pdf_path}")

# Convert PDF to images
print("Starting PDF to image conversion...")
try:
    pages = convert_from_path(pdf_path, 300, poppler_path=r'C:\poppler\Library\bin')
    print(f"Converted {len(pages)} pages from PDF")
except Exception as e:
    print(f"Error during PDF to image conversion: {e}")

# Define the columns to extract
columns = ['Row Number', 'Date of Distribution', 'Family Food Kit', 'Baby Food Kit', 'Phone Number']
data = []
print("Columns defined")

# Helper function to check if a string contains a date
def contains_date(string):
    return any(char.isdigit() for char in string)

print("Starting to process each page...")

# Process each page
for i, page in enumerate(pages):
    print(f"Processing page {i+1}")
    # Convert page to image and perform OCR
    text = pytesseract.image_to_string(page)
    print(f"OCR completed for page {i+1}")
    
    # Split text into lines
    lines = text.split('\n')
    print(f"Extracted {len(lines)} lines from page {i+1}")
    
    # Parse lines to extract relevant information
    for line in lines:
        parts = line.split()
        if len(parts) >= 5 and contains_date(parts[1]):  # Ensuring there are enough parts in the line and it contains a date
            row_number = parts[0]
            date_of_distribution = parts[1]
            family_food_kit = parts[2]
            baby_food_kit = parts[3]
            phone_number = parts[4]
            data.append([row_number, date_of_distribution, family_food_kit, baby_food_kit, phone_number])
    print(f"Page {i+1} processed")

# Create a DataFrame
df = pd.DataFrame(data, columns=columns)
print("DataFrame created")

# Save the DataFrame to a CSV file
csv_path = r"C:\Users\ghici\Documents\Laolaltă\M4P\2024\Dopo\April Funds\Apps\my_streamlit_app\distribution_list.csv"
df.to_csv(csv_path, index=False)
print(f"Data extracted and saved to {csv_path}")
