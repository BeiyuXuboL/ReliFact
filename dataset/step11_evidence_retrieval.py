import faiss
import numpy as np
import json
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import math


evidence_corpus = json.load(open("evidence_set.json", "r"))
statements = json.load(open("merged_claim_w_refinedEvience_w_MisEvidence_v3.json", "r"))

ground_truth = {}
for sample in evidence_corpus:
    if sample['claim_id'] not in ground_truth:
        ground_truth[sample['claim_id']] = []
    if sample['evidence_type'] == 'gold_evidence':
        ground_truth[sample['claim_id']].append(sample["evidence_id"])

evidence_texts = [entry["content"] for entry in evidence_corpus]
evidence_metadata = [{"claim_id": entry["claim_id"], "evidence_type": entry["evidence_type"], "evidence_id": entry["evidence_id"]} for entry in evidence_corpus]

semantic_model = SentenceTransformer('all-MiniLM-L6-v2')

evidence_embeddings = semantic_model.encode(evidence_texts)


evidence_embeddings = np.array(evidence_embeddings).astype(np.float32)
faiss.normalize_L2(evidence_embeddings)
index = faiss.IndexFlatL2(evidence_embeddings.shape[1])
index.add(evidence_embeddings)


def retrieve_evidences(statement, top_k=10):
    statement_embedding = semantic_model.encode([statement])
    statement_embedding = np.array(statement_embedding).astype(np.float32)

    distances, indices = index.search(statement_embedding, top_k)
    retrieved_evidences = []
    for rank, idx in enumerate(indices[0], 1):
        metadata = evidence_metadata[idx]
        retrieved_evidences.append({
            "rank": rank,
            "claim_id": metadata["claim_id"],
            "evidence_text": evidence_texts[idx],
            "evidence_type": metadata["evidence_type"],
            "evidence_id": metadata["evidence_id"],
            "score": distances[0][rank - 1]
        })
    return retrieved_evidences


retrieved_results = []
for stmt in tqdm(statements):
    result = retrieve_evidences(stmt["claim"], top_k=10)
    retrieved_results.append({"claim_id": stmt["claim_id"], "retrieved_evidences": result})
    stmt["retrieved_evidences"] = [{"evidence_id": meta["evidence_id"],"evidence": meta["evidence_text"],"evidence_type": meta["evidence_type"],"score": float(meta["score"])} for meta in result]


output_path = "final_dataset.json"

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(statements, f, ensure_ascii=False, indent=4)

print(f"Retrieved evidences have been saved to {output_path}")



def evaluate_retrieval(ground_truth, retrieved_results, top_k=10):
    precision_scores, recall_scores, f1_scores, mrr_scores, ndcg_scores = [], [], [], [], []

    for retrieval in retrieved_results:
        statement_id = retrieval["claim_id"]
        retrieved_ids = [e["evidence_id"] for e in retrieval["retrieved_evidences"][:top_k]]
        relevant_ids = set(ground_truth.get(statement_id, []))

        # Precision, Recall, F1
        retrieved_relevant = set(retrieved_ids) & relevant_ids
        precision = len(retrieved_relevant) / len(retrieved_ids) if retrieved_ids else 0
        recall = len(retrieved_relevant) / len(relevant_ids) if relevant_ids else 0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall > 0 else 0

        # MRR
        mrr = 0
        for rank, evidence_id in enumerate(retrieved_ids, 1):
            if evidence_id in relevant_ids:
                mrr = 1 / rank
                break

        # nDCG
        dcg = sum(1 / math.log2(rank + 1) for rank, evidence_id in enumerate(retrieved_ids, 1) if evidence_id in relevant_ids)
        idcg = sum(1 / math.log2(rank + 1) for rank in range(1, min(len(relevant_ids), top_k) + 1))
        ndcg = dcg / idcg if idcg > 0 else 0

        precision_scores.append(precision)
        recall_scores.append(recall)
        f1_scores.append(f1)
        mrr_scores.append(mrr)
        ndcg_scores.append(ndcg)

    return {
        "Precision@k": sum(precision_scores) / len(precision_scores),
        "Recall@k": sum(recall_scores) / len(recall_scores),
        "F1@k": sum(f1_scores) / len(f1_scores),
        "MRR": sum(mrr_scores) / len(mrr_scores),
        "nDCG": sum(ndcg_scores) / len(ndcg_scores),
    }

metrics = evaluate_retrieval(ground_truth, retrieved_results, top_k=10)

print("Retrieval Metrics:")
for metric, value in metrics.items():
    print(f"{metric}: {value:.4f}")







# from sentence_transformers import SentenceTransformer
# from rank_bm25 import BM25Okapi
# import numpy as np
# import math
# import json
# from tqdm import tqdm

# evidence_corpus = json.load(open("/home/gwy/liuxubo/ours_benchmark_noName/dataset/evidence_set.json", "r"))
# statements = json.load(open("/home/gwy/liuxubo/ours_benchmark_noName/dataset/final_dataset_v4.json", "r"))


# ground_truth = {}
# for sample in evidence_corpus:
#     if sample['claim_id'] not in ground_truth:
#         ground_truth[sample['claim_id']] = []
#     if sample['evidence_type'] == 'gold_evidence':
#         ground_truth[sample['claim_id']].append(sample["evidence_id"])


# semantic_model = SentenceTransformer('/home/gwy/liuxubo/ours_benchmark_noName/model/baseline/backbone/all-MiniLM-L6-v2')


# evidence_texts = [entry["content"] for entry in evidence_corpus]
# evidence_metadata = [{"claim_id": entry["claim_id"], "evidence_type": entry["evidence_type"], "evidence_id": entry["evidence_id"]} for entry in evidence_corpus]


# tokenized_corpus = [text.split() for text in evidence_texts]
# bm25 = BM25Okapi(tokenized_corpus)


# evidence_embeddings = semantic_model.encode(evidence_texts)

# # ** Step 3: Retrieve Evidences for a Statement **
# def retrieve_evidences(statement, top_k=10):
#     query_tokens = statement.split()
#     query_embedding = semantic_model.encode([statement])


#     bm25_scores = bm25.get_scores(query_tokens)
#     top_50_indices = np.argsort(bm25_scores)[::-1][:50]


#     candidate_embeddings = [evidence_embeddings[idx] for idx in top_50_indices]
#     similarities = np.dot(candidate_embeddings, query_embedding[0])
#     top_10_indices = np.argsort(similarities)[::-1][:top_k]


#     retrieved_evidences = []
#     for rank, idx in enumerate(top_10_indices, 1):
#         evidence_idx = top_50_indices[idx]
#         metadata = evidence_metadata[evidence_idx]
#         retrieved_evidences.append({
#             "rank": rank,
#             "claim_id": metadata["claim_id"],
#             "evidence_text": evidence_texts[evidence_idx],
#             "evidence_type": metadata["evidence_type"],
#             "evidence_id": metadata["evidence_id"],
#             "score": similarities[idx]
#         })
#     return retrieved_evidences


# retrieved_results = []
# for stmt in tqdm(statements):
#     result = retrieve_evidences(stmt["claim"], top_k=10)
#     retrieved_results.append({"claim_id": stmt["claim_id"], "retrieved_evidences": result})


# def evaluate_retrieval(ground_truth, retrieved_results, top_k=5):
#     precision_scores, recall_scores, f1_scores, mrr_scores, ndcg_scores = [], [], [], [], []

#     for retrieval in retrieved_results:
#         statement_id = retrieval["claim_id"]
#         retrieved_ids = [e["evidence_id"] for e in retrieval["retrieved_evidences"][:top_k]]
#         relevant_ids = set(ground_truth.get(statement_id, []))

#         # Precision, Recall, F1
#         retrieved_relevant = set(retrieved_ids) & relevant_ids
#         precision = len(retrieved_relevant) / len(retrieved_ids) if retrieved_ids else 0
#         recall = len(retrieved_relevant) / len(relevant_ids) if relevant_ids else 0
#         f1 = 2 * precision * recall / (precision + recall) if precision + recall > 0 else 0

#         # MRR
#         mrr = 0
#         for rank, evidence_id in enumerate(retrieved_ids, 1):
#             if evidence_id in relevant_ids:
#                 mrr = 1 / rank
#                 break

#         # nDCG
#         dcg = sum(1 / math.log2(rank + 1) for rank, evidence_id in enumerate(retrieved_ids, 1) if evidence_id in relevant_ids)
#         idcg = sum(1 / math.log2(rank + 1) for rank in range(1, min(len(relevant_ids), top_k) + 1))
#         ndcg = dcg / idcg if idcg > 0 else 0


#         precision_scores.append(precision)
#         recall_scores.append(recall)
#         f1_scores.append(f1)
#         mrr_scores.append(mrr)
#         ndcg_scores.append(ndcg)


#     return {
#         "Precision@k": sum(precision_scores) / len(precision_scores),
#         "Recall@k": sum(recall_scores) / len(recall_scores),
#         "F1@k": sum(f1_scores) / len(f1_scores),
#         "MRR": sum(mrr_scores) / len(mrr_scores),
#         "nDCG": sum(ndcg_scores) / len(ndcg_scores),
#     }


# metrics = evaluate_retrieval(ground_truth, retrieved_results, top_k=5)

# print("Retrieval Metrics:")
# for metric, value in metrics.items():
#     print(f"{metric}: {value:.4f}")











# from rank_bm25 import BM25Okapi
# import numpy as np
# import math
# import json
# from tqdm import tqdm


# evidence_corpus = json.load(open("/home/gwy/liuxubo/ours_benchmark_noName/dataset/evidence_set.json", "r"))
# statements = json.load(open("/home/gwy/liuxubo/ours_benchmark_noName/dataset/final_dataset_v4.json", "r"))


# ground_truth = {}
# for sample in evidence_corpus:
#     if sample['claim_id'] not in ground_truth:
#         ground_truth[sample['claim_id']] = []
#     if sample['evidence_type'] == 'gold_evidence':
#         ground_truth[sample['claim_id']].append(sample["evidence_id"])


# evidence_texts = [entry["content"] for entry in evidence_corpus]
# evidence_metadata = [{"claim_id": entry["claim_id"], "evidence_type": entry["evidence_type"], "evidence_id": entry["evidence_id"]} for entry in evidence_corpus]


# tokenized_corpus = [text.split() for text in evidence_texts]
# bm25 = BM25Okapi(tokenized_corpus)



# def retrieve_evidences(statement, top_k=10):
#     query_tokens = statement.split()
    

#     bm25_scores = bm25.get_scores(query_tokens)
#     top_k_indices = np.argsort(bm25_scores)[::-1][:top_k]


#     retrieved_evidences = []
#     for rank, idx in enumerate(top_k_indices, 1):
#         metadata = evidence_metadata[idx]
#         retrieved_evidences.append({
#             "rank": rank,
#             "claim_id": metadata["claim_id"],
#             "evidence_text": evidence_texts[idx],
#             "evidence_type": metadata["evidence_type"],
#             "evidence_id": metadata["evidence_id"],
#             "score": bm25_scores[idx]
#         })
#     return retrieved_evidences


# retrieved_results = []
# for stmt in tqdm(statements):
#     result = retrieve_evidences(stmt["claim"], top_k=5)
#     retrieved_results.append({"claim_id": stmt["claim_id"], "retrieved_evidences": result})



# def evaluate_retrieval(ground_truth, retrieved_results, top_k=10):
#     precision_scores, recall_scores, f1_scores, mrr_scores, ndcg_scores = [], [], [], [], []

#     for retrieval in retrieved_results:
#         statement_id = retrieval["claim_id"]
#         retrieved_ids = [e["evidence_id"] for e in retrieval["retrieved_evidences"][:top_k]]
#         relevant_ids = set(ground_truth.get(statement_id, []))

#         # Precision, Recall, F1
#         retrieved_relevant = set(retrieved_ids) & relevant_ids
#         precision = len(retrieved_relevant) / len(retrieved_ids) if retrieved_ids else 0
#         recall = len(retrieved_relevant) / len(relevant_ids) if relevant_ids else 0
#         f1 = 2 * precision * recall / (precision + recall) if precision + recall > 0 else 0

#         # MRR
#         mrr = 0
#         for rank, evidence_id in enumerate(retrieved_ids, 1):
#             if evidence_id in relevant_ids:
#                 mrr = 1 / rank
#                 break

#         # nDCG
#         dcg = sum(1 / math.log2(rank + 1) for rank, evidence_id in enumerate(retrieved_ids, 1) if evidence_id in relevant_ids)
#         idcg = sum(1 / math.log2(rank + 1) for rank in range(1, min(len(relevant_ids), top_k) + 1))
#         ndcg = dcg / idcg if idcg > 0 else 0


#         precision_scores.append(precision)
#         recall_scores.append(recall)
#         f1_scores.append(f1)
#         mrr_scores.append(mrr)
#         ndcg_scores.append(ndcg)


#     return {
#         "Precision@k": sum(precision_scores) / len(precision_scores),
#         "Recall@k": sum(recall_scores) / len(recall_scores),
#         "F1@k": sum(f1_scores) / len(f1_scores),
#         "MRR": sum(mrr_scores) / len(mrr_scores),
#         "nDCG": sum(ndcg_scores) / len(ndcg_scores),
#     }


# metrics = evaluate_retrieval(ground_truth, retrieved_results, top_k=5)



# print("Retrieval Metrics:")
# for metric, value in metrics.items():
#     print(f"{metric}: {value:.4f}")