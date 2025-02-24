import json
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz
import os
import re
from tqdm import tqdm




with open("merged_claims.json", 'r') as file:
    dataset = json.load(file)
html_folder = "saved_pages"

site_set = set()
samples_diffSite = {}
for sample in dataset:
    site = sample["url"].split("/")[2]
    if site not in samples_diffSite:
        samples_diffSite[site] = [sample["claim_id"]]
    else:
        samples_diffSite[site].append(sample["claim_id"])
    
num = 0
for k,v in samples_diffSite.items():
    print(k,len(v))
    num += len(v)
assert num == len(dataset)

print(samples_diffSite.keys())


def africacheck_process(html_code, target_text):
    soup = BeautifulSoup(html_code, "html.parser")
    similarity_threshold = 80

    matched_p_tag = None
    best_score = 0
    for p_tag in soup.find_all("p"):
        p_text = p_tag.get_text()
        score = fuzz.partial_ratio(target_text, p_text)
        if score > similarity_threshold and score > best_score:
            best_score = score
            matched_p_tag = p_tag

    if matched_p_tag:
        try:
            current_field_item = matched_p_tag.find_parent("div", class_="field__item")
            next_field_item = current_field_item.find_next_sibling("div", class_="field__item")
            
            if next_field_item:
                following_text = next_field_item.get_text(separator="\n", strip=True)
                return re.sub(r'\s+', ' ', following_text).strip()
            else:
                return None
        except:
            return None
    else:
        return None

num = 0
sample_ids = samples_diffSite["africacheck.org"]
res = []
wrong_conut = 0
for sample_id in tqdm(sample_ids):
    html_path = os.path.join(html_folder,f"{sample_id}.html")
    with open(html_path, "r", encoding="utf-8") as file:
        html_code = file.read()
    target_text = dataset[sample_id - 1]["claim"]
    res_dict = dataset[sample_id - 1].copy()
    extracted_raw_text = africacheck_process(html_code, target_text)
    res_dict["raw_evidence"] = extracted_raw_text
    res.append(res_dict)
    if extracted_raw_text == None:
        wrong_conut += 1
with open(r'claims_w_raw_evidence\africacheck_org.json', 'w') as json_file:
    json.dump(res, json_file, indent=4)
print("wrong_conut:", wrong_conut)

    


def politifact_process(html_code, target_text):
    similarity_threshold = 80
    
    soup = BeautifulSoup(html_code, "html.parser")

    section_tag = soup.find('section', class_='o-stage')
    if section_tag:
        statement_quote_div = section_tag.find('div', class_='m-statement__quote')
        if statement_quote_div:
            statement_quote_text = statement_quote_div.get_text(strip=True)
            score = fuzz.partial_ratio(target_text, statement_quote_text)
            
            if score > similarity_threshold:
                short_on_time_div = soup.find('div', class_='short-on-time')
                if short_on_time_div:
                    content = []
                    for child in short_on_time_div.children:
                        if child.name == 'p':
                            content.append(child.get_text(strip=True))
                        elif child.name == 'ul': 
                            content.extend(
                                li.get_text(strip=True) for li in child.find_all('li')
                            )
                    if content:
                        return "\n\n".join(content).strip()
                    
            following_paragraphs = []
            next_tag = statement_quote_div.find_next()

            while next_tag:
                if next_tag.name == 'div':
                    break
                
                if next_tag.name == 'p':
                    paragraph_text = ""

                    for element in next_tag.children:
                        if element.name == 'em' or element.name == 'strong':
                                continue
                        if isinstance(element, str):
                            paragraph_text += element
                        else:
                            paragraph_text += element.get_text()
                    if paragraph_text:
                        following_paragraphs.append(paragraph_text.strip())

                next_tag = next_tag.find_next()
            return "\n\n".join(following_paragraphs)
    

    article_tag = soup.find('article', class_='m-textblock')

    if article_tag:
        matched_tag = None
        best_score = 0

        for tag in article_tag.find_all(["p"]):  
            tag_text = tag.get_text(strip=True)
            score = fuzz.partial_ratio(target_text, tag_text)
            if score > similarity_threshold and score > best_score:
                best_score = score
                matched_tag = tag
        
        for tag in article_tag.find_all(["div"]):  
            tag_text = tag.get_text(strip=True)
            score = fuzz.partial_ratio(target_text, tag_text)
            if score > similarity_threshold and score > best_score:
                best_score = score
                matched_tag = tag

        if matched_tag:
            following_paragraphs = []
            next_tag = matched_tag.find_next()
            
            while next_tag:
                if next_tag.name == 'div':
                    break
                
                if next_tag.name == 'p':
                    paragraph_text = ""

                    for element in next_tag.children:
                        if element.name == 'em' or element.name == 'strong':
                            continue
            
                        if isinstance(element, str):
                            paragraph_text += element
                        else:
                            paragraph_text += element.get_text()
                    following_paragraphs.append(paragraph_text.strip())
                next_tag = next_tag.find_next()

            formatted_text = "\n\n".join(following_paragraphs)
            return formatted_text
        else:
            return None 
    else:
        return None  

num = 0
sample_ids = samples_diffSite["www.politifact.com"]
res = []
wrong_conut = 0
for sample_id in tqdm(sample_ids):
    html_path = os.path.join(html_folder,f"{sample_id}.html")
    with open(html_path, "r", encoding="utf-8") as file:
        html_code = file.read()
    target_text = dataset[sample_id - 1]["claim"]
    res_dict = dataset[sample_id - 1].copy()
    extracted_raw_text = politifact_process(html_code, target_text)
    # print(extracted_raw_text)
    # break
    res_dict["raw_evidence"] = extracted_raw_text
    res.append(res_dict)
    # break
    if extracted_raw_text == None or extracted_raw_text == "":
        wrong_conut += 1
    # if sample_id >= 900:
    #     break
with open(r'claims_w_raw_evidence\www_politifact_com.json', 'w') as json_file:
    json.dump(res, json_file, indent=4)
print("wrong_conut:", wrong_conut)


def leadstories_process(html_code):
    soup = BeautifulSoup(html_code, "html.parser")
    content_div = soup.find('div', class_='mod-full-article-content rte-container')
    
    if not content_div:
        return None
    
    blockquote = content_div.find('blockquote')
    
    if not blockquote:
        return None
    
    content_after_blockquote = []
    for element in blockquote.find_next_siblings():
        if element.get_text(strip=True):  
            content_after_blockquote.append(element.get_text())
    
    return "\n".join(content_after_blockquote).strip()

num = 0
sample_ids = samples_diffSite["leadstories.com"]
res = []
wrong_conut = 0
for sample_id in tqdm(sample_ids):
    html_path = os.path.join(html_folder,f"{sample_id}.html")
    with open(html_path, "r", encoding="utf-8") as file:
        html_code = file.read()
    # target_text = dataset[sample_id - 1]["claim"]
    res_dict = dataset[sample_id - 1].copy()
    extracted_raw_text = leadstories_process(html_code)
    # print(extracted_raw_text)
    # break
    res_dict["raw_evidence"] = extracted_raw_text
    res.append(res_dict)
    # break
    if extracted_raw_text == None or extracted_raw_text == "":
        wrong_conut += 1
    # if sample_id >= 900:
    #     break
with open(r'claims_w_raw_evidence\leadstories_com.json', 'w') as json_file:
    json.dump(res, json_file, indent=4)
print("wrong_conut:", wrong_conut)



def factcheck_afp_process(html_code):
    soup = BeautifulSoup(html_code, 'html.parser')
    wrapper_div = soup.find('div', class_='wrapper-body')
    if not wrapper_div:
        return None
    
    paragraphs = wrapper_div.find_all('p')   
    extracted_text = []
    for p in paragraphs:
        p_text = p.get_text()
        
        extracted_text.append(p_text)
    
    return "\n".join(extracted_text)


num = 0
sample_ids = samples_diffSite["factcheck.afp.com"]
res = []
wrong_conut = 0
for sample_id in tqdm(sample_ids):
    html_path = os.path.join(html_folder,f"{sample_id}.html")
    with open(html_path, "r", encoding="utf-8") as file:
        html_code = file.read()
    # target_text = dataset[sample_id - 1]["claim"]
    res_dict = dataset[sample_id - 1].copy()
    extracted_raw_text = factcheck_afp_process(html_code)
    # print(extracted_raw_text)
    # break
    res_dict["raw_evidence"] = extracted_raw_text
    res.append(res_dict)
    # break
    if extracted_raw_text == None or extracted_raw_text == "":
        wrong_conut += 1
    # if sample_id >= 900:
    # break
with open(r'claims_w_raw_evidence\factcheck_afp_com.json', 'w') as json_file:
    json.dump(res, json_file, indent=4)
print("wrong_conut:", wrong_conut)



# def factcheck_process(html):
#     # 140
#     pass

def checkyourfact_process(html_code):
    soup = BeautifulSoup(html_code, 'html.parser')
    text_tag = soup.find('div', id="ob-read-more-selector")
    # print(text_tag)
    if not text_tag:
        return None
    fact_check_tag = text_tag.find('p', string=lambda x: x and "Fact Check:" in x)
    # print(fact_check_tag)
    if not fact_check_tag:
        return None
    extracted_text = []
    for sibling in fact_check_tag.find_all_next():
        if sibling.name == 'em':
            continue
        elif sibling.name == 'p':
            extracted_text.append(sibling.get_text())
            # extracted_text.extend(texts)
    
    return '\n'.join(extracted_text).strip()
    
num = 0
sample_ids = samples_diffSite["checkyourfact.com"]
res = []
wrong_conut = 0
for sample_id in tqdm(sample_ids):
    html_path = os.path.join(html_folder,f"{sample_id}.html")
    with open(html_path, "r", encoding="utf-8") as file:
        html_code = file.read()
    # target_text = dataset[sample_id - 1]["claim"]
    res_dict = dataset[sample_id - 1].copy()
    extracted_raw_text = checkyourfact_process(html_code)
    # print(extracted_raw_text)
    # break
    res_dict["raw_evidence"] = extracted_raw_text
    res.append(res_dict)
    # break
    if extracted_raw_text == None or extracted_raw_text == "":
        wrong_conut += 1
    # if sample_id >= 900:
    # break
with open(r'claims_w_raw_evidence\checkyourfact_com.json', 'w') as json_file:
    json.dump(res, json_file, indent=4)
print("wrong_conut:", wrong_conut)




def verafiles_process(html_code):
    soup = BeautifulSoup(html_code, 'html.parser')
    content_div = soup.find('div', class_='entry-content space-y-6')
    result_text = []
    if content_div:
        for tag in content_div.find_all(['p', 'h5']):
            if tag.name == 'h5' and tag.get('id') == 'reader-request-form':
                break
            else:
                for unwanted_tag in tag.find_all(['em', 'h5']):
                    unwanted_tag.decompose()
                result_text.append(tag.get_text())

    return '\n'.join(result_text).strip()


num = 0
sample_ids = samples_diffSite["verafiles.org"]
res = []
wrong_conut = 0
for sample_id in tqdm(sample_ids):
    html_path = os.path.join(html_folder,f"{sample_id}.html")
    with open(html_path, "r", encoding="utf-8") as file:
        html_code = file.read()
    # target_text = dataset[sample_id - 1]["claim"]
    res_dict = dataset[sample_id - 1].copy()
    extracted_raw_text = verafiles_process(html_code)
    # print(extracted_raw_text)
    # break
    res_dict["raw_evidence"] = extracted_raw_text
    res.append(res_dict)
    # break
    if extracted_raw_text == None or extracted_raw_text == "":
        wrong_conut += 1
    # if sample_id >= 900:
    # break
with open(r'claims_w_raw_evidence\verafiles_org.json', 'w') as json_file:
    json.dump(res, json_file, indent=4)
print("wrong_conut:", wrong_conut)




def newsweek_process(html_code):
    soup = BeautifulSoup(html_code, 'html.parser')
    fact_check_tag = soup.find('p', class_='fact-check false-editable', string=lambda x: x and "The Facts" in x)
    end_check_tag = soup.find('p', class_='fact-check false-editable', string=lambda x: x and "The Ruling" in x)
    if not fact_check_tag:
        return None
    extracted_text = []
    for sibling in fact_check_tag.find_all_next():
        if sibling.name == 'em':
            continue
        elif sibling == end_check_tag:
            break
        elif sibling.name == 'p':
            extracted_text.append(sibling.get_text())
        else:
            continue
    return '\n'.join(extracted_text).strip()

num = 0
sample_ids = samples_diffSite["www.newsweek.com"]
res = []
wrong_conut = 0
for sample_id in tqdm(sample_ids):
    html_path = os.path.join(html_folder,f"{sample_id}.html")
    with open(html_path, "r", encoding="utf-8") as file:
        html_code = file.read()
    # target_text = dataset[sample_id - 1]["claim"]
    res_dict = dataset[sample_id - 1].copy()
    extracted_raw_text = newsweek_process(html_code)
    # print(extracted_raw_text)
    # break
    res_dict["raw_evidence"] = extracted_raw_text
    res.append(res_dict)
    # break
    if extracted_raw_text == None or extracted_raw_text == "":
        wrong_conut += 1
    # if sample_id >= 900:
    # break
with open(r'claims_w_raw_evidence\www_newsweek_com.json', 'w') as json_file:
    json.dump(res, json_file, indent=4)
print("wrong_conut:", wrong_conut)



def fullfact_process(html_code):
    soup = BeautifulSoup(html_code, 'html.parser')
    cms_content_div = soup.find('div', class_='cms-content')
    
    if not cms_content_div:
        return None
    extracted_text = []
    for sibling in cms_content_div.find_all('p', recursive=False):
        extracted_text.append(sibling.get_text())
    
    return '\n'.join(extracted_text).strip()

num = 0
sample_ids = samples_diffSite["fullfact.org"]
res = []
wrong_conut = 0
for sample_id in tqdm(sample_ids):
    html_path = os.path.join(html_folder,f"{sample_id}.html")
    with open(html_path, "r", encoding="utf-8") as file:
        html_code = file.read()
    # target_text = dataset[sample_id - 1]["claim"]
    res_dict = dataset[sample_id - 1].copy()
    extracted_raw_text = fullfact_process(html_code)
    # print(extracted_raw_text)
    # break
    res_dict["raw_evidence"] = extracted_raw_text
    res.append(res_dict)
    # break
    if extracted_raw_text == None or extracted_raw_text == "":
        wrong_conut += 1
    # if sample_id >= 900:
    # break
with open(r'claims_w_raw_evidence\fullfact_org.json', 'w') as json_file:
    json.dump(res, json_file, indent=4)
print("wrong_conut:", wrong_conut)

def usatoday_process(html_code):
    soup = BeautifulSoup(html_code, 'html.parser')
    rating_tag = soup.find('h2', string=re.compile(r"^Our rating:"))
    sources_tag = soup.find('h2',  string=re.compile(r"^Our fact-check sources:"))
    if not sources_tag:
        sources_tag = soup.find('h2',  string=re.compile(r"^Our sources:"))
    p_texts = []
    # print(sources_tag)
    if rating_tag and sources_tag:
        ss = True
        next = None
        while ss:
            for nn in rating_tag.find_next_siblings():
                # print(nn.name)
                if nn.name == 'h2':
                    # print(nn)
                    ss = False
                    break
                else:
                    next = nn
                
        # rating_tag = rating_tag.find_next()
        for sibling in next.find_next_siblings():
            if sibling == sources_tag:
                break
            if sibling.name == 'p':
                if sibling.find('strong'):
                    continue
                p_texts.append(sibling.get_text())
    if '\n'.join(p_texts).strip() == "":
        start = soup.find('h2',  string=re.compile(r"^The claim:"))
        end = soup.find('h2', string=re.compile(r"^Our rating:"))
        if start:
            # print(start)
            ss = True
            next = None
            # print(next)
            while ss:
                for nn in start.find_next_siblings():
                    # print(nn.name)
                    if nn.name == 'h2':
                        # print(nn)
                        ss = False
                        break
                    else:
                        next = nn
            for sibling in next.find_next_siblings():
                if sibling == end:
                    break
                if sibling.name == 'p':
                    if sibling.find('strong'):
                        continue
                    p_texts.append(sibling.get_text())

    return '\n'.join(p_texts).strip()

num = 0
sample_ids = samples_diffSite["www.usatoday.com"]
res = []
wrong_conut = 0
for sample_id in tqdm(sample_ids):
    html_path = os.path.join(html_folder,f"{sample_id}.html")
    with open(html_path, "r", encoding="utf-8") as file:
        html_code = file.read()
    # target_text = dataset[sample_id - 1]["claim"]
    res_dict = dataset[sample_id - 1].copy()
    extracted_raw_text = usatoday_process(html_code)
    # print(extracted_raw_text)
    # break
    res_dict["raw_evidence"] = extracted_raw_text
    res.append(res_dict)
    # break
    if extracted_raw_text == None or extracted_raw_text == "":
        wrong_conut += 1
    # if sample_id >= 900:
    # break
with open(r'claims_w_raw_evidence\www_usatoday_com.json', 'w') as json_file:
    json.dump(res, json_file, indent=4)
print("wrong_conut:", wrong_conut)

# def altnews_process(html):
#     # 143
#     pass

def indiatoday_process(html_code):
    soup = BeautifulSoup(html_code, 'html.parser')
    h3_tags = soup.find_all('h3')
    texts_from_second_h3 = []
    # print(h3_tags)
    if len(h3_tags) >= 2:
        second_h3_tag = h3_tags[1]
        # start = second_h3_tag.copy()
        # .find_parent().find_next().find_next()
        # print(second_h3_tag.find_next().find_next().find_next())
        # print(second_h3_tag.find_next_siblings())
        while True:
            second_h3_tag = second_h3_tag.find_next()
            if second_h3_tag is None:
                break
            # print(second_h3_tag.parent,start.parent)
            if second_h3_tag.name == 'p':
                # print(sibling)
                texts_from_second_h3.append(second_h3_tag.get_text())
    
    return '\n'.join(texts_from_second_h3).strip()

num = 0
sample_ids = samples_diffSite["www.indiatoday.in"]
res = []
wrong_conut = 0
for sample_id in tqdm(sample_ids):
    # if sample_id != 1328:
    #     continue
    html_path = os.path.join(html_folder,f"{sample_id}.html")
    with open(html_path, "r", encoding="utf-8") as file:
        html_code = file.read()
    # target_text = dataset[sample_id - 1]["claim"]
    res_dict = dataset[sample_id - 1].copy()
    extracted_raw_text = indiatoday_process(html_code)
    # print(extracted_raw_text)
    # break
    res_dict["raw_evidence"] = extracted_raw_text
    res.append(res_dict)
    # break
    if extracted_raw_text == None or extracted_raw_text == "":
        wrong_conut += 1
    # if sample_id >= 900:
    # break
with open(r'claims_w_raw_evidence\www_indiatoday_in.json', 'w') as json_file:
    json.dump(res, json_file, indent=4)
print("wrong_conut:", wrong_conut)

def newsmeter_process(html_code):
    soup = BeautifulSoup(html_code, "html.parser")
    news_div = soup.find('div', class_='py-3 news-story')
    first_h2 = news_div.find('h2')
    if not first_h2:
        first_h2 = news_div.find('p', string=re.compile(r"^Fact Check"))
    if not first_h2:
        first_h2 = news_div.find('b', string=re.compile(r"^Fact Check"))
    if not first_h2:
        first_h2 = news_div.find('b', string=re.compile(r"^FACT CHECK"))

    # print(news_div.find('p',text=lambda text: text and "FACT CHECK:" in text))
    # print(first_h2)
    extracted_texts = []
    if first_h2:
        h2_found = False
        if first_h2.find_parent('div') == news_div:
            # print(news_div.find_all())
            # for element in news_div.find_all(): 
            for element in first_h2.find_next_siblings():  
                extracted_texts.append(element.get_text())
            return '\n'.join(extracted_texts).strip()
        parent_div = first_h2.find_parent('div')
        # print(parent_div)
        for child in news_div.find_all(recursive=False):
            if child == parent_div:
                h2_found = True  
                # print(first_h2.find_next_siblings())
                if first_h2.name == 'b':
                    first_h2 = first_h2.find_parent()
                for element in first_h2.find_next_siblings():  
                    extracted_texts.append(element.get_text())
            elif h2_found:
                # print(child)
                if child.name == 'div':  
                    # print(child.find_next())
                    for element in child.find_all():
                        if element.name == 'p':
                            extracted_texts.append(element.get_text())
    return '\n'.join(extracted_texts).strip()


num = 0
sample_ids = samples_diffSite["newsmeter.in"]
res = []
wrong_conut = 0
for sample_id in tqdm(sample_ids):
    # if sample_id != 2477:
    #     continue
    html_path = os.path.join(html_folder,f"{sample_id}.html")
    with open(html_path, "r", encoding="utf-8") as file:
        html_code = file.read()
    # target_text = dataset[sample_id - 1]["claim"]
    res_dict = dataset[sample_id - 1].copy()
    extracted_raw_text = newsmeter_process(html_code)
    # print(extracted_raw_text)
    # break
    res_dict["raw_evidence"] = extracted_raw_text
    res.append(res_dict)
    # break
    if extracted_raw_text == None or extracted_raw_text == "":
        wrong_conut += 1
    # if sample_id >= 900:
    # break
with open(r'claims_w_raw_evidence\newsmeter_in.json', 'w') as json_file:
    json.dump(res, json_file, indent=4)
print("wrong_conut:", wrong_conut)


def vishvasnews_process(html_code):
    soup = BeautifulSoup(html_code, 'html.parser')
    investigation_tag = soup.find('h2', class_='wp-block-heading', string=re.compile(r"^Investigation"))
    # print(investigation_tag)
    if not investigation_tag:
        investigation_tag = soup.find('h2', class_='wp-block-heading', string=re.compile(r"^ Investigation"))
    if not investigation_tag:
        all_p_tags = soup.find_all('p')
        for p_tag in all_p_tags:
            # if p_tag.get_text(strip=True) == "Investigation:" or strong_tag.get_text(strip=True) == "Investigation":

            strong_tag = p_tag.find('strong')
            if (strong_tag and ((strong_tag.get_text(strip=True) == "Investigation:" or strong_tag.get_text(strip=True) == "Investigation") or (strong_tag.get_text(strip=True) == "Vishvas News Investigation:" or strong_tag.get_text(strip=True) == "Vishvas News Investigation:"))):
                investigation_tag = p_tag
                break 
            # elif p_tag.get_text(strip=True) == "Investigation:" or strong_tag.get_text(strip=True) == "Investigation":
            #     investigation_tag = p_tag
            #     break 
    # print(investigation_tag)
    if not investigation_tag:
        investigation_tag = soup.find('p', string=re.compile(r"^Investigation"))
    if not investigation_tag:
        investigation_tag = soup.find('p', string=re.compile(r"^Vishvas News Investigation"))
    if not investigation_tag:
        investigation_tag = soup.find('strong', string=re.compile(r"^Investigation"))
    if not investigation_tag:
        h2_tags = soup.find_all('h2', class_='wp-block-heading')
        for h2 in h2_tags:
            strong_tag = h2.find('strong')  
            if strong_tag and "Investigation" in strong_tag.get_text():
                investigation_tag = h2
                
    extracted_texts = []
    if investigation_tag:
        current = investigation_tag.find_next()
        while current:
            if current.name == 'p'  and current.find('strong')   and current.strong.get_text(strip=True) == "Conclusion:":
                break
            if current.name:
                extracted_texts.append(current.get_text())
            current = current.find_next()
    return '\n'.join(extracted_texts).strip()


num = 0
sample_ids = samples_diffSite["www.vishvasnews.com"]
res = []
wrong_conut = 0
for sample_id in tqdm(sample_ids):
    # if sample_id != 1457:
    #     continue
    html_path = os.path.join(html_folder,f"{sample_id}.html")
    with open(html_path, "r", encoding="utf-8") as file:
        html_code = file.read()
    # target_text = dataset[sample_id - 1]["claim"]
    res_dict = dataset[sample_id - 1].copy()
    extracted_raw_text = vishvasnews_process(html_code)
    # print(extracted_raw_text)
    # break
    res_dict["raw_evidence"] = extracted_raw_text
    res.append(res_dict)
    # break
    if extracted_raw_text == None or extracted_raw_text == "":
        wrong_conut += 1
    # if sample_id >= 900:
    # break
with open(r'claims_w_raw_evidence\www_vishvasnews_com.json', 'w') as json_file:
    json.dump(res, json_file, indent=4)
print("wrong_conut:", wrong_conut)

# def rappler_process(html_code):
#     # 121
#     pass

def factly_process(html_code):
    soup = BeautifulSoup(html_code, 'html.parser')
    investigation_tag = soup.find('div', class_='post-content description ')
    target_text = investigation_tag.find('blockquote', class_='wp-block-quote')
    extracted_texts = []
    if target_text:
        for sibling in target_text.find_next_siblings():
            extracted_texts.append(sibling.get_text())
    
    return '\n'.join(extracted_texts).strip()

num = 0
sample_ids = samples_diffSite["factly.in"]
res = []
wrong_conut = 0
for sample_id in tqdm(sample_ids):
    # if sample_id != 1457:
    #     continue
    html_path = os.path.join(html_folder,f"{sample_id}.html")
    with open(html_path, "r", encoding="utf-8") as file:
        html_code = file.read()
    # target_text = dataset[sample_id - 1]["claim"]
    res_dict = dataset[sample_id - 1].copy()
    extracted_raw_text = factly_process(html_code)
    # print(extracted_raw_text)
    # break
    res_dict["raw_evidence"] = extracted_raw_text
    res.append(res_dict)
    # break
    if extracted_raw_text == None or extracted_raw_text == "":
        wrong_conut += 1
    # if sample_id >= 900:
    # break
with open(r'claims_w_raw_evidence\factly_in.json', 'w') as json_file:
    json.dump(res, json_file, indent=4)
print("wrong_conut:", wrong_conut)


def boomlive_process(html_code):
    soup = BeautifulSoup(html_code, 'html.parser')
    investigation_tag = soup.find('div', class_='details-story-wrapper ')
    # if not investigation_tag:
    #     investigation_tag = soup.find('div', class_='details-story-wrapper')
    if not investigation_tag:
        investigation_tag = soup.find('div', class_='pasted-from-word-wrapper fact_Check')
    # print(investigation_tag)
    extracted_texts = []
    if investigation_tag:
        target_text = investigation_tag.find('h3')
        if target_text and ("fact" not in target_text.get_text().lower()):
            target_text = False

        if not target_text:
            target_text = investigation_tag.find('h2')
        if target_text and ("fact" not in target_text.get_text().lower()):
            target_text = False
        # print(target_text)
        if not target_text:
            
            all_p_tags = investigation_tag.find_all('p')
            for p_tag in all_p_tags:
                # if p_tag.get_text(strip=True) == "Investigation:" or strong_tag.get_text(strip=True) == "Investigation":
                # strong_tag = p_tag.find('span')
                if "fact" in p_tag.get_text().lower():
                # if (strong_tag and ((strong_tag.get_text(strip=True) == "Investigation:" or strong_tag.get_text(strip=True) == "Investigation") or (strong_tag.get_text(strip=True) == "Vishvas News Investigation:" or strong_tag.get_text(strip=True) == "Vishvas News Investigation:"))):
                    target_text = p_tag
                    break 
        if target_text:
            for sibling in target_text.find_next_siblings():
                if sibling.name in ["a","p"]:
                    extracted_texts.append(sibling.get_text())
    
    return '\n'.join(extracted_texts).strip()



num = 0
sample_ids = samples_diffSite["www.boomlive.in"]
res = []
wrong_conut = 0
for sample_id in tqdm(sample_ids):
    # if sample_id != 1969:
    #     continue
    html_path = os.path.join(html_folder,f"{sample_id}.html")
    with open(html_path, "r", encoding="utf-8") as file:
        html_code = file.read()
    # target_text = dataset[sample_id - 1]["claim"]
    res_dict = dataset[sample_id - 1].copy()
    extracted_raw_text = boomlive_process(html_code)
    # print(extracted_raw_text)
    # break
    res_dict["raw_evidence"] = extracted_raw_text
    res.append(res_dict)
    # break
    if extracted_raw_text == None or extracted_raw_text == "":
        wrong_conut += 1
    # if sample_id >= 900:
    # break
with open(r'claims_w_raw_evidence\www_boomlive_in.json', 'w') as json_file:
    json.dump(res, json_file, indent=4)
print("wrong_conut:", wrong_conut)