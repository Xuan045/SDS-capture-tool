import PyPDF2
import pandas as pd

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ''
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text()
    return text

def create_list_from_text(text):
    lines = text.split('\n')
    rows = [line.split('\t') for line in lines]
    return rows

def extract_data(data_list):
    extracted_data = []
    for i, row in enumerate(data_list):
        for element in row:
            if '物理狀態' in element:
                _, value = element.split('物理狀態', 1)
                cleaned_value = value.strip()
                extracted_data.append((f"{cleaned_value}",))
                break
            elif any(keyword in element for keyword in ['No.)', '化學品名稱']):
                _, value = element.split(':', 1)
                cleaned_value = value.strip()
                extracted_data.append((f"{cleaned_value}",))
                break
    return extracted_data

# Replace 'SDS_downloads/213462.pdf' with the actual path to your Sigma Aldrich SDS PDF file
pdf_path = 'SDS_downloads/213462.pdf'

# Extract text from PDF
pdf_text = extract_text_from_pdf(pdf_path)

# Create a list from the text
data_list = create_list_from_text(pdf_text)

# Extract relevant data
extracted_data = extract_data(data_list)

# Create a DataFrame
df = pd.DataFrame(extracted_data, columns=['Extracted Data'])

# Save DataFrame to an Excel file
excel_file_path = 'extracted_data.xlsx'
df.to_excel(excel_file_path, index=False)

print(f"Data has been saved to {excel_file_path}")
