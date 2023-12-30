from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
import requests
import re
import os

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
    "plugins.always_open_pdf_externally": True
}
chrome_options.add_experimental_option("prefs", prefs)

# Initialize the Chrome WebDriver
driver = webdriver.Chrome(options=chrome_options)

# To GOOGLE and search
driver.get('https://www.google.com/')
search_box = driver.find_element(By.NAME, 'q')
keyword = 'Gibco 17504-044'
search_box.send_keys(keyword)
search_box.send_keys(Keys.RETURN)

# Wait for the results to load
wait = WebDriverWait(driver, 10)
results = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.g')))

# Enter the right product page
for result in results:
    link = result.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
    if link.startswith('https://www.thermofisher.com/') and '/product/' in link:
        driver.get(link)
        print("Navigated to:", driver.current_url)
        break

# Accept Cookies options (if necessary)
try:
    accept_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="truste-consent-button"]')))
    accept_button.click()
    print("Clicked accept button")
except Exception:
    print("No accept button found")
    pass  # If no cookie button found

# Find the SDS button
wait = WebDriverWait(driver, 10)
try:
    # Wait for the button to be clickable
    sds_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[span[contains(text(), 'SDS')]]")))
    sds_button.click()
    print("Clicked on the SDS button")
except TimeoutException:
    print("SDS button not found or not clickable")

# Product dropdown options
# Open the dropdown
product_dropdown = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'c-dropdown__selected-option')))
product_dropdown.click()

# Wait until dropdown options are visible
wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'c-dropdown__inner-options')))

# Find and click the matching option
options = driver.find_elements(By.CLASS_NAME, 'c-dropdown__option')
product_number = ''.join(re.findall(r'\d+', keyword)) # Product number

for option in options:
    if option.text.strip() == product_number:
        option.click()
        break
else:
    print("No matching option found")

# Open the language dropdown
language_dropdown = driver.find_element(By.XPATH, '//*[@id="modal"]/div/div/div[3]/div/div[2]/div[2]/div/div[1]')
driver.execute_script("arguments[0].scrollIntoView(true);", language_dropdown)
language_dropdown.click()

# Select the 'Chinese (Traditional)' option
chinese_option = driver.find_element(By.XPATH, "//div[contains(@class, 'c-dropdown__option') and contains(text(), 'Chinese (Traditional)')]")
ActionChains(driver).move_to_element(chinese_option).click(chinese_option).perform()
print("Selected language: Chinese (Traditional)")

# Before clicking the download button, get the current window handle first
current_window = driver.current_window_handle

# Click the download button
download_button = driver.find_element(By.XPATH, '//*[@id="modal"]/div/div/div[4]/button[1]')
download_button.click()
print("Clicked download button")

# Wait for a new window or tab to open
wait.until(EC.number_of_windows_to_be(2))

# Switch to the new window
windows = driver.window_handles
new_window = [window for window in windows if window != current_window][0]
driver.switch_to.window(new_window)

# Get the URL of the new window
new_url = driver.current_url
print("New URL:", new_url)

# Download the PDF
response = requests.get(new_url.split('url=')[1])

if response.status_code == 200:
    with open(os.path.join(folder_name, f'{keyword}.pdf'), 'wb') as f:
        f.write(response.content)
    print("PDF downloaded successfully")
else:
    print("Failed to download PDF")

# Close the browser
driver.quit()
