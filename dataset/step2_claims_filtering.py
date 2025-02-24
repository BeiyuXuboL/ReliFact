import json
import random

raw_claims_path = 'raw_claims.json'
with open('raw_claims.json', 'r') as json_file:
    raw_claims = json.load(json_file)

print("num of raw claims:",len(raw_claims))

# filter by "claimant" and "claimDate"
filtered_claims_1 = [claim for claim in raw_claims
                     if 'claimant' in claim and 'claimDate' in claim]

print("num of filtered_claims_1:",len(filtered_claims_1))

# filter by modality 
filtered_claims_2 = [
    claim for claim in filtered_claims_1
    if not any(keyword in claim['text'].lower() for keyword in ["image", "video", "audio","photo"])
]
print("num of filtered_claims_2:",len(filtered_claims_2))

# filter by label 
true = ["true","correct","mostly true","largely true","mostly correct"]
false = ["pants on fire","false","incorrect","unsupported","not supported"]
nei = ["unfounded","unproven","unsubstantiated","uninformed","unconfirmed","unverified","unproven Care","uncorroborated","speculation","unknown cause","unvalidated","unproven claim","undocumented","unsourced","unsourced info","undetermined","no evidence he said that","not announced","no records","no reports","no record","no report","no proof","no evidence","can't verify","no source","not endorsed","no information","no such report","no proven link","contradictions","not verified","not reported"]


# S
filtered_claims = [
    claim for claim in filtered_claims_2
    if any(review.get('textualRating').lower() in true for review in claim.get('claimReview', []))
]
filtered_supported_claims = []

seen = set()
for claim in filtered_claims:
    claim_text = claim['text']
    if claim_text not in seen:
        filtered_supported_claims.append(claim)
        seen.add(claim_text)
print("num of filtered_supported_claims:",len(filtered_supported_claims))


# NEI
nei_claims = []
for claim in filtered_claims_2:
    for review in claim.get('claimReview', []):
        textualRating = review.get('textualRating', "").lower()  
        if "no evidence" in textualRating:
            nei_claims.append(claim)  
            break 


filtered_claims = []
for claim in filtered_claims_2:
    for review in claim.get('claimReview', []):
        textual_rating = review.get('textualRating')
        if textual_rating and (textual_rating.lower() in nei or "unproven" in textual_rating.lower()):
            filtered_claims.append(claim)  
            break  
filtered_claims = filtered_claims + nei_claims

filtered_claims = [
    claim for claim in filtered_claims
    if claim not in filtered_supported_claims
]
seen = set()
filtered_nei_claims = []
for claim in filtered_claims:
    claim_text = claim['text']
    if claim_text not in seen:
        filtered_nei_claims.append(claim)
        seen.add(claim_text)
print("num of filtered_nei_claims:",len(filtered_nei_claims))


# R
filtered_refuted_claims = [
    claim for claim in filtered_claims_2
    if any(review.get('textualRating').lower() in false for review in claim.get('claimReview', []))
]
filtered_refuted_claims = [
    claim for claim in filtered_refuted_claims
    if claim not in filtered_nei_claims and claim not in filtered_supported_claims
]

refuted_claims = random.sample(filtered_refuted_claims, 2000)
# refuted_claims = filtered_refuted_claims
unique_sites = set()
for claim in filtered_claims_2:
    for review in claim.get('claimReview', []):
        site = review.get('publisher', {}).get('site', "")
        if site:  
            unique_sites.add(site)

filtered_refuted_claims = []
for claim in refuted_claims:
    claim_text = claim['text']
    if claim_text not in seen:
        filtered_refuted_claims.append(claim)
        seen.add(claim_text)

num_unique_sites = len(unique_sites)

print("num of filtered_refuted_claims and sites:",len(filtered_refuted_claims),num_unique_sites)



with open('supported_claims.json', 'w') as json_file:
    json.dump(filtered_supported_claims, json_file, indent=4)

with open('nei_claims.json', 'w') as json_file:
    json.dump(filtered_nei_claims, json_file, indent=4)


with open('refuted_claims.json', 'w') as json_file:
    json.dump(filtered_refuted_claims, json_file, indent=4)