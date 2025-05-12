import requests
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse
import json

def analyze_tracking(url):
    # Part 1: Basic HTML analysis
    print("[+] Analyzing HTML structure...")
    response = requests.get(url)
    
    # Check for common tracking parameters in HTML
    tracking_indicators = {
        'google-analytics': ['ga.js', 'analytics.js', 'gtag.js'],
        'facebook': ['facebook.net', 'fbpixel'],
        'matomo': ['matomo.js'],
        'advertising': ['googletagmanager.com', 'doubleclick.net']
    }
    
    for line in response.text.split('\n'):
        for key, indicators in tracking_indicators.items():
            if any(indicator in line for indicator in indicators):
                print(f"⚠️ Found {key.upper()} tracking in HTML: {line.strip()}")
    
    # Part 2: Browser-based analysis with network monitoring
    print("\n[+] Launching browser for deep analysis...")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        
        # Capture all network requests
        def log_request(request):
            if any(ext in request.url for ext in ['collect', 'pixel', 'track', 'log']):
                print(f"🔗 Tracking Request: {request.method} {request.url}")
                print(f"   Headers: {json.dumps(request.headers, indent=2)}")
                if request.post_data:
                    print(f"   POST Data: {request.post_data}")
        
        page.on("request", log_request)
        
        page.goto(url)
        
        # Check for cookies
        cookies = context.cookies()
        if cookies:
            print("\n🍪 Cookies Found:")
            for cookie in cookies:
                if any(key in cookie['name'] for key in ['_ga', '_gid', '_gat', 'session', 'track']):
                    print(f"  🔍 Tracking Cookie: {cookie['name']} (Domain: {cookie['domain']})")
        
        # Check localStorage
        storage = page.evaluate("() => JSON.stringify(window.localStorage)")
        if storage != '{}':
            print("\n📦 LocalStorage Contents:")
            print(json.dumps(json.loads(storage), indent=2)
            )
        # Check for common analytics frameworks
        analytics_detected = page.evaluate('''() => {
            const indicators = {
                'Google Analytics': typeof ga !== 'undefined',
                'Google Tag Manager': typeof google_tag_manager !== 'undefined',
                'Facebook Pixel': typeof fbq !== 'undefined',
                'Matomo': typeof _paq !== 'undefined',
                'Hotjar': typeof hj !== 'undefined'
            };
            return indicators;
        }''')
        
        print("\n📊 Analytics Detection Results:")
        for service, detected in analytics_detected.items():
            status = "✅ Detected" if detected else "❌ Not found"
            print(f"  {service}: {status}")
        
        browser.close()

    # Part 3: Header analysis
    print("\n[+] Analyzing response headers...")
    security_headers = ['Content-Security-Policy', 'X-Content-Type-Options', 
                       'Strict-Transport-Security', 'X-Frame-Options']
    for header in security_headers:
        value = response.headers.get(header)
        print(f"  {header}: {value or 'Not present'}")

if __name__ == "__main__":
    target_url = input("Enter URL to analyze: ")
    analyze_tracking(target_url)