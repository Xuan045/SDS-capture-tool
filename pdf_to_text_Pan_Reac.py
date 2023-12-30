from pypdf import PdfReader

def pdf_to_text_pan_reac(sds_input):
    pdf_file=sds_input
    reader=PdfReader(pdf_file)
    sentence=[]
    for i in range(0,len(reader.pages)):
        eachpage=reader.pages[i]
        text=eachpage.extract_text()
        text=text.split("\n")
        for j in range(0,len(text)):
            text[j]=text[j].strip("·").strip()
            sentence.append(text[j])
    for i in range(0,len(sentence)):
        if sentence[i]=="CAS 編號:":
            CAS_No=sentence[i+1]
        elif sentence[i].startswith("化學品中文(英文)名稱, 化學品俗名或商品名:"):
            Name_zh=sentence[i].split(":")[1]
        elif sentence[i].startswith("DOT "):
            if len((" ").join(sentence[i].split(" ")[1:len(sentence[i].split(" "))]).split(","))>1:
                Name_en=(" ").join(sentence[i].split(" ")[1:len(sentence[i].split(" "))]).split(",")[0]
            else:
                Name_en=(" ").join(sentence[i].split(" ")[1:len(sentence[i].split(" "))])
        elif sentence[i].startswith("形狀"):
            Form=(sentence[i].split(":")[1])
    if Form=="液體":
        for item in sentence:
            if item.startswith("密度"):
                Density=item.split(":")[1]
    else:
        Density=""
    
    return CAS_No, Name_zh, Name_en, Form, Density

sds_input="SDS_downloads/sds_361007_zh-tw.pdf"
print(pdf_to_text_pan_reac(sds_input))