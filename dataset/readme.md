# Dataset Preparation

This folder contains all the scripts and data files necessary to build the dataset for the fact-checking pipeline. Below is a step-by-step guide to constructing the dataset, starting from collecting claims to splitting the final dataset for model use.

## Steps to Build the Dataset

### 1. **Claim Search** (`step1_claim_search.py`)
The first step is to retrieve claims.
```bash
python step1_claim_search.py
```

### 2. **Claims Filtering** (`step2_claims_filtering.py`)
Once claims are retrieved, we filter out irrelevant or duplicate claims to ensure high-quality data. This step ensures that only meaningful claims are processed further.
```bash
python step2_claims_filtering.py
```

### 3. **Merge Claims** (`step3_merge_claims.py`)
This step merges the claims from different sources into a unified format for further processing.
```bash
python step3_merge_claims.py
```

### 4. **Crawl Web Pages for Evidence** (`step4_crawl_webPages.py`)
Web pages are crawled to gather relevant evidence for the claims. This script uses predefined search terms or URLs to collect web data.
```bash
python step4_crawl_webPages.py
```

### 5. **Web Pages Preprocessing** (`step5_webPages_preprocessing.py`)
After crawling, the collected web pages need to be cleaned and preprocessed. This step includes removing irrelevant content, formatting issues, and ensuring the pages are suitable for evidence extraction.
```bash
python step5_webPages_preprocessing.py
```

### 6. **Evidence Cleaning** (`step6_evidence_cleaning.py`)
This step cleans up the evidence extracted from the web pages, removing any noise or irrelevant data. Only the most relevant and trustworthy pieces of evidence are retained for further use.
```bash
python step6_evidence_cleaning.py
```

### 7. **Misleading Evidence Generation** (`step7_misleading_evidence_generation.py`)
This script generates misleading evidence based on the original web content, simulating how misinformation can be generated or altered.
```bash
python step7_misleading_evidence_generation.py
```

### 8. **Misleading Processing** (`step8_misleading_processing.py`)
The generated misleading evidence is processed for further evaluation. This includes checking for inconsistencies and ensuring that it aligns with the intended misleading criteria.
```bash
python step8_misleading_processing.py
```


### 9. **Same Misleading Generation** (`step9_same_misleading_generation.py`)
This step generates additional misleading evidence by rewriting the gold evidence.
```bash
python step9_same_misleading_generation.py
```


### 10. **Mixing Evidence** (`step10_mix_evidence.py`)
Once the evidence is ready, this step mixes different pieces of evidence (both true and misleading) to simulate real-world scenarios where multiple conflicting pieces of evidence are present.
```bash
python step10_mix_evidence.py
```


### 11. **Evidence Retrieval** (`step11_evidence_retrieval.py`)
After mixing, relevant evidence is retrieved for each claim, ensuring that the evidence supports or contradicts the claim as required for the fact-checking process.
```bash
python step11_evidence_retrieval.py
```


### 12. **Split Dataset** (`step12_split_dataset.py`)
Finally, the dataset is split into training, validation, and test sets. This step ensures that the data is ready for use in model training and evaluation.
```bash
python step12_split_dataset.py
```

---