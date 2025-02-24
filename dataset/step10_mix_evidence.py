import json
import random

data_path = "merged_claim_w_refinedEvience_w_MisEvidence_v3.json"
save_path = "evidence_set.json"

data = json.load(open(data_path, "r"))

# sample['refined_evidence'] = '.'.join([e for e in evidence_list if 'satire' not in e.lower() and 'false' not in e.lower() and 'fake' not in e.lower() and 'claim' not in e.lower() and 'vishvas news' not in e.lower() and 'newsweek' not in e.lower() and 'india today' not in e.lower() and 'usa today' not in e.lower() and 'newsmeter' not in e.lower() and 'lead stories' not in e.lower() and 'politifact' not in e.lower() and 'full fact' not in e.lower() and 'factly' not in e.lower() and 'check your fact' not in e.lower()])
# sample['refined_evidence'] = sample['refined_evidence'].replace('viral','')

gold_evidence_path = 'merged_claim_w_refinedEvience.json'
gold_evidence = json.load(open(gold_evidence_path,'r'))

evidence_set = []
for sample in data:
    claim_id = sample["claim_id"]
    for gold_sample in gold_evidence:
        if claim_id == gold_sample["claim_id"]:
            evidence_list = gold_sample["refined_evidence"].split(".")
            refined_evidence = ('.'.join([e for e in evidence_list if 'satire' not in e.lower() and 'false' not in e.lower() and 'fake' not in e.lower() and 'claim' not in e.lower() and 'vishvas news' not in e.lower() and 'newsweek' not in e.lower() and 'india today' not in e.lower() and 'usa today' not in e.lower() and 'newsmeter' not in e.lower() and 'lead stories' not in e.lower() and 'politifact' not in e.lower() and 'full fact' not in e.lower() and 'factly' not in e.lower() and 'check your fact' not in e.lower()])).replace('viral','')
            refined_evidence = refined_evidence.split("\n")
            for evidence in refined_evidence:
                if len(evidence) >= 10:
                    evidence_set.append({
                        "claim_id": claim_id,
                        "evidence_type": "gold_evidence",
                        "content": evidence
                    })
            break

    # refined_evidence = sample["refined_evidence"].split("\n")
    processed_misleading_evidence = sample["processed_misleading_evidence"].split("\n")
    misleading_evidence_similarWithGold = sample["misleading_evidence_similarWithGold"].split("\n")
    # for evidence in refined_evidence:
    #     if len(evidence) >= 10:
    #         evidence_set.append({
    #             "claim_id": claim_id,
    #             "evidence_type": "gold_evidence",
    #             "content": evidence
    #         })
    for evidence in processed_misleading_evidence:
        if len(evidence) >= 10:
            evidence_set.append({
                "claim_id": claim_id,
                "evidence_type": "fabricated_misleading_evidence",
                "content": evidence
            })
    for evidence in misleading_evidence_similarWithGold:
        if len(evidence) >= 10:
            evidence_set.append({
                "claim_id": claim_id,
                "evidence_type": "rewritten_misleading_evidence",
                "content": evidence
            })
random.shuffle(evidence_set)
count_index = 1
for evidence in evidence_set:
    evidence["evidence_id"] = count_index
    count_index += 1
print(len(evidence_set))
with open(save_path, "w") as f:
    json.dump(evidence_set, f, indent=4)