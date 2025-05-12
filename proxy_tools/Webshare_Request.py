import os
import requests

# === Configuration ===
TOKEN = "20re8ri629n16nk718m1fj61q7busf95b043k0t0"
PROXY_SAVE_PATH = "./data/input/proxies.txt"
REFRESH_FIRST = True  # Set to False if you don't want to refresh before downloading

# === Functions ===
def refresh_proxy_list():
    print("[*] Refreshing proxy list...")
    response = requests.post(
        "https://proxy.webshare.io/api/v2/proxy/list/refresh/",
        headers={"Authorization": f"Token {TOKEN}"}
    )
    if response.status_code == 204:
        print("[✓] Proxy list refreshed successfully.")
    else:
        print("[✗] Failed to refresh proxy list:", response.status_code, response.text)

def download_proxy_list():
    print("[*] Downloading proxy list...")
    url = f"https://proxy.webshare.io/api/v2/proxy/list/download/jrdtdufojdsasvlhuvrftmdnwskxbvgmouoculej/-/any/username/direct/-/"
    response = requests.get(url)

    if response.status_code == 200:
        os.makedirs(os.path.dirname(PROXY_SAVE_PATH), exist_ok=True)
        with open(PROXY_SAVE_PATH, "w") as f:
            f.write(response.text)
        print(f"[✓] Proxies saved to {PROXY_SAVE_PATH}")
    else:
        print("[✗] Failed to download proxies:", response.status_code, response.text)

# === Main Execution ===
if __name__ == "__main__":
    if REFRESH_FIRST:
        refresh_proxy_list()
    download_proxy_list()
