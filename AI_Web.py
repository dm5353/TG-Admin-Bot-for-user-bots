from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

username = config['AI']['email']
password = config['AI']['password']
link = config['AI']['link']

options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--disable-gpu")

driver = None

async def talk(text, url):
    if url != "none":
        driver.get(url)
    input_box = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "textarea")))
    input_box.clear()
    input_box.send_keys(text + Keys.RETURN)
    time.sleep(10)
    response = driver.find_elements(By.TAG_NAME, "p")[-2].text
    return response, driver.current_url

async def login():
    global driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(link)

    try:
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="amzn-captcha-verify-button"]')))
        print("Капча есть")
        driver.quit()
        await login()
    except TimeoutException:
        print("Капча отсутствует")

    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div/div/div/div/form/button"))).click()
    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "/html/body/div/main/div/section/form/div[1]/label[1]/input"))).send_keys(username)
    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "/html/body/div/main/div/section/form/div[1]/label[2]/input"))).send_keys(password)
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div/main/div/section/form/div[2]/button"))).click()

async def quit():
    global driver
    if driver:
        driver.quit()