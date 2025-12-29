#!/usr/bin/env python3
"""Example: Self-refinement workflow for EDGAR extractors.

This example demonstrates:
1. Creating extraction failure records
2. Analyzing failures to find alternative patterns
3. Generating refinement suggestions
4. Reviewing suggestions for manual application
"""

import asyncio

from edgar.data.fortune100 import Company
from edgar.refinement import ExtractionFailure, ExtractorRefiner
from edgar.services.sec_edgar_client import SecEdgarClient


async def example_sct_refinement():
    """Example: Analyze SCT extraction failure and suggest improvements."""
    print("=" * 60)
    print("Example: SCT Extractor Self-Refinement")
    print("=" * 60)

    # Create sample company
    company = Company(
        rank=1,
        name="Example Corp",
        ticker="EXMP",
        cik="0000000001",
        sector="Technology",
    )

    # Simulate HTML from a filing with non-standard header
    html_sample = """
    <html>
    <body>
        <h2>Named Executive Officer Compensation</h2>
        <p>The following table presents compensation for our NEOs.</p>
        <table>
            <tr>
                <th>Name and Principal Position</th>
                <th>Fiscal Year</th>
                <th>Base Salary</th>
                <th>Stock Awards</th>
                <th>Non-Equity Incentive</th>
                <th>All Other Compensation</th>
                <th>Total</th>
            </tr>
            <tr>
                <td>Jane Doe<br/>Chief Executive Officer</td>
                <td>2024</td>
                <td>$800,000</td>
                <td>$2,500,000</td>
                <td>$1,200,000</td>
                <td>$50,000</td>
                <td>$4,550,000</td>
            </tr>
            <tr>
                <td>John Smith<br/>Chief Financial Officer</td>
                <td>2024</td>
                <td>$600,000</td>
                <td>$1,500,000</td>
                <td>$800,000</td>
                <td>$40,000</td>
                <td>$2,940,000</td>
            </tr>
        </table>
    </body>
    </html>
    """

    # Create extraction failure record
    failure = ExtractionFailure(
        company=company,
        form_type="DEF 14A",
        html_sample=html_sample,
        error_message="Summary Compensation Table not found",
        extractor_type="SCTExtractor",
        filing_url="https://www.sec.gov/example",
    )

    # Initialize refiner
    sec_client = SecEdgarClient()
    refiner = ExtractorRefiner(sec_client=sec_client, min_confidence=0.7)

    # Analyze failure
    print("\n1. Analyzing extraction failure...")
    suggestions = await refiner.analyze_failures([failure])

    print(f"   ✅ Generated {len(suggestions)} suggestions\n")

    # Display suggestions
    print("2. Refinement Suggestions:")
    print("-" * 60)

    for i, suggestion in enumerate(suggestions, 1):
        print(f"\nSuggestion #{i}:")
        print(f"  Pattern Type: {suggestion.pattern_type}")
        print(f"  Confidence:   {suggestion.confidence:.2%}")
        print(f"  Current:      {suggestion.current_pattern}")
        print(f"  Suggested:    {suggestion.suggested_pattern[:80]}")
        print(f"  Reasoning:    {suggestion.reasoning[:150]}...")

    # Generate report
    print("\n" + "=" * 60)
    print("3. Full Refinement Report:")
    print("=" * 60)
    report = refiner.generate_refinement_report(suggestions)
    print(report)

    return suggestions


async def example_tax_refinement():
    """Example: Analyze tax extraction failure and suggest improvements."""
    print("\n" + "=" * 60)
    print("Example: Tax Extractor Self-Refinement")
    print("=" * 60)

    # Create sample company
    company = Company(
        rank=2,
        name="Tax Example Inc.",
        ticker="TAXE",
        cik="0000000002",
        sector="Financial Services",
    )

    # Simulate HTML with alternative section headers
    html_sample = """
    <html>
    <body>
        <h3>Income Tax Expense</h3>
        <table>
            <tr>
                <td></td>
                <th>2024</th>
                <th>2023</th>
                <th>2022</th>
            </tr>
            <tr>
                <td colspan="4"><b>Current Tax Expense</b></td>
            </tr>
            <tr>
                <td>Federal</td>
                <td>$1,200</td>
                <td>$1,000</td>
                <td>$900</td>
            </tr>
            <tr>
                <td>State and Local</td>
                <td>$300</td>
                <td>$250</td>
                <td>$200</td>
            </tr>
            <tr>
                <td>International</td>
                <td>$500</td>
                <td>$450</td>
                <td>$400</td>
            </tr>
            <tr>
                <td colspan="4"><b>Deferred Tax Benefit</b></td>
            </tr>
            <tr>
                <td>Federal</td>
                <td>($200)</td>
                <td>($150)</td>
                <td>($100)</td>
            </tr>
            <tr>
                <td>State and Local</td>
                <td>($50)</td>
                <td>($30)</td>
                <td>($20)</td>
            </tr>
        </table>
    </body>
    </html>
    """

    # Create extraction failure
    failure = ExtractionFailure(
        company=company,
        form_type="10-K",
        html_sample=html_sample,
        error_message="Tax expense is $0",
        extractor_type="TaxExtractor",
        filing_url="https://www.sec.gov/example2",
    )

    # Initialize refiner
    sec_client = SecEdgarClient()
    refiner = ExtractorRefiner(sec_client=sec_client, min_confidence=0.7)

    # Analyze failure
    print("\n1. Analyzing tax extraction failure...")
    suggestions = await refiner.analyze_failures([failure])

    print(f"   ✅ Generated {len(suggestions)} suggestions\n")

    # Display suggestions
    print("2. Refinement Suggestions:")
    print("-" * 60)

    for i, suggestion in enumerate(suggestions, 1):
        print(f"\nSuggestion #{i}:")
        print(f"  Pattern Type: {suggestion.pattern_type}")
        print(f"  Confidence:   {suggestion.confidence:.2%}")
        print(f"  Reasoning:    {suggestion.reasoning[:200]}...")

    return suggestions


async def main():
    """Run refinement examples."""
    print("\n" + "=" * 60)
    print("EDGAR Self-Refinement Module Examples")
    print("=" * 60)

    # Example 1: SCT refinement
    sct_suggestions = await example_sct_refinement()

    # Example 2: Tax refinement
    tax_suggestions = await example_tax_refinement()

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"\nTotal Suggestions: {len(sct_suggestions) + len(tax_suggestions)}")
    print(f"  - SCT:  {len(sct_suggestions)}")
    print(f"  - Tax:  {len(tax_suggestions)}")

    print("\nNext Steps:")
    print("1. Review suggestions for high-confidence patterns")
    print("2. Manually add suggested patterns to extractors")
    print("3. Re-run extractions to verify improvements")
    print("4. Iterate as needed")

    print("\nFor real-world usage, run:")
    print("  python scripts/refine_extractors.py")


if __name__ == "__main__":
    asyncio.run(main())
