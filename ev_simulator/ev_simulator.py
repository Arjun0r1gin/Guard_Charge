import sys
import os
import time
import requests
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from attack_modes import get_safe_profile, get_partial_profile, get_rogue_profile
from session_manager import SessionManager

import win32api
import win32con
import win32gui

BACKEND_URL = "http://localhost:8000"
DETECTION_ENDPOINT = f"{BACKEND_URL}/detection/run"

PORTS = {
    1: {
        "label": "Port 1 — Tata Power Koramangala",
        "scenario": "SAFE",
        "charger_id": 1,
        "profile_fn": get_safe_profile,
    },
    2: {
        "label": "Port 2 — Ather Grid HSR Layout",
        "scenario": "PARTIAL",
        "charger_id": 2,
        "profile_fn": get_partial_profile,
    },
    3: {
        "label": "Port 3 — ChargeZone MG Road (ROGUE)",
        "scenario": "ROGUE",
        "charger_id": 3,
        "profile_fn": get_rogue_profile,
    },
}

manager = SessionManager()
insertion_count = 0
lock = threading.Lock()


def print_banner():
    print("\n" + "=" * 60)
    print("   GUARDCHARGE — EV Charging Security Simulator")
    print("   Every plug-in, verified.")
    print("=" * 60)
    print("\n  Waiting for USB insertion...")
    print("  Insert 1  →  Safe charger      (VERIFIED)")
    print("  Insert 2  →  Partial anomaly   (SUSPICIOUS)")
    print("  Insert 3  →  Rogue charger     (CONFIRMED ROGUE)")
    print("\n  Press Ctrl+C to exit.\n")


def print_result(result: dict):
    score        = result["score"]
    status       = result["status"]
    action       = result["action"]
    hard_blocked = result["hard_blocked"]
    explanation  = result["confidence_explanation"]

    print("\n" + "=" * 60)

    if status == "VERIFIED":
        signal = "GREEN  —  CHARGING AUTHORIZED"
    elif status == "SUSPICIOUS":
        signal = "YELLOW —  WARNING ISSUED"
    elif status == "LIKELY_ROGUE":
        signal = "ORANGE —  CHARGING BLOCKED"
    else:
        signal = "RED    —  HARD BLOCK — DO NOT CHARGE"

    print(f"\n  *** {signal} ***")
    print(f"\n  Trust Score   : {score}/100")
    print(f"  Status        : {status}")
    print(f"  Action        : {action}")
    print(f"  Hard Blocked  : {hard_blocked}")
    print(f"\n  Detection Engine Explanation:")
    for line in explanation.split("\n"):
        print(f"    {line}")
    print("\n" + "=" * 60)
    print("\n  Waiting for next USB insertion...\n")


def simulate_plug_in(port_label: str):
    print(f"\n  {'=' * 58}")
    print(f"  [USB] Plug-in event detected")
    print(f"  [USB] Port : {port_label}")
    print(f"  {'=' * 58}")
    time.sleep(0.5)
    print("\n  [STEP 1] Establishing connection with charging station...")
    time.sleep(0.5)
    print("  [STEP 2] Initiating TLS handshake...")
    time.sleep(0.5)
    print("  [STEP 3] Retrieving station certificate...")
    time.sleep(0.3)


def run_scenario(port_number: int):
    port = PORTS[port_number]
    simulate_plug_in(port["label"])

    session = manager.start(
        charger_id=port["charger_id"],
        port=f"Port {port_number}",
        scenario=port["scenario"],
    )

    print("\n  [STEP 4] Running GuardCharge detection pipeline...")
    print()

    profile = port["profile_fn"](port["charger_id"])

    print("\n  [STEP 5] Sending data to GuardCharge backend...")
    time.sleep(0.4)

    try:
        response = requests.post(DETECTION_ENDPOINT, json=profile, timeout=10)
        response.raise_for_status()
        result = response.json()
    except requests.exceptions.ConnectionError:
        print("\n  [ERROR] Cannot reach backend.")
        print("  Make sure uvicorn is running: uvicorn main:app --reload")
        return
    except Exception as e:
        print(f"\n  [ERROR] {e}")
        return

    print("  [STEP 6] Result received from detection engine.")

    print_result(result)

    manager.complete(
        score=result["score"],
        status=result["status"],
        action=result["action"],
        explanation=result["confidence_explanation"],
        hard_blocked=result["hard_blocked"],
    )


# ── Windows USB detection via hidden message window ──────────────────

WM_DEVICECHANGE      = 0x0219
DBT_DEVICEARRIVAL    = 0x8000   # device inserted
DBT_DEVTYP_VOLUME    = 0x0002   # logical volume (USB drive)


def on_usb_inserted():
    global insertion_count
    with lock:
        insertion_count += 1
        count = ((insertion_count - 1) % 3) + 1

        if count > 3:
            with lock:
                insertion_count = 1
                count = 1

    print(f"\n  [USB] Insertion #{count} detected.")
    threading.Thread(target=run_scenario, args=(count,), daemon=True).start()


def wnd_proc(hwnd, msg, wparam, lparam):
    if msg == WM_DEVICECHANGE and wparam == DBT_DEVICEARRIVAL:
        # lparam points to DEV_BROADCAST_HDR — check devtype
        import ctypes
        hdr_type = ctypes.c_uint32.from_address(lparam + 4).value
        if hdr_type == DBT_DEVTYP_VOLUME:
            on_usb_inserted()
    return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)


def create_listener_window():
    wc = win32gui.WNDCLASS()
    wc.lpfnWndProc   = wnd_proc
    wc.lpszClassName = "GuardChargeUSBListener"
    wc.hInstance     = win32api.GetModuleHandle(None)
    win32gui.RegisterClass(wc)

    hwnd = win32gui.CreateWindow(
        wc.lpszClassName,
        "GuardCharge USB Listener",
        0, 0, 0, 0, 0,
        0, 0,
        wc.hInstance,
        None
    )
    return hwnd


def main():
    print_banner()

    try:
        requests.get(f"{BACKEND_URL}/chargers/", timeout=5)
    except requests.exceptions.ConnectionError:
        print("\n  [ERROR] Backend is not running.")
        print("  Start it: cd backend && uvicorn main:app --reload\n")
        sys.exit(1)

    print("  Backend connected successfully.\n")

    create_listener_window()

    print("  Listening for USB insertions...\n")

    try:
        win32gui.PumpMessages()
    except KeyboardInterrupt:
        print("\n  Exiting GuardCharge simulator. Goodbye.\n")


if __name__ == "__main__":
    main()