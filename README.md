# Web Search Agent

A Python-based web search agent that uses Google Custom Search API to find companies based on keywords and geographic location, then extracts and displays company contact information (name, email, address, phone) in a formatted HTML output.

## Features

- **Google Custom Search Integration**: Uses Google Custom Search API for reliable search results.
- **Improved Information Extraction**: Automatically extracts and cleanses:
  - Company name (with English translation)
  - Email address
  - Phone number
  - Physical address (with English translation)
- **Automatic Filtering**:
  - **Quality Control**: Filters out "empty" or low-quality records that lack basic contact info.
  - **Deduplication**: Ensures only unique websites (by domain) are listed.
  - **Non-Company Blocking**: Automatically excludes social media, directories, and marketplaces (e.g., Facebook, Yelp, Amazon) to focus on actual company websites.
- **Smart Decoding & Translation**:
  - Detects website encoding to fix "REPLACEMENT CHARACTER" issues.
  - Translates foreign-language company names and addresses to English (requires `deep-translator`).
- **Geographic Filtering**: Search results filtered by location.
- **HTML Output**: Beautiful, formatted HTML report with all results.

## Prerequisites

1. **Python 3.7+** installed on your system
2. **Google Custom Search API Key**: 
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the "Custom Search API"
   - Create credentials (API Key)
3. **Google Custom Search Engine ID**:
   - Go to [Google Custom Search](https://cse.google.com/cse/)
   - Create a new search engine (enable "Search the entire web")
   - Get your Search Engine ID (CX)

## Installation

1. Clone or download this repository.

2. Install required dependencies:
```bash
pip install requests beautifulsoup4
```

3. (Optional) For translation features, install `deep-translator`:
```bash
pip install deep-translator
```

## Configuration

You can set your API credentials in two ways:

### Option 1: Environment Variables (Recommended)
```bash
export GOOGLE_API_KEY="your-api-key-here"
export GOOGLE_SEARCH_ENGINE_ID="your-search-engine-id-here"
```

### Option 2: Enter at Runtime
The script will prompt you for the credentials if they are not set in your environment.

## Usage

Run the updated v2 script:
```bash
python web_search_agent_v2.py
```

The script will prompt you for:
1. **Search Keywords**: What to search for (e.g., "restaurants", "law firms", "plumbers")
2. **Geographic Location**: Where to search (e.g., "New York", "San Francisco CA", "Tokyo Japan")
3. **Maximum Number of Entries**: How many results to process (default: 10)

### Example
```
Enter search keywords: sushi restaurants
Enter geographic location: Tokyo Japan
Enter maximum number of entries: 20
```

## Output

The script generates an HTML file named `search_results_[timestamp].html` containing:
- Search parameters used
- Table with unique, verified company information
- Clickable links to company websites
- Formatted, professional layout

## How It Works (v2)

1. **Search Phase**: Uses Google Custom Search API to find relevant websites.
2. **Scraping & Cleaning Phase**: 
   - Visits each result URL.
   - **Encoding Fix**: Detects charset to prevent mojibake.
   - **Translation**: Translates name/address to English if needed.
   - **Extraction**: EXTRACTS Name, Email, Phone, Address, JSON-LD data.
3. **Filtering Phase**:
   - **Blocklist**: Drops known non-company sites (Social Media, Directories).
   - **Validation**: Drops records with no contact info.
   - **Deduplication**: Keeps only one result per unique domain.
4. **Output Phase**: Generates a clean HTML report.

## License

This project is provided as-is for educational and personal use.
