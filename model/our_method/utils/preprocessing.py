SEP_TK = "[SEP]"

def feed_claim_with_context(examples):
    input_text = []
    for c in zip(
        examples['claim'],
        # examples['claimant']
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
        # print(f'{claim} {SEP_TK} {gold_evidence}')
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


def multi_task_data_processing(examples):
    res1 = []
    res2 = []
    for claim, system_evidence, system_evidence_list in zip(
        examples['claim'],
        examples['system_evidence'],
        examples['system_evidence_list']
    ):
        # if split not in train_or_test:
        #     return input_text
        
        res1.append(f'{claim} {SEP_TK} {system_evidence}')
        item = []
        for evidence in system_evidence_list:
            item.append(f'{claim} {SEP_TK} {evidence}')
        res2.append(item)
    return res1, res2

def multi_task_data_processing_for_mocheg(examples):
    res1 = []
    res2 = []
    for claim, system_evidence in zip(
        examples['Claim'],
        examples['Evidence']
    ):      
        item = []
        system_evidence_list = system_evidence.split("[SEP_LXB]")
        new_system_evidence = ' '.join(system_evidence_list)
        res1.append(f'{claim} {SEP_TK} {new_system_evidence}')
        for evidence in system_evidence_list:
            item.append(f'{claim} {SEP_TK} {evidence}')
        res2.append(item)
    return res1, res2

