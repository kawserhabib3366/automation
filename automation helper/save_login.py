import json
import logging
import os
import pickle
import re
import subprocess
import sys
import time
from glob import glob
from typing import List, Optional

import undetected_chromedriver as uc
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


# =======================
# CONFIG & CONSTANTS
# =======================
BASEDIR = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__))

LOG_FILE = os.path.join(BASEDIR, "scraper.log")



# =======================
# LOGGER SETUP
# =======================
logger = logging.getLogger("tiktok")
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    stream_handler = logging.StreamHandler()
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)


def get_chrome_major_version() -> int:
    """
    Detects the installed Chrome major version.
    Works on Windows and Linux/Mac fallback.
    """
    try:
        # Windows registry query
        output = subprocess.check_output(
            r'reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version',
            shell=True, text=True
        )
        match = re.search(r"version\s+REG_SZ\s+([\d.]+)", output)
        if match:
            version = int(match.group(1).split('.')[0])
            logger.info(f"Chrome version detected from registry: {version}")
            return version
    except Exception:
        logger.debug("Windows registry query failed, trying fallback.")

    try:
        # Fallback: run 'chrome --version' (Linux/macOS)
        output = subprocess.check_output(["chrome", "--version"], text=True)
        match = re.search(r"(\d+)\.\d+\.\d+\.\d+", output)
        if match:
            version = int(match.group(1))
            logger.info(f"Chrome version detected from 'chrome --version': {version}")
            return version
    except Exception:
        logger.debug("Fallback chrome --version check failed.")

    logger.error("Could not detect Chrome version. Please ensure Chrome is installed and in PATH.")
    sys.exit(1)


def init_driver(headless: bool = False) -> uc.Chrome:
    """
    Initialize undetected_chromedriver with appropriate options.
    """
    version = get_chrome_major_version()
    logger.info(f"Initializing ChromeDriver with Chrome version {version} (headless={headless})")

    options = uc.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--no-sandbox")
    #options.add_argument("--blink-settings=imagesEnabled=false")

    driver = uc.Chrome(version_main=version, options=options)
    driver.maximize_window()
    return driver


def load_cookies(driver: uc.Chrome, cookie_file: str = "auth.pkl") -> None:
    """
    Load cookies from a pickle file and add to the driver session.
    """
    if not os.path.exists(cookie_file):
        logger.error(f"Cookie file {cookie_file} not found.")
        return

    with open(cookie_file, "rb") as f:
        cookies = pickle.load(f)
    for cookie in cookies:
        cookie.pop('expiry', None)  # Remove expiry if present to avoid issues
        try:
            driver.add_cookie(cookie)
        except Exception as e:
            logger.warning(f"Failed to add cookie {cookie.get('name', '')}: {e}")
    logger.info("Cookies loaded into browser.")


def load_cookies_json(driver, cookie_file: str = "auth.json") -> None:
    """
    Load cookies from a JSON file and add to the driver session.
    """
    if not os.path.exists(cookie_file):
        logger.error(f"Cookie file {cookie_file} not found.")
        return

    with open(cookie_file, "r") as f:
        cookies = json.load(f)

    for cookie in cookies:
        cookie.pop('expiry', None)  # Remove expiry if present to avoid issues
        try:
            driver.add_cookie(cookie)
        except Exception as e:
            logger.warning(f"Failed to add cookie {cookie.get('name', '')}: {e}")
    logger.info("Cookies loaded into browser.")




def save_cookies(driver: uc.Chrome, files: str = "auth.json") -> None:
    pkl_file=files+".pkl"
    json_file=files+".json"

    """
    Save cookies from current session into JSON and pickle files.
    """
    cookies = driver.get_cookies()
    with open(json_file, "w", encoding="utf-8") as f_json:
        json.dump(cookies, f_json, indent=2)
    with open(pkl_file, "wb") as f_pkl:
        pickle.dump(cookies, f_pkl)
    logger.info(f"Cookies saved to {json_file} and {pkl_file}.")





import tkinter as tk
from tkinter import messagebox

def open_cookie_saver_gui(driver):
    def on_save_click():
        filename = entry_save.get().strip()
        if not filename:
            messagebox.showerror("Error", "Please enter a filename.")
            return
        try:
            save_cookies(driver, filename)
            messagebox.showinfo("Success", f"Cookies saved as '{filename}.json' and '{filename}.pkl'")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save cookies: {e}")

    def on_load_click():
        filename = entry_load.get().strip()
        if not filename:
            messagebox.showerror("Error", "Please enter a filename.")
            return
        try:
            load_cookies_json(driver, filename)
            messagebox.showinfo("Success", f"Cookies loaded from '{filename}.json' and '{filename}.pkl'")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load cookies: {e}")

    window = tk.Tk()
    window.title("TikTok Cookie Manager")

    # Save Section
    tk.Label(window, text="Enter filename to save cookies:").pack(pady=(10, 0))
    entry_save = tk.Entry(window, width=30)
    entry_save.pack(pady=5)
    entry_save.insert(0, "auth")  # default
    save_button = tk.Button(window, text="Save Cookies", command=on_save_click)
    save_button.pack(pady=10)

    # Load Section
    tk.Label(window, text="Enter filename to load cookies:").pack(pady=(20, 0))
    entry_load = tk.Entry(window, width=30)
    entry_load.pack(pady=5)
    entry_load.insert(0, "auth")  # default
    load_button = tk.Button(window, text="Load Cookies", command=on_load_click)
    load_button.pack(pady=10)

    window.mainloop()


if __name__ == "__main__":
    driver = init_driver(headless=False)

    open_cookie_saver_gui(driver)


