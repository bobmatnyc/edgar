#!/usr/bin/env python3
"""
Test real XBRL executive compensation extraction
"""

import asyncio
import logging
import edgar
from edgar import Company

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_real_xbrl_extraction():
    """Test real XBRL executive compensation extraction"""
    
    print("🚀 TESTING REAL XBRL EXECUTIVE COMPENSATION EXTRACTION")
    print("=" * 70)
    
    edgar.set_identity("test.user@example.com")
    
    # Test with Apple
    company = Company("AAPL")
    print(f"📊 Extracting from {company.name}")
    
    # Get proxy filings
    proxy_filings = company.get_filings(form="DEF 14A")
    proxy_filing = proxy_filings[0]
    
    print(f"📄 Proxy: {proxy_filing.accession_number}")
    print(f"📅 Date: {proxy_filing.filing_date}")
    
    # Get XBRL object
    xbrl = proxy_filing.obj()
    
    print(f"\n🔍 XBRL EXECUTIVE COMPENSATION EXTRACTION")
    print("-" * 50)
    
    # Method 1: Search for compensation facts
    try:
        print("🔍 Method 1: Searching for compensation facts...")
        comp_facts = xbrl.facts.search_facts("compensation")
        print(f"   Found {len(comp_facts)} compensation facts")
        
        for fact in comp_facts[:5]:
            print(f"   • {fact.concept}: {fact.value}")
            
    except Exception as e:
        print(f"   ❌ Search facts failed: {e}")
    
    # Method 2: Get all facts as DataFrame
    try:
        print("\n🔍 Method 2: Converting to DataFrame...")
        facts_df = xbrl.facts.to_dataframe()
        print(f"   DataFrame shape: {facts_df.shape}")
        print(f"   Columns: {list(facts_df.columns)}")
        
        # Look for executive compensation concepts
        if 'concept' in facts_df.columns:
            comp_mask = facts_df['concept'].str.contains(
                'compensation|salary|bonus|stock|option|executive|officer|director', 
                case=False, na=False
            )
            comp_facts_df = facts_df[comp_mask]
            
            print(f"   🎯 Executive compensation facts: {len(comp_facts_df)}")
            
            if len(comp_facts_df) > 0:
                print(f"   📋 Compensation concepts found:")
                for concept in comp_facts_df['concept'].unique()[:10]:
                    print(f"      • {concept}")
                
                # Show sample values
                print(f"   💰 Sample compensation values:")
                for _, row in comp_facts_df.head(5).iterrows():
                    concept = row['concept']
                    value = row.get('value', 'N/A')
                    print(f"      • {concept}: {value}")
        
    except Exception as e:
        print(f"   ❌ DataFrame method failed: {e}")
    
    # Method 3: Get unique concepts to see what's available
    try:
        print("\n🔍 Method 3: Getting unique concepts...")
        unique_concepts = xbrl.facts.get_unique_concepts()
        print(f"   Total unique concepts: {len(unique_concepts)}")
        
        # Filter for executive compensation related concepts
        exec_concepts = [c for c in unique_concepts if any(
            keyword in c.lower() for keyword in 
            ['compensation', 'salary', 'bonus', 'stock', 'option', 'executive', 'officer', 'director']
        )]
        
        print(f"   🎯 Executive compensation concepts: {len(exec_concepts)}")
        for concept in exec_concepts[:15]:
            print(f"      • {concept}")
            
        # Get facts for each executive compensation concept
        if exec_concepts:
            print(f"\n💰 EXECUTIVE COMPENSATION DATA:")
            for concept in exec_concepts[:5]:  # Show first 5
                try:
                    concept_facts = xbrl.facts.get_facts_by_concept(concept)
                    print(f"   📊 {concept}: {len(concept_facts)} facts")
                    
                    for fact in concept_facts[:3]:  # Show first 3 facts
                        print(f"      • Value: {fact.value}")
                        if hasattr(fact, 'context'):
                            print(f"        Context: {fact.context}")
                        
                except Exception as e:
                    print(f"      ❌ Error getting facts for {concept}: {e}")
        
    except Exception as e:
        print(f"   ❌ Unique concepts method failed: {e}")
    
    # Method 4: Check statements for executive compensation
    try:
        print("\n🔍 Method 4: Checking XBRL statements...")
        
        # Check disclosures (likely to contain executive compensation)
        if hasattr(xbrl.statements, 'disclosures'):
            disclosures = xbrl.statements.disclosures()
            print(f"   📋 Disclosures found: {len(disclosures) if disclosures else 0}")
            
            if disclosures:
                for i, disclosure in enumerate(disclosures[:3]):
                    print(f"      Disclosure {i+1}: {disclosure}")
        
        # Check cover page
        if hasattr(xbrl.statements, 'cover_page'):
            cover_page = xbrl.statements.cover_page()
            print(f"   📄 Cover page: {cover_page is not None}")
            
            if cover_page is not None:
                print(f"      Cover page data available")
        
    except Exception as e:
        print(f"   ❌ Statements method failed: {e}")
    
    print(f"\n🎯 XBRL EXTRACTION ANALYSIS COMPLETE")
    print(f"💡 This shows us exactly what XBRL data is available for executive compensation")

async def main():
    """Main test function"""
    
    await test_real_xbrl_extraction()

if __name__ == "__main__":
    asyncio.run(main())
