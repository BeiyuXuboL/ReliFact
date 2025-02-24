# ReliFact: Identifying Reliable Evidence for Fact-Checking

## Getting started

Clone the repository and install the requirements:
```bash
pip install -r requirements.txt
```

## Project Structure

### `dataset/`

- **data/**: Dataset folder.
- **step1_claim_search.py**: Retrieves claims for fact-checking.
- **step2_claims_filtering.py**: Filters relevant claims from the dataset.
- **step3_merge_claims.py**: Merges claims into a unified format.
- **step4_crawl_webPages.py**: Crawls web pages for evidence.
- **step5_webPages_preprocessing.py**: Preprocesses crawled web pages.
- **step6_evidence_cleaning.py**: Cleans the collected evidence.
- **step7_misleading_evidence_generation.py**: Generates misleading evidence for validation.
- **step8_misleading_processing.py**: Processes misleading evidence for further use.
- **step9_same_misleading_generation.py**: Generates consistent misleading evidence.
- **step10_mix_evidence.py**: Mixes evidence for diversity.
- **step11_evidence_retrieval.py**: Retrieves relevant evidence for fact-checking.
- **step12_split_dataset.py**: Splits dataset into training and testing sets.

### `model/`
Contains the implementation of the baseline and proposed fact-checking methods.
- **baseline/**: Contains the baseline model and utilities.
  - **utils/**: Contains scripts for additional utilities and preprocessing.
  - **classifier.py**: Defines the baseline classifier.
  - **llm4fc.py**: Implements the language model for fact-checking.
  - **run_veracity_classification.sh**: Script for running the baseline model.
- **our_method/**: Contains the scripts for the proposed method.
  - **utils/**: Contains utilities and additional methods for the proposed approach.
  - **classifier.py**: Defines the classifier for our proposed method.
  - **llm4fc.py**: Implements the language model for our method.
  - **run_veracity_classification.sh**: Script for running the proposed method.


## Acknowledgments
Our repository builds on [Fact-checking-via-Raw-Evidence](https://github.com/jifan-chen/Fact-checking-via-Raw-Evidence). Thanks for open-sourcing!


## Contact

If you have any questions, please feel free to contact me at: [liuxubo@dbis.nankai.edu.cn](liuxubo@dbis.nankai.edu.cn).
