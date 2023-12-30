from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
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
search_box.send_keys('PanReac 67-64-1')
search_box.send_keys(Keys.RETURN)

# Wait for the results to load
wait = WebDriverWait(driver, 10)
results = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.g')))

# Enter the right Sigma-Aldrich product page
for result in results:
    link = result.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
    if link.startswith('https://www.itwreagents.com/') and '/product/' in link:
        driver.get(link)
        print("Navigated to:", driver.current_url)
        break

# Accept Cookies options (if necessary)
try:
    accept_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="CybotCookiebotDialogBodyLevelButtonLevelOptinAllowallSelection"]')))
    accept_button.click()
except Exception:
    pass  # If no cookie button found

# Find the SDS button
wait = WebDriverWait(driver, 10)
sds_link = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "sds_ajaxlist")))
sds_link.click()
# print("Clicked SDS button")

# Get the downloaded file name
# try:
#     # 嘗試找到Taiwanese選項
#     pdf_link = wait.until(EC.visibility_of_element_located((By.XPATH, "//a[@title='SDS Taiwan (chinese)']")))
# except TimeoutException:
#     # 如果找不到Taiwanese選項，則選擇USA (english)
#     pdf_link = wait.until(EC.visibility_of_element_located((By.XPATH, "//a[@title='SDS USA (english)']")))

pdf_link = wait.until(EC.visibility_of_element_located((By.XPATH, "//a[@title='SDS Taiwan (chinese)']")))
pdf_url = pdf_link.get_attribute("href")

response = requests.get(pdf_url)

# File name
file_name = pdf_url.split('/')[-1]

if response.status_code == 200:
    with open(os.path.join(folder_name, file_name), 'wb') as f:
        f.write(response.content)
    print("PDF downloaded successfully")
else:
    print("Failed to download PDF")

# Close the browser
driver.quit()
