import os
import argparse
import subprocess
import random
import time
import shutil
import requests
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from fake_useragent import UserAgent
import undetected_chromedriver as uc

# === Config and Directories ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
INPUT_DIR = os.path.join(DATA_DIR, "input")
OUTPUT_DIR = os.path.join(DATA_DIR, "output")
LOG_DIR = os.path.join(DATA_DIR, "logs")

for d in [INPUT_DIR, OUTPUT_DIR, LOG_DIR]:
    os.makedirs(d, exist_ok=True)

PROXY_INPUT_FILE = os.path.join(INPUT_DIR, "proxies.txt")
VALID_PROXIES_FILE = os.path.join(OUTPUT_DIR, "valid_proxies_checked.txt")
BAD_PROXIES_FILE = os.path.join(OUTPUT_DIR, "bad_proxies.txt")
HISTORY_LOG_FILE = os.path.join(LOG_DIR, "valid_proxies_history.txt")
PROCESSED_LOG = os.path.join(LOG_DIR, "processed_proxies.txt")

REMAINING_FILE_PATTERN = os.path.join(OUTPUT_DIR, "proxyz_remaining_{}.txt")

STARTER_URL = "https://cikgumall.com/aff/BiteBloom"
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

# === Proxy Functions ===

def fetch_proxies():
    print("[*] Running ProxyScrape.py...")
    subprocess.run(["python", "proxy_tools/ProxyScrape.py"], check=True)

def validate_proxy(proxy, timeout=4):
    proxy_types = [f"http://{proxy}", f"https://{proxy}", f"socks5h://{proxy}"]
    for proxy_url in proxy_types:
        try:
            res = requests.get("http://httpbin.org/ip", proxies={"http": proxy_url, "https": proxy_url}, timeout=timeout)
            if res.status_code == 200:
                return True
        except:
            continue
    return False

def test_proxy_http(proxy):
    try:
        r = requests.get("http://www.gstatic.com/generate_204", proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"}, timeout=8)
        return r.status_code == 204
    except:
        return False

def manual_check_batch(batch, batch_num):
    good, bad = [], []
    print(f"[Batch {batch_num}] Manual checking...")

    def check(proxy, index):
        if validate_proxy(proxy) or test_proxy_http(proxy):
            good.append(proxy)
        else:
            bad.append(proxy)
        if (index + 1) % 10 == 0 or index == len(batch) - 1:
            print(f"    - Checked {index + 1}/{len(batch)} proxies manually...")

    with ThreadPoolExecutor(max_workers=300) as executor:
        futures = {executor.submit(check, p, i): p for i, p in enumerate(batch)}
        for _ in as_completed(futures): pass

    return good, bad

def run_checker_subprocess(batch, batch_index):
    temp_file = REMAINING_FILE_PATTERN.format(batch_index)
    with open(temp_file, "w") as f:
        for p in batch:
            f.write(p + "\n")

    result = subprocess.run([
        "python", "proxy_tools/proxyChecker.py",
        "-p", "http", "-t", "10", "-s", STARTER_URL,
        "-l", temp_file
    ], capture_output=True, text=True)

    good = []
    if result.returncode == 0:
        good = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    else:
        print(f"[!] proxyChecker.py failed on batch {batch_index}: {result.stderr}")

    return good

def scrape_and_check(sample_limit=None):
    fetch_proxies()

    all_proxies = set()
    for path in [PROXY_INPUT_FILE, HISTORY_LOG_FILE]:
        if os.path.exists(path):
            with open(path, 'r') as f:
                all_proxies.update(line.strip() for line in f if line.strip())

    if os.path.exists(PROCESSED_LOG):
        with open(PROCESSED_LOG, 'r') as f:
            all_proxies -= set(line.strip() for line in f if line.strip())

    all_proxies = list(all_proxies)
    if sample_limit:
        all_proxies = all_proxies[:sample_limit]

    print(f"[*] Validating {len(all_proxies)} proxies...")

    batch_size = 100
    final_good, final_bad = [], []

    for i in range(0, len(all_proxies), batch_size):
        batch = all_proxies[i:i+batch_size]
        batch_num = i // batch_size + 1

        good1, bad1 = manual_check_batch(batch, batch_num)
        remaining = list(set(batch) - set(good1))

        print("[*] Running proxyChecker.py in parallel for remaining proxies...")
        good2 = run_checker_subprocess(remaining, batch_num)

        good = list(set(good1 + good2))
        bad = list(set(batch) - set(good))

        final_good.extend(good)
        final_bad.extend(bad)

        # Write batch outputs
        with open(VALID_PROXIES_FILE, 'a') as f:
            for p in good:
                f.write(p + "\n")
        with open(HISTORY_LOG_FILE, 'a') as f:
            for p in good:
                f.write(p + "\n")
        with open(BAD_PROXIES_FILE, 'a') as f:
            for p in bad:
                f.write(p + "\n")
        with open(PROCESSED_LOG, 'a') as f:
            for p in batch:
                f.write(p + "\n")

        print(f"[✓] Finished: {len(good)} good proxies, {len(bad)} bad proxies")

    print("[✓] All batches complete.")
    return list(set(final_good))

def simulate_visit_with_proxy(proxy, target_url):
    ua = UserAgent()
    error_keywords = [
        "ERR_TIMED_OUT",
        "ERR_CONNECTION_RESET",
        "ERR_TUNNEL_CONNECTION_FAILED",
        "ERR_EMPTY_RESPONSE"
    ]

    try:
        chrome_options = uc.ChromeOptions()
        chrome_options.add_argument(f"--user-agent={ua.random}")
        chrome_options.add_argument(f"--proxy-server=http://{proxy}")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--incognito")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--allow-insecure-localhost")

        print(f"[→] Launching Chrome with proxy {proxy}")
        driver = uc.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)

        # Visit starter page
        driver.get(STARTER_URL)
        time.sleep(random.uniform(2, 5))

        # Check for errors on starter page
        page_source = driver.page_source
        if any(err in page_source for err in error_keywords):
            print(f"[x] Proxy {proxy} failed on STARTER page due to network error.")
            driver.quit()
            return False

        # Visit target
        driver.get(target_url)
        time.sleep(random.uniform(5, 8))

        # Check for errors again
        page_source = driver.page_source
        if any(err in page_source for err in error_keywords):
            print(f"[x] Proxy {proxy} failed on TARGET page due to network error.")
            driver.quit()
            return False

        for _ in range(random.randint(3, 6)):
            driver.execute_script("window.scrollBy(0, window.innerHeight / 2);")
            time.sleep(random.uniform(1, 2))

        wait_time = random.randint(10, 15)
        print(f"[✓] Stayed {wait_time}s on {target_url}")
        time.sleep(wait_time)
        driver.quit()

        with open(LOG_FILE_PATH, "a") as f:
            f.write(proxy + "\n")

        return True

    except Exception as e:
        print(f"[!] Visit failed with proxy {proxy}: {e}")
        try:
            driver.quit()
        except:
            pass
        return False

def run_visits(proxies, total_visits=100):
    def visit_job():
        for i in range(total_visits):
            proxy = random.choice(proxies)
            url = random.choice(TARGET_URLS)
            print(f"\n[Visit {i+1}/{total_visits}] Using {proxy}")
            simulate_visit_with_proxy(proxy, url)
            time.sleep(random.randint(5, 8))

    t = threading.Thread(target=visit_job)
    t.start()
    t.join()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sample', type=int, help="Limit number of proxies to test for quick debugging")
    args = parser.parse_args()

    good_proxies = scrape_and_check(sample_limit=args.sample)
    
    # Check by file if runtime list is unexpectedly empty
    if not good_proxies:
        if os.path.exists(VALID_PROXIES_FILE):
            with open(VALID_PROXIES_FILE, 'r') as f:
                good_proxies = [line.strip() for line in f if line.strip()]
            print(f"[!] Loaded {len(good_proxies)} proxies from saved file instead.")
    
    if not good_proxies:
        print("[!] No good proxies available to run visit simulation.")
        return

    print(f"[✓] Total {len(good_proxies)} valid proxies found. Starting visit simulation...")
    run_visits(good_proxies)

    # Deduplicate history log
    if os.path.exists(HISTORY_LOG_FILE):
        with open(HISTORY_LOG_FILE, 'r') as f:
            unique = sorted(set(line.strip() for line in f if line.strip()))
        with open(HISTORY_LOG_FILE, 'w') as f:
            for line in unique:
                f.write(line + "\n")
        print(f"[*] Updated {HISTORY_LOG_FILE} with {len(unique)} unique entries.")


if __name__ == "__main__":
    main()


#python AffClicker_w_ProxyChecker.py --sample 100
