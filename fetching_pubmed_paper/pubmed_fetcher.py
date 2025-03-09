import requests
import xmltodict
import json
import argparse

def fetch_pubmed_papers(query):
    """Fetches research papers from PubMed based on the given query."""
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": 10  # Fetch up to 10 papers for now
    }

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        data = response.json()
        return data.get("esearchresult", {}).get("idlist", [])
    else:
        print("Error fetching data from PubMed:", response.status_code)
        return []

def fetch_paper_details(paper_ids):
    """Fetches detailed information for each PubMed paper ID."""
    if not paper_ids:
        print("No paper IDs found.")
        return None

    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "pubmed",
        "id": ",".join(paper_ids),  # Pass multiple paper IDs
        "retmode": "xml"  # XML format for full details
    }

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        return response.text  # Returning XML response
    else:
        print("Error fetching details from PubMed:", response.status_code)
        return None

def parse_pubmed_xml(xml_data):
    """Parses PubMed XML and extracts useful details."""
    parsed_data = xmltodict.parse(xml_data)

    # Debugging: Print raw parsed XML to dictionary
    print("\nDEBUG: Parsed XML to Dictionary Format:\n", parsed_data)

    articles = parsed_data.get("PubmedArticleSet", {}).get("PubmedArticle", [])

    extracted_data = []
    
    for article in articles:
        medline_citation = article.get("MedlineCitation", {})
        article_info = medline_citation.get("Article", {})

        # Extract Title
        title = article_info.get("ArticleTitle", "No Title Found")

        # Extract Authors
        author_list = article_info.get("AuthorList", {}).get("Author", [])
        authors = []
        if isinstance(author_list, list):
            for author in author_list:
                last_name = author.get("LastName", "")
                fore_name = author.get("ForeName", "")
                full_name = f"{fore_name} {last_name}".strip()
                if full_name:
                    authors.append(full_name)

        # Extract Affiliations
        affiliations = []
        if isinstance(author_list, list) and author_list:
            for author in author_list:
                affiliation_info = author.get("AffiliationInfo", [])
                if isinstance(affiliation_info, list):
                    for aff in affiliation_info:
                        if "Affiliation" in aff:
                            affiliations.append(aff["Affiliation"])

        extracted_data.append({
            "title": title,
            "authors": authors,
            "affiliations": affiliations
        })

    return extracted_data

def save_to_json(data, filename="pubmed_results.json"):
    """Saves extracted PubMed data to a JSON file."""
    with open(filename, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=False)
    print(f"\n✅ Data saved successfully to {filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch PubMed research papers based on a query.")
    parser.add_argument("query", type=str, help="Search term for PubMed articles")
    args = parser.parse_args()

    query = args.query  # Get user input
    print(f"\n🔍 Searching PubMed for: {query}")

    paper_ids = fetch_pubmed_papers(query)
    print("Fetched Paper IDs:", paper_ids)

    if paper_ids:
        details = fetch_paper_details(paper_ids)
        print("\nExtracting Paper Details...")

        parsed_data = parse_pubmed_xml(details)

        for index, paper in enumerate(parsed_data, 1):
            print(f"\n🔹 Paper {index}:")
            print(f"📌 Title: {paper['title']}")
            print(f"📝 Authors: {', '.join(paper['authors']) if paper['authors'] else 'No Authors Found'}")
            print(f"🏛️ Affiliations: {', '.join(paper['affiliations']) if paper['affiliations'] else 'No Affiliations Found'}")

        # Save the extracted data to JSON
        save_to_json(parsed_data)