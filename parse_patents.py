
import re
import os
import json

import subprocess

DOCX_FILE = 'Resources/Peter Sweeney Patents.docx'
HTML_FILE = 'Resources/patents.html'
JSON_FILE = 'src/data/patents.json'

# Ensure output directory exists
os.makedirs(os.path.dirname(JSON_FILE), exist_ok=True)

# Convert DOCX to HTML using textutil (macOS) to ensure fresh data
if os.path.exists(DOCX_FILE):
    try:
        subprocess.run(['textutil', '-convert', 'html', DOCX_FILE, '-output', HTML_FILE], check=True)
        print(f"Converted {DOCX_FILE} to {HTML_FILE}")
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to convert docx: {e}")
        # Continue if HTML exists

if not os.path.exists(HTML_FILE):
    print(f"Error: {HTML_FILE} not found")
    exit(1)

with open(HTML_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

patents = []
# Split by rows
rows = content.split('<tr>')

for row in rows:
    # Skip if no patent number span class found (roughly)
    # The structure we saw: 1.<span class="s1">Number</span>Title
    # Note: textutil output might vary slightly but we saw <span class="s1">
    
    # Match the main patent line: 1.<span...>Number</span>Title...
    m_main = re.search(r'(\d+)\.<span[^>]*>(.*?)</span>(.*?)</p>', row, re.DOTALL)
    if not m_main:
        continue
    
    p_index = m_main.group(1).strip()
    p_number_raw = m_main.group(2).strip()
    # Clean number (remove HTML tags if any)
    p_number = re.sub(r'<[^>]+>', '', p_number_raw).strip()
    
    p_title_raw = m_main.group(3).strip()
    p_title = re.sub(r'\s+', ' ', p_title_raw).strip()
    
    # Extract Country and Date from subsequent paragraph(s) in the row
    # Pattern: <p class="p2">US - 10.03.2011</p>
    m_meta = re.search(r'<p[^>]*>([A-Z]{2})\s+-\s+(\d{2}\.\d{2}\.\d{4})</p>', row)
    p_country = ""
    p_date = ""
    if m_meta:
        p_country = m_meta.group(1).strip()
        p_date = m_meta.group(2).strip()

    # --- TITLE CORRECTION ---
    TITLE_OVERRIDES = {
        '223540': 'Systems of computerized agents and user-directed semantic networking',
        '227140': 'System and method for performing a semantic operation on a digital social network',
        '248313': 'Preference guided data exploration and semantic processing',
        '227201': 'Methods and device for providing information of interest to one or more users',
        '227139': 'System and method for using knowledge representation to provide information based on environmental input',
        '223541': 'Systems and methods for analyzing and synthesizing complex knowledge representations'
    }
    
    if p_number in TITLE_OVERRIDES:
        p_title = TITLE_OVERRIDES[p_number]
    else:
        # Smart Sentence Case:
        # If ALL CAPS, capitalize. Using a strict check to avoid messing up mixed case.
        # Remove non-alpha chars to check "isupper" purely on letters.
        letters = re.sub(r'[^a-zA-Z]', '', p_title)
        if letters and letters.isupper():
            p_title = p_title.capitalize()

    # --- LINK GENERATION ---
    # Google Patents: https://patents.google.com/patent/{Country}{CleanNumber}
    # Clean number: remove non-alphanumeric (like slashes in WO/...)
    clean_number = re.sub(r'[^A-Za-z0-9]', '', p_number)
    
    # Ensure country is valid (2 chars). If missing, we can't link effectively.
    if p_country:
        # Check if number already starts with country (e.g. WO/...)
        # We ignore case for check, assuming country is usually uppercase
        if clean_number.upper().startswith(p_country.upper()):
            link = f"https://patents.google.com/patent/{clean_number}"
        else:
            link = f"https://patents.google.com/patent/{p_country}{clean_number}"
    else:
        # Fallback to WIPO search if no country
        link = f"https://patentscope.wipo.int/search/en/result.jsf?queryString={p_number}"

    patents.append({
        'index': p_index,
        'number': p_number,
        'title': p_title,
        'country': p_country,
        'date': p_date,
        'link': link
    })


print(f"Parsed {len(patents)} patents")
with open(JSON_FILE, 'w', encoding='utf-8') as f:
    json.dump(patents, f, indent=2)

