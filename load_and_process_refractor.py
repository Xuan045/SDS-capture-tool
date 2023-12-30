import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from process_text import *
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
                link = f"https://www.sigmaaldrich.com/TW/en/search/{cas_num}?facet=facet_brand%3ASigma-Aldrich&focus=products&page=1&perpage=30&region=global&sort=relevance&term={cas_num}&type=product"
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

        # Wait for the SDS button to be clickable
        time.sleep(3)
        sds_buttons[0].click()
        
        # Click ZF-zf option
        zf_option = driver.find_element(By.ID, 'sds-link-ZF')
        zf_option.click()

        # Wait for the new file to be downloaded
        new_file_name = wait_for_new_file(folder_name)
        if new_file_name is None:
            print("No new file detected in the download folder within the timeout period.")
            return "Fail to download", None, None, None, None, None, None

        file_path = os.path.join(folder_name, new_file_name)

        # Get the CAS number, chemical name, physical state and density
        cas_num, ch_name, en_name, physical_state, density = pdf_to_text_sigma(file_path)
        return "Downloaded successfully", new_file_name, cas_num, ch_name, en_name, physical_state, density

    except Exception as e:
        print(f"Error during download: {e}")
        return "Error during download", None, None, None, None, None, None

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
    wait = WebDriverWait(driver, 10)

    try:
        # Accept Cookies options (if necessary)
        try:
            accept_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="CybotCookiebotDialogBodyLevelButtonLevelOptinAllowallSelection"]')))
            accept_button.click()
        except Exception:
            pass  # If no cookie button found

        # Find the SDS button
        sds_link = driver.find_element(By.CLASS_NAME, "sds_ajaxlist")
        driver.execute_script("arguments[0].click();", sds_link)

        pdf_link = wait.until(EC.visibility_of_element_located((By.XPATH, "//a[@title='SDS Taiwan (chinese)']")))
        pdf_url = pdf_link.get_attribute("href")

        response = requests.get(pdf_url)

        # File name
        file_name = pdf_url.split('/')[-1]

        if response.status_code == 200:
            file_path = os.path.join(folder_name, file_name)
            with open(file_path, 'wb') as f:
                f.write(response.content)

            # Extract information from the downloaded PDF
            cas_num, ch_name, en_name, physical_state, density = pdf_to_text_itwreagents(file_path)
            return "Download successfully", file_name, cas_num, ch_name, en_name, physical_state, density
        else:
            return "Fail to download", None, None, None, None, None, None

    except Exception as e:
        print(f"An error occurred: {e}")
        return "Error during download", None, None, None, None, None, None


def download_sds_from_scbt(driver, folder_name):
    wait = WebDriverWait(driver, 10)

    try:
        # Check if the current URL contains the Chinese path
        if '/zh/' in driver.current_url:
            driver.delete_all_cookies()
            # Replace the Chinese path with the English path
            english_url = driver.current_url.replace('/zh/', '/')
            driver.get(english_url)
            driver.refresh()
            wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))

        # Expand SDS page
        def click_sds_button_with_js(driver):
            sds_button = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "button[data-gtm-event-id='certficateAnalysisTab']")))
            driver.execute_script("arguments[0].click();", sds_button)

        click_sds_button_with_js(driver)

        # Get the PDF download link
        submit_button = driver.find_element(By.CSS_SELECTOR, "a.submitBtn")
        pdf_url = submit_button.get_attribute("href")

        # Download the PDF
        response = requests.get(pdf_url)
        file_name = pdf_url.split('/')[-1].split('?')[0]

        if response.status_code == 200:
            file_path = os.path.join(folder_name, file_name)
            with open(file_path, 'wb') as f:
                f.write(response.content)

            # Extract information from the downloaded PDF
            cas_num, ch_name, en_name, physical_state, density = pdf_to_text_scbt(file_path)
            return "Download successfully", file_name, cas_num, ch_name, en_name, physical_state, density
        else:
            return "Fail to download", None, None, None, None, None, None

    except Exception as e:
        print(f"An error occurred: {e}")
        return "Error during download", None, None, None, None, None, None


def download_from_thermofisher(driver, folder_name, keyword):
    try:
        driver.delete_all_cookies()
        wait = WebDriverWait(driver, 10)

        # Accept Cookies options (if necessary)
        try:
            accept_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="truste-consent-button"]')))
            accept_button.click()
        except Exception:
            pass  # If no cookie button found

        # Find and click the SDS button
        sds_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[span[contains(text(), 'SDS')]]")))
        sds_button.click()

        # Handle product dropdown options
        try:
            # Check if the product dropdown is present
            product_dropdown = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'c-dropdown__selected-option')))
            if product_dropdown.is_displayed():
                product_dropdown.click()
                wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'c-dropdown__inner-options')))
                options = driver.find_elements(By.CLASS_NAME, 'c-dropdown__option')
                product_number = ''.join(re.findall(r'\d+', keyword))

                for option in options:
                    if option.text.strip() == product_number:
                        option.click()
                        break
                    else:
                        option.click()
                else:
                    return "Fail to download", None, None, None, None, None, None
        except Exception:
            print("Product dropdown not found, proceeding without it.")
            pass

        # Handle language selection and download
        
        language_dropdown = driver.find_element(By.CSS_SELECTOR, "#modal > div > div > div.c-modal__content > div > div:nth-child(2) > div.c-dropdown > div > div.c-dropdown__selected-option")
        driver.execute_script("arguments[0].scrollIntoView(true);", language_dropdown)
        language_dropdown.click()
        chinese_option = driver.find_element(By.XPATH, "//div[contains(@class, 'c-dropdown__option') and contains(text(), 'Chinese (Traditional)')]")
        ActionChains(driver).move_to_element(chinese_option).click(chinese_option).perform()
        download_button = driver.find_element(By.XPATH, '//*[@id="modal"]/div/div/div[4]/button[1]')
        download_button.click()
        
        # Wait for new file to appear in the download folder
        file_name = wait_for_new_file(folder_name, timeout=30)
        
        if file_name:
            file_path = os.path.join(folder_name, file_name)
            # Extract PDF information
            cas_num, ch_name, en_name, physical_state, density = pdf_to_text_thermofisher(file_path)
            return "Downloaded successfully", file_name, cas_num, ch_name, en_name, physical_state, density
        else:
            return "Download failed", None, None, None, None, None, None

    except Exception as e:
        print(f"An error occurred: {e}")
        return "Error during download", None, None, None, None, None, None

def wait_for_new_file(folder_path, timeout=30):
    """Wait for a new file to appear in the folder and return its name."""
    initial_files = set(os.listdir(folder_path))
    end_time = time.time() + timeout

    while time.time() < end_time:
        current_files = set(os.listdir(folder_path))
        new_files = current_files - initial_files
        if new_files:
            for file_name in new_files:
                if file_name.lower().endswith('.pdf'):
                    # Remove everything after '.pdf'
                    clean_file_name = file_name.split('.pdf')[0] + '.pdf'
                    return clean_file_name
        time.sleep(1)  # Check every second

    return None  # No new file within the timeout

def download_from_usp(driver, folder_name, keyword):
    try:
        cat_number = keyword.split(' ')[-1]
        url = f'https://static.usp.org/pdf/EN/referenceStandards/msds/{cat_number}.pdf'
        response = requests.get(url)

        if response.status_code == 200:
            file_path = os.path.join(folder_name, f'{cat_number}.pdf')
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            # Extract information from the downloaded PDF
            cas_num, ch_name, en_name, physical_state, density = pdf_to_text_usp(file_path)
            return "Download successfully", f'{cat_number}.pdf', cas_num, ch_name, en_name, physical_state, density
        else:
            # If direct download fails, try downloading from the website
            wait = WebDriverWait(driver, 10)
            sds_button = wait.until(EC.visibility_of_element_located((By.XPATH, '//a[contains(text(), "Safety data sheet.pdf")]')))
            sds_button.click()

            file_name = keyword.split(' ')[-1]
            file_path = os.path.join(folder_name, f'{file_name}.pdf')
            if wait_for_file_download_completion(file_path):
                cas_num, ch_name, en_name, physical_state, density = pdf_to_text_usp(file_path)
                return "Download successfully", f'{file_name}.pdf', cas_num, ch_name, en_name, physical_state, density
            else:
                return "Fail to download", None, None, None, None, None, None

    except Exception as e:
        print(f"An error occurred: {e}")
        return "Error during download", None, None, None, None, None, None


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
    download_results, file_names, cas_nums, ch_names, en_names, physical_states, densities = [], [], [], [], [], [], []
    for keyword in keyword_list:
        print(f'Start downloading SDS for {keyword}')
        try:
            download_result, file_name, cas_number, ch_name, en_name, physical_state, density = download_sds(driver, keyword, folder_name)
            print(f'Download complete for {keyword}')
        except Exception as e:
            print(f'Error during download for {keyword}: {e}')
            download_result, file_name, cas_number, ch_name, en_name, physical_state, density = 'Error', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A'

        download_results.append(download_result)
        file_names.append(file_name or 'N/A')
        cas_nums.append(cas_number or 'N/A')
        ch_names.append(ch_name or 'N/A')
        en_names.append(en_name or 'N/A')
        physical_states.append(physical_state or 'N/A')
        densities.append(density or 'N/A')

    # Quit the driver after completion
    driver.quit()

    # Save the download results
    df['download_result'] = download_results
    df['file_name'] = file_names
    df['cas_number'] = cas_nums
    df['chinese_name'] = ch_names
    df['english_name'] = en_names
    df['physical_state'] = physical_states
    df['density'] = densities
    df.to_excel("sds_results_file.xlsx", index=False)

if __name__ == '__main__':
    main()
    