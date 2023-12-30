from pypdf import PdfReader
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup

def pdf_to_text_sigma(pdf_file):
    try:
        with open(pdf_file, 'rb') as file:
            pdf_reader = PdfReader(file)
            text = ''
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()
        
        # Create a list from the text
        lines = text.split('\n')
        rows = [line.strip().split('\t') for line in lines]
        
        cas_number, ch_name, chemical_name, physical_state, density = None, None, None, None, None

        # Find indices of 'Section 3:' and 'Section 4:'
        section_3_start = rows.index(['Section 3:'])
        section_4_start = text.find('部分 4:', section_3_start)

        # Extract text between 'Section 3:' and 'Section 4:'
        section_3_text = text[section_3_start:section_4_start].strip()
        # print(section_3_text)

        # Find CAS number
        cas_number_match = re.search(r'No\.\) : (\d{5}-\d{2}-\d)', section_3_text)
        if cas_number_match:
            cas_number = cas_number_match.group(1)
        else:
            cas_number = None

        # Find chemical name
        ch_name_match = re.search(r'成分 分類 濃度或濃度範圍\s*([^\s]+)\s*([^\s]+)', section_3_text)
        if ch_name_match:
            ch_name = ch_name_match.group(2)
            chemical_name = ch_name_match.group(2)
        else:
            ch_name = None
            chemical_name = None
        
        # Extract relevant data
        for i, row in enumerate(rows):
            for element in row:
                if '化學品名稱' in element:
                    ch_name = element.split('化學品名稱', 1)[1].strip()
                if '物理狀態' in element:
                    try:
                        physical_state = element.split('物理狀態', 1)[1].strip()
                    except IndexError:
                        pass

                if 'No.)' in element:
                    try:
                        cas_number = element.split('No.)', 1)[1].split(':', 1)[1].strip().replace(' ', '')
                    except (IndexError, ValueError):
                        pass

                if '化學品名稱' in element:
                    try:
                        chemical_name = element.split('化學品名稱', 1)[1]
                        chemical_name = re.sub(r'[^a-zA-Z\s]', '', chemical_name).strip()
                    except IndexError:
                        pass
                
                if cas_number and physical_state == '液體':
                    for i, row in enumerate(rows):
                        for element in row:
                            if '相對密度' in element:
                                try:
                                    density = element.split('相對密度', 1)[1].strip()
                                except IndexError:
                                    pass
        print(cas_number, ch_name, chemical_name, physical_state, density)
        return cas_number, ch_name, chemical_name, physical_state, density
    except Exception as e:
        return None, None, None, None, None
    
pdf_file = 'SDS_downloads/213462.pdf'
pdf_to_text_sigma(pdf_file)
