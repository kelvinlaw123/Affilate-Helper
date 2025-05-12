import undetected_chromedriver as uc
import time
import os

# Setup headless browser
options = uc.ChromeOptions()
options.headless = True  # run in background
options.add_argument("--window-size=1920,1080")
prefs = {"profile.managed_default_content_settings.images": 2}
options.add_experimental_option("prefs", prefs)

driver = uc.Chrome(options=options)
driver.get("https://proxiware.com/free-proxy-list")
time.sleep(5)

# Inject scraping script
js_script = r"""
window.collectedProxies = [];
function delay(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }

function scrapePage(page = 0) {
  if (page >= 10) return;

  const rows = Array.from(document.querySelectorAll('td'));
  for (let i = 0; i < rows.length - 1; i++) {
    const ip = rows[i].innerText.trim();
    const port = rows[i + 1].innerText.trim();
    if (/^\d+\.\d+\.\d+\.\d+$/.test(ip) && /^\d+$/.test(port)) {
      window.collectedProxies.push(`${ip}:${port}`);
    }
  }

  const nextBtn = document.querySelector('.next-button');
  if (nextBtn) {
    nextBtn.click();
    setTimeout(() => scrapePage(page + 1), 1500);
  }
}

document.querySelector('#speedSelect').value = 'fast';
document.querySelector('#speedSelect').dispatchEvent(new Event('change'));
setTimeout(() => scrapePage(), 1000);
"""



driver.execute_script(js_script)
time.sleep(20)  # wait for scraping to finish

# Get result
proxies = driver.execute_script("return window.collectedProxies;")
output_path = r"C:\Users\Nzettodess\Downloads\Affilate Clicker\data\input\proxies.txt"

if proxies:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write("\n".join(proxies))
    print(f"Saved {len(proxies)} proxies to {output_path}")
else:
    print("No proxies found!")

driver.quit()
