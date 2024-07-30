import streamlit as st
import pandas as pd
from rapidfuzz import fuzz
import textdistance

st.set_page_config(page_title='Data Analysis and Cleaning App', layout='wide')

# Function to normalize phone numbers by removing non-numeric characters and ensuring proper length
def normalize_phone(phone):
    phone = ''.join(filter(str.isdigit, str(phone)))
    if len(phone) == 8:  # Assume local format without country code
        phone = '373' + phone  # Prepend country code
    elif len(phone) == 11 and phone.startswith('373'):
        phone = '0' + phone[3:]  # Convert to local format
    return phone

# Function to normalize dates by parsing and formatting to a standard format
def normalize_date(date):
    try:
        return pd.to_datetime(date, errors='coerce').strftime('%Y-%m-%d')
    except ValueError:
        return None

# Function to get the Soundex code of a string
def soundex_code(s):
    if not s:  # Check for empty string
        return ""
    s = s.upper()
    soundex = s[0]
    dictionary = {
        "BFPV": "1",
        "CGJKQSXZ": "2",
        "DT": "3",
        "L": "4",
        "MN": "5",
        "R": "6",
    }
    for char in s[1:]:
        for key in dictionary.keys():
            if char in key:
                code = dictionary[key]
                if code != soundex[-1]:
                    soundex += code
    soundex = soundex[:4].ljust(4, "0")
    return soundex

# Function to find the best match for a given target row in the base dataset
def find_best_match(target_row, base_df, phone_weight, date_weight):
    best_match = None
    second_best_match = None
    highest_score = 0
    second_highest_score = 0
    possible_matches = []

    for _, base_row in base_df.iterrows():
        phone_score = fuzz.ratio(str(target_row['NormalizedPhone']), str(base_row['NormalizedPhone'])) if target_row['NormalizedPhone'] and base_row['NormalizedPhone'] else 0
        date_score = fuzz.ratio(str(target_row['NormalizedDate']), str(base_row['NormalizedDate'])) if target_row['NormalizedDate'] and base_row['NormalizedDate'] else 0
        
        # Phonetic matching
        target_phone_soundex = soundex_code(target_row['NormalizedPhone'])
        base_phone_soundex = soundex_code(base_row['NormalizedPhone'])
        phonetic_score = fuzz.ratio(target_phone_soundex, base_phone_soundex) if target_phone_soundex and base_phone_soundex else 0
        
        # Edit distance
        edit_distance_score = 100 - (textdistance.levenshtein.normalized_distance(target_row['NormalizedPhone'], base_row['NormalizedPhone']) * 100) if target_row['NormalizedPhone'] and base_row['NormalizedPhone'] else 0
        
        # Combined score
        total_score = (phone_score * phone_weight) + (date_score * date_weight) + (phonetic_score * phone_weight * 0.5) + (edit_distance_score * phone_weight * 0.5)
        
        if total_score > highest_score:
            second_highest_score = highest_score
            second_best_match = best_match
            highest_score = total_score
            best_match = base_row
        elif total_score > second_highest_score:
            second_highest_score = total_score
            second_best_match = base_row
        
        possible_matches.append((base_row, total_score))
    
    possible_matches = sorted(possible_matches, key=lambda x: x[1], reverse=True)
    
    return best_match, second_best_match, highest_score, second_highest_score, date_score, phonetic_score, edit_distance_score, possible_matches

# Function to calculate probabilistic matching score
def probabilistic_match_score(phone_score, date_score, phonetic_score, edit_distance_score):
    return (phone_score + date_score + phonetic_score + edit_distance_score) / 4

# Main workflow
workflow = st.sidebar.selectbox('Select Workflow', ['Analyze & Normalize'])

if workflow == 'Analyze & Normalize':
    st.header("Analyze & Normalize Data")
    base_file = st.file_uploader("Upload Base Truth CSV", type=["csv"])
    target_file = st.file_uploader("Upload Target CSV", type=["csv"])

    if base_file and target_file:
        base_df = pd.read_csv(base_file)
        target_df = pd.read_csv(target_file)

        st.write("Base dataset:")
        base_start = st.number_input("Starting row for Base dataset", min_value=0, max_value=len(base_df)-1, value=0)
        base_rows = st.number_input("Number of rows to display and analyze from Base dataset", min_value=1, max_value=len(base_df)-base_start, value=5)
        st.dataframe(base_df.iloc[base_start:base_start+base_rows])

        st.write("Target dataset:")
        target_start = st.number_input("Starting row for Target dataset", min_value=0, max_value=len(target_df)-1, value=0)
        target_rows = st.number_input("Number of rows to display and analyze from Target dataset", min_value=1, max_value=len(target_df)-target_start, value=5)
        st.dataframe(target_df.iloc[target_start:target_start+target_rows])

        reference_col = st.selectbox("Select reference base column", base_df.columns.tolist())
        target_col = st.selectbox("Select target column for analysis", target_df.columns.tolist())
        date_col = st.selectbox("Select date column for analysis", target_df.columns.tolist())
        
        phone_weight = st.slider("Set weight for phone number", min_value=0.0, max_value=1.0, value=0.7)
        date_weight = st.slider("Set weight for date", min_value=0.0, max_value=1.0, value=0.3)
        threshold = st.slider("Set threshold for high-confidence corrections", min_value=0.0, max_value=100.0, value=90.0)
        
        # Normalize phone numbers and dates
        base_df['NormalizedPhone'] = base_df[reference_col].apply(normalize_phone)
        base_df['NormalizedDate'] = base_df[date_col].apply(normalize_date)
        target_df['NormalizedPhone'] = target_df[target_col].apply(normalize_phone)
        target_df['NormalizedDate'] = target_df[date_col].apply(normalize_date)

        if st.button("Analyze Data"):
            match_info_list = []
            summary_stats = {'Total Matches': 0, 'Total Possible Matches': 0, 'Low Confidence Matches': 0, 'Match Score Distribution': {}, 'Corrections Summary': {'Corrections Applied': 0, 'Corrections Not Applied': 0, 'Reasons for Non-application': {'Low Confidence': 0, 'Possible Matches': 0}}}
            progress_bar = st.progress(0)

            for i, row in enumerate(target_df.iloc[target_start:target_start+target_rows].iterrows()):
                _, target_row = row
                best_match, second_best_match, score, second_best_score, date_score, phonetic_score, edit_distance_score, possible_matches = find_best_match(target_row, base_df.iloc[base_start:base_start+base_rows], phone_weight, date_weight)
                probabilistic_score = probabilistic_match_score(score, date_score, phonetic_score, edit_distance_score)
                second_probabilistic_score = probabilistic_match_score(second_best_score, date_score, phonetic_score, edit_distance_score)
                
                # Convert possible matches to a readable string format
                possible_matches_str = '; '.join([f"{match[0][reference_col]} ({match[1]:.2f}%)" for match in possible_matches[:5]])
                
                match_info = {
                    'Row Number': target_row.name,
                    'Correction Applied': 'Yes' if probabilistic_score > threshold else 'No',
                    'Reference Match Percentage': f"{probabilistic_score:.2f}%",
                    'Base Column Match Percentage': f"{date_score:.2f}%",  # Use date match score here
                    'Target Value': target_row[target_col],
                    'Base Column Value': best_match[reference_col] if best_match is not None else '',
                    'Second Best Match Value': second_best_match[reference_col] if second_best_match is not None else '',
                    'Reference Match Characters': target_row['NormalizedPhone'],
                    'Additional Match Characters': len(target_row['NormalizedPhone']),
                    'Reference Value': best_match['NormalizedPhone'] if best_match is not None else '',
                    'Second Best Reference Value': second_best_match['NormalizedPhone'] if second_best_match is not None else '',
                    'Target Dataset Values': [str(x) for x in target_row.tolist()],
                    'Base Dataset Values': [str(x) for x in best_match.tolist()] if best_match is not None else [],
                    'Second Best Match Dataset Values': [str(x) for x in second_best_match.tolist()] if second_best_match is not None else [],
                    'Second Best Match Percentage': f"{second_probabilistic_score:.2f}%",
                    'Possible Matches': possible_matches_str
                }

                if best_match is not None and probabilistic_score > threshold:  # High threshold for high confidence corrections
                    target_row['CorrectedPhone'] = best_match[reference_col]
                    target_row['CorrectedDate'] = best_match[date_col]
                else:
                    target_row['CorrectedPhone'] = target_row[reference_col]
                    target_row['CorrectedDate'] = target_row[date_col]

                match_info_list.append(match_info)
                progress_bar.progress((i + 1) / len(target_df.iloc[target_start:target_start+target_rows]))
                
                # Update summary statistics
                summary_stats['Total Matches'] += 1 if probabilistic_score > threshold else 0
                summary_stats['Total Possible Matches'] += 1 if 80 <= probabilistic_score < 100 else 0
                summary_stats['Low Confidence Matches'] += 1 if probabilistic_score < 80 else 0
                score_range = f"{int(probabilistic_score // 10) * 10}-{int(probabilistic_score // 10) * 10 + 9}%"
                summary_stats['Match Score Distribution'][score_range] = summary_stats['Match Score Distribution'].get(score_range, 0) + 1
                summary_stats['Corrections Summary']['Corrections Applied'] += 1 if probabilistic_score > threshold else 0
                summary_stats['Corrections Summary']['Corrections Not Applied'] += 1 if probabilistic_score <= threshold else 0
                summary_stats['Corrections Summary']['Reasons for Non-application']['Low Confidence'] += 1 if probabilistic_score < 80 else 0
                summary_stats['Corrections Summary']['Reasons for Non-application']['Possible Matches'] += 1 if 80 <= probabilistic_score < 100 else 0

            # Create an annotated dataframe from the match info list
            annotated_df = pd.DataFrame(match_info_list)

            st.write("Match Summary:")
            st.json(summary_stats)
            st.write("Annotated Data:")
            st.dataframe(annotated_df.style.apply(lambda x: ['background: lightgreen' if v == 'Yes' else '' for v in x], axis=1, subset=['Correction Applied']))
            st.download_button(label="Download Annotated Data", data=annotated_df.to_csv(index=False), file_name='annotated_data.csv', mime='text/csv')

            # Display connected table for visual validation
            connected_rows = []
            for mi in match_info_list:
                if mi['Base Dataset Values']:
                    connected_row = {**mi}
                    connected_row.update({f"Matched {k}": v for k, v in zip(base_df.columns, mi['Base Dataset Values'])})
                    connected_rows.append(connected_row)
                else:
                    connected_rows.append(mi)
            connected_df = pd.DataFrame(connected_rows)

            st.write("Connected Table for Validation:")
            st.dataframe(connected_df)
            st.download_button(label="Download Connected Data", data=connected_df.to_csv(index=False), file_name='connected_data.csv')
