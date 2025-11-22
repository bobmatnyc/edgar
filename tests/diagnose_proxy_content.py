#!/usr/bin/env python3
"""
Diagnose proxy statement content to understand why text extraction is failing
"""

import asyncio
import logging
import edgar
from edgar import Company

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def diagnose_proxy_content():
    """Diagnose what's actually in the proxy statements"""
    
    print("🔍 DIAGNOSING PROXY STATEMENT CONTENT")
    print("=" * 60)
    
    edgar.set_identity("test.user@example.com")
    
    # Test with Apple
    company = Company("AAPL")
    print(f"📊 Analyzing {company.name}")
    
    # Get proxy filings
    proxy_filings = company.get_filings(form="DEF 14A")
    
    if not proxy_filings:
        print("❌ No proxy filings found")
        return
    
    proxy_filing = proxy_filings[0]
    print(f"📄 Latest proxy: {proxy_filing.accession_number}")
    print(f"📅 Filing date: {proxy_filing.filing_date}")
    
    # Get filing object
    filing_obj = proxy_filing.obj()
    
    # Check available attributes
    print(f"\n🔍 Available attributes:")
    for attr in dir(filing_obj):
        if not attr.startswith('_'):
            print(f"   • {attr}")
    
    # Check if this is XBRL data
    if hasattr(filing_obj, 'facts'):
        print(f"\n🎯 THIS IS XBRL DATA!")
        print(f"📊 Facts: {len(filing_obj.facts)} XBRL facts available")
        print(f"📊 Contexts: {len(filing_obj.contexts)} XBRL contexts")

        # Look for executive compensation facts
        print(f"🔍 Exploring XBRL facts...")

        # Try different ways to access facts
        try:
            # Method 1: Use query to find compensation facts
            comp_facts = filing_obj.facts.filter(concept="*compensation*")
            print(f"📊 Compensation facts (filter): {len(comp_facts)}")

            for fact in comp_facts[:5]:
                print(f"   • {fact.concept}: {fact.value}")

        except Exception as e:
            print(f"❌ Filter method failed: {e}")

        try:
            # Method 2: Use pandas conversion
            facts_df = filing_obj.facts.to_pandas()
            print(f"📊 Facts DataFrame shape: {facts_df.shape}")
            print(f"📊 Columns: {list(facts_df.columns)}")

            # Look for compensation-related concepts
            comp_mask = facts_df['concept'].str.contains('compensation|salary|bonus|stock|option|executive|officer', case=False, na=False)
            comp_facts_df = facts_df[comp_mask]

            print(f"🎯 Executive compensation facts found: {len(comp_facts_df)}")

            if len(comp_facts_df) > 0:
                print(f"📋 Compensation concepts:")
                for concept in comp_facts_df['concept'].unique()[:10]:
                    print(f"   • {concept}")

        except Exception as e:
            print(f"❌ Pandas method failed: {e}")

        try:
            # Method 3: Check available methods on facts
            print(f"\n🔍 Facts object methods:")
            for method in dir(filing_obj.facts):
                if not method.startswith('_'):
                    print(f"   • {method}")

        except Exception as e:
            print(f"❌ Methods inspection failed: {e}")

        # Check statements
        if hasattr(filing_obj, 'statements'):
            statements = filing_obj.statements
            print(f"\n📋 XBRL Statements available:")
            for stmt_name in dir(statements):
                if not stmt_name.startswith('_'):
                    print(f"   • {stmt_name}")

    # Check text content
    if hasattr(filing_obj, 'text'):
        text_content = filing_obj.text()
        print(f"\n📝 Text content length: {len(text_content)} characters")
        print(f"📝 First 500 characters:")
        print("-" * 50)
        print(text_content[:500])
        print("-" * 50)
    
    # Check HTML content
    if hasattr(filing_obj, 'html'):
        try:
            html_content = filing_obj.html()
            print(f"\n🌐 HTML content length: {len(html_content)} characters")
            print(f"🌐 First 500 characters:")
            print("-" * 50)
            print(html_content[:500])
            print("-" * 50)
        except Exception as e:
            print(f"❌ Error getting HTML: {e}")
    
    # Check documents
    if hasattr(filing_obj, 'documents'):
        documents = filing_obj.documents
        print(f"\n📋 Documents: {len(documents)} found")
        
        for i, doc in enumerate(documents[:3]):  # Show first 3
            print(f"   Document {i+1}:")
            print(f"      Type: {getattr(doc, 'type', 'Unknown')}")
            print(f"      Filename: {getattr(doc, 'filename', 'Unknown')}")
            
            # Try to get document content
            if hasattr(doc, 'text'):
                try:
                    doc_text = doc.text()
                    print(f"      Text length: {len(doc_text)} characters")
                    
                    # Look for executive compensation keywords
                    keywords = ['executive compensation', 'summary compensation', 'salary', 'bonus', 'stock awards']
                    found_keywords = []
                    for keyword in keywords:
                        if keyword.lower() in doc_text.lower():
                            found_keywords.append(keyword)
                    
                    if found_keywords:
                        print(f"      🎯 Found keywords: {', '.join(found_keywords)}")
                        
                        # Show context around "summary compensation"
                        if 'summary compensation' in doc_text.lower():
                            idx = doc_text.lower().find('summary compensation')
                            context = doc_text[max(0, idx-200):idx+500]
                            print(f"      📊 Summary compensation context:")
                            print(f"         {context[:300]}...")
                    else:
                        print(f"      ⚠️ No executive compensation keywords found")
                        
                except Exception as e:
                    print(f"      ❌ Error getting document text: {e}")
    
    # Check attachments
    if hasattr(filing_obj, 'attachments'):
        attachments = filing_obj.attachments
        print(f"\n📎 Attachments: {len(attachments)} found")
        
        for i, attachment in enumerate(attachments[:3]):
            print(f"   Attachment {i+1}: {getattr(attachment, 'filename', 'Unknown')}")

async def main():
    """Main diagnostic function"""
    
    await diagnose_proxy_content()
    
    print(f"\n🎯 DIAGNOSIS COMPLETE")
    print(f"💡 This will help us understand how to properly extract proxy content")

if __name__ == "__main__":
    asyncio.run(main())
