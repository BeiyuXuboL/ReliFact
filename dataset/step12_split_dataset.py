import json
import random
import os
import json
from datetime import datetime

data_path = "final_dataset.json"

with open(data_path, "r") as f:
    dataset = json.load(f)


claim_dates = [sample['claimDate'] for sample in dataset]


def parse_date(date_str):
    """
    'yyyy-mm-ddTHH:MM:SSZ'。
    """
    return datetime.strptime(date_str[:-1], "%Y-%m-%dT%H:%M:%S")


dates = [parse_date(date) for date in claim_dates]


min_date = min(dates)
max_date = max(dates)


print(f"ClaimDate from: {min_date} to {max_date}")

base_dir = "data"


supported = []
refuted = []
nei = []
for sample in dataset:
    if sample["label"] == "supported":
        supported.append(sample)
    elif sample["label"] == "refuted":
        refuted.append(sample)
    elif sample["label"] == "nei":
        nei.append(sample)

print(len(supported))
print(len(refuted))
print(len(nei))


random.seed(1212)

# def parse_date(date_str):
#     return datetime.strptime(date_str[:-1], "%Y-%m-%dT%H:%M:%S")


def sort_by_claim_date(data):
    return sorted(data, key=lambda x: parse_date(x['claimDate']))


supported_sorted = sort_by_claim_date(supported)
refuted_sorted = sort_by_claim_date(refuted)
nei_sorted = sort_by_claim_date(nei)


def split_data_by_date(sorted_data, train_end_date, val_end_date, test_end_date):
    train_data = [sample for sample in sorted_data if parse_date(sample['claimDate']) <= parse_date(train_end_date)]
    val_data = [sample for sample in sorted_data if parse_date(sample['claimDate']) > parse_date(train_end_date) and parse_date(sample['claimDate']) <= parse_date(val_end_date)]
    test_data = [sample for sample in sorted_data if parse_date(sample['claimDate']) > parse_date(val_end_date) and parse_date(sample['claimDate']) <= parse_date(test_end_date)]
    return train_data, val_data, test_data


train_end_date = "2023-12-01T00:00:00Z"  
val_end_date = "2024-05-01T00:00:00Z"   
test_end_date = "2024-11-03T00:00:00Z"   


supported_train, supported_val, supported_test = split_data_by_date(supported_sorted, train_end_date, val_end_date, test_end_date)
refuted_train, refuted_val, refuted_test = split_data_by_date(refuted_sorted, train_end_date, val_end_date, test_end_date)
nei_train, nei_val, nei_test = split_data_by_date(nei_sorted, train_end_date, val_end_date, test_end_date)


train_set = supported_train + refuted_train + nei_train
val_set = supported_val + refuted_val + nei_val
test_set = supported_test + refuted_test + nei_test



evidence_set_path = 'evidence_set.json'
evidence_set = json.load(open(evidence_set_path,"r"))

def data_processing(data):
    res = []
    for sample in data:
        item = {}
        item["claim_id"] = sample["claim_id"]
        item["claim"] = sample["claim"]
        item["label"] = sample["label"]
        item["claimant"] = sample["claimant"]
        item["claimDate"] = sample["claimDate"]
        item["url"] = sample["url"]
        item["gold_evidence"] = sample["refined_evidence"]
        system_evidence = ''
        system_evidence_list = []
        system_evidence_label_list = []
        for ee in reversed(sample["retrieved_evidences"]):
            system_evidence_list.append(ee['evidence'].replace('\n',''))
            system_evidence += ee['evidence']
            for evidence in evidence_set:
                if ee["evidence_id"] == evidence["evidence_id"]:
                    if sample["claim_id"] == evidence["claim_id"] and evidence["evidence_type"] == 'gold_evidence':
                        system_evidence_label_list.append(1)
                        break
                    system_evidence_label_list.append(0)
                    break

        # sample["retrieved_evidences"] = sample["retrieved_evidences"].reverse()
        assert len(system_evidence_list) == len(system_evidence_label_list), print(len(system_evidence_list),len(system_evidence_label_list))
        item["system_evidence"] = system_evidence
        item["system_evidence_list"] = system_evidence_list
        item["system_evidence_label_list"] = system_evidence_label_list
        # item["system_evidence"] = '.'.join([e["evidence"] for e in sample["retrieved_evidences"].reverse()])
        res.append(item)
    return res

train_set = data_processing(train_set)
val_set = data_processing(val_set)
test_set = data_processing(test_set)


for sample in train_set:
    sample['split'] = 'train'

for sample in val_set:
    sample['split'] = 'val'

for sample in test_set:
    sample['split'] = 'test'


random.shuffle(train_set)
random.shuffle(val_set)
random.shuffle(test_set)


print(f"\nTRAIN: {len(train_set)}")
print(f"\nVAL: {len(val_set)}")
print(f"\nTEST: {len(test_set)}")

print("\nTRAIN:")
print(f"supported: {len(supported_train)}, refuted: {len(refuted_train)}, nei: {len(nei_train)}")

print("\nVAL:")
print(f"supported: {len(supported_val)}, refuted: {len(refuted_val)}, nei: {len(nei_val)}")

print("\nTEST:")
print(f"supported: {len(supported_test)}, refuted: {len(refuted_test)}, nei: {len(nei_test)}")

def save_to_file(data, file_name):
    with open(file_name, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
 

save_to_file(train_set, os.path.join(base_dir, "train.jsonl"))
save_to_file(val_set, os.path.join(base_dir, "val.jsonl"))
save_to_file(test_set, os.path.join(base_dir, "test.jsonl"))