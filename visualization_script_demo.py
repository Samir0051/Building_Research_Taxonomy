import openai
from openai import OpenAI
import docx
import ast
import os
import openai
import re
import json
import pandas as pd

client = OpenAI(api_key="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")

keywords_file = "paper_keyword_mapping.txt"     
domain_terms_file = "term_domains.txt"          
health_clusters_file = "health_output.json"
methodology_clusters_file = "method_output.json"

mapping_output_file = "paper_cluster_mapping.json"
health_matches_file = "health_matches.txt"
methodology_matches_file = "methodology_matches.txt"

def parse_domain_terms(file_path):
     health_terms = []
     methodology_terms = []
     with open(file_path, "r") as f:
         for line in f:
             parts = line.strip().split("\t")
             if len(parts) == 2:
                 term, domain = parts[0].strip(), parts[1].strip()
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
                {"role": "user", "content": f"""
                    Analyze the following keywords and determine if it matches terms in the health domain or methodology domain.

                    Keywords: "{keyword}"
                    Health Domain Terms: {health_terms}
                    Methodology Domain Terms: {methodology_terms}

                    Respond with 'Health', 'Methodology', or 'None' based on the match.
                    """}
            ],
            max_tokens=150,
            n=1,
            temperature=0.5
    )
    return str(response.choices[0].message.content).strip()

health_terms, methodology_terms = parse_domain_terms(domain_terms_file)

with open(keywords_file, "r", encoding="utf-8") as f:
    keywords_data = f.readlines()

print("RUNNING MATCHING SCRIPT")
for line in keywords_data:
    line = line.strip()
    parts = line.split("\t")
    print("\nProcessing a new paper...")
    if len(parts) >= 3:
        year, paper_title, keywords = parts[0], parts[1], parts[2]
        individual_keywords = [kw.strip() for kw in keywords.split(",")]
        health_keywords = []
        methodology_keywords = []
        for keyword in individual_keywords:
            classification = classify_keyword_with_chatgpt(keyword, health_terms, methodology_terms)
            if classification == "Health":
                health_keywords.append(keyword)
            elif classification == "Methodology":
                methodology_keywords.append(keyword)

        if health_keywords:
            health_line = f"{year}\t{paper_title}\t{', '.join(health_keywords)}"
            with open(health_matches_file, "a", encoding="utf-8") as health_file:
                health_file.write(health_line + "\n")
            print("Health match!: " + paper_title + "\t" + "Keywords: " + str(health_keywords))


        if methodology_keywords:
            methodology_line = f"{year}\t{paper_title}\t{', '.join(methodology_keywords)}"
            with open(methodology_matches_file, "a", encoding="utf-8") as methodology_file:
                methodology_file.write(methodology_line + "\n")
            print("Methodology match!: " + paper_title + "\t" + "Keywords: " + str(methodology_keywords))

def load_papers(filename):
    papers = []
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if "\t" in line:
                parts = line.split("\t")
            else:
                parts = re.split(r'\s{2,}', line)
            if len(parts) >= 3:
                paper = {
                    "Year": parts[0].strip(),
                    "Paper Title": parts[1].strip(),
                    "Keywords": parts[2].strip()
                }
                papers.append(paper)
    return papers

def load_matches(filename):
    papers = []
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
        if "\t" in line:
            parts = line.split("\t")
        else:
            parts = re.split(r'\s{2,}', line)
        if len(parts) >= 3:
            paper = {
                "Year": parts[0].strip(),
                "Paper Title": parts[1].strip(),
                "Keywords": parts[2].strip()
            }
            papers.append(paper)
    return papers

def load_clusters(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def map_paper_to_clusters(paper_keywords, clusters):
    paper_keywords_lower = paper_keywords.lower()
    matched_clusters = []
    for cluster in clusters:
       # print(f"Checking cluster '{cluster['name']}' with terms {cluster['terms']}")
        for term in cluster["terms"]:
            pattern = r'\b' + re.escape(term.lower()) + r'\b'
            if re.search(pattern, paper_keywords_lower):
                matched_clusters.append(cluster["id"])
                break
    return matched_clusters

def create_cluster_mapping(papers, clusters):
    mapping = {cluster["id"]: {"name": cluster["name"], "count": 0, "papers": []} for cluster in clusters}
    print("mapping papers")
    for paper in papers:
        matches = map_paper_to_clusters(paper["Keywords"], clusters)
        for cluster_id in matches:
            mapping[cluster_id]["count"] += 1
            mapping[cluster_id]["papers"].append(paper)
    return mapping


def extract_papers_and_cluster_names(domain_mapping):
    clusters = []
    aggregatedCounts = {}
    for cluster in domain_mapping.values():
        if cluster["count"] > 0:
            clusters.append(cluster["name"])
            aggregatedCounts[cluster["name"]] = cluster["count"]
    clusters.sort(key=lambda x: aggregatedCounts[x], reverse=True)

    paper_dict = {}
    for cluster in domain_mapping.values():
        for paper in cluster["papers"]:
            key = (paper["Year"], paper["Paper Title"])
            if key not in paper_dict:
                paper_dict[key] = paper
    papers = list(paper_dict.values())
    return papers, clusters, aggregatedCounts

def compute_year_counts(domain_mapping):
    year_counts = {}
    for cluster in domain_mapping.values():
        if cluster["count"] > 0:
            cname = cluster["name"]
            if cname not in year_counts:
                year_counts[cname] = {}
            for paper in cluster["papers"]:
                year = paper["Year"]
                year_counts[cname][year] = year_counts[cname].get(year, 0) + 1
    return year_counts

def generate_html_visualization_from_mapping(mapping_file, domain, output_html, title, years_override=None):
    print("generating visualization")
    with open(mapping_file, "r", encoding="utf-8") as f:
        mapping = json.load(f)
    domain_mapping = mapping[f"{domain}_clusters"]
    
    aggregatedCounts = {}
    cluster_papers = {}
    for cluster in domain_mapping.values():
        if cluster["count"] > 0:
            cname = cluster["name"]
            aggregatedCounts[cname] = aggregatedCounts.get(cname, 0) + cluster["count"]
            if cname not in cluster_papers:
                cluster_papers[cname] = []
            cluster_papers[cname].extend(cluster["papers"])
    
    sortedClusters = sorted(aggregatedCounts.keys(), key=lambda x: aggregatedCounts[x], reverse=True)

    for cluster in domain_mapping.values():
        for paper in cluster["papers"]:
            yearStr = str(paper["Year"]).strip()
            normalized = re.sub(r'\D', '', yearStr)
            if normalized == "":
                normalized = yearStr
            paper["Year"] = str(int(normalized))

    if years_override is None:
        all_years = set()
        for cluster in domain_mapping.values():
            for paper in cluster["papers"]:
                all_years.add(paper["Year"])
        years = sorted(list(all_years))
    else:
        years = sorted(years_override)
    
    yearCounts = {}
    for cluster in domain_mapping.values():
        if cluster["count"] > 0:
            cname = cluster["name"]
            if cname not in yearCounts:
                yearCounts[cname] = {}
            for paper in cluster["papers"]:
                y = paper["Year"]
                yearCounts[cname][y] = yearCounts[cname].get(y, 0) + 1
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
      <style>
        body {{
          font-family: Arial, sans-serif;
          text-align: center;
        }}
        #plot {{
          width: 90%;
          height: 800px;
          margin: auto;
        }}
        #paper-table-container {{
          margin-top: 25px;
        }}
        table {{
          width: 90%;
          margin: auto;
          border-collapse: collapse;
        }}
        th, td {{
          border: 1px solid #ddd;
          padding: 8px;
        }}
        th {{
          background-color: #f2f2f2;
        }}
      </style>
    </head>
    <body>
      <div id="plot"></div>
      <h2>Associated Papers</h2>
      <div id="paper-table-container"></div>
      <script>
        var aggregatedCounts = {json.dumps(aggregatedCounts)};
        var yearCounts = {json.dumps(yearCounts)};
        var sortedClusters = {json.dumps(sortedClusters)};
        var years = {json.dumps(years)};
        var clusterPapers = {json.dumps(cluster_papers)};
        
        function createTraces(selectedClusters) {{
          var traces = [];
          years.forEach(function(year) {{
            var counts = selectedClusters.map(function(cluster) {{
              return (yearCounts[cluster] && yearCounts[cluster][year]) ? yearCounts[cluster][year] : 0;
            }});
            traces.push({{
              x: selectedClusters,
              y: counts,
              type: 'bar',
              name: year
            }});
          }});
          return traces;
        }}

        var data = createTraces(sortedClusters);

        var layout = {{
          title: '{title}',
          height: 800,
          barmode: 'stack',
          xaxis: {{
            title: 'Cluster Name',
            tickangle: 45,
            tickfont: {{
              size: 10
            }},
            automargin: true
          }},
          yaxis: {{
            title: 'Number of Papers'
          }},
          margin: {{l: 150, r: 150, t: 100, b: 250}}
        }};

        Plotly.newPlot('plot', data, layout);

        document.getElementById('plot').on('plotly_click', function(eventData) {{
          var point = eventData.points[0];
          var clickedCluster = point.x;
          var matchingPapers = clusterPapers[clickedCluster] || [];
          var container = document.getElementById('paper-table-container');
          container.innerHTML = "";
          if (matchingPapers.length === 0) {{
            container.innerHTML = "<p>No papers found for this cluster.</p>";
            return;
          }}
          var table = document.createElement('table');
          var thead = document.createElement('thead');
          var headerRow = document.createElement('tr');
          ['Year', 'Paper Title', 'Keywords'].forEach(function(header) {{
            var th = document.createElement('th');
            th.textContent = header;
            headerRow.appendChild(th);
          }});
          thead.appendChild(headerRow);
          table.appendChild(thead);
          var tbody = document.createElement('tbody');
          matchingPapers.forEach(function(paper) {{
            var tr = document.createElement('tr');
            var tdYear = document.createElement('td');
            tdYear.textContent = paper.Year;
            tr.appendChild(tdYear);
            var tdTitle = document.createElement('td');
            tdTitle.textContent = paper["Paper Title"];
            tr.appendChild(tdTitle);
            var tdKeywords = document.createElement('td');
            tdKeywords.textContent = paper.Keywords;
            tr.appendChild(tdKeywords);
            tbody.appendChild(tr);
          }});
          table.appendChild(tbody);
          container.appendChild(table);
        }});
      </script>
    </body>
    </html>
    """
    
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html_content)

health_papers = load_matches(health_matches_file)
methodology_papers = load_matches(methodology_matches_file)
health_clusters = load_clusters(health_clusters_file)
methodology_clusters = load_clusters(methodology_clusters_file)

health_mapping = create_cluster_mapping(health_papers, health_clusters)
methodology_mapping = create_cluster_mapping(methodology_papers, methodology_clusters)

combined_mapping = {
    "health_clusters": health_mapping,
    "methodology_clusters": methodology_mapping
}

with open(mapping_output_file, "w", encoding="utf-8") as f:
    json.dump(combined_mapping, f, indent=4)

generate_html_visualization_from_mapping(
    mapping_file=mapping_output_file,
    domain="methodology",
    output_html="clusters_with_papers_methodology.html",
    title="Methodology Paper Network"
)

generate_html_visualization_from_mapping(
    mapping_file=mapping_output_file,
    domain="health",
    output_html="clusters_with_papers_health.html",
    title="Health Paper Network"
)
print("Finished!")
