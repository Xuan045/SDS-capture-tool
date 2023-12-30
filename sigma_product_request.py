import requests
from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from process_text import *
import requests
import time
import re
import os

def download_sds(driver, keyword, folder_name):
    """
    Download the SDS for a given keyword and brand.
    This function handles the brand detection and calls the appropriate download function.
    """
    try:
        success, brand_name = search_and_navigate(driver, keyword)
        if success:
            if brand_name == 'sigmaaldrich':
                return download_sds_from_sigma(driver, folder_name)
            elif brand_name == 'itwreagents':
                return download_sds_from_itwreagents(driver, folder_name)
            elif brand_name == 'scbt':
                return download_sds_from_scbt(driver, folder_name)
            elif brand_name == 'thermofisher':
                return download_from_thermofisher(driver, folder_name, keyword)
            elif brand_name == 'bionovas':
                return download_sds_from_sigma(driver, folder_name)  # Assumed sigmaaldrich for bionovas
            elif brand_name == 'usp':
                return download_from_usp(driver, folder_name, keyword)
            else:
                return "Brand not supported", None, None, None, None, None, None
        else:
            return f"{keyword} not found", None, None, None, None, None, None
    except Exception as e:
        return f"Error during download: {e}", None, None, None, None, None, None
    
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
            if brand_name == 'sigmaaldrich':
                cas_num = keyword.split(' ')[1]
                link = f"https://www.sigmaaldrich.com/TW/en/search/{cas_num}?facet=facet_brand%3ASigma-Aldrich&focus=products&page=1&perpage=30&sort=relevance&term={cas_num}&type=cas_number"
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

    try:
        # Accept Cookies options (if necessary)
        try:
            accept_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="onetrust-accept-btn-handler"]')))
            accept_button.click()
        except Exception:
            pass

        # Find the most relevant SDS button (the first one)
        sds_buttons = driver.find_elements(By.CSS_SELECTOR, "button[data-testid^='sds-']")
        if not sds_buttons:
            print("No SDS buttons found")
            return "Fail to download", None, None, None, None, None, None

        sds_buttons[0].click()
        
        # Click ZF-zf option
        zf_option = driver.find_element(By.ID, 'sds-link-ZF')
        zf_option.click()

        # Get file name
        file_name = zf_option.get_attribute('href').split('/')[-1].split('?')[0]
        file_path = os.path.join(folder_name, f'{file_name}.pdf')

        if not download_and_check_file(driver, file_path):
            # Download the EN version if ZF version is not available
            en_option = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="sds-link-EN"]')))
            en_option.click()

            if os.path.exists(file_path):
                os.remove(file_path)  # Remove the ZF version if it exists

            if not download_and_check_file(driver, file_path):
                return "Fail to download English version", None, None, None, None, None, None

        # Get the CAS number, chemical name, physical state and density
        cas_num, ch_name, en_name, physical_state, density = pdf_to_text_sigma(file_path)
        return "Downloaded successfully", f'{file_name}.pdf', cas_num, ch_name, en_name, physical_state, density

    except Exception as e:
        print(f"Error during download: {e}")
        return "Error during download", None, None, None, None, None, None

def download_and_check_file(driver, file_path):
    """Check if the file is downloaded successfully and not empty"""
    try:
        WebDriverWait(driver, 15).until(lambda driver: os.path.exists(file_path))
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

def main():
    # Set the directory for saving the downloaded file
    # Get the current working directory
    cwd = os.getcwd()
    folder_name = f'{cwd}/SDS_downloads'
    if not os.path.exists(folder_name):
        os.mkdir(folder_name)

    # Load the keywords from the Excel file
    # sds_file = 'sds_file.xlsx'
    # df = pd.read_excel(sds_file, header=0)

    keyword_list = ['Sigma-Aldrich 606-68-8']

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
    download_results, file_names, cas_nums, ch_names, en_names, physical_states, densities = [], [], [], [], [], [], []
    for keyword in keyword_list:
        print(f'Start downloading SDS for {keyword}')
        download_result, file_name, cas_number, ch_name, en_name, physical_state, density = download_sds(driver, keyword, folder_name)
        download_results.append(download_result)
        file_names.append(file_name or 'N/A')
        cas_nums.append(cas_number or 'N/A')
        ch_names.append(ch_name or 'N/A')
        en_names.append(en_name or 'N/A')
        physical_states.append(physical_state or 'N/A')
        densities.append(density or 'N/A')
    print(download_results, file_names, cas_nums, ch_names, en_names, physical_states, densities)

    # Quit the driver after completion
    driver.quit()

    # Save the download results
    # df['download_result'] = download_results
    # df['file_name'] = file_names
    # df['cas_number'] = cas_nums
    # df['chinese_name'] = ch_names
    # df['english_name'] = en_names
    # df['physical_state'] = physical_states
    # df['density'] = densities
    # df.to_excel("sds_results_file.xlsx", index=False)

if __name__ == '__main__':
    main()
    
