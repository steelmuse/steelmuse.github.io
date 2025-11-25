import requests

def check_redirects(url):
    try:
        # We pretend to be a standard browser to see how the server responds
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'}
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"Testing: {url}")
        print("-" * 40)
        
        # Print every step in the redirect chain
        if response.history:
            for i, step in enumerate(response.history):
                print(f"Step {i+1}: {step.status_code} -> {step.url}")
            print(f"Final : {response.status_code} -> {response.url}")
        else:
            print(f"No redirects. Status: {response.status_code}")
            
    except Exception as e:
        print(f"Error reaching {url}: {e}")
    print("\n")

# Test all variations to find the loop
check_redirects("http://steelmuse.com")
check_redirects("http://www.steelmuse.com")
check_redirects("https://steelmuse.com")
check_redirects("https://www.steelmuse.com")
