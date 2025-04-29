import openai
from openai import OpenAI
import docx
import ast
import os
import re

client = #api key

keywords_file = "2020_2024_data.txt"
domain_terms_file = "TermDomains.txt"
health_output_file = "2020_2024_health_matches.txt"
methodology_output_file = "2020_2024_methodology_matches.txt"

def parse_domain_terms(file_path):
    health_terms = []
    methodology_terms = []
    with open(file_path, "r") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) == 2:
                term, domain = parts
                if domain == "H":
                    health_terms.append(term)
                elif domain == "M":
                    methodology_terms.append(term)
    return health_terms, methodology_terms

def classify_keyword_with_chatgpt(keyword, health_terms, methodology_terms):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an expert in bioinformatic terminology."},
            {"role": "user", "content": f""" Analyze the following keyword and determine if it matches terms in the health domain or methodology domain.
            Keyword: "{keyword}" Health Domain Terms: {health_terms} Methodology Domain Terms: {methodology_terms} Respond with 'Health', 'Methodology', or 'None' based on the match.
            """ }
        ],
        max_tokens=10,
        temperature=0.0
    )
    return response.choices[0].message.content.strip()

health_terms, methodology_terms = parse_domain_terms(domain_terms_file)

health_matches_set = set()
methodology_matches_set = set()

with open(keywords_file, "r") as f:
    keywords_data = f.readlines()
with open(health_output_file, "a") as health_file, open(methodology_output_file, "a") as methodology_file:
     for line in keywords_data:
        parts = re.split(r'\s{6,}', line.strip())
        print(parts)
        print(len(parts))
        if len(parts) < 4:
            continue

        year, category, paper_title, keywords = parts
        individual_keywords = [kw.strip() for kw in keywords.split(",")]
        
        health_keywords = []
        methodology_keywords = []

        for kw in individual_keywords:
            cls = classify_keyword_with_chatgpt(kw, health_terms, methodology_terms)
            if cls == "Health":
                health_keywords.append(kw)
                health_matches_set.add(kw)
            elif cls == "Methodology":
                methodology_keywords.append(kw)
                methodology_matches_set.add(kw)

        if health_keywords:
            line_out = f"{year}\t{category}\t{paper_title}\t{', '.join(health_keywords)}"
            health_file.write(line_out + "\n")

        if methodology_keywords:
            line_out = f"{year}\t{category}\t{paper_title}\t{', '.join(methodology_keywords)}"
            methodology_file.write(line_out + "\n")
print(f"Distinct Health keywords matched:      {len(health_matches_set)}")
print(f"Distinct Methodology keywords matched: {len(methodology_matches_set)}")
