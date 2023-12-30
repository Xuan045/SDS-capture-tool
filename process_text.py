from pypdf import PdfReader
import re

def pdf_to_text_thermofisher(pdf_file):
    try:
        with open(pdf_file, 'rb') as pdf_file:
            pdf_reader = PdfReader(pdf_file)
            text = ''
            for i, page in enumerate(pdf_reader.pages): #get every page
                    text += pdf_reader.pages[i].extract_text().strip()
            line_list = text.split('\n') #每行存成list

        all_words_list = []
        for i, line in enumerate(line_list): #一行中的字串存成lis
            if line[0] == '三': #中文名from成分辨識資料(另建一個list)
                x = line_list[i:i+4] 
                y = x[-1]
                z = y.split(' ')
            # print(z)
            else:
                world_list = line.split(' ') 
                all_words_list.append(world_list)

        chinese_name, english_name, cas_num, physical_state, relative_density = None, None, None, None, None
        for item in all_words_list:
            # for item2 in item:
            if item[0] == '产品说明:':
                chinese_name = item[-1]
                if chinese_name.isalpha() == True: #抓中文名from成分辨識資料
                    chinese_name = z[0]
            elif item[0] == 'Product':
                english_name_list = item[2:]
                english_name = ' '.join(english_name_list)
            elif item[0] == '化學文摘社登記號碼(CAS':
                cas_num = item[-1]
            elif item[0] == '物質狀態':
                physical_state = item[-1]
            elif item[0] == '比重' and physical_state == '液體':
                a = item[14:16] #比重數字和空格排列不同
                relative_density = ''.join(a).strip()

        return cas_num, chinese_name, english_name, physical_state, relative_density

    except Exception as e:
        # print(f"Error extracting information from PDF: {e}")
        return None, None, None, None, None


def pdf_to_text_scbt(pdf_file):
    product_cas, ch_name, product_name, physical_state, product_density = None, None, None, None, None
    try:
        pdf_reader = PdfReader(pdf_file)
        text = ''
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:  # Check if the page text is not None
                text += page_text.strip()

        lines = text.split('\n')  # Split text into lines
        all_words_list = [line.split(' ') for line in lines]  # Split each line into words

        for info in all_words_list:
            if info[0] == 'Product' and info[1] == 'Name':
                    product_name = info[2:]
                    product_name = ' '.join(product_name)
                    # print(product_name)
            elif info[0] == 'CAS' and info[1] == 'No':
                    product_cas = info[2]
                    # print(product_cas)
            elif info [0] == 'Physical' and info[1] == 'State':
                    physical_state = info[2]
                    # print(physical_state)
            elif info [0] == 'Liquid' and info [1] == 'Density' and physical_state == 'Liquid':
                    product_density = info[2]
                    print(product_density)
        return product_cas, ch_name, product_name, physical_state, product_density

    except Exception :
        # print(f"Error extracting information from PDF: ")
        return product_cas, ch_name, product_name, physical_state, product_density
    
    
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

        # Extract relevant data
        for i, row in enumerate(rows):
            for element in row:
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

        return cas_number, ch_name, chemical_name, physical_state, density
    except Exception as e:
        return None, None, None, None, None
    
def pdf_to_text_itwreagents(pdf_file):
    try:
        reader = PdfReader(pdf_file)
        sentence = []

        for i in range(len(reader.pages)):
            eachpage = reader.pages[i]
            text = eachpage.extract_text()

            # check if the page is not empty
            if text:
                text = text.split("\n")
                for j in range(len(text)):
                    text[j] = text[j].strip("·").strip()
                    sentence.append(text[j])

        CAS_No, Name_zh, Name_en, Form, Density = None, None, None, None, None

        for i in range(len(sentence)):
            if sentence[i] == "CAS 編號:" and i+1 < len(sentence):
                CAS_No = sentence[i + 1]
            elif sentence[i].startswith("化學品中文(英文)名稱, 化學品俗名或商品名:"):
                Name_zh = sentence[i].split(":")[1]
            elif sentence[i].startswith("DOT "):
                if len(" ".join(sentence[i].split(" ")[1:]).split(",")) > 1:
                    Name_en = " ".join(sentence[i].split(" ")[1:]).split(",")[0]
                else:
                    Name_en = " ".join(sentence[i].split(" ")[1:])
            elif sentence[i].startswith("形狀"):
                Form = sentence[i].split(":")[1]

        if Form == "液體":
            for item in sentence:
                if item.startswith("密度"):
                    Density = item.split(":")[1]

        return CAS_No, Name_zh, Name_en, Form, Density

    except Exception as e:
        print(f"An error occurred: {e}")
        return None, None, None, None, None


def pdf_to_text_usp(pdf_file):
    try:
        reader = PdfReader(pdf_file)

        all_text = ""
        for page in reader.pages:
            page_text = page.extract_text().strip()
            lines = page_text.split('\n')
            non_empty_lines = [line for line in lines if line.strip() != '']
            cleaned_text = '\n'.join(non_empty_lines)
            all_text += cleaned_text + '\n'
            
        cas_num, ch_name, en_name, physical_state, density = None, None, None, None, None

        # Extract paragraphs starting with numbers
        paragraphs = re.findall(r'(\d+\..*?)(?=\n\d+\.)', all_text, re.DOTALL)

        # Store each paragraph in a separate variable
        for i, paragraph in enumerate(paragraphs, 1):
            vars()['paragraph_' + str(i)] = paragraph.strip()

        # Extract the product identifier and CAS number from the identification paragraph
        identify_paragraph = paragraphs[0]
        en_name = re.findall(r'\s*(.+?)Product identifier', identify_paragraph)[0].strip()
        cas_num = re.findall(r'(\d+[-\d]+)\sCAS number', identify_paragraph)[0]

        # Extract physical state from the property paragraph
        property_paragraph = paragraphs[8]
        physical_state = re.findall(r'\s*(.+?)Physical state', property_paragraph)[0].strip()
        physical_state = re.sub(r'[^\w\s]', '', physical_state)

        # If physical state is liquid, then get the relative density
        if physical_state == 'Liquid':
            density = re.findall(r'Relative density\s*(.+?)\s*', property_paragraph)[0].strip()
            density = re.sub(r'[^\w\s]', '', density)

        return cas_num, ch_name, en_name, physical_state, density

    except Exception as e:
        print(f"Error extracting information from PDF: {str(e)}")
        return None, None, None, None, None
