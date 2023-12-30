from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import requests
import os
import time

# Set the directory for saving the downloaded file
# Get the current working directory
cwd = os.getcwd()
folder_name = f'{cwd}/SDS_downloads'
if not os.path.exists(folder_name):
    os.mkdir(folder_name)

chrome_options = webdriver.ChromeOptions()
prefs = {
    "download.default_directory": folder_name,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "plugins.always_open_pdf_externally": True,
    "intl.accept_languages": "en,en-US"
}
chrome_options.add_experimental_option("prefs", prefs)

# Initialize the Chrome WebDriver
driver = webdriver.Chrome(options=chrome_options)

# To GOOGLE and search
driver.get('https://www.google.com/')
search_box = driver.find_element(By.NAME, 'q')
search_box.send_keys('Santa Cruz 97-67-6')
search_box.send_keys(Keys.RETURN)

# Wait for the results to load
wait = WebDriverWait(driver, 10)
results = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.g')))

# Enter the right product page
for result in results:
    link = result.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
    # Check if the link starts with the specified URL
    if link.startswith('https://www.scbt.com/'):
        # Navigate to the link
        driver.get(link)
        print("Navigated to:", driver.current_url)

        # Check if the current URL contains the Chinese path
        if '/zh/' in driver.current_url:
            driver.delete_all_cookies()
            # Replace the Chinese path with the English path
            english_url = driver.current_url.replace('/zh/', '/')
            # Navigate to the English version of the page
            driver.get(english_url)
            driver.refresh()
            wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
            print("Switched to English version:", driver.current_url)
        break


# Expand SDS page
sds_button = wait.until(EC.visibility_of_element_located((By.XPATH, "//button[contains(., 'SDS & Certificate of Analysis')]")))
sds_button.click()

# # Language dropdown options
# dropdown = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "select.MuiNativeSelect-select")))
# # dropdown = driver.find_element(By.CSS_SELECTOR, "select.MuiNativeSelect-select")
# select = Select(dropdown)
# select.select_by_value('1')

# Get the PDF download link
submit_button = driver.find_element(By.CSS_SELECTOR, "a.submitBtn")
pdf_url = submit_button.get_attribute("href")

# Download the PDF
response = requests.get(pdf_url)
# File name
file_name = pdf_url.split('/')[-1].split('?')[0]

# Save the PDF
if response.status_code == 200:
    with open(os.path.join(folder_name, file_name), 'wb') as f:
        f.write(response.content)
    print("PDF downloaded successfully")
else:
    print("Failed to download PDF")

# Close the browser
driver.quit()
