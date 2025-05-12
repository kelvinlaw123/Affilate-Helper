# Affiliate-Helper

**Affiliate-Helper** is an automation tool designed to simulate real web traffic through affiliate URLs. It scrapes public proxies and performs automated visits to your custom affiliate links using GitHub Actions or Windows Task Scheduler. This tool is best used on affiliate systems that do not implement strong bot detection or use headless-resistant tracking (like Google Analytics, Cloudflare, etc.).

---

## 🚀 Features

- ✅ Automatically scrape fresh proxies from public sources
- ✅ Run headless traffic simulations using aiohttp and Selenium
- ✅ Schedule automated visits via GitHub Actions or locally on Windows
- ✅ No server required – runs entirely on GitHub or Windows Task Scheduler
- ✅ Easy to customize with your own target and start URLs

---

## 🧠 Disclaimer

This tool is for **educational and testing purposes only**. Do not use this tool for malicious or fraudulent activities. The developers are not responsible for any misuse of this software.

---

## ⚠️ Requirements

- Public websites with minimal bot protection
- No JavaScript-based tracking or advanced CAPTCHA
- Optional: Your own proxy list (`data/input/proxies.txt`)

---

## 🛠️ Setup Instructions

### 1. Fork the Repository

Click the `Fork` button on GitHub and create your own copy of this project.

### 2. Customize URLs

Edit the `AffClicker_w_Aiohttp.py` file and set:

```python
STARTER_URL = "https://yourdomain.com/start/aff/yourrff"
TARGET_URL = "https://affiliate.network.com/aff/yourrff"
```
You can replace "yourrff" in the STARTER_URL and TARGET_URL with your actual referral code.

### 3. (Optional) Add Your Own Proxies
Place your proxy list inside the file: data/input/proxies.txt

Format: one proxy per line, in either ip:port or user:pass@ip:port format.

#### 🔄 Automation Options
##### Option A: GitHub Actions (Cloud Automation)
GitHub Actions is preconfigured to run every 60 minutes.

###### 📌 Limits

GitHub Free plan includes 2,000 minutes/month. Consider switching to local automation after reaching the limit.


To Enable:
1. Go to the Actions tab in your forked repo 

2. Click "Enable workflows"

3. Monitor logs via GitHub Actions UI


##### Option B: Windows Task Scheduler (Local Automation)

1. Import the pre-made scheduler: Local Run\Run Affiliate Helper.xml

2. Edit the .xml file or scheduled task to:  Run every 10 minutes

3. Use run_minimized.vbs instead of directly calling the .bat (to start minimized)

4. Update file paths: Make sure absolute/path/to/your/run_minimized.vbs is correctly set in Task Scheduler

5. Inside the .bat and .vbs, update:
```python
set BASE_DIR=absolute\path\to\your\Repo\Affilate Helper
```

## 🧪 Run Locally (Manual)
Install Python 3.9+ and dependencies:

```bash
pip install -r requirements.txt
```
```bash
python proxy_tools/GitScraping.py
python AffClicker_w_Aiohttp.py
```

## 📄 License

This project is licensed under the [Apache License 2.0](LICENSE).


## 🙋 FAQ
Q: Can I use this on my own affiliate links?

A: Yes, just edit the URLs in the Python script.

Q: Can I use my own proxies?

A: Yes, just paste them in data/input/proxies.txt.

## 💬 Contact
Feel free to open an issue or PR if you'd like to contribute or ask questions.
