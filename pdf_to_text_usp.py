import re
from PyPDF2 import PdfReader

def extract_info_from_pdf(pdf_file):
    try:
        # Load PDF document
        reader = PdfReader(pdf_file)

        # Get all pages text
        all_text = ""
        for page in reader.pages:
            page_text = page.extract_text().strip()
            lines = page_text.split('\n')
            non_empty_lines = [line for line in lines if line.strip() != '']
            cleaned_text = '\n'.join(non_empty_lines)
            all_text += cleaned_text + '\n'

        # Extract paragraphs starting with numbers
        paragraphs = re.findall(r'(\d+\..*?)(?=\n\d+\.)', all_text, re.DOTALL)

        # Store each paragraph in a separate variable
        for i, paragraph in enumerate(paragraphs, 1):
            vars()['paragraph_' + str(i)] = paragraph.strip()

        # Extract the product identifier and CAS number from the identification paragraph
        identify_paragraph = paragraphs[0]
        product_identifier = re.findall(r'\s*(.+?)Product identifier', identify_paragraph)[0].strip()
        cas_numbers = re.findall(r'(\d+[-\d]+)\sCAS number', identify_paragraph)[0]

        # Extract physical state from the property paragraph
        property_paragraph = paragraphs[8]
        physical_state = re.findall(r'\s*(.+?)Physical state', property_paragraph)[0].strip()
        physical_state = re.sub(r'[^\w\s]', '', physical_state)

        # Initialize relative_density as None
        relative_density = None

        # If physical state is liquid, then get the relative density
        if physical_state == 'Liquid':
            relative_density = re.findall(r'Relative density\s*(.+?)\s*', property_paragraph)[0].strip()
            relative_density = re.sub(r'[^\w\s]', '', relative_density)

        return product_identifier, cas_numbers, physical_state, relative_density

    except Exception as e:
        print(f"Error extracting information from PDF: {str(e)}")
        return None, None, None, None

pdf_file = 'SDS_downloads/1365000.pdf'
product_identifier, cas_numbers, physical_state, relative_density = extract_info_from_pdf(pdf_file)

if product_identifier and cas_numbers and physical_state:
    print(f"Product Identifier: {product_identifier}")
    print(f"CAS Numbers: {cas_numbers}")
    print(f"Physical State: {physical_state}")
    print(f"Relative Density: {relative_density}")
