# Model

This folder contains the implementation of both the baseline and the proposed methods for the fact-checking pipeline. Below is an explanation of the two main directories: **baseline** and **our_method**.

## `baseline/`
The **baseline** folder contains the implementation of the traditional approach for fact-checking. This approach is used as a reference to compare the performance of our proposed method. The baseline method generally focuses on standard fact-checking techniques, such as content alignment with retrieved evidence, without integrating evidence reliability assessment.


## `our_method/`
The **our_method** folder contains the scripts for the proposed method. This method builds on the baseline but introduces a key enhancement: the integration of **evidence reliability assessment**. Our approach aims to improve fact-checking by not only evaluating the consistency of claims with retrieved evidence but also assessing the trustworthiness of the evidence itself.


---

In summary, the **baseline** folder contains the traditional fact-checking approach for comparison, while the **our_method** folder introduces multi-task learning approach that integrates evidence reliability evaluation to improve fact-checking accuracy.
