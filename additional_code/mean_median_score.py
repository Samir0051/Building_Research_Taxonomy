import os
import re
import numpy as np
folder_path = "200_2020_2024_health_domain"

def extract_similarity_score(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for line in reversed(lines):
        match = re.search(r"Average Pairwise Similarity Score: ([\d\.]+)", line)
        if match:
            return float(match.group(1))
    return None
similarity_scores = []
for filename in os.listdir(folder_path):
    if filename.endswith("_terms.txt"):
        file_path = os.path.join(folder_path, filename)
        score = extract_similarity_score(file_path)
        if score is not None:
            similarity_scores.append(score)
if similarity_scores:
    overall_avg_similarity = np.mean(similarity_scores)
    median_similarity = np.median(similarity_scores)
    print(f"Overall Average Pairwise Similarity Score Across Clusters: {overall_avg_similarity}")
    print(f"Overall Median Pairwise Similarity Score Across Clusters: {median_similarity}")
