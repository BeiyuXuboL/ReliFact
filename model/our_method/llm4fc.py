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
    data_path = "test.jsonl"
    ori_data = []
    # res = []
    result = []
    with open(data_path, 'r') as f:
        for line in f:
            ori_data.append(json.loads(line.strip()))

        label_classes = ['refuted', 'nei', 'supported']
        # num_labels = len(label_classes)
        label_to_id = {v: i for i, v in enumerate(label_classes)}
        # "prediction": 2,
        # "label": 2
    # count = 0 
    evidence_reliability_list = json.load(open('/llm_result/test_reliability.json','r'))
    for index, item in tqdm(enumerate(ori_data)):
        # count += 1
        label = item["label"].lower()
        claim = item["Claim"]
        gold_evidence = item["gold_evidence"]
       
        evidence_reliability = evidence_reliability_list[index]
        
        prompt = 'Can you fact-check a claim for me? Classify the given claim into three labels: "supported", "refuted" or "not enough evidence". Let’s think step by step. \nGiven claim: %s \nRetrieval evidence:\n' % (claim)
        for i,e in enumerate(gold_evidence):
            prompt += e
            prompt += "| Reliability score: %.4f \n" % evidence_reliability[i]

        messages = [{"role": "user", "content": prompt},]
        # response = gpt_chat_completion(messages=messages, model='gpt-3.5-turbo-1106', temperature=0.0)
        response = gpt_chat_completion(messages=messages, model='gpt-4o', temperature=0.0)
        # print(response)
        try:
            res = {
                "claim_id": item["claim_id"],
                "label": label_to_id[label]
            }
            if "refuted" in response.lower():
                res["prediction"] = label_to_id['refuted']
            elif "supported" in response:
                res["prediction"] = label_to_id['supported']
            else:
                res["prediction"] = label_to_id['nei']
        except:
            continue
        result.append(res)

        # if count==5:
        #     break
        # print(res)
        # exit(0)
        # res_item = item.copy()
        # res_item["misleading_evidence_similarWithGold"] = response
        # res.append(res_item)
        # break
    with open("/llm_result/test_4o.json", 'w') as file:
        json.dump(result, file, indent=4)

main()

