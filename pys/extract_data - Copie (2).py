import os
import sys
import subprocess

# Ensure Tesseract is installed
try:
    import pytesseract
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pytesseract"])

# Ensure Pillow is installed
try:
    from PIL import Image
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow"])

# Ensure pandas is installed
try:
    import pandas as pd
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas"])

import pytesseract
from PIL import Image
import pandas as pd

# Set Tesseract executable path on Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Directory where the images are stored
# Replace this with the actual path to your image files
image_dir = r'C:\Users\ghici\Documents\Laolaltă\M4P\2024\Dopo\April Funds\Apps\my_streamlit_app\images'

# List of image files
image_files = [
    'distributionlist2-0.png', 'distributionlist2-1.png', 'distributionlist2-2.png',
    'distributionlist2-3.png', 'distributionlist2-4.png', 'distributionlist2-5.png',
    'distributionlist2-6.png', 'distributionlist2-7.png', 'distributionlist2-8.png',
    'distributionlist2-9.png'
]

# Initialize a list to hold the extracted data
extracted_data = []

# Function to perform OCR on an image and extract text
def extract_text_from_image(image_path):
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image, lang='eng')
    return text

# Function to parse the extracted text
def parse_text(text):
    lines = text.split('\n')
    for line in lines:
        # Split the line into fields
        fields = line.split()
        if len(fields) < 7:  # Ensure the line has enough fields
            continue
        name = ' '.join(fields[:2])
        date = fields[2]
        age = fields[3]
        gender = fields[4]
        household_members = fields[5]
        nationality = fields[6]
        food_kit = '1' if '1' in fields[7:] else '0'
        hygiene_kit = '1' if '1' in fields[7:] else '0'
        telephone = fields[-2]
        signature = fields[-1]
        extracted_data.append([name, date, age, gender, household_members, nationality, food_kit, hygiene_kit, telephone, signature])

# Perform OCR and extract data from each image
for image_file in image_files:
    image_path = os.path.join(image_dir, image_file)
    text = extract_text_from_image(image_path)
    parse_text(text)

# Convert the extracted data to a DataFrame
columns = ['Name', 'Date', 'Age', 'Gender', 'Household Members', 'Nationality', 'Family Food Kit', 'Family Hygiene Kit', 'Telephone', 'Signature']
df = pd.DataFrame(extracted_data, columns=columns)

# Save the DataFrame to a CSV file
output_csv = os.path.join(image_dir, 'extracted_data.csv')
df.to_csv(output_csv, index=False)

print(f"Data extracted and saved to {output_csv}")
