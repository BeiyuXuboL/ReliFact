import os
import json
from openai import OpenAI
# import argparse
import time
from tqdm import tqdm


os.environ['OPENAI_BASE_URL'] = 'OPENAI_BASE_URL'
os.environ['OPENAI_API_KEY'] = 'OPENAI_API_KEY'


def gpt_chat_completion(**kwargs):
    backoff_time = 1
    max_wait_time = 30
    start_time = time.time()
    while True:
        try:
            if time.time() - start_time > max_wait_time:
                print("Time out，skip！")
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
                print("Token limit, skip!")
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
    data_path = "merged_claim_w_refinedEvience_w_MisEvidence.json"
    ori_data = json.load(open(data_path, 'r'))
    res = []
    # count = 0
    with open('prompt_for_misleadingProcessing.txt', 'r') as file:
        content = file.read()
    for item in tqdm(ori_data):

        ori_evidence = item["misleading_evidence"]

        template_input = content + ori_evidence + "\n\nOutput:"
     
        messages = [{"role": "user", "content": template_input},]
        response = gpt_chat_completion(messages=messages, model='gpt-3.5-turbo-1106', temperature=1.0)
        # print(response)
        # exit(0)
        res_item = item.copy()
        res_item["processed_misleading_evidence"] = response
        res.append(res_item)
        # break
    with open("merged_claim_w_refinedEvience_w_MisEvidence_v2.json", 'w') as file:
        json.dump(res, file, indent=4)

main()
