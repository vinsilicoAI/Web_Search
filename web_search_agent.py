#!/usr/bin/env python3
"""
Web Search Agent - Searches for companies using Google Search API
and extracts contact information (name, email, address, phone)
"""

import os
import sys
import json
import re
import requests
from urllib.parse import urlparse, quote_plus
from html import escape
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import time


class WebSearchAgent:
    """Agent to search web and extract company information"""
    
    def __init__(self, api_key: str, search_engine_id: str):
        """
        Initialize the search agent
        
        Args:
            api_key: Google Custom Search API key
            search_engine_id: Google Custom Search Engine ID
        """
        self.api_key = api_key
        self.search_engine_id = search_engine_id
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search_google(self, keywords: str, location: str, max_results: int = 10) -> List[Dict]:
        """
        Search Google using Custom Search API
        
        Args:
            keywords: Search keywords
            location: Geographic location filter
            max_results: Maximum number of results to return
            
        Returns:
            List of search result dictionaries
        """
        results = []
        query = f"{keywords} {location}"
        
        print(f"Searching Google with query: '{query}'")
        
        # Google Custom Search API allows 10 results per request
        num_requests = (max_results + 9) // 10
        
        for i in range(num_requests):
            start_index = i * 10 + 1
            params = {
                'key': self.api_key,
                'cx': self.search_engine_id,
                'q': query,
                'num': min(10, max_results - len(results)),
                'start': start_index
            }
            
            try:
                response = self.session.get(self.base_url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                # Check for API errors in response
                if 'error' in data:
                    error_info = data['error']
                    error_msg = error_info.get('message', 'Unknown error')
                    print(f"Google API Error: {error_msg}", file=sys.stderr)
                    if 'errors' in error_info:
                        for err in error_info['errors']:
                            print(f"  - {err.get('message', '')}", file=sys.stderr)
                    break
                
                if 'items' in data:
                    print(f"Found {len(data['items'])} results in this batch")
                    for item in data['items']:
                        results.append({
                            'title': item.get('title', ''),
                            'link': item.get('link', ''),
                            'snippet': item.get('snippet', '')
                        })
                        
                        if len(results) >= max_results:
                            break
                else:
                    print(f"No 'items' in API response. Response keys: {list(data.keys())}")
                    if 'searchInformation' in data:
                        total_results = data['searchInformation'].get('totalResults', '0')
                        print(f"Total results available: {total_results}")
                    break
                
                # Rate limiting - be respectful
                time.sleep(0.5)
                
            except requests.exceptions.HTTPError as e:
                print(f"HTTP Error searching Google: {e}", file=sys.stderr)
                try:
                    error_data = response.json()
                    print(f"Error details: {error_data}", file=sys.stderr)
                except:
                    print(f"Response text: {response.text[:500]}", file=sys.stderr)
                break
            except requests.exceptions.RequestException as e:
                print(f"Error searching Google: {e}", file=sys.stderr)
                break
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON response: {e}", file=sys.stderr)
                print(f"Response text: {response.text[:500]}", file=sys.stderr)
                break
        
        print(f"Total search results collected: {len(results)}")
        return results[:max_results]
    
    def extract_email(self, text: str) -> Optional[str]:
        """Extract email address from text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            # Filter out common false positives
            filtered = [e for e in emails if not any(x in e.lower() for x in ['example.com', 'test.com', 'domain.com'])]
            return filtered[0] if filtered else emails[0]
        return None
    
    def extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number from text"""
        # Common phone patterns
        patterns = [
            r'\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # US format
            r'\+?\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}',  # International
        ]
        
        for pattern in patterns:
            phones = re.findall(pattern, text)
            if phones:
                return phones[0].strip()
        return None
    
    def extract_address(self, text: str) -> Optional[str]:
        """Extract address from text"""
        # Look for common address patterns
        address_patterns = [
            r'\d+\s+[A-Za-z0-9\s,]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct|Place|Pl)[\s,]+[A-Za-z\s,]+(?:[A-Z]{2})?\s+\d{5}',
            r'\d+\s+[A-Za-z0-9\s,]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct|Place|Pl)',
        ]
        
        for pattern in address_patterns:
            addresses = re.findall(pattern, text, re.IGNORECASE)
            if addresses:
                return addresses[0].strip()
        return None
    
    def scrape_company_info(self, url: str) -> Dict[str, Optional[str]]:
        """
        Scrape company information from a webpage
        
        Args:
            url: URL to scrape
            
        Returns:
            Dictionary with company information
        """
        info = {
            'company_name': None,
            'email': None,
            'address': None,
            'phone': None,
            'url': url
        }
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get all text
            text = soup.get_text()
            text = ' '.join(text.split())  # Normalize whitespace
            
            # Extract company name from title or h1
            title_tag = soup.find('title')
            if title_tag:
                info['company_name'] = title_tag.get_text().strip()
            
            h1_tag = soup.find('h1')
            if h1_tag and not info['company_name']:
                info['company_name'] = h1_tag.get_text().strip()
            
            # Extract email
            info['email'] = self.extract_email(text)
            
            # Extract phone
            info['phone'] = self.extract_phone(text)
            
            # Extract address
            info['address'] = self.extract_address(text)
            
            # Look for structured data (JSON-LD, microdata)
            json_ld = soup.find_all('script', type='application/ld+json')
            for script in json_ld:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        # Check for Organization schema
                        if data.get('@type') == 'Organization' or 'Organization' in str(data.get('@type', '')):
                            if not info['company_name'] and 'name' in data:
                                info['company_name'] = data['name']
                            if not info['email'] and 'email' in data:
                                info['email'] = data['email']
                            if not info['phone'] and 'telephone' in data:
                                info['phone'] = data['telephone']
                            if not info['address'] and 'address' in data:
                                addr = data['address']
                                if isinstance(addr, dict):
                                    addr_parts = []
                                    for key in ['streetAddress', 'addressLocality', 'addressRegion', 'postalCode']:
                                        if key in addr:
                                            addr_parts.append(addr[key])
                                    if addr_parts:
                                        info['address'] = ', '.join(addr_parts)
                except:
                    pass
            
            # Rate limiting
            time.sleep(1)
            
        except Exception as e:
            print(f"Error scraping {url}: {e}", file=sys.stderr)
        
        return info
    
    def search_and_extract(self, keywords: str, location: str, max_entries: int = 10) -> List[Dict]:
        """
        Main method to search and extract company information
        
        Args:
            keywords: Search keywords
            location: Geographic location
            max_entries: Maximum number of entries to process
            
        Returns:
            List of company information dictionaries
        """
        print(f"Searching for: {keywords} in {location}...")
        search_results = self.search_google(keywords, location, max_entries)
        
        print(f"Found {len(search_results)} results. Extracting company information...")
        company_info_list = []
        
        for i, result in enumerate(search_results, 1):
            print(f"Processing {i}/{len(search_results)}: {result['link']}")
            info = self.scrape_company_info(result['link'])
            
            # Use search result title if no company name found
            if not info['company_name']:
                info['company_name'] = result['title']
            
            # Add snippet information if missing
            if not info['email']:
                info['email'] = self.extract_email(result['snippet'])
            if not info['phone']:
                info['phone'] = self.extract_phone(result['snippet'])
            if not info['address']:
                info['address'] = self.extract_address(result['snippet'])
            
            company_info_list.append(info)
        
        return company_info_list
    
    def generate_html(self, company_info_list: List[Dict], keywords: str, location: str) -> str:
        """
        Generate HTML output from company information
        
        Args:
            company_info_list: List of company information dictionaries
            keywords: Search keywords used
            location: Location searched
            
        Returns:
            HTML string
        """
        escaped_keywords = escape(keywords)
        escaped_location = escape(location)
        count = len(company_info_list)
        generated_time = time.strftime('%Y-%m-%d %H:%M:%S')
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Company Search Results</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        .search-info {{
            background-color: #e8f5e9;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .search-info p {{
            margin: 5px 0;
            color: #2e7d32;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th {{
            background-color: #4CAF50;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 12px;
            border-bottom: 1px solid #ddd;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .company-name {{
            font-weight: bold;
            color: #1976d2;
        }}
        .url {{
            color: #1976d2;
            text-decoration: none;
        }}
        .url:hover {{
            text-decoration: underline;
        }}
        .missing {{
            color: #999;
            font-style: italic;
        }}
        .stats {{
            margin-top: 20px;
            padding: 15px;
            background-color: #f0f0f0;
            border-radius: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Company Search Results</h1>
        <div class="search-info">
            <p><strong>Keywords:</strong> {escaped_keywords}</p>
            <p><strong>Location:</strong> {escaped_location}</p>
            <p><strong>Total Results:</strong> {count}</p>
        </div>
        <table>
            <thead>
                <tr>
                    <th>Company Name</th>
                    <th>Email</th>
                    <th>Phone</th>
                    <th>Address</th>
                    <th>Website</th>
                </tr>
            </thead>
            <tbody>
"""
        
        for info in company_info_list:
            company_name = escape(info.get('company_name', 'N/A')) if info.get('company_name') else '<span class="missing">N/A</span>'
            email = escape(info.get('email', 'N/A')) if info.get('email') else '<span class="missing">N/A</span>'
            phone = escape(info.get('phone', 'N/A')) if info.get('phone') else '<span class="missing">N/A</span>'
            address = escape(info.get('address', 'N/A')) if info.get('address') else '<span class="missing">N/A</span>'
            url = escape(info.get('url', '#'))
            
            html += f"""
                <tr>
                    <td class="company-name">{company_name}</td>
                    <td>{email}</td>
                    <td>{phone}</td>
                    <td>{address}</td>
                    <td><a href="{url}" target="_blank" class="url">{url}</a></td>
                </tr>
"""
        
        html += f"""
            </tbody>
        </table>
        <div class="stats">
            <p><strong>Generated:</strong> {generated_time}</p>
        </div>
    </div>
</body>
</html>"""
        
        return html


def main():
    """Main function to run the web search agent"""
    # Get API credentials from environment or user input
    api_key = os.getenv('GOOGLE_API_KEY')
    search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
    
    if not api_key:
        api_key = input("Enter your Google Custom Search API Key: ").strip()
    if not search_engine_id:
        search_engine_id = input("Enter your Google Custom Search Engine ID: ").strip()
    
    if not api_key or not search_engine_id:
        print("Error: API key and Search Engine ID are required", file=sys.stderr)
        sys.exit(1)
    
    # Get user input
    keywords = input("Enter search keywords: ").strip()
    location = input("Enter geographic location: ").strip()
    
    try:
        max_entries = int(input("Enter maximum number of entries (default 10): ").strip() or "10")
    except ValueError:
        max_entries = 10
    
    if not keywords:
        print("Error: Keywords are required", file=sys.stderr)
        sys.exit(1)
    
    # Create agent and search
    agent = WebSearchAgent(api_key, search_engine_id)
    company_info = agent.search_and_extract(keywords, location, max_entries)
    
    if not company_info:
        print("\n⚠️  No results found. Possible reasons:")
        print("  1. API key or Search Engine ID may be incorrect")
        print("  2. API quota may be exceeded")
        print("  3. No search results match your query")
        print("  4. Check the error messages above for details")
        sys.exit(1)
    
    # Generate HTML
    html_output = agent.generate_html(company_info, keywords, location)
    
    # Save to file
    output_file = f"search_results_{int(time.time())}.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_output)
    
    print(f"\n✅ Results saved to: {output_file}")
    print(f"✅ Found {len(company_info)} companies")


if __name__ == "__main__":
    main()

