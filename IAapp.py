import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import pandas as pd
import streamlit as st
from io import BytesIO

# Function to crawl and extract URLs
def get_website_urls(base_url):
    visited = set()
    to_visit = set([base_url])
    unique_urls = set()
    domain = urlparse(base_url).netloc

    st.write(f"Starting to crawl the website: {base_url}")

    while to_visit:
        current_url = to_visit.pop()
        if current_url not in visited:
            visited.add(current_url)
            st.write(f"Visiting URL: {current_url}")
            try:
                response = requests.get(current_url, timeout=10)
                response.encoding = 'utf-8'  # Force UTF-8 encoding
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'lxml')  # Use 'lxml' parser
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        full_url = urljoin(base_url, href)
                        if urlparse(full_url).netloc == domain and full_url not in visited:
                            to_visit.add(full_url)
                            unique_urls.add(full_url)
                else:
                    st.write(f"Error: Received status code {response.status_code} for {current_url}")
            except requests.exceptions.RequestException as e:
                st.write(f"Error crawling {current_url}: {e}")

    st.write(f"Finished crawling. Found {len(unique_urls)} unique internal URLs.")
    return sorted(unique_urls)

# Function to organize URLs hierarchically
def organize_urls_hierarchically(urls):
    hierarchy = []
    sorted_urls = sorted(urls, key=lambda x: x.split('/'))
    max_depth = max(len(urlparse(url).path.strip('/').split('/')) for url in sorted_urls if urlparse(url).path.strip('/'))

    for url in sorted_urls:
        path = urlparse(url).path.strip('/')
        if not path:
            continue
        parts = path.split('/')
        levels = ["/" + "/".join(parts[:i+1]) for i in range(len(parts))]
        while len(levels) < max_depth:
            levels.append("")
        hierarchy.append((*levels, url))

    return hierarchy

# Function to export data to an Excel file
def export_to_excel(hierarchy):
    max_levels = max(len(entry) - 1 for entry in hierarchy)
    columns = [f'Navigation Level {i+1}' for i in range(max_levels)] + ['Current URL Address']
    df = pd.DataFrame(hierarchy, columns=columns)
    
    # Create a buffer to save the Excel file in-memory
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='URLs')
        writer.save()
    buffer.seek(0)
    return buffer

# Streamlit UI elements
st.title("Website URL Crawler")

# User input for the website URL
base_url = st.text_input("Enter the base URL of the website to crawl:", "https://example.com")

if base_url:
    if st.button('Start Crawling'):
        if not base_url.startswith("http"):
            st.error("Please enter a valid URL starting with 'http' or 'https'.")
        else:
            urls = get_website_urls(base_url)
            if not urls:
                st.write("No URLs found.")
            else:
                hierarchy = organize_urls_hierarchically(urls)
                st.write(f"Found {len(hierarchy)} URLs.")
                
                # Provide download link for the Excel file
                excel_file = export_to_excel(hierarchy)
                st.download_button(
                    label="Download URLs as Excel file",
                    data=excel_file,
                    file_name="website_urls.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
