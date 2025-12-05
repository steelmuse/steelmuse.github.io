import re
import os
import json
import ssl
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

RSS_URL = "https://patentscope.wipo.int/search/en/6f0ed051-6416-4af0-a6cb-79cd7d8b07b2/rss.xml"
RSS_FILE = 'Resources/patents.xml'
JSON_FILE = 'src/data/patents.json'
DOCX_FILE = 'Resources/Peter Sweeney Patents.docx' # Keep for reference

# Ensure output directory exists
os.makedirs(os.path.dirname(JSON_FILE), exist_ok=True)
os.makedirs(os.path.dirname(RSS_FILE), exist_ok=True)

# 1. Fetch RSS Feed
print(f"Downloading RSS feed from {RSS_URL}...")
try:
    # Use unverified context to avoid SSL certificate issues
    context = ssl._create_unverified_context()
    with urllib.request.urlopen(RSS_URL, context=context) as response, open(RSS_FILE, 'wb') as out_file:
        data = response.read()
        out_file.write(data)
    print("Download complete.")
except Exception as e:
    print(f"Error downloading RSS feed: {e}")
    # If download fails, we might still want to try parsing the existing file if it exists
    if not os.path.exists(RSS_FILE):
        print("No local RSS file available. Exiting.")
        exit(1)
    print("Using existing local RSS file.")

print(f"Parsing RSS: {RSS_FILE}")

try:
    tree = ET.parse(RSS_FILE)
    root = tree.getroot()
except ET.ParseError as e:
    print(f"Error parsing XML: {e}")
    exit(1)

# Namespaces in RSS usually: <rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/">
namespaces = {'dc': 'http://purl.org/dc/elements/1.1/'}

patents = []
# RSS 2.0 structure: <rss><channel><item>...
channel = root.find('channel')
if channel is None:
    print("Error: No channel found in RSS")
    exit(1)
    
items = channel.findall('item')

idx = 1
for item in items:
    p = {}
    
    # Title
    title_elem = item.find('title')
    title = title_elem.text if title_elem is not None else ""
    title = title.strip() if title else ""
    # Clean title
    title = re.sub(r'\s+', ' ', title).strip()
    
    # Date
    pub_date_elem = item.find('pubDate')
    pub_date_str = pub_date_elem.text if pub_date_elem is not None else ""
    p_date = ""
    if pub_date_str:
        try:
            # Parse: Thu, 10 Mar 2011 09:00:00 GMT
            # We strip GMT just in case '%Z' is tricky across platforms without strict timezone libs
            clean_date_str = pub_date_str.replace(" GMT", "").strip()
            dt = datetime.strptime(clean_date_str, "%a, %d %b %Y %H:%M:%S")
            # Format: DD.MM.YYYY
            p_date = dt.strftime("%d.%m.%Y")
        except ValueError:
            # Fallback or try with %Z if system supports
            try:
                dt = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %Z")
                p_date = dt.strftime("%d.%m.%Y")
            except:
                pass

    # Identifier / Number / Country
    # <dc:identifier>US12345</dc:identifier>
    # There can be multiple.
    ids = item.findall('dc:identifier', namespaces)
    if not ids:
        continue
        
    id_texts = []
    for x in ids:
        if x.text:
            id_texts.append(x.text.strip())
            
    if not id_texts:
        continue
    
    # Strategy: Look for WO/, US20..., or take the last one.
    vocab_id = id_texts[-1] # Default to last
    
    # Iterate to find better candidate
    # Priority: starts with WO/ -> High
    # Priority: starts with US20 (Publication) -> High
    for i in id_texts:
        if i.startswith("WO/"):
            vocab_id = i
            break
        if i.startswith("US20") and len(i) > 10:
             vocab_id = i
             # Keep looking if we find a WO later? Unlikely for same item.
             
    # Extract Country Code (First 2 chars)
    country = vocab_id[:2].upper()
    
    # Extract Number
    number = vocab_id
    if country == "WO":
        number = vocab_id # Keep WO/YYYY/NNNN
    else:
        # Check if number starts with country code (e.g. US2011...)
        if number.upper().startswith(country):
            number = number[len(country):]

    # --- TITLE CORRECTION ---
    TITLE_OVERRIDES = {
        '223540': 'Systems of computerized agents and user-directed semantic networking',
        '227140': 'System and method for performing a semantic operation on a digital social network',
        '248313': 'Preference guided data exploration and semantic processing',
        '227201': 'Methods and device for providing information of interest to one or more users',
        '227139': 'System and method for using knowledge representation to provide information based on environmental input',
        '223541': 'Systems and methods for analyzing and synthesizing complex knowledge representations'
    }
    
    if number in TITLE_OVERRIDES:
        title = TITLE_OVERRIDES[number]
    else:
        # Smart Sentence Case logic
        letters = re.sub(r'[^a-zA-Z]', '', title)
        if letters and letters.isupper():
            title = title.capitalize()

    # --- LINK EXTRACTION ---
    # Use the link provided in the RSS feed as requested
    link_elem = item.find('link')
    link = link_elem.text.strip() if link_elem is not None and link_elem.text else ""
    
    # Fallback only if missing (shouldn't happen per user)
    if not link:
         clean_number = re.sub(r'[^A-Za-z0-9]', '', number)
         if country:
             if clean_number.upper().startswith(country):
                link = f"https://patents.google.com/patent/{clean_number}"
             else:
                 link = f"https://patents.google.com/patent/{country}{clean_number}"
         else:
             link = f"https://patentscope.wipo.int/search/en/result.jsf?queryString={number}"

    p['index'] = str(idx)
    p['number'] = number
    p['title'] = title
    p['country'] = country
    p['date'] = p_date
    p['link'] = link
    
    patents.append(p)
    idx += 1

print(f"Parsed {len(patents)} patents")
with open(JSON_FILE, 'w', encoding='utf-8') as f:
    json.dump(patents, f, indent=2)
