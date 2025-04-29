import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter
from rake_nltk import Rake
from transformers import AutoTokenizer, AutoModel
from torch.utils.data import Dataset, DataLoader
import torch
from openai import OpenAI
import ast

def parse_input_data(file_path):
    data = []
    with open(file_path, 'r') as file:
        for line in file:
            parts = line.strip().split('\t')
            if len(parts) >= 3:
                terms = parts[3].split(', ')
                print(terms)
                data.append(terms)
    return data

input_file_path = "2020_2024_health_matches.txt"
input_data = parse_input_data(input_file_path)

terms = list(set(term for sublist in input_data for term in sublist))

tokenizer = AutoTokenizer.from_pretrained("microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext")
model = AutoModel.from_pretrained("microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext")

class GlossaryDataset(Dataset):
    def __init__(self, terms):
        self.terms = terms

    def __len__(self):
        return len(self.terms)

    def __getitem__(self, idx):
        return self.terms[idx]

def encode_terms_in_batches(terms, batch_size=8):
    dataset = GlossaryDataset(terms)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

    all_embeddings = []
    for batch in dataloader:
        print("Processing new batch")
        inputs = tokenizer(batch, padding=True, truncation=True, return_tensors='pt', max_length=512)
        with torch.no_grad():
            outputs = model(**inputs)
        embeddings = outputs.last_hidden_state.mean(dim=1)
        all_embeddings.append(embeddings)

    return torch.cat(all_embeddings).numpy()

X = encode_terms_in_batches(terms)

k = 200  # Cluster Num.
kmeans = KMeans(n_clusters=k, random_state=42)
kmeans.fit(X)

cluster_labels = kmeans.labels_

cluster_terms = {i: [] for i in range(k)}
for i, label in enumerate(cluster_labels):
    cluster_terms[label].append(terms[i])

for cluster, terms_in_cluster in cluster_terms.items():
    cluster_filename = f"cluster_{cluster}_terms.txt"
    with open(cluster_filename, 'w') as file:
        file.write(f"Cluster {cluster} Terms:\n")
        for term in terms_in_cluster:
            file.write(f"{term}\n")
