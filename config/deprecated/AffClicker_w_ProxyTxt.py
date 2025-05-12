import argparse
import requests
import random
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import undetected_chromedriver as uc
from fake_useragent import UserAgent

# Config
STARTER_URL = "https://cikgumall.com/aff/BiteBloom"
PROXY_FILE_PATH = r"C:\Users\Nzettodess\Downloads\Affilate Clicker\data\input\proxies.txt"
LOG_FILE_PATH = r"C:\Users\Nzettodess\Downloads\Affilate Clicker\data\logs\valid_proxies_history.txt"
VISITS_PER_PROXY = 5  # Number of visits per valid proxy with different user-agents

TARGET_URLS = [
    "https://cikgumall.com/product/tvia-kordial-buah-asli-1-liter/aff/BiteBloom",
    "https://cikgumall.com/product/ryverra-panned-chocolate-40g/aff/BiteBloom",
    "https://cikgumall.com/product/premium-lite-edition-brownies-cookies-cocoa-bakers/aff/BiteBloom",
    "https://cikgumall.com/product/nyambal-sambal-ikan-masin/aff/BiteBloom",
    "https://cikgumall.com/aff/BiteBloom",
    "https://cikgumall.com/product/hotel-toiletries-by-anastays/aff/BiteBloom",
    "https://cikgumall.com/product/mrs-refreshing-scent-mini-pack-10ml/aff/BiteBloom",
    "https://cikgumall.com/product/teega-crispy-machos-salted-100g-2/aff/BiteBloom",
    "https://cikgumall.com/product/estana-tiramisu-choco-dates-milk-chocolate-150g/aff/BiteBloom",
    "https://cikgumall.com/product/estana-bar-chocolate-45g/aff/BiteBloom",
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

def validate_proxy(proxy, timeout=6):
    proxy_schemes = {
        "socks5": f"socks5h://{proxy}",
        "socks4": f"socks4://{proxy}",
        "http": f"http://{proxy}",
        "https": f"https://{proxy}"
    }
    for protocol, proxy_url in proxy_schemes.items():
        try:
            proxies = {"http": proxy_url, "https": proxy_url}
            res = requests.get("https://cikgumall.com/aff/BiteBloom", proxies=proxies, timeout=timeout)
            if res.status_code == 200:
                print(f"[✓] {protocol.upper()} proxy works: {proxy} → {res.json()['origin']}")
                return protocol
        except Exception:
            continue
    print(f"[x] Proxy {proxy} failed all protocols.")
    return None

def simulate_visit_worker(proxy, target_urls, visits_per_proxy):
    success_count = 0
    for _ in range(visits_per_proxy):
        url = random.choice(target_urls)
        success = simulate_visit_with_proxy(proxy, url)
        if not success:
            print(f"[!] Proxy {proxy} failed during visit. Halting further visits.")
            return success_count  # Stop using this proxy if failure occurs
        success_count += 1
    return success_count

def simulate_visit_with_proxy(proxy, target_url, user_agent):
    error_keywords = [
        "ERR_TIMED_OUT", "ERR_CONNECTION_RESET",
        "ERR_TUNNEL_CONNECTION_FAILED", "ERR_EMPTY_RESPONSE"
    ]
    server_debug_signatures = [
        "REMOTE_ADDR", "REQUEST_METHOD", "REQUEST_URI", "HTTP_USER_AGENT"
    ]

    try:
        chrome_options = uc.ChromeOptions()
        chrome_options.add_argument(f"--user-agent={user_agent}")
        chrome_options.add_argument(f"--proxy-server=http://{proxy}")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--incognito")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--allow-insecure-localhost")
        chrome_options.add_argument("--headless=new")

        print(f"[→] Launching Chrome with proxy {proxy} and user-agent: {user_agent}")
        driver = uc.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)

        driver.get(STARTER_URL)
        time.sleep(random.uniform(2, 5))
        if any(err in driver.page_source for err in error_keywords):
            print(f"[x] Proxy {proxy} failed on STARTER page.")
            driver.quit()
            return False
        if any(sig in driver.page_source for sig in server_debug_signatures):
            print(f"⚠️ Proxy {proxy} hit debug/info dump page.")
            driver.quit()
            return False

        driver.get(target_url)
        time.sleep(random.uniform(5, 8))
        if any(err in driver.page_source for err in error_keywords):
            print(f"[x] Proxy {proxy} failed on TARGET page.")
            driver.quit()
            return False

        for _ in range(random.randint(3, 6)):
            driver.execute_script("window.scrollBy(0, window.innerHeight / 2);")
            time.sleep(random.uniform(1, 2))

        wait_time = random.randint(10, 15)
        print(f"[✓] Stayed {wait_time}s on {target_url}")
        time.sleep(wait_time)
        driver.quit()
        return True

    except Exception as e:
        print(f"[!] Visit failed with proxy {proxy}: {e}")
        try:
            driver.quit()
        except:
            pass
        return False

def run_parallel_visits(all_proxies, target_urls, workers=500):
    print("[*] Validating proxies in parallel...")
    validated = []
    ua = UserAgent()

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(validate_proxy, p): p for p in all_proxies}
        for future in as_completed(futures):
            protocol = future.result()
            if protocol:
                validated.append(futures[future])

    print(f"[✓] Found {len(validated)} working proxies.")
    total_valid_proxies = len(validated)
    total_attempts = 0
    total_successes = 0

    for proxy in validated:
        for _ in range(VISITS_PER_PROXY):
            user_agent = ua.random
            target = random.choice(target_urls)
            success = simulate_visit_with_proxy(proxy, target, user_agent)
            total_attempts += 1
            if success:
                total_successes += 1
            else:
                break  # Stop using this proxy if it fails once

        print(f"\n[📊 STATS]")
        print(f"  Total working proxies: {total_valid_proxies}")
        print(f"  Visit progress: {total_attempts}")
        print(f"  Successful visits (no error/debug): {total_successes}\n")

        if total_successes >= total_valid_proxies * VISITS_PER_PROXY:
            break  # Early exit if desired count is met

    print("[✔] Visit simulation completed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=500, help="Concurrent threads for validating and visiting")
    args = parser.parse_args()

    all_proxies = load_proxies(PROXY_FILE_PATH)
    random.shuffle(all_proxies)
    print(f"[*] Loaded {len(all_proxies)} total proxies.")
    run_parallel_visits(all_proxies, TARGET_URLS, workers=args.workers)
