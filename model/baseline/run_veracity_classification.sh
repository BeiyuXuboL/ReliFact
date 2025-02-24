#!/usr/bin/env bash
model_name_path="microsoft/deberta-large"
classifier="classifier.py"
train_file="train.jsonl"
validation_file="val.jsonl"
test_file="test.jsonl"
output_dir="./model_output/"
eval_steps=50
max_seq_length=512
train_batch_size=12
eval_batch_size=8
epochs=25
learning_rate=3e-5
gradient_accumulation_steps=2

use_gold_evidence=true
use_misleading_evidence_train=false
use_misleading_evidence_test=false

metric_for_best_model="MAE"
gpu_num=1

# 2185465
# 53534856 
# 6162168
# 8643512
# 2438724

seed=2438724
num_class=3

while [ $# -gt 0 ]; do
   if [[ $1 == *"--"* ]]; then
        param="${1/--/}"
        declare $param="$2"
   fi
  shift
done

CUDA_VISIBLE_DEVICES=0 python -m torch.distributed.launch --nproc_per_node ${gpu_num} --master_port 1235 ${classifier} \
--model_name_or_path ${model_name_path} \
--cache_dir "./cache" \
--train_file ${train_file} \
--validation_file ${validation_file} \
--test_file ${test_file} \
--do_train false \
--do_eval false \
--do_predict true \
--logging_strategy steps \
--logging_first_step true \
--logging_steps 100 \
--evaluation_strategy steps \
--max_seq_length ${max_seq_length} \
--eval_steps ${eval_steps} \
--save_strategy steps \
--save_steps ${eval_steps} \
--save_total_limit 1 \
--metric_for_best_model ${metric_for_best_model} \
--load_best_model_at_end true \
--greater_is_better false \
--gradient_accumulation_steps ${gradient_accumulation_steps} \
--num_train_epochs ${epochs} \
--learning_rate ${learning_rate} \
--output_dir ${output_dir} \
--overwrite_output_dir false \
--per_device_train_batch_size ${train_batch_size} \
--per_device_eval_batch_size ${eval_batch_size} \
--report_to none \
--seed ${seed} \
--use_gold_evidence ${use_gold_evidence} \
--use_misleading_evidence_train ${use_misleading_evidence_train} \
--use_misleading_evidence_test ${use_misleading_evidence_test} \
--dataset_name "ReliFact" \
--num_class ${num_class} \