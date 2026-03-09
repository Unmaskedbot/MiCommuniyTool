#!/usr/bin/python3

import os
import importlib

# ===== INSTALL REQUIRED LIBRARIES =====
while True:
    for lib in ["requests", "ntplib"]:
        try:
            importlib.import_module(lib)
        except ModuleNotFoundError:
            os.system(f"pip install {lib}")
            break
    else:
        break

import requests
import json
import time
import ntplib
from datetime import datetime, timedelta, timezone

# ==========================================
#            CONFIGURATION
# ==========================================

new_bbs_serviceToken = "YOUR_SERVICE_TOKEN_HERE"
deviceId = "YOUR_DEVICE_ID_HERE"

api = "https://api.vip.miui.com/mtop/planet/vip/member/"

User = "XiaomiCommunity/5.4.18 (Linux; Android 14)"

versionCode = "500418"
versionName = "5.4.18"

# ==========================================

U_apply = api + "apply/bl-auth"
U_info = api + "user/data"
U_state = api + "apply/bl-state"

headers = {
    "User-Agent": User,
    "Content-Type": "application/json",
    "Cookie": f"new_bbs_serviceToken={new_bbs_serviceToken};versionCode={versionCode};versionName={versionName};deviceId={deviceId};"
}

# ===== COLORS =====
CYAN="\033[96m"
GREEN="\033[92m"
YELLOW="\033[93m"
RED="\033[91m"
WHITE="\033[97m"
BOLD="\033[1m"
RESET="\033[0m"

print(f"""
{CYAN}{BOLD}╔══════════════════════════════════════╗
║        Xiaomi Community Unlock Permission Tool        ║
╚══════════════════════════════════════╝{RESET}
""")

# ==========================================
#           ACCOUNT INFO
# ==========================================

def account_info():

    try:

        info = requests.get(U_info, headers=headers).json()["data"]

        level = info["level_info"]["level"]
        title = info["level_info"]["level_title"]
        current = info["level_info"]["current_value"]
        maxv = info["level_info"]["max_value"]

        next_points = maxv - current

        print(f"""
{CYAN}{BOLD}╔══════════════════════════════════════╗
║             ACCOUNT INFO             ║
╠══════════════════════════════════════╣
║ Days in Community : {info['registered_day']}
║ Level             : LV{level} {title}
║ Points            : {current}
║ Points to Next LV : {next_points}
╚══════════════════════════════════════╝
{RESET}
""")

    except Exception as e:

        exit(f"{RED}Failed to get account info\n{e}{RESET}")

# ==========================================
#           ACCOUNT STATE
# ==========================================

def state_request():

    print(f"{GREEN}\nChecking account state...{RESET}")

    try:

        state = requests.get(U_state, headers=headers).json()["data"]

        is_pass = state.get("is_pass")
        button = state.get("button_state")
        deadline = state.get("deadline_format","")

        if is_pass == 1:

            exit(f"{GREEN}✔ Bootloader already unlocked until {deadline}{RESET}")

        if button == 1:
            print(f"{YELLOW}Account eligible for bootloader unlock{RESET}")

        elif button == 2:
            exit(f"{RED}Account error, try again after {deadline}{RESET}")

        elif button == 3:
            exit(f"{RED}Account must be older than 30 days{RESET}")

    except Exception as e:

        exit(f"{RED}State request error: {e}{RESET}")

# ==========================================
#           APPLY REQUEST
# ==========================================

def apply_request():

    print(f"\n{WHITE}[APPLY REQUEST]{RESET}")

    try:

        r = requests.post(U_apply,
                data=json.dumps({"is_retry": True}),
                headers=headers)

        print("Server Time:", r.headers.get("Date"))

        data = r.json()

        if data.get("code") != 0:
            exit(data)

        result = data["data"]["apply_result"]
        deadline = data["data"].get("deadline_format","")

        if result == 1:

            print(f"{GREEN}Application successful{RESET}")
            state_request()

        elif result == 3:

            print(f"{YELLOW}Daily quota reached. Retry tomorrow {deadline}{RESET}")
            return 1

        elif result == 4:

            exit(f"{RED}Account error. Try after {deadline}{RESET}")

        else:

            print(data)

    except Exception as e:

        exit(f"{RED}Apply error: {e}{RESET}")

# ==========================================
#           TIME FUNCTIONS
# ==========================================

def ntp_time():

    client = ntplib.NTPClient()

    servers = ["pool.ntp.org","time.google.com","time.windows.com"]

    for s in servers:

        try:

            r = client.request(s,version=3)

            return datetime.fromtimestamp(r.tx_time,timezone.utc)

        except:
            pass

    return datetime.now(timezone.utc)

def beijing_time():

    return ntp_time().astimezone(timezone(timedelta(hours=8)))

# ==========================================
#           LATENCY TEST
# ==========================================

def measure_latency():

    samples=[]

    for _ in range(5):

        try:

            start=time.perf_counter()

            requests.post(U_apply,headers=headers,data="{}",timeout=2)

            samples.append((time.perf_counter()-start)*1000)

        except:
            pass

    if len(samples)<3:
        return 200

    samples.sort()

    trim=int(len(samples)*0.2)

    samples=samples[trim:-trim] if trim else samples

    return sum(samples)/len(samples)*1.3

# ==========================================
#         DAILY SCHEDULER
# ==========================================

def scheduler():

    tz=timezone(timedelta(hours=8))

    while True:

        now=beijing_time()

        target=now.replace(hour=23,minute=57,second=0,microsecond=0)

        if now>=target:

            target+=timedelta(days=1)

        print(f"\nNext run at: {target}")

        while datetime.now(tz)<target:

            time.sleep(30)

        latency=measure_latency()

        execute_time=target+timedelta(minutes=3)-timedelta(milliseconds=latency)

        print("Execution time:",execute_time)

        while datetime.now(tz)<execute_time:

            time.sleep(0.5)

        result=apply_request()

        if result==1:

            return 1

# ==========================================

account_info()
state_request()

while True:

    r=scheduler()

    if r!=1:
        break
