import os
import torch
import numpy as np
from transformers import AutoTokenizer, AutoModel
from scipy.spatial.distance import cosine
from concurrent.futures import ThreadPoolExecutor
import itertools

model_name = "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

folder_path = "200_2020_2024_health_domain"
model = AutoModel.from_pretrained(model_name)

def get_embedding(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state[:, 0, :].squeeze().numpy()

def compute_average_similarity(terms):
    if len(terms) < 2:
        return 0

    embeddings = {term: get_embedding(term) for term in terms}
    print(terms)
    sims = [ 1.0 - cosine(embeddings[t1], embeddings[t2])
             for t1, t2 in itertools.combinations(terms, 2)]

    return float(np.mean(sims))
def process_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    terms = []
    in_terms_section = False
    for line in lines:
        line = line.strip()
        if line.startswith("Cluster") and "Terms" in line:
            in_terms_section = True
            continue
        elif in_terms_section and line:
            terms.append(line)
    if terms:
        avg_similarity = compute_average_similarity(terms)
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"\nAverage Pairwise Similarity Score: {avg_similarity:.4f}\n")

def main():
    files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith("_terms.txt")]
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        executor.map(process_file, files)
    print("Processing complete!")

if __name__ == "__main__":
    main()
