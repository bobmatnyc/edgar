#!/usr/bin/env python3
"""
Debug XBRL concepts to find the correct executive compensation field names
"""

import asyncio
import logging
import pandas as pd
import edgar
from edgar import Company

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_xbrl_concepts():
    """Debug XBRL concepts to find executive compensation fields"""
    
    print("🔍 DEBUGGING XBRL CONCEPTS FOR EXECUTIVE COMPENSATION")
    print("=" * 70)
    
    edgar.set_identity("test.user@example.com")
    
    # Test with Apple (we know it has XBRL data)
    company = Company("AAPL")
    print(f"📊 Debugging {company.name}")
    
    # Get proxy filing
    proxy_filings = company.get_filings(form="DEF 14A")
    proxy_filing = proxy_filings[0]
    
    print(f"📄 Proxy: {proxy_filing.accession_number}")
    
    # Get XBRL object
    xbrl = proxy_filing.obj()
    
    # Get all facts as DataFrame
    facts_df = xbrl.facts.to_dataframe()
    
    print(f"\n📊 XBRL Facts Analysis:")
    print(f"   Total facts: {len(facts_df)}")
    print(f"   Columns: {list(facts_df.columns)}")
    
    # Show all unique concepts
    print(f"\n📋 ALL XBRL CONCEPTS:")
    unique_concepts = facts_df['concept'].unique()
    for i, concept in enumerate(unique_concepts, 1):
        print(f"   {i:2d}. {concept}")
    
    # Look for executive compensation related concepts
    print(f"\n🎯 EXECUTIVE COMPENSATION RELATED CONCEPTS:")
    exec_concepts = []
    for concept in unique_concepts:
        concept_lower = concept.lower()
        if any(keyword in concept_lower for keyword in [
            'compensation', 'salary', 'bonus', 'stock', 'option', 'executive', 
            'officer', 'director', 'peo', 'neo', 'pay', 'award'
        ]):
            exec_concepts.append(concept)
    
    if exec_concepts:
        for i, concept in enumerate(exec_concepts, 1):
            print(f"   {i:2d}. {concept}")
            
            # Show sample values for this concept
            concept_facts = facts_df[facts_df['concept'] == concept]
            if len(concept_facts) > 0:
                sample_fact = concept_facts.iloc[0]
                value = sample_fact['value']
                
                # Show truncated value if it's very long
                if isinstance(value, str) and len(value) > 200:
                    print(f"       Value: {value[:200]}...")
                else:
                    print(f"       Value: {value}")
                
                # Show dimensions if available
                for col in concept_facts.columns:
                    if col.startswith('dim_') and pd.notna(sample_fact[col]):
                        print(f"       {col}: {sample_fact[col]}")
    else:
        print("   ❌ No executive compensation concepts found")
    
    # Check for specific patterns we expect
    print(f"\n🔍 SEARCHING FOR SPECIFIC PATTERNS:")
    
    patterns = [
        'PEO',
        'NEO', 
        'TotalCompensation',
        'ActuallyPaid',
        'Average',
        'Amount'
    ]
    
    for pattern in patterns:
        matching_concepts = [c for c in unique_concepts if pattern in c]
        if matching_concepts:
            print(f"   📊 Concepts containing '{pattern}':")
            for concept in matching_concepts:
                print(f"      • {concept}")
        else:
            print(f"   ❌ No concepts found containing '{pattern}'")
    
    # Show facts with numeric values (likely compensation amounts)
    print(f"\n💰 NUMERIC FACTS (Likely Compensation):")
    numeric_facts = facts_df[facts_df['numeric_value'].notna()]
    
    if len(numeric_facts) > 0:
        print(f"   Found {len(numeric_facts)} numeric facts")
        
        # Sort by numeric value descending to find large compensation amounts
        numeric_facts_sorted = numeric_facts.sort_values('numeric_value', ascending=False)
        
        print(f"   📊 Top 10 largest numeric values:")
        for i, (_, fact) in enumerate(numeric_facts_sorted.head(10).iterrows(), 1):
            concept = fact['concept']
            value = fact['numeric_value']
            print(f"      {i:2d}. {concept}: ${value:,.0f}")
    
    # Check dimensions for executive identification
    print(f"\n👥 EXECUTIVE IDENTIFICATION DIMENSIONS:")
    dimension_cols = [col for col in facts_df.columns if col.startswith('dim_')]
    
    for dim_col in dimension_cols:
        unique_dims = facts_df[dim_col].dropna().unique()
        if len(unique_dims) > 0:
            print(f"   📊 {dim_col}:")
            for dim_val in unique_dims[:10]:  # Show first 10
                print(f"      • {dim_val}")

async def main():
    """Main debug function"""
    
    await debug_xbrl_concepts()
    
    print(f"\n🎯 DEBUG COMPLETE")
    print(f"💡 This will show us the exact XBRL concept names to use")

if __name__ == "__main__":
    asyncio.run(main())
