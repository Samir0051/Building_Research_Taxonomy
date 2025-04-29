import os
folder_path = "200_2020_2024_health_domain"

for filename in os.listdir(folder_path):
    if filename.startswith("cluster_") and filename.endswith("_terms.txt"):
        file_path = os.path.join(folder_path, filename)

        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        terms = [
            line.strip()
            for line in lines[1:]
            if line.strip() and not line.lower().startswith("average pairwise similarity score")
        ]

        if len(terms) <= 1:
          print(f"Deleting {filename} (only {len(terms)} term{'s' if len(terms) != 1 else ''})")
          os.remove(file_path)
