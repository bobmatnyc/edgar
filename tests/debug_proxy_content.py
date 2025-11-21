#!/usr/bin/env python3
"""
Debug proxy filing content to understand the structure
"""

import requests
from bs4 import BeautifulSoup
import re

def debug_proxy_content():
    """Debug the actual proxy filing content"""
    
    # Apple's 2024 proxy filing URL (from our test)
    url = "https://www.sec.gov/Archives/edgar/data/320193/000130817924000010/laapl2024_def14a.htm"
    
    headers = {
        'User-Agent': 'Edgar Analyzer Tool contact@example.com',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            content = response.text
            print(f"Successfully fetched proxy filing, length: {len(content)}")
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for the actual Summary Compensation Table
            print("\n=== Searching for Summary Compensation Table ===")
            
            # Search for text containing "summary compensation table"
            summary_comp_text = soup.find_all(text=re.compile(r'summary compensation table', re.IGNORECASE))
            print(f"Found {len(summary_comp_text)} instances of 'summary compensation table'")
            
            for i, text in enumerate(summary_comp_text[:3]):  # Show first 3
                print(f"\nInstance {i+1}: {text.strip()[:100]}...")
                
                # Find the parent element and look for nearby tables
                parent = text.parent
                while parent and parent.name != 'table':
                    parent = parent.parent
                    if parent and parent.name == 'table':
                        break
                    # Also check siblings
                    if parent:
                        next_table = parent.find_next('table')
                        if next_table:
                            print(f"Found table after summary comp text:")
                            rows = next_table.find_all('tr')[:5]  # First 5 rows
                            for j, row in enumerate(rows):
                                cells = row.find_all(['td', 'th'])
                                row_text = ' | '.join([cell.get_text().strip()[:50] for cell in cells[:6]])
                                print(f"  Row {j}: {row_text}")
                            break
            
            # Also search for known executive names
            print("\n=== Searching for known Apple executives ===")
            known_execs = ['Tim Cook', 'Luca Maestri', 'Katherine Adams', 'Deirdre O\'Brien']
            
            for exec_name in known_execs:
                matches = soup.find_all(text=re.compile(re.escape(exec_name), re.IGNORECASE))
                print(f"\nFound {len(matches)} instances of '{exec_name}'")
                
                for match in matches[:2]:  # Show first 2
                    # Find if this is in a table
                    parent = match.parent
                    while parent and parent.name not in ['table', 'body']:
                        parent = parent.parent
                    
                    if parent and parent.name == 'table':
                        print(f"  Found '{exec_name}' in a table!")
                        # Get the row containing this name
                        row = match.parent
                        while row and row.name != 'tr':
                            row = row.parent
                        
                        if row:
                            cells = row.find_all(['td', 'th'])
                            row_text = ' | '.join([cell.get_text().strip()[:30] for cell in cells])
                            print(f"    Row: {row_text}")
                            
                            # Check if this looks like a compensation table
                            row_text_lower = row_text.lower()
                            if any(word in row_text_lower for word in ['salary', 'bonus', 'stock', 'total', 'compensation', '$']):
                                print(f"    *** This looks like a compensation row! ***")
                                
                                # Show the table structure
                                table = row.find_parent('table')
                                if table:
                                    all_rows = table.find_all('tr')
                                    print(f"    Table has {len(all_rows)} rows")
                                    
                                    # Show header row
                                    if all_rows:
                                        header_cells = all_rows[0].find_all(['td', 'th'])
                                        header_text = ' | '.join([cell.get_text().strip()[:20] for cell in header_cells])
                                        print(f"    Header: {header_text}")
                                break
                        
        else:
            print(f"Failed to fetch proxy filing: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_proxy_content()
