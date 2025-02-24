import json

claim_id = 1

def label_rewrite(samples,label="supported"):
    global claim_id
    res = []
    for sample in samples:
        item = {}
        item["claim_id"] = claim_id
        claim_id += 1
        item["claim"] = sample["text"]
        item["label"] = label
        item["claimant"] = sample["claimant"]
        item["claimDate"] = sample["claimDate"]
        item["url"] = sample["claimReview"][0]["url"]
        res.append(item.copy())
    return res
        

with open('nei_claims.json', 'r') as json_file:
    nei_ = json.load(json_file)
with open('supported_claims.json', 'r') as json_file:
    supported_ = json.load(json_file)
with open('refuted_claims.json', 'r') as json_file:
    refuted_ = json.load(json_file)

nei_relabel = label_rewrite(nei_, label="nei")

supported_relabel = label_rewrite(supported_, label="supported")

refuted_relabel = label_rewrite(refuted_, label="refuted")

total = nei_relabel + supported_relabel + refuted_relabel

with open('merged_claims.json', 'w') as json_file:
    json.dump(total, json_file, indent=4)