import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
import requests
import time
import re
import os

def find_brand_name(keyword):
    brand_aliases = {
        'sigmaaldrich': ['sigma-aldrich', 'sigma aldrich', 'sigma', 'merck'],
        'itwreagents': ['panreac', 'panreac applichem'],
        'scbt': ['santa cruz', 'santa cruz biotechnology', 'santacruz'],
        'thermofisher': ['gibco', 'gibco invitrogen'],
        'bionovas': ['bionovas', 'bionovas canada'],
        'usp': ['usp', 'usp reference standards']
    }

    # lower case all the keys and values
    brand_aliases = {k.lower(): [alias.lower() for alias in v] for k, v in brand_aliases.items()}

    # lower case the keyword
    lower_keyword = keyword.lower()

    # find the brand name
    for brand, aliases in brand_aliases.items():
        for alias in aliases:
            if alias in lower_keyword:
                print(f'Brand name: {brand}')
                return brand

    return "can't recognize"

def search_and_navigate(driver, keyword):
    # Brand name
    brand_name = find_brand_name(keyword)
    if brand_name == "can't recognize":
        return False, None
    ######## Bionovas convert to Sigma-Aldrich for now ########
    elif brand_name == 'bionovas':
        brand_name = 'sigmaaldrich'
        keyword = keyword + " site:" + brand_name + ".com"
    ###########################################################
    # Search keyword
    elif brand_name == 'usp':
        keyword = keyword
    else:
        keyword = keyword + " site:" + brand_name + ".com"
    
    # To GOOGLE and search
    driver.get('https://www.google.com/')
    search_box = driver.find_element(By.NAME, 'q')
    search_box.send_keys(keyword)
    search_box.send_keys(Keys.RETURN)

    # Wait for the results to load
    wait = WebDriverWait(driver, 10)
    results = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.g')))

    # Enter the right product page
    for result in results:
        link = result.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
        if valid_link_for_brand(link, brand_name):
            driver.get(link)
            return True, brand_name
    return False, None

def valid_link_for_brand(link, brand_name):
    if brand_name == 'sigmaaldrich' and link.startswith('https://www.sigmaaldrich.com') and '/search/' in link:
        return True
    elif brand_name == 'itwreagents' and link.startswith('https://www.itwreagents.com/') and '/product/' in link:
        return True
    elif brand_name == 'scbt' and link.startswith('https://www.scbt.com/'):
        return True
    elif brand_name == 'thermofisher' and link.startswith('https://www.thermofisher.com/') and '/product/' in link:
        return True
    elif brand_name == 'bionovas' and link.startswith('https://bionovas.ca/') and '/p/' in link:
        return True
    elif brand_name == 'usp' and link.startswith('https://store.usp.org/product'):
        return True
    else:
        return False

def download_sds_from_sigma(driver, folder_name):
    driver.delete_all_cookies()
    wait = WebDriverWait(driver, 10)
    # Accept Cookies options (if necessary)
    try:
        accept_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="onetrust-reject-all-handler"]')))
        accept_button.click()
    except Exception:
        pass # If no cookie button found

    # Find the desired button
    sds_buttons = driver.find_elements(By.CSS_SELECTOR, "button[data-testid^='sds-']")
    if sds_buttons:
        # Get product ID
        data_testid = sds_buttons[0].get_attribute("data-testid")
        sds_buttons[0].click()
    else:
        print("No SDS buttons found")
        return "Fail to download", None
    
    # Click ZF-zf option
    zf_option = driver.find_element(By.ID, 'sds-link-ZF')
    zf_option.click()

    # Get file name
    file_name = zf_option.get_attribute('href').split('/')[-1].split('?')[0]
    file_path = os.path.join(folder_name, f'{file_name}.pdf')

    if not download_and_check_file(driver, file_path):
        # download the en version if zf version is not available
        en_option = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="sds-link-EN"]')))
        en_option.click()
        if os.path.exists(file_path):
            os.remove(file_path)

        if download_and_check_file(driver, file_path):
            return "Downloaded English version successfully", f'{file_name}.pdf'
        else:
            return "Fail to download English version", None
    else:
        return "Download successfully", f'{file_name}.pdf'

def download_and_check_file(driver, file_path):
    """Check if the file is downloaded successfully and not empty"""
    try:
        WebDriverWait(driver, 20).until(lambda driver: os.path.exists(file_path))
        return wait_for_file_download_completion(file_path)
    except TimeoutException:
        return False

def wait_for_file_download_completion(file_path, timeout=20):
    """Wait until the file size becomes stable to ensure download completion"""
    previous_size = -1
    start_time = time.time()

    while time.time() - start_time < timeout:
        current_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        if current_size > 0 and current_size == previous_size:
            return True  # File size is stable and not empty
        previous_size = current_size
        time.sleep(1)  # Wait for 1 second before checking again

    return False  # Timeout reached or file size still 0

def download_sds_from_itwreagents(driver, folder_name):
    driver.delete_all_cookies()
    # Accept Cookies options (if necessary)
    try:
        accept_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="CybotCookiebotDialogBodyLevelButtonLevelOptinAllowallSelection"]')))
        accept_button.click()
    except Exception:
        pass  # If no cookie button found

    # Find the SDS button
    wait = WebDriverWait(driver, 10)
    # sds_link = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "sds_ajaxlist")))
    # sds_link.click()
    sds_link = driver.find_element(By.CLASS_NAME, "sds_ajaxlist")
    driver.execute_script("arguments[0].click();", sds_link)

    pdf_link = wait.until(EC.visibility_of_element_located((By.XPATH, "//a[@title='SDS Taiwan (chinese)']")))
    pdf_url = pdf_link.get_attribute("href")

    response = requests.get(pdf_url)

    # File name
    file_name = pdf_url.split('/')[-1]

    if response.status_code == 200:
        with open(os.path.join(folder_name, file_name), 'wb') as f:
            f.write(response.content)
        return "Download successfully", file_name
    else:
        return "Fail to download", None

def download_sds_from_scbt(driver, folder_name):
    wait = WebDriverWait(driver, 10)
    try:
        # Check if the current URL contains the Chinese path
        if '/zh/' in driver.current_url:
            driver.delete_all_cookies()
            # Replace the Chinese path with the English path
            english_url = driver.current_url.replace('/zh/', '/')
            # Navigate to the English version of the page
            driver.get(english_url)
            driver.refresh()
            # Wait for the page to load
            wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))

        # Expand SDS page
        def click_sds_button_with_js(driver):
            sds_button = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "button[data-gtm-event-id='certficateAnalysisTab']")))
            driver.execute_script("arguments[0].click();", sds_button)

        # Click the SDS button
        click_sds_button_with_js(driver)

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
            return "Download successfully", file_name
        else:
            return "Fail to download", None
    except Exception as e:
        print(f"An error occurred: {e}")
        return "Error during download", None

def download_from_thermofisher(driver, folder_name, keyword):
    # Accept Cookies options (if necessary)
    try:
        accept_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="truste-consent-button"]')))
        accept_button.click()
    except Exception:
        pass  # If no cookie button found

    # Find the SDS button
    wait = WebDriverWait(driver, 10)
    try:
        # Wait for the button to be clickable
        sds_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[span[contains(text(), 'SDS')]]")))
        sds_button.click()
    except TimeoutException:
        result = "Fail to download"

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
        return "Fail to download", None

    # Open the language dropdown
    language_dropdown = driver.find_element(By.XPATH, '//*[@id="modal"]/div/div/div[3]/div/div[2]/div[2]/div/div[1]')
    driver.execute_script("arguments[0].scrollIntoView(true);", language_dropdown)
    language_dropdown.click()

    # Select the 'Chinese (Traditional)' option
    chinese_option = driver.find_element(By.XPATH, "//div[contains(@class, 'c-dropdown__option') and contains(text(), 'Chinese (Traditional)')]")
    ActionChains(driver).move_to_element(chinese_option).click(chinese_option).perform()

    # Before clicking the download button, get the current window handle first
    current_window = driver.current_window_handle

    # Click the download button
    download_button = driver.find_element(By.XPATH, '//*[@id="modal"]/div/div/div[4]/button[1]')
    download_button.click()

    # Wait for a new window or tab to open
    wait.until(EC.number_of_windows_to_be(2))

    # Switch to the new window
    windows = driver.window_handles
    new_window = [window for window in windows if window != current_window][0]
    driver.switch_to.window(new_window)

    # Get the URL of the new window
    new_url = driver.current_url

    # Download the PDF
    response = requests.get(new_url.split('url=')[1])

    if response.status_code == 200:
        with open(os.path.join(folder_name, f'{keyword}.pdf'), 'wb') as f:
            f.write(response.content)
        return "Download successfully", f'{keyword}.pdf'
    else:
        return "Fail to download", None

def download_from_usp(driver, folder_name, keyword):
    # Download from URL directly
    try:
        cas_num = keyword.split(' ')[-1]
        url = f'https://static.usp.org/pdf/EN/referenceStandards/msds/{cas_num}.pdf'
        response = requests.get(url)
        if response.status_code == 200:
            with open(os.path.join(folder_name, f'{cas_num}.pdf'), 'wb') as f:
                f.write(response.content)
            return "Download successfully", f'{cas_num}.pdf'
        else:
            # Download from the website
            # Find SDS button
            wait = WebDriverWait(driver, 10)
            sds_button = wait.until(EC.visibility_of_element_located((By.XPATH, '//a[contains(text(), "Safety data sheet.pdf")]')))
            sds_button.click()

            # Get the downloaded file name
            file_name = keyword.split(' ')[-1]
            try:
                WebDriverWait(driver, 20).until(
                    lambda driver: os.path.exists(os.path.join(folder_name, f'{file_name}.pdf'))
                )
                return "Download successfully", f'{file_name}.pdf'
            except TimeoutException:
                return "Fail to download", None            
    except:
        return "Fail to download", None


def main():
    # Set the directory for saving the downloaded file
    # Get the current working directory
    cwd = os.getcwd()
    folder_name = f'{cwd}/SDS_downloads'
    if not os.path.exists(folder_name):
        os.mkdir(folder_name)

    # Load the keywords from the Excel file
    sds_file = 'sds_file.xlsx'
    df = pd.read_excel(sds_file, header=0)

    keyword_list = []
    for index, row in df.iterrows():
        keyword = " ".join(str(word).strip() for word in row)
        keyword_list.append(keyword)

    # Initialize the Chrome WebDriver
    chrome_options = webdriver.ChromeOptions()
    prefs = {
        "download.default_directory": folder_name,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(options=chrome_options)

    # Search and download
    download_results = []
    file_names = []
    for keyword in keyword_list:
        success, brand_name = search_and_navigate(driver, keyword)
        if success:
            if brand_name == 'sigmaaldrich':
                download_result, file_name = download_sds_from_sigma(driver, folder_name)
                download_results.append(download_result)
                file_names.append(file_name)
            elif brand_name == 'itwreagents':
                download_result, file_name = download_sds_from_itwreagents(driver, folder_name)
                download_results.append(download_result)
                file_names.append(file_name)
            elif brand_name == 'scbt':
                download_result, file_name = download_sds_from_scbt(driver, folder_name)
                download_results.append(download_result)
                file_names.append(file_name)
            elif brand_name == 'thermofisher':
                download_result, file_name = download_from_thermofisher(driver, folder_name, keyword)
                download_results.append(download_result)
                file_names.append(file_name)
            elif brand_name == 'bionovas':
                download_result, file_name = download_sds_from_sigma(driver, folder_name)
                download_results.append(download_result)
                file_names.append(file_name)
            elif brand_name == 'usp':
                download_result, file_name = download_from_usp(driver, folder_name, keyword)
                download_results.append(download_result)
                file_names.append(file_name)
            else:
                pass
        else:
            print(f'{keyword} not found')

    driver.quit()

    # Save the download results
    df['download_result'] = download_results
    df['file_name'] = file_names
    df.to_excel("sds_results_file.xlsx", index=False)

if __name__ == '__main__':
    main()
