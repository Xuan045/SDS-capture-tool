import PyPDF2

def extract_info_from_gibcopdf(pdf_file):
    #pdf reader
    pdf_reader = PyPDF2.PdfReader(pdf_file)

    #extract whole pages
    text = ''
    for i, page in enumerate(pdf_reader.pages): #get every page
            text += pdf_reader.pages[i].extract_text().strip()
    line_list = text.split('\n') #每行存成list
    # print(text)
    # print(line_list)
    allworld_list = []
    for i, line in enumerate(line_list): #一行中的字串存成lis
        if line[0] == '三': #中文名from成分辨識資料(另建一個list)
            x = line_list[i:i+4] 
            y = x[-1]
            z = y.split(' ')
            # print(z)
        else:
            world_list = line.split(' ') 
            allworld_list.append(world_list)
    # print(allworld_list)

    #將要的資料抓出來
    for item in allworld_list:
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
        elif item[0] == '比重':
            a = item[14:16] #比重數字和空格排列不同
            relative_density = ''.join(a).strip()
    return chinese_name, english_name, cas_num, physical_state, relative_density

pdf_file = 'SDS_downloads/Isopropanol_MTR_CGV4_TA.pdf'
chinese_name, english_name, cas_num, physical_state, relative_density = extract_info_from_gibcopdf(pdf_file)
print(f'CAS No.: {cas_num}')
print(f'中文名: {chinese_name}')
print(f'英文名: {english_name}')
print(f'物質型態: {physical_state}')
if physical_state == '液體':
    print(f'比重: {relative_density}')


# pdf_file.close()