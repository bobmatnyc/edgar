"""Example usage of TaxExtractor for extracting income tax data from 10-K filings."""

from edgar.extractors.tax import TaxData, TaxExtractor

# Example HTML from a 10-K filing
MOCK_10K_HTML = """
<html>
<body>
    <h2>Note 12 - Provision for Income Taxes</h2>

    <p>The components of income tax expense are as follows:</p>

    <table>
        <tr>
            <th>Year Ended December 31,</th>
            <th>2024</th>
            <th>2023</th>
            <th>2022</th>
        </tr>
        <tr>
            <td>Current:</td>
            <td></td>
            <td></td>
            <td></td>
        </tr>
        <tr>
            <td>  Federal</td>
            <td>$2,500,000</td>
            <td>$2,200,000</td>
            <td>$1,800,000</td>
        </tr>
        <tr>
            <td>  State</td>
            <td>$450,000</td>
            <td>$400,000</td>
            <td>$350,000</td>
        </tr>
        <tr>
            <td>  Foreign</td>
            <td>$750,000</td>
            <td>$680,000</td>
            <td>$620,000</td>
        </tr>
        <tr>
            <td>Total Current</td>
            <td>$3,700,000</td>
            <td>$3,280,000</td>
            <td>$2,770,000</td>
        </tr>
        <tr>
            <td>Deferred:</td>
            <td></td>
            <td></td>
            <td></td>
        </tr>
        <tr>
            <td>  Federal</td>
            <td>($250,000)</td>
            <td>$120,000</td>
            <td>$180,000</td>
        </tr>
        <tr>
            <td>  State</td>
            <td>($45,000)</td>
            <td>$25,000</td>
            <td>$35,000</td>
        </tr>
        <tr>
            <td>  Foreign</td>
            <td>$85,000</td>
            <td>($60,000)</td>
            <td>$70,000</td>
        </tr>
        <tr>
            <td>Total Deferred</td>
            <td>($210,000)</td>
            <td>$85,000</td>
            <td>$285,000</td>
        </tr>
        <tr>
            <td><b>Total Income Tax Expense</b></td>
            <td><b>$3,490,000</b></td>
            <td><b>$3,365,000</b></td>
            <td><b>$3,055,000</b></td>
        </tr>
    </table>

    <p>
        The Company's effective tax rate was 21.5% for 2024,
        22.0% for 2023, and 21.8% for 2022.
    </p>
</body>
</html>
"""


def main():
    """Demonstrate TaxExtractor usage."""
    # Create extractor instance
    extractor = TaxExtractor(company="Example Corp", cik="0001234567")

    # Extract tax data from HTML
    tax_data: TaxData = extractor.extract({"html": MOCK_10K_HTML})

    # Display results
    print(f"Company: {tax_data.company}")
    print(f"CIK: {tax_data.cik}")
    print(f"Number of years extracted: {len(tax_data.tax_years)}\n")

    # Display tax data for each year
    for tax_year in tax_data.tax_years:
        print(f"Year: {tax_year.year}")
        print(f"  Current Tax:")
        print(f"    Federal:  ${tax_year.current_federal:,.2f}")
        print(f"    State:    ${tax_year.current_state:,.2f}")
        print(f"    Foreign:  ${tax_year.current_foreign:,.2f}")
        print(f"    Total:    ${tax_year.total_current:,.2f}")
        print(f"  Deferred Tax:")
        print(f"    Federal:  ${tax_year.deferred_federal:,.2f}")
        print(f"    State:    ${tax_year.deferred_state:,.2f}")
        print(f"    Foreign:  ${tax_year.deferred_foreign:,.2f}")
        print(f"    Total:    ${tax_year.total_deferred:,.2f}")
        print(f"  Total Tax Expense: ${tax_year.total_tax_expense:,.2f}")
        if tax_year.effective_tax_rate > 0:
            print(f"  Effective Tax Rate: {tax_year.effective_tax_rate:.1%}")
        print()

    # Use convenience properties
    print(f"Latest Tax Expense: ${tax_data.latest_tax_expense:,.2f}")
    print(f"Latest Effective Rate: {tax_data.latest_effective_rate:.1%}")


if __name__ == "__main__":
    main()
