import os
import time
import logging
from functools import wraps
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    NoSuchElementException, TimeoutException, WebDriverException
)
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from urllib.parse import urlparse, parse_qs
import pandas as pd

# ─────────────── CONFIGURATION ───────────────



SELENIUM_GRID_URL = "18.118.63.89:4444"

TARGET_URL = "https://connect.milwaukeetool.com/"

MAIL="developer_01@biedlers.com"
PASSW="Czy9u6_xddZhF.q"


LOGIN_TIMEOUT = 30
NAV_TIMEOUT = 30
SHORT_TIMEOUT = 1
LONG_TIMEOUT=60
RETRY_ATTEMPTS = 3
RETRY_DELAY = 2
HEADLESS_MODE = False  # Set to False for debugging







# ─────────────── LOGGER SETUP ───────────────
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


# ─────────────── CHROME OPTIONS ───────────────


def create_remote_driver(grid_url: str, headless: bool = False):
    options = Options()

    # Stable flags

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--disable-gpu")

    options.add_argument("--disable-popup-blocking")

    options.add_argument("--disable-infobars")
    options.add_argument("--disable-default-apps")
    options.add_argument("--disable-software-rasterizer")

    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-crash-reporter")
    options.add_argument("--disable-sync")
    options.add_argument("--metrics-recording-only")


    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--enable-features=NetworkService,NetworkServiceInProcess")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    )

    if headless:
        options.add_argument("--headless=new")

    prefs = {
        "profile.managed_default_content_settings.images": 1,
        "profile.default_content_setting_values.notifications": 2,
        "profile.managed_default_content_settings.stylesheets": 2,
        "profile.managed_default_content_settings.fonts": 2,
   
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    options.add_experimental_option("prefs", prefs)

    # Just pass options (NOT desired_capabilities!)
    # driver = webdriver.Remote(
    #     command_executor=grid_url,
    #     options=options
    # )
    driver=webdriver.Chrome(options=options)

    driver.set_page_load_timeout(60)
    driver.implicitly_wait(10)
    return driver


# ─────────────── DECORATOR ───────────────
def retry(max_attempts=RETRY_ATTEMPTS, delay=RETRY_DELAY, exceptions=(Exception,)):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    logging.warning(f"{fn.__name__} failed on attempt {attempt}/{max_attempts}: {e}")
                    time.sleep(delay)
            logging.error(f"{fn.__name__} failed after {max_attempts} attempts.")
            raise last_exc
        return wrapper
    return decorator


#########################################
def intialize():
    logging.info("Connecting to remote Selenium Grid...")
    driver = create_remote_driver(SELENIUM_GRID_URL, headless=HEADLESS_MODE)


    logging.info("Connected. Navigating to target URL...")
    #driver.get(TARGET_URL)
    logging.info(f"Page title: {driver.title}")
    return driver







from selenium import webdriver
from selenium.webdriver.common.by import By
import os
import requests

# ======= Utility Functions =======

def create_folder(path):
    """Create folder if not exists."""
    os.makedirs(path, exist_ok=True)

def download_file(url, filepath):
    """Download a file from URL with proper headers."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0'
    }
    try:
        with requests.get(url, stream=True, headers=headers) as r:
            if r.status_code == 200:
                with open(filepath, "wb") as f:
                    for chunk in r.iter_content(1024):
                        f.write(chunk)
                print(f"Downloaded: {filepath}")
            else:
                print(f"Failed to download {filepath}, Status: {r.status_code}")
    except Exception as e:
        print(f"Error downloading {filepath}: {e}")

# ======= Baldor Download Functions =======

def download_baldor_image(driver, sku, folder):
    """Download the main product image."""
    create_folder(folder)
    imagelink = driver.find_element(By.XPATH, "//img[@class='product-image']").get_attribute("src")
    if "/api/images/451?bc=white&as=1&h=512&w=512" in imagelink:
        print("no image found....")
        return
    image_name = os.path.join(folder, f"Baldor_{sku}.jpg")
    download_file(imagelink, image_name)




def download_baldor_pdfs(driver, sku, base_folder):
    """Download all PDFs, separate folders for type, handles duplicates."""
    connection_folder = os.path.join(base_folder, "Connection_Diagram")
    dimension_folder = os.path.join(base_folder, "Dimension_Sheet")
    create_folder(connection_folder)
    create_folder(dimension_folder)

    pdf_counter = {
        "Connection Diagram": 0,
        "Dimension Sheet": 0
    }

    # Corrected XPath
    groups = driver.find_elements(By.XPATH, '//div[@ng-repeat="drawing in drawings | groupBy: \'kind\': \'drwByKind\'"]')

    for group in groups:
        try:
            pdf_type = group.find_element(By.TAG_NAME, "h3").text.strip()
        except:
            continue

        if pdf_type not in pdf_counter:
            pdf_counter[pdf_type] = 0

        links = group.find_elements(By.XPATH, ".//a[@ng-repeat='drw in drawing.items']")
        for link in links:
            pdf_counter[pdf_type] += 1
            pdf_url = link.get_attribute("href")
            suffix = "" if pdf_counter[pdf_type] == 1 else f"0{pdf_counter[pdf_type]}"
            filename = f"Baldor_{sku}_{pdf_type.replace(' ', '_')}{suffix}.pdf"

            if pdf_type == "Connection Diagram":
                filepath = os.path.join(connection_folder, filename)
            elif pdf_type == "Dimension Sheet":
                filepath = os.path.join(dimension_folder, filename)
            else:
                filepath = os.path.join(base_folder, filename)

            download_file(pdf_url, filepath)




def download_baldor_product(driver,sku, download_folder="downloads", headless=False):
    """Main function to download Baldor image and PDFs by SKU."""
    create_folder(download_folder)


    

    url = f"https://www.baldor.com/catalog/{sku}#tab=%22drawings%22"
    driver.get(url)

    # Download image in separate folder
    download_baldor_image(driver, sku, os.path.join(download_folder, "Images"))

    # Download PDFs into their respective folders
    download_baldor_pdfs(driver, sku, os.path.join(download_folder, "PDFs"))


    print(f"All files for SKU {sku} downloaded successfully!")





INPUT_EXCEL = "baldor.xlsx"

# Column names
SKU_WITHOUT_IMAGE = "SKU WITHOUT IMAGE"
SKU_WITHOUT_DIMENSION = "SKU WITHOUT DIMENSION SHEETS"
SKU_WITHOUT_CONNECTION = "SKU WITHOUT CONNECTION DIAGRAMS"

def process_baldor_excel(driver,input_excel=INPUT_EXCEL, download_folder="Baldor_Files", headless=True):
    """
    Reads an Excel file and processes SKUs from the given columns.
    Calls download_baldor_product for each unique SKU found.
    """
    # Check if Excel file exists
    if not os.path.exists(input_excel):
        logging.critical(f"Excel file not found: {input_excel}")
        return

    # Load the Excel file
    df = pd.read_excel(input_excel)

    # Check if required columns exist
    missing_columns = [col for col in [SKU_WITHOUT_IMAGE, SKU_WITHOUT_DIMENSION, SKU_WITHOUT_CONNECTION] if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing columns in Excel file: {', '.join(missing_columns)}")

    # Combine SKUs from all three columns
    all_skus = pd.concat([
        df[SKU_WITHOUT_IMAGE].dropna(),
        df[SKU_WITHOUT_DIMENSION].dropna(),
        df[SKU_WITHOUT_CONNECTION].dropna()
    ]).unique()

    print(f"Found {len(all_skus)} unique SKUs to download.")

    # Process each SKU
    for i, sku in enumerate(all_skus, start=1):
        print(f"[{i}/{len(all_skus)}] Processing SKU: {sku}")
        download_baldor_product(driver,sku=sku, download_folder=download_folder, headless=headless)






# ======= Example Usage =======
if __name__ == "__main__":
    driver = driver=intialize()
    #sku_input = "EM2513T-58"
    #download_baldor_product(sku_input, download_folder="Baldor_Files", headless=True)
    process_baldor_excel(driver,input_excel=INPUT_EXCEL, download_folder="Baldor_Files", headless=True)






