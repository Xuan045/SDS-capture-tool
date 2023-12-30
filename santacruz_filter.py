import PyPDF2

#open pdf
pdf_file = open('SDS_downloads/sc-358659.pdf', 'rb')
#pdf reader
pdf_reader = PyPDF2.PdfReader(pdf_file)

#extract whole pages
def extract_info_from_pdf(pdf_file):
        try:
                text = ''
                for i,page in enumerate(pdf_reader.pages): #get every page
                        text += pdf_reader.pages[i].extract_text().strip()
                        line_list = text.split('\n') #每行存成list
                # print(text)
                        # print(line_list)
                        allworld_list = []
                        for line in line_list: #一行中的字串存成list
                                world_list = line.split(' ') 
                                allworld_list.append(world_list)
                        # print(allworld_list)

                for info in allworld_list:
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
                        elif info [0] == 'Liquid' and info [1] == 'Density':
                                product_density = info[2]
                                # print(product_density)
                return product_name, product_cas, physical_state, product_density
        
        except Exception :
                # print(f"Error extracting information from PDF: ")
                return product_name, product_cas, physical_state, None
                    
product_name, product_cas, physical_state, product_density = extract_info_from_pdf(pdf_file)

if product_name and product_cas and physical_state:
    print(f"Product Identifier: {product_name}")
    print(f"CAS Numbers: {product_cas}")
    print(f"Physical State: {physical_state}")
    if physical_state == 'liquid':
        print(f"Relative Density: {product_density}")

pdf_file.close()

