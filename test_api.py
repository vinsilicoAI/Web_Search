#!/usr/bin/env python3
"""
Simple test script to verify Google Custom Search API is working
"""

import os
import sys
import requests
import json


def test_google_api(api_key: str, search_engine_id: str):
    """Test Google Custom Search API with a simple query"""
    
    base_url = "https://www.googleapis.com/customsearch/v1"
    
    params = {
        'key': api_key,
        'cx': search_engine_id,
        'q': 'restaurants San Francisco',
        'num': 3
    }
    
    print("Testing Google Custom Search API...")
    print(f"API Key: {api_key[:10]}...{api_key[-5:]}")
    print(f"Search Engine ID: {search_engine_id}")
    print(f"Query: restaurants San Francisco")
    print("\nMaking API request...")
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'error' in data:
                print("\n❌ API Error:")
                error_info = data['error']
                print(f"  Message: {error_info.get('message', 'Unknown')}")
                if 'errors' in error_info:
                    for err in error_info['errors']:
                        print(f"  - {err.get('message', '')} ({err.get('reason', '')})")
                return False
            
            if 'items' in data:
                print(f"\n✅ Success! Found {len(data['items'])} results")
                print("\nSample results:")
                for i, item in enumerate(data['items'][:3], 1):
                    print(f"\n{i}. {item.get('title', 'N/A')}")
                    print(f"   URL: {item.get('link', 'N/A')}")
                    print(f"   Snippet: {item.get('snippet', 'N/A')[:100]}...")
                return True
            else:
                print("\n⚠️  No 'items' in response")
                print(f"Response keys: {list(data.keys())}")
                if 'searchInformation' in data:
                    total = data['searchInformation'].get('totalResults', '0')
                    print(f"Total results: {total}")
                return False
        else:
            print(f"\n❌ HTTP Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Response: {response.text[:500]}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request failed: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"\n❌ JSON decode error: {e}")
        print(f"Response: {response.text[:500]}")
        return False


if __name__ == "__main__":
    api_key = os.getenv('GOOGLE_API_KEY')
    search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
    
    if not api_key:
        api_key = input("Enter your Google Custom Search API Key: ").strip()
    if not search_engine_id:
        search_engine_id = input("Enter your Google Custom Search Engine ID: ").strip()
    
    if not api_key or not search_engine_id:
        print("Error: API key and Search Engine ID are required", file=sys.stderr)
        sys.exit(1)
    
    success = test_google_api(api_key, search_engine_id)
    
    if success:
        print("\n✅ API is working correctly!")
    else:
        print("\n❌ API test failed. Please check your credentials and API setup.")
        sys.exit(1)

