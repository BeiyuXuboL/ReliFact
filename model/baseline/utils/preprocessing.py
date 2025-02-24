SEP_TK = "[SEP]"


def feed_claim_with_context(examples):
    input_text = []
    for c in zip(
        examples['claim'],
    ):
        input_text.append(
            f"{c}"
        )
    return input_text

def concat_claim_gold_evidence(input_text, examples):
    res = []
    for claim, raw_claim, gold_evidence in zip(
        input_text,
        examples['claim'],
        examples['gold_evidence']
    ):
        evidence_list = gold_evidence.split('\n')
        evidence = '.'.join(evidence_list)

        res.append(f'{raw_claim} {SEP_TK} {evidence}')
    return res




def concat_claim_misleading_evidence(input_text, examples, train_or_test):
    res = []
    for claim, p, gold_evidence, system_evidence, split in zip(
        examples['claim'],
        examples['claimant'],
        examples['gold_evidence'],
        examples['system_evidence'],
        examples['split']
    ):
        if split not in train_or_test:
            return input_text

        res.append(f'{claim} {SEP_TK} {system_evidence}')
    return res
