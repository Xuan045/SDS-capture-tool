from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Initialize the Chrome WebDriver
driver = webdriver.Chrome()

# To GOOGLE
driver.get('https://www.google.com/')

# Search for the key word
search_box = driver.find_element(By.NAME, 'q')
search_box.send_keys('151-21-3 MERCK')

# Press Enter to search
search_box.send_keys(Keys.RETURN)

# Wait for the results to load
wait = WebDriverWait(driver, 10)
results = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.g')))

# Enter the right website
for result in results:
    link = result.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
    if link.startswith('https://www.sigmaaldrich.com') and '/product/' in link:
        driver.get(link)


# Close the browser
driver.quit()