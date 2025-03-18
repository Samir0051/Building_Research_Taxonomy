#!/bin/bash

files=(
  "health_matches.txt"
  "methodology_matches.txt"
  "clusters_with_papers_health.html"
  "clusters_with_papers_methodology.html"
  "paper_cluster_mapping.json"
)

for file in "${files[@]}"; do
  if [ -f "$file" ]; then
    echo "Removing $file..."
    rm "$file"
  else
    echo "$file not found."
  fi
done
