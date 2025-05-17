import argparse
import asyncio
import sys
import random
import time
import os
import logging
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
import aiohttp
from aiohttp import BasicAuth
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

# Create logs folder if not exists
os.makedirs("logs", exist_ok=True)

# Log file name with timestamp
log_filename = datetime.now().strftime("Local Run/logs/run_%Y%m%d_%H%M%S.log")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)  # output to CMD
    ]
)

# Suppress asyncio SSLProtocol noisy errors
logging.getLogger('asyncio').setLevel(logging.CRITICAL)

# Fix for Windows compatibility with aiodns
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Config
STARTER_URL = "https://cikgumall.com/aff/4212"
PROXY_FILE_PATH = "data/input/proxies.txt"
LOG_FILE_PATH = "data/logs/valid_proxies_history.txt"
VISITS_PER_PROXY = 1  # Number of visits per valid proxy with different user-agents

TARGET_URLS = [
    "https://cikgumall.com/product/tvia-kordial-buah-asli-1-liter/aff/4212",
    "https://cikgumall.com/product/ryverra-panned-chocolate-40g/aff/4212",
    "https://cikgumall.com/product/premium-lite-edition-brownies-cookies-cocoa-bakers/aff/4212",
    "https://cikgumall.com/product/nyambal-sambal-ikan-masin/aff/4212",
    "https://cikgumall.com/aff/4212",
    "https://cikgumall.com/product/hotel-toiletries-by-anastays/aff/4212",
    "https://cikgumall.com/product/mrs-refreshing-scent-mini-pack-10ml/aff/4212",
    "https://cikgumall.com/product/teega-crispy-machos-salted-100g-2/aff/4212",
    "https://cikgumall.com/product/estana-tiramisu-choco-dates-milk-chocolate-150g/aff/4212",
    "https://cikgumall.com/product/estana-bar-chocolate-45g/aff/4212",
]

def load_proxies(path):
    proxies = set()
    if os.path.exists(path):
        with open(path, 'r') as file:
            proxies.update(line.strip() for line in file if line.strip())
    if os.path.exists(LOG_FILE_PATH):
        with open(LOG_FILE_PATH, 'r') as file:
            proxies.update(line.strip() for line in file if line.strip())
    return list(proxies)

async def validate_proxy_async(session, proxy):
    parts = proxy.strip().split(":")
    
    # Authenticated proxy (username:password)
    if len(parts) == 4:
        ip, port, user, pwd = parts
        proxy_url = f"http://{ip}:{port}"
        auth = BasicAuth(user, pwd)
        try:
            async with session.get(
                "https://cikgumall.com/aff/4212",
                proxy=proxy_url,
                proxy_auth=auth,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as res:
                if res.status == 200:
                    print(f"[✓] Authenticated proxy works: {proxy_url}")
                    return proxy
        except Exception as e:
            print(f"[x] Authenticated proxy failed: {proxy_url} | {e}")
        return None

    # Unauthenticated proxy (no username:password)
    elif len(parts) == 2:
        ip, port = parts
        schemes = ["http", "https", "socks4", "socks5"]
        for scheme in schemes:
            proxy_url = f"{scheme}://{ip}:{port}"
            try:
                async with session.get(
                    "https://cikgumall.com/aff/4212",
                    proxy=proxy_url,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as res:
                    if res.status == 200:
                        print(f"[✓] Unauthenticated proxy works: {proxy_url}")
                        return proxy
            except Exception:
                continue
        print(f"[x] Proxy failed all schemes: {proxy}")
        return None

    else:
        print(f"[!] Invalid proxy format: {proxy}")
        return None

async def validate_proxies_async(proxies):
    validated = []
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [validate_proxy_async(session, proxy) for proxy in proxies]
        results = await asyncio.gather(*tasks)
        validated = [r for r in results if r]
    return validated

def setup_selenium_driver(proxy=None, user_agent=None):
    """Setup a Selenium driver with proper configurations to bypass Cloudflare"""
    options = Options()
    
    # Set user agent if provided
    if user_agent:
        options.add_argument(f'--user-agent={user_agent}')
    
    # Set proxy if provided
    if proxy:
        parts = proxy.strip().split(":")
        if len(parts) == 4:  # Authenticated proxy
            ip, port, username, password = parts
            manifest_json = """
            {
                "version": "1.0.0",
                "manifest_version": 2,
                "name": "Chrome Proxy",
                "permissions": [
                    "proxy",
                    "tabs",
                    "unlimitedStorage",
                    "storage",
                    "webRequest",
                    "webRequestBlocking"
                ],
                "background": {
                    "scripts": ["background.js"]
                }
            }
            """
            
            background_js = f"""
            var config = {{
                mode: "fixed_servers",
                rules: {{
                    singleProxy: {{
                        scheme: "http",
                        host: "{ip}",
                        port: parseInt({port})
                    }},
                    bypassList: []
                }}
            }};
            chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});
            function callbackFn(details) {{
                return {{
                    authCredentials: {{
                        username: "{username}",
                        password: "{password}"
                    }}
                }};
            }}
            chrome.webRequest.onAuthRequired.addListener(
                callbackFn,
                {{urls: ["<all_urls>"]}},
                ['blocking']
            );
            """
            
            # Create a proxy extension
            proxy_extension_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'proxy_extension')
            os.makedirs(proxy_extension_dir, exist_ok=True)
            
            with open(os.path.join(proxy_extension_dir, 'manifest.json'), 'w') as f:
                f.write(manifest_json)
            
            with open(os.path.join(proxy_extension_dir, 'background.js'), 'w') as f:
                f.write(background_js)
            
            options.add_extension(proxy_extension_dir)
        
        elif len(parts) == 2:  # Unauthenticated proxy
            ip, port = parts
            options.add_argument(f'--proxy-server=http://{ip}:{port}')
    
    # Standard options to help bypass detection
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--incognito")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Uncomment for headless mode (but sometimes Cloudflare can detect this)
    # options.add_argument("--headless=new")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # Apply stealth settings
    stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )
    
    return driver

def wait_for_cloudflare(driver, timeout=30):
    """Wait for Cloudflare challenge to be solved"""
    try:
        # First wait for Cloudflare challenge page (if it appears)
        try:
            cloudflare_detected = False
            
            # Look for common Cloudflare elements
            if "Just a moment" in driver.page_source or "Checking your browser" in driver.page_source:
                print("[⏳] Cloudflare challenge detected, waiting for it to pass...")
                cloudflare_detected = True
                
                # Wait a bit for CF to initialize its check
                time.sleep(5)
                
                # Wait for the Cloudflare challenge to disappear (max 25 seconds)
                start_time = time.time()
                while time.time() - start_time < 25:
                    if "Just a moment" not in driver.page_source and "Checking your browser" not in driver.page_source:
                        print("[✓] Cloudflare challenge passed!")
                        break
                    time.sleep(1)
            
            if not cloudflare_detected:
                print("[✓] No Cloudflare challenge detected")
                
        except Exception as e:
            print(f"[!] Error while waiting for Cloudflare: {e}")
        
        # Now wait for the actual page content to load
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        return True
    except Exception as e:
        print(f"[!] Timed out waiting for page to load: {e}")
        return False

def simulate_visit_with_selenium(proxy, target_url, user_agent):
    """Visit a website using Selenium with Cloudflare bypass capabilities"""
    try:
        print(f"[→] Launching Selenium with proxy {proxy} and user-agent: {user_agent}")
        driver = setup_selenium_driver(proxy, user_agent)
        
        # Visit the starter URL first
        driver.get(STARTER_URL)
        
        # Wait for Cloudflare to be bypassed
        if not wait_for_cloudflare(driver):
            print(f"[x] Failed to bypass Cloudflare for {STARTER_URL}")
            driver.quit()
            return False
        
        # Realistic delay
        time.sleep(random.uniform(3, 5))
        
        # Check for errors
        error_keywords = [
            "ERR_TIMED_OUT", "ERR_CONNECTION_RESET",
            "ERR_TUNNEL_CONNECTION_FAILED", "ERR_EMPTY_RESPONSE"
        ]
        server_debug_signatures = [
            "REMOTE_ADDR", "REQUEST_METHOD", "REQUEST_URI", "HTTP_USER_AGENT"
        ]
        
        if any(err in driver.page_source for err in error_keywords):
            print(f"[x] Proxy {proxy} failed on STARTER page.")
            driver.quit()
            return False
        if any(sig in driver.page_source for sig in server_debug_signatures):
            print(f"⚠️ Proxy {proxy} hit debug/info dump page.")
            driver.quit()
            return False
        
        # Visit the target URL
        driver.get(target_url)
        
        # Wait for Cloudflare to be bypassed on the target page
        if not wait_for_cloudflare(driver):
            print(f"[x] Failed to bypass Cloudflare for {target_url}")
            driver.quit()
            return False
        
        # Realistic delay
        time.sleep(random.uniform(4, 7))
        
        # Check for errors on target page
        if any(err in driver.page_source for err in error_keywords):
            print(f"[x] Proxy {proxy} failed on TARGET page.")
            driver.quit()
            return False
        
        # Simulate realistic user behavior
        # Scroll down the page
        for _ in range(random.randint(3, 6)):
            scroll_amount = random.randint(100, 500)
            driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(random.uniform(1, 2.5))
        
        # Sometimes scroll back up
        if random.random() > 0.7:
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(random.uniform(1, 2))
        
        # Stay on the page for a while
        wait_time = random.randint(15, 25)
        print(f"[✓] Stayed {wait_time}s on {target_url}")
        time.sleep(wait_time)
        
        # Sometimes click on page elements (if they exist)
        try:
            elements = driver.find_elements(By.TAG_NAME, "button")
            if elements and random.random() > 0.7:
                random_element = random.choice(elements)
                if random_element.is_displayed() and random_element.is_enabled():
                    driver.execute_script("arguments[0].scrollIntoView();", random_element)
                    time.sleep(0.5)
                    random_element.click()
                    time.sleep(random.uniform(2, 4))
        except Exception:
            pass  # Ignore errors when trying to click elements
        
        # Close the browser
        driver.quit()
        return True
        
    except Exception as e:
        print(f"[!] Visit failed with proxy {proxy}: {e}")
        try:
            driver.quit()
        except:
            pass
        return False

def run_parallel_visits(all_proxies, target_urls, workers=5):
    print("[*] Validating proxies asynchronously...")
    validated = asyncio.run(validate_proxies_async(all_proxies))

    print(f"[✓] Found {len(validated)} working proxies.")
    logging.info(f"[✓] Found {len(validated)} working proxies.")
    total_valid_proxies = len(validated)
    total_attempts = 0
    total_successes = 0

    ua = UserAgent()
    
    # Using a smaller thread pool due to the resource-intensive nature of Selenium
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_proxy = {}
        
        for proxy in validated:
            for _ in range(VISITS_PER_PROXY):
                user_agent = ua.random
                target = random.choice(target_urls)
                
                # Submit the task to the executor
                future = executor.submit(simulate_visit_with_selenium, proxy, target, user_agent)
                future_to_proxy[future] = proxy
                
                # Limit concurrent tasks to avoid overwhelming the system
                while len(future_to_proxy) >= workers:
                    for future in list(future_to_proxy.keys()):
                        if future.done():
                            success = future.result()
                            total_attempts += 1
                            if success:
                                total_successes += 1
                            future_to_proxy.pop(future)
                    time.sleep(0.5)
        
        # Wait for remaining tasks to complete
        for future in future_to_proxy:
            success = future.result()
            total_attempts += 1
            if success:
                total_successes += 1

    print(f"\n[📊 FINAL STATS]")
    print(f"  Total working proxies: {total_valid_proxies}")
    print(f"  Total visits attempted: {total_attempts}")
    print(f"  Successful visits (no error/debug): {total_successes}\n")
    logging.info(f"  Total working proxies: {total_valid_proxies}")
    logging.info(f"  Total visits attempted: {total_attempts}")
    logging.info(f"  Successful visits (no error/debug): {total_successes}\n")

    print("[✔] Visit simulation completed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=5, help="Concurrent threads for Selenium instances")
    args = parser.parse_args()

    all_proxies = load_proxies(PROXY_FILE_PATH)
    random.shuffle(all_proxies)
    print(f"[*] Loaded {len(all_proxies)} total proxies.")
    logging.info(f"[*] Loaded {len(all_proxies)} total proxies.")
    run_parallel_visits(all_proxies, TARGET_URLS, workers=args.workers)
    logging.info("=== Run ended ===\n")