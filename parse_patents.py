
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
    
    if 'class="s1"' not in row:
        continue
    
    # Extract ID, Number, Title
    # Pattern: Digit dot, span, number, close span, title
    # We use non-greedy matches
    # Regex breakdown:
    # (\d+)\.  -> Group 1: Index (e.g. 1.)
    # <span[^>]*>(.*?)</span> -> Group 2: Number (inside span)
    # (.*?)</p> -> Group 3: Title (until end of paragraph)
    
    m_main = re.search(r'(\d+)\.<span[^>]*>(.*?)</span>(.*?)</p>', row, re.DOTALL)
    if not m_main:
        continue
    
    index = m_main.group(1).strip()
    number = m_main.group(2).strip()
    title = m_main.group(3).strip()
    
    # Clean title: remove newlines/extra spaces
    title = re.sub(r'\s+', ' ', title).strip()
    
    # Smart Sentence Case:
    # 1. If title is ALL CAPS, convert to sentence case (capitalize first, lower rest).
    # 2. If title is Mixed Case, preserve it (it might contain correct acronyms).
    if title and title.isupper():
        title = title.capitalize()

    
    # Extract Country and Date
    # Pattern: <p class="p2">US - 10.03.2011</p>
    # We look for [A-Z]{2} - [Digit/Dot]
    m_data = re.search(r'<p[^>]*>([A-Z]{2})\s+-\s+(\d{2}\.\d{2}\.\d{4})</p>', row)
    country = ""
    date = ""
    if m_data:
        country = m_data.group(1)
        date = m_data.group(2)
    
    
    # Construct WIPO link
    # Using a search query for the patent number is robust
    link = f"https://patentscope.wipo.int/search/en/result.jsf?queryString={number}"
    
    patents.append({
        'index': index,
        'number': number,
        'title': title,
        'country': country,
        'date': date,
        'link': link
    })


print(f"Parsed {len(patents)} patents")
with open(JSON_FILE, 'w', encoding='utf-8') as f:
    json.dump(patents, f, indent=2)

