import os
import json
from openai import OpenAI
# import argparse
import time
from tqdm import tqdm

folder_path = 'claims_w_raw_evidence'  
output_file = 'merged_claim_after_dataCleaning.json'


json_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]


merged_data = []


for file_name in json_files:
    file_path = os.path.join(folder_path, file_name)
    
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        merged_data.extend(data)  

print(len(merged_data))
with open(output_file, 'w', encoding='utf-8') as output:
    json.dump(merged_data, output, ensure_ascii=False, indent=4)




os.environ['OPENAI_BASE_URL'] = 'OPENAI_BASE_URL'
os.environ['OPENAI_API_KEY'] = 'OPENAI_API_KEY'


def gpt_chat_completion(**kwargs):
    backoff_time = 1
    max_wait_time = 20
    start_time = time.time()
    while True:
        try:
            if time.time() - start_time > max_wait_time:
                print("Time out, skip")
                return ""
            client = OpenAI()
            response = client.chat.completions.create(**kwargs)
            if type(response) == str:
                return response_parser(response)
            else:
                return response.choices[0].message.content
        except Exception as e:
            # print(e)
            if "context length" in str(e):
                print("Token limit, skip")
                return ""
            time.sleep(backoff_time)
            backoff_time *= 1.5


def response_parser(response):
    response = response.strip().split("data: ")[1:]
    result = ''
    for r in response:
        if r == '[DONE]':
            break
        delta = json.loads(r)['choices'][0]['delta']
        if 'content' in delta:
            result += delta['content']
    return result

def main():
    ori_data = json.load(open(output_file, 'r'))
    res = []
    # count = 0
    for item in tqdm(ori_data):
        # count += 1
        # if count<=2543:
        #     continue
        claim = item["claim"]
        claimant = item["claimant"]
        ori_evidence = item["raw_evidence"]
        if ori_evidence == "":
            res_item = item.copy()
            res_item["refined_evidence"] = ""
            res.append(res_item)
            continue
        template_input = "I have a claim, a claimant, and a set of evidence extracted from the web. Your task is to refine the evidence as follows:\n 1. Retain only the portions of the evidence that are relevant to the claim, considering the Claimant as well. If an entire piece of evidence is relevant, retain it in full.\n 2. You are allowed to truncate or omit parts of the evidence, but you must not add, summarize, or infer any information.\n 3. Each retained evidence piece must strictly consist of content found in the original evidence.\n 4.Limit the output to a maximum of ten concise and distinct pieces of evidence.\n Claim: %s \n Claimant: %s \n Original Evidence: %s \n Refined Evidence:" % (claim, claimant, ori_evidence)
        messages = [{"role": "user", "content": template_input},]
        response = gpt_chat_completion(messages=messages, model='gpt-3.5-turbo-1106', temperature=1.0)
        res_item = item.copy()
        res_item["refined_evidence"] = response
        res.append(res_item)
    with open("merged_claim_w_refinedEvience.json", 'w') as file:
        json.dump(res, file, indent=4)

main()
