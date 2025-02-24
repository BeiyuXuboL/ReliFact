import json
import logging
import os
import datasets
import transformers
import sys
import numpy as np
from transformers import (
    AutoConfig,
    AutoTokenizer,
    AutoModel,
    Trainer,
    HfArgumentParser,
    TrainingArguments,
    set_seed,
    EvalPrediction,
    EarlyStoppingCallback
)
from transformers.trainer_utils import get_last_checkpoint
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error, precision_score, recall_score
from utils.other_arguments import DataArguments, ModelArguments
from utils.preprocessing import multi_task_data_processing, multi_task_data_processing_for_mocheg
from torch import nn
import torch


logger = logging.getLogger(__name__)
SEP_TK = "[SEP]"
# save_save = []

# nn.Sequential
class MultiTaskModel(nn.Module):
    def __init__(self, model_args, num_labels=3):
        super(MultiTaskModel, self).__init__()

        config = AutoConfig.from_pretrained(
        model_args.config_name if model_args.config_name else model_args.model_name_or_path,
        num_labels=num_labels,
        # finetuning_task=data_args.task_name,
        cache_dir=model_args.cache_dir,
        )
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_args.tokenizer_name if model_args.tokenizer_name else model_args.model_name_or_path,
            cache_dir=model_args.cache_dir,
            use_fast=model_args.use_fast_tokenizer,
        )
        self.model = AutoModel.from_pretrained(
            model_args.model_name_or_path,
            config=config,
            cache_dir=model_args.cache_dir,
        )
        
        self.evidence_classifier = nn.Linear(config.hidden_size, 2)
        self.claim_classifier = nn.Linear(config.hidden_size, 3)
        self.loss_fn_claim = nn.CrossEntropyLoss()
        self.loss_fn_evidence = nn.CrossEntropyLoss()

    # for ================================ ReliFact dataset ===============================================
    def forward(self, input_ids, attention_mask, input_ids2, attention_mask2, labels, label2):
        claim_verification_output = self.model(input_ids=input_ids, attention_mask=attention_mask)
        claim_verification_logits = self.claim_classifier(claim_verification_output.last_hidden_state[:, 0, :])
        loss_claim = self.loss_fn_claim(claim_verification_logits, labels)

        input_ids2 = input_ids2.view(-1, input_ids2.size(-1))
        attention_mask2 = attention_mask2.view(-1, attention_mask2.size(-1))
        label2 = label2.view(-1)
        evidence_classification_output = self.model(input_ids=input_ids2, attention_mask=attention_mask2)
        evidence_classification_logits = self.evidence_classifier(evidence_classification_output.last_hidden_state[:, 0, :])
        # print(evidence_classification_logits)
        # reliability_data = nn.functional.softmax(evidence_classification_logits, dim=-1).view(-1,10,2).cpu().numpy()
        # second_column = reliability_data[0, :, 1].tolist()
        # global save_save
        # save_save.append(second_column)
        # print(evidence_classification_logits.shape)

        loss_evidence = self.loss_fn_evidence(evidence_classification_logits, label2)

        total_loss = loss_claim + 0.5 * loss_evidence

        return {
            "loss": total_loss,
            "logits": claim_verification_logits,
            "labels": labels
        }
    


    

def compute_metrics(p: EvalPrediction):
    preds = p.predictions[0] if isinstance(p.predictions, tuple) else p.predictions
    preds = np.argmax(preds, axis=1)
      
    mae = mean_absolute_error(y_true=p.label_ids[0], y_pred=preds)
    accuracy = accuracy_score(y_true=p.label_ids[0], y_pred=preds)
    f1_marco = f1_score(y_true=p.label_ids[0], y_pred=preds, average='macro')
    f1_micro = f1_score(y_true=p.label_ids[0], y_pred=preds, average='micro')
    precision_macro = precision_score(y_true=p.label_ids[0], y_pred=preds, average='macro', zero_division=0)
    recall_macro = recall_score(y_true=p.label_ids[0], y_pred=preds, average='macro', zero_division=0)


    return {'MAE': mae,
            'Accuracy': accuracy,
            'f1-macro': f1_marco,
            'f1-micro': f1_micro,
            "precision_macro": precision_macro,
            "recall_macro": recall_macro}


def main():
    # Get args
    # training args denotes the HF training args
    # args denotes the arguments defined in the Salesforce config files
    parser = HfArgumentParser(
        (TrainingArguments, DataArguments, ModelArguments))
    training_args, data_args, model_args = parser.parse_args_into_dataclasses()
    set_seed(training_args.seed)
    # Setup logging
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        datefmt="%m/%d/%Y %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    log_level = training_args.get_process_log_level()
    logger.setLevel(log_level)
    datasets.utils.logging.set_verbosity(log_level)
    transformers.utils.logging.set_verbosity(log_level)
    transformers.utils.logging.enable_default_handler()
    transformers.utils.logging.enable_explicit_format()

    # Detecting last checkpoint.
    last_checkpoint = None
    if os.path.isdir(training_args.output_dir) and training_args.do_train and not training_args.overwrite_output_dir:
        last_checkpoint = get_last_checkpoint(training_args.output_dir)
        if last_checkpoint is None and len(os.listdir(training_args.output_dir)) > 0:
            raise ValueError(
                f"Output directory ({training_args.output_dir}) already exists and is not empty. "
                "Use --overwrite_output_dir to overcome."
            )
        elif last_checkpoint is not None and training_args.resume_from_checkpoint is None:
            logger.info(
                f"Checkpoint detected, resuming training at {last_checkpoint}. To avoid this behavior, change "
                "the `--output_dir` or add `--overwrite_output_dir` to train from scratch."
            )

    # load datasets
    data_files = {}
    if training_args.do_train:
        data_files["train"] = data_args.train_file
    if training_args.do_eval:
        data_files['validation'] = data_args.validation_file
    if training_args.do_predict:
        data_files['test'] = data_args.test_file

    raw_datasets = datasets.load_dataset(
        "json",
        data_files=data_files,
        cache_dir=model_args.cache_dir,
    )

    if data_args.num_class == 3:
        label_classes = ['refuted', 'nei', 'supported']
        num_labels = len(label_classes)
        label_to_id = {v: i for i, v in enumerate(label_classes)}
    
    # Load pretrained model and tokenizer
    #
    # In distributed training, the .from_pretrained methods guarantee that only one local process can concurrently
    # download model & vocab.
    # config = AutoConfig.from_pretrained(
    #     model_args.config_name if model_args.config_name else model_args.model_name_or_path,
    #     num_labels=num_labels,
    #     # finetuning_task=data_args.task_name,
    #     cache_dir=model_args.cache_dir,
    # )
    tokenizer = AutoTokenizer.from_pretrained(
        model_args.tokenizer_name if model_args.tokenizer_name else model_args.model_name_or_path,
        cache_dir=model_args.cache_dir,
        use_fast=model_args.use_fast_tokenizer,
    )
    # model = AutoModelForSequenceClassification.from_pretrained(
    #     model_args.model_name_or_path,
    #     config=config,
    #     cache_dir=model_args.cache_dir,
    # )
    model = MultiTaskModel(model_args=model_args)

    if model_args.checkponit_path is not None:
        print("Load checkpoint")
        weights = torch.load(model_args.checkponit_path)
        model.load_state_dict(weights, strict=False)

    # def add_decomp_questions(text, decomp):
    #     for q in decomp:
    #         text += " " + q.strip()
    #     return text

    # def add_answers(text, ans):
    #     for a in ans:
    #         text += " " + a.strip()
    #     return text

    def convert_raw_to_indices(examples):
        if data_args.dataset_name == "ReliFact":
            input_text1, input_text2 = multi_task_data_processing(examples)
            result1 = tokenizer(
            input_text1,
            padding="max_length",
            truncation=True,
            max_length=data_args.max_seq_length
            )
            result2 = []
            for sub_data in input_text2:
                result = tokenizer(
                    sub_data,
                    padding="max_length",
                    truncation=True,
                    max_length=data_args.max_seq_length
                )
                result2.append(result)

            total_result = {
                'input_ids': result1['input_ids'],  
                'attention_mask': result1['attention_mask'], 
                'input_ids2': [r['input_ids'] for r in result2],  
                'attention_mask2': [r['attention_mask'] for r in result2]
            }
            # Map labels to IDs (not necessary for GLUE tasks)
            if label_to_id is not None and "label" in examples:
                total_result["labels"] = [(label_to_id[l]) if l != -1 else -1 for l in
                                examples["label"]]
                total_result["label2"] = [l for l in examples["system_evidence_label_list"]]
            # print(total_result["label2"])
            # print(type(total_result["label2"]))
            return total_result
        if data_args.dataset_name == "MOCHEG":
            input_text1, input_text2 = multi_task_data_processing_for_mocheg(examples)
            result1 = tokenizer(
            input_text1,
            padding="max_length",
            truncation=True,
            max_length=data_args.max_seq_length
            )
            result2 = []
            for sub_data in input_text2:
                result = tokenizer(
                    sub_data,
                    padding="max_length",
                    truncation=True,
                    max_length=data_args.max_seq_length
                )
                result2.append(result)

            total_result = {
                'input_ids': result1['input_ids'],  
                'attention_mask': result1['attention_mask'], 
                'input_ids2': [r['input_ids'] for r in result2],  
                'attention_mask2': [r['attention_mask'] for r in result2]
            }
            # Map labels to IDs (not necessary for GLUE tasks)
            if label_to_id is not None and "label" in examples:
                total_result["labels"] = [(label_to_id[l.lower()]) if l != -1 else -1 for l in
                                examples["label"]]
            return total_result
                    
            
        # Tokenize the texts
        
    
    with training_args.main_process_first(desc="dataset map pre-processing"):
        raw_datasets = raw_datasets.map(
            convert_raw_to_indices,
            batched=True,
            load_from_cache_file=False,
            desc="Running tokenizer on dataset",
        )
        if data_args.dataset_name == "MOCHEG":
            raw_datasets=raw_datasets.remove_columns(['cleaned_truthfulness'])
        if data_args.dataset_name == "ReliFact":
            raw_datasets=raw_datasets.remove_columns(['label'])


    if training_args.do_train:
        if "train" not in raw_datasets:
            raise ValueError("--do_train requires a train dataset")
        train_dataset = raw_datasets["train"]
        if data_args.max_train_samples is not None:
            max_train_samples = min(len(train_dataset), data_args.max_train_samples)
            train_dataset = train_dataset.select(range(max_train_samples))
    else:
        train_dataset = None

    if training_args.do_eval:
        if "validation" not in raw_datasets and "validation_matched" not in raw_datasets:
            raise ValueError("--do_eval requires a validation dataset")
        eval_dataset = raw_datasets["validation"]
        if data_args.max_eval_samples is not None:
            max_eval_samples = min(len(eval_dataset), data_args.max_eval_samples)
            eval_dataset = eval_dataset.select(range(max_eval_samples))
    else:
        eval_dataset = None

    if training_args.do_predict:
        if "test" not in raw_datasets:
            raise ValueError("--do_predict requires a test dataset")
        predict_dataset = raw_datasets["test"]
        if data_args.max_predict_samples is not None:
            max_predict_samples = min(len(predict_dataset), data_args.max_predict_samples)
            predict_dataset = predict_dataset.select(range(max_predict_samples))
    else:
        predict_dataset = None

    es_callback = EarlyStoppingCallback(early_stopping_patience=2)
    # Initialize our Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset if training_args.do_train else None,
        eval_dataset=eval_dataset if training_args.do_eval else None,
        compute_metrics=compute_metrics,
        tokenizer=tokenizer,
        callbacks=[es_callback]
    )

    # Training
    if training_args.do_train:
        checkpoint = None
        if training_args.resume_from_checkpoint is not None:
            checkpoint = training_args.resume_from_checkpoint
        elif last_checkpoint is not None:
            checkpoint = last_checkpoint
        train_result = trainer.train(resume_from_checkpoint=checkpoint)
        metrics = train_result.metrics
        max_train_samples = (
            data_args.max_train_samples if data_args.max_train_samples is not None else len(
                train_dataset)
        )
        metrics["train_samples"] = min(max_train_samples, len(train_dataset))

        trainer.save_model()  # Saves the tokenizer too for easy upload

        trainer.log_metrics("train", metrics)
        trainer.save_metrics("train", metrics)
        trainer.save_state()

    # Evaluation
    if training_args.do_eval:
        logger.info("*** Evaluate ***")
        metrics = trainer.evaluate(eval_dataset=eval_dataset)
        max_eval_samples = (
            data_args.max_eval_samples if data_args.max_eval_samples is not None else len(
                eval_dataset)
        )
        metrics["eval_samples"] = min(max_eval_samples, len(eval_dataset))
        trainer.log_metrics("eval", metrics)
        trainer.save_metrics("eval", metrics)
    # global save_save
    # with open('/llm_result/val_reliability.json', 'w') as json_file:
    #     json.dump(save_save, json_file, indent=4)
    #     print(len(save_save))
    
    # save_save = []

    # Prediction
    if training_args.do_predict:
        logger.info("*** Predict ***")
        # metrics = trainer.predict(predict_dataset, metric_key_prefix="test")
        prediction_bundle = trainer.predict(predict_dataset, metric_key_prefix="test")
        metrics = prediction_bundle.metrics
        predictions = prediction_bundle.predictions
        labels = prediction_bundle.label_ids[0]
        output = []
        for p, l in zip(predictions, labels):
            print(np.argmax(p), l)
            output.append({
                "prediction": int(np.argmax(p)),
                "label": int(l)
            })
        print(output)
        output_predict_file = os.path.join(training_args.output_dir, f"predict_results_{training_args.seed}.json")
        max_eval_samples = (
            data_args.max_eval_samples if data_args.max_eval_samples is not None else len(
                eval_dataset)
        )
        json.dump(output, open(output_predict_file, "w"), indent=4)
        metrics["test_samples"] = min(max_eval_samples, len(eval_dataset))
        trainer.log_metrics("test", metrics)
        trainer.save_metrics("test", metrics)
    
    # with open('/llm_result/test_reliability.json', 'w') as json_file:
    #     json.dump(save_save, json_file, indent=4)
    #     print(len(save_save))


if __name__ == "__main__":
    main()