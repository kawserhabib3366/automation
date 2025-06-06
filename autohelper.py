import logging
import json
import pickle
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc


# =======================
# LOGGING CONFIGURATION
# =======================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

file_handler = logging.FileHandler("scraper.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Usage:
# logging.info(f"VARI: {variable} | vari: {variable}")


# =======================
# DECORATORS & UTILITIES
# =======================

def box_decorator(text: str) -> None:
    """Prints text inside a box-style border."""
    width = len(text) + 4
    print(f"╔{'═' * width}╗")
    print(f"║  {text}  ║")
    print(f"╚{'═' * width}╝")

def star_decorator(text: str) -> None:
    """Prints text inside a star-style border."""
    border = "*" * (len(text) + 4)
    print(f"{border}\n* {text} *\n{border}")

def seperator(n: int = 20) -> None:
    """Prints a horizontal line separator."""
    print("-" * n)


# =======================
# SELENIUM HELPERS
# =======================

def get_driver(headless: bool = False) -> uc.Chrome:
    """
    Initializes and returns a Selenium driver (undetected-chromedriver).
    
    Args:
        headless (bool): Whether to run in headless mode.
    
    Returns:
        uc.Chrome: Configured Chrome driver.
    """
    options = uc.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--no-sandbox")
    return uc.Chrome(options=options)


def login(driver: uc.Chrome) -> None:
    """
    Loads cookies from 'cookies.json' and adds them to the driver.
    
    Args:
        driver (uc.Chrome): Selenium driver instance.
    """
    with open("cookies.json", "r") as file:
        cookies = json.load(file)
        for cookie in cookies:
            driver.add_cookie(cookie)


def savelogin(driver: uc.Chrome) -> None:
    """
    Saves cookies from the current session into JSON and pickle formats.
    
    Args:
        driver (uc.Chrome): Selenium driver instance.
    """
    with open("cookies.json", "w") as file:
        json.dump(driver.get_cookies(), file)
    with open("cookies.pkl", "wb") as file:
        pickle.dump(driver.get_cookies(), file)


def wait_for_element(driver, by: By, value: str, timeout: int = 10):
    """
    Waits for a single element to be present in the DOM.
    
    Args:
        driver: Selenium WebDriver.
        by (By): Locator strategy.
        value (str): The locator value.
        timeout (int): Maximum time to wait.
    
    Returns:
        WebElement: Found element.
    """
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))


def wait_for_elements(driver, by: By, value: str, timeout: int = 10):
    """
    Waits for all matching elements to be present in the DOM.
    
    Args:
        driver: Selenium WebDriver.
        by (By): Locator strategy.
        value (str): The locator value.
        timeout (int): Maximum time to wait.
    
    Returns:
        list[WebElement]: List of found elements.
    """
    return WebDriverWait(driver, timeout).until(EC.presence_of_all_elements_located((by, value)))


def finebytext(driver, exact_text: str, timeout: int = 10):
    """
    Finds an element by its exact visible text using XPath.
    
    Args:
        driver: Selenium WebDriver.
        exact_text (str): The exact text to match.
        timeout (int): Maximum time to wait.
    
    Returns:
        WebElement | None: The matched element, or None if not found.
    """
    xpath = f"//*[normalize-space(text()) = \"{exact_text}\"]"
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        return element
    except Exception:
        logger.error(f"Error finding exact text '{exact_text}'")
        return None




# =======================
# PERSONAL NOTES / SNIPPETS
# =======================


"""
XPATH EXAMPLES:
---------------------
1. Relative to parent: .//div[1]/div/div[2]/div[2]/span[1]/span
2. Role-based:         //*[@role="menuitem"]




LOOP ELEMENTS:
---------------------
for index in range(10):
    driver.find_elements(By.CSS_SELECTOR, f'li[data-id$=" - {index}"]')




TEXT CONTENT:
---------------------
link.get_attribute("textContent").strip()





JS EXECUTIONS:
---------------------
driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", x)
driver.execute_script("arguments[0].scrollIntoView(true);", x)
driver.execute_script("arguments[0].click();", x)
driver.execute_script(f"window.open('{href}', '_blank');")





ANCESTOR ELEMENT:
---------------------
root = a.find_element(By.XPATH, "ancestor::div[@data-testid='eventbox']")
root.get_attribute("class")
"""
