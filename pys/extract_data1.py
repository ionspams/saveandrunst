import json
import pandas as pd
import os
import glob
import re

def calculate_centroid(polygon):
    x_coords = polygon[0::2]
    y_coords = polygon[1::2]
    centroid = [sum(x_coords) / len(x_coords), sum(y_coords) / len(y_coords)]
    return centroid

def parse_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        json_data = json.load(file)
    
    words = json_data['analyzeResult']['pages'][0]['words']
    extracted_data = {'Name': [], 'Date': [], 'Family Food Kit': [], 'Family Hygiene Kit': [], 'Baby Hygiene Kit': [], 'Telephone Number': []}

    for word in words:
        content = word['content']
        if 'boundingRegions' in word:
            polygon = word['boundingRegions'][0]['polygon']
        elif 'polygon' in word:
            polygon = word['polygon']
        else:
            continue
        centroid = calculate_centroid(polygon)

        # Classify the content
        if re.match(r'^\d{6,13}$', content):  # Phone numbers
            extracted_data['Telephone Number'].append(content)
        elif re.match(r'^\d{1,2}[-./]\d{1,2}[-./](\d{2}|\d{4})$', content):  # Dates
            extracted_data['Date'].append(content)
        elif re.match(r'^[\d]{1,2}$', content):  # Kit counts
            # Determine the type of kit based on approximate column position
            if 4 < centroid[0] <= 6:
                extracted_data['Family Food Kit'].append(content)
            elif 6 < centroid[0] <= 8:
                extracted_data['Family Hygiene Kit'].append(content)
            elif 8 < centroid[0] <= 10:
                extracted_data['Baby Hygiene Kit'].append(content)
        else:  # Assuming it's a name or other text
            extracted_data['Name'].append(content)
    
    # Print extracted data for debugging
    print(f"Extracted data from {file_path}:")
    for key, value in extracted_data.items():
        print(f"{key}: {value}")

    return extracted_data

def save_to_csv(data, output_file):
    max_length = max([len(data[key]) for key in data.keys()])
    for key in data.keys():
        while len(data[key]) < max_length:
            data[key].append('')
    df = pd.DataFrame(data)
    df.to_csv(output_file, index=False)

def main(input_files, output_file):
    all_data = {'Name': [], 'Date': [], 'Family Food Kit': [], 'Family Hygiene Kit': [], 'Baby Hygiene Kit': [], 'Telephone Number': []}
    for file in input_files:
        extracted_data = parse_json(file)
        for key in all_data.keys():
            all_data[key].extend(extracted_data[key])
    
    save_to_csv(all_data, output_file)

if __name__ == "__main__":
    input_files = glob.glob('json_files/*.json')
    output_file = 'extracted_data.csv'
    main(input_files, output_file)
