from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
    "plugins.always_open_pdf_externally": True
}
chrome_options.add_experimental_option("prefs", prefs)

# Initialize the Chrome WebDriver
driver = webdriver.Chrome(options=chrome_options)

# To GOOGLE and search
driver.get('https://www.google.com/')
search_box = driver.find_element(By.NAME, 'q')
keyword = '606-68-8 Sigma-Aldrich site:sigmaaldrich.com'
search_box.send_keys('606-68-8 Sigma-Aldrich site:sigmaaldrich.com')
search_box.send_keys(Keys.RETURN)

# Wait for the results to load
wait = WebDriverWait(driver, 10)
results = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.g')))

# Enter the right Sigma-Aldrich product page
for result in results:
    link = result.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
    if link.startswith('https://www.sigmaaldrich.com') and '/search/' in link:
        driver.get(link)
        print("Navigated to:", driver.current_url)
        break

# Accept Cookies options (if necessary)
try:
    accept_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="onetrust-accept-btn-handler"]')))
    accept_button.click()
except Exception:
    pass  # If no cookie button found

sds_buttons = driver.find_elements(By.CSS_SELECTOR, "button[data-testid^='sds-']")

if sds_buttons:
    # Get product ID
    data_testid = sds_buttons[0].get_attribute("data-testid")
    print(data_testid)
    sds_buttons[0].click()
else:
    print("No SDS buttons found")

# Click ZF-zf option
zf_option = driver.find_element(By.ID, 'sds-link-ZF')
zf_option.click()

# Wait for the PDF download
file_name = data_testid.split('-SIGMA')[-1].lower() if '-SIGMA' in data_testid else keyword.split('')[0]
print(file_name)
WebDriverWait(driver, 10).until(
    lambda driver: os.path.exists(os.path.join(folder_name, f'{file_name}.pdf'))
)
time.sleep(1)

# Close the browser
driver.quit()
