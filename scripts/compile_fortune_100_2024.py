#!/usr/bin/env python3
"""
Compile Fortune 100 2024 list with CIK numbers and fiscal year end data.
Based on Fortune 500 2024 rankings and SEC EDGAR data.
"""

import json
from datetime import datetime
from pathlib import Path


# Fortune 100 companies for 2024 (from Fortune.com search results)
FORTUNE_100_2024 = [
    # Top 10
    {"rank": 1, "name": "Walmart", "ticker": "WMT", "cik": "0000104169", "fye_month": 1, "sector": "Retail"},
    {"rank": 2, "name": "Amazon.com", "ticker": "AMZN", "cik": "0001018724", "fye_month": 12, "sector": "E-commerce/Technology"},
    {"rank": 3, "name": "Apple", "ticker": "AAPL", "cik": "0000320193", "fye_month": 9, "sector": "Technology"},
    {"rank": 4, "name": "UnitedHealth Group", "ticker": "UNH", "cik": "0000731766", "fye_month": 12, "sector": "Healthcare"},
    {"rank": 5, "name": "Berkshire Hathaway", "ticker": "BRK.A", "cik": "0001067983", "fye_month": 12, "sector": "Conglomerate"},
    {"rank": 6, "name": "CVS Health", "ticker": "CVS", "cik": "0000064803", "fye_month": 12, "sector": "Healthcare"},
    {"rank": 7, "name": "Exxon Mobil", "ticker": "XOM", "cik": "0000034088", "fye_month": 12, "sector": "Energy"},
    {"rank": 8, "name": "Alphabet", "ticker": "GOOGL", "cik": "0001652044", "fye_month": 12, "sector": "Technology"},
    {"rank": 9, "name": "McKesson", "ticker": "MCK", "cik": "0000927653", "fye_month": 3, "sector": "Healthcare Distribution"},
    {"rank": 10, "name": "Cencora", "ticker": "COR", "cik": "0001140859", "fye_month": 9, "sector": "Healthcare Distribution"},

    # 11-20
    {"rank": 11, "name": "Costco Wholesale", "ticker": "COST", "cik": "0000909832", "fye_month": 8, "sector": "Retail"},
    {"rank": 12, "name": "Microsoft", "ticker": "MSFT", "cik": "0000789019", "fye_month": 6, "sector": "Technology"},
    {"rank": 13, "name": "Chevron", "ticker": "CVX", "cik": "0000093410", "fye_month": 12, "sector": "Energy"},
    {"rank": 14, "name": "Cardinal Health", "ticker": "CAH", "cik": "0000721371", "fye_month": 6, "sector": "Healthcare Distribution"},
    {"rank": 15, "name": "Citigroup", "ticker": "C", "cik": "0000831001", "fye_month": 12, "sector": "Financial Services"},
    {"rank": 16, "name": "Phillips 66", "ticker": "PSX", "cik": "0001534701", "fye_month": 12, "sector": "Energy"},
    {"rank": 17, "name": "Marathon Petroleum", "ticker": "MPC", "cik": "0001510295", "fye_month": 12, "sector": "Energy"},
    {"rank": 18, "name": "Centene", "ticker": "CNC", "cik": "0001071739", "fye_month": 12, "sector": "Healthcare"},
    {"rank": 19, "name": "Ford Motor", "ticker": "F", "cik": "0000037996", "fye_month": 12, "sector": "Automotive"},
    {"rank": 20, "name": "Fannie Mae", "ticker": "FNMA", "cik": "0000310522", "fye_month": 12, "sector": "Financial Services"},

    # 21-30
    {"rank": 21, "name": "Home Depot", "ticker": "HD", "cik": "0000354950", "fye_month": 1, "sector": "Retail"},
    {"rank": 22, "name": "JPMorgan Chase", "ticker": "JPM", "cik": "0000019617", "fye_month": 12, "sector": "Financial Services"},
    {"rank": 23, "name": "Bank of America", "ticker": "BAC", "cik": "0000070858", "fye_month": 12, "sector": "Financial Services"},
    {"rank": 24, "name": "Elevance Health", "ticker": "ELV", "cik": "0001156039", "fye_month": 12, "sector": "Healthcare"},
    {"rank": 25, "name": "Valero Energy", "ticker": "VLO", "cik": "0001035002", "fye_month": 12, "sector": "Energy"},
    {"rank": 26, "name": "Kroger", "ticker": "KR", "cik": "0000056873", "fye_month": 1, "sector": "Retail"},
    {"rank": 27, "name": "General Motors", "ticker": "GM", "cik": "0001467858", "fye_month": 12, "sector": "Automotive"},
    {"rank": 28, "name": "Walgreens Boots Alliance", "ticker": "WBA", "cik": "0001618921", "fye_month": 8, "sector": "Healthcare"},
    {"rank": 29, "name": "Freddie Mac", "ticker": "FMCC", "cik": "0001026214", "fye_month": 12, "sector": "Financial Services"},
    {"rank": 30, "name": "Verizon Communications", "ticker": "VZ", "cik": "0000732712", "fye_month": 12, "sector": "Telecommunications"},

    # 31-40
    {"rank": 31, "name": "Meta Platforms", "ticker": "META", "cik": "0001326801", "fye_month": 12, "sector": "Technology"},
    {"rank": 32, "name": "Comcast", "ticker": "CMCSA", "cik": "0001166691", "fye_month": 12, "sector": "Telecommunications/Media"},
    {"rank": 33, "name": "AT&T", "ticker": "T", "cik": "0000732717", "fye_month": 12, "sector": "Telecommunications"},
    {"rank": 34, "name": "Tesla", "ticker": "TSLA", "cik": "0001318605", "fye_month": 12, "sector": "Automotive/Technology"},
    {"rank": 35, "name": "Target", "ticker": "TGT", "cik": "0000027419", "fye_month": 1, "sector": "Retail"},
    {"rank": 36, "name": "Wells Fargo", "ticker": "WFC", "cik": "0000072971", "fye_month": 12, "sector": "Financial Services"},
    {"rank": 37, "name": "Goldman Sachs Group", "ticker": "GS", "cik": "0000886982", "fye_month": 12, "sector": "Financial Services"},
    {"rank": 38, "name": "Humana", "ticker": "HUM", "cik": "0000049071", "fye_month": 12, "sector": "Healthcare"},
    {"rank": 39, "name": "State Farm Insurance Cos.", "ticker": "N/A", "cik": "", "fye_month": 12, "sector": "Insurance"},
    {"rank": 40, "name": "Morgan Stanley", "ticker": "MS", "cik": "0000895421", "fye_month": 12, "sector": "Financial Services"},

    # 41-50
    {"rank": 41, "name": "Johnson & Johnson", "ticker": "JNJ", "cik": "0000200406", "fye_month": 12, "sector": "Healthcare"},
    {"rank": 42, "name": "Walt Disney", "ticker": "DIS", "cik": "0001744489", "fye_month": 9, "sector": "Entertainment/Media"},
    {"rank": 43, "name": "Dell Technologies", "ticker": "DELL", "cik": "0001571996", "fye_month": 1, "sector": "Technology"},
    {"rank": 44, "name": "United Parcel Service", "ticker": "UPS", "cik": "0001090727", "fye_month": 12, "sector": "Logistics"},
    {"rank": 45, "name": "PepsiCo", "ticker": "PEP", "cik": "0000077476", "fye_month": 12, "sector": "Consumer Goods"},
    {"rank": 46, "name": "FedEx", "ticker": "FDX", "cik": "0001048911", "fye_month": 5, "sector": "Logistics"},
    {"rank": 47, "name": "StoneX Group", "ticker": "SNEX", "cik": "0001023844", "fye_month": 9, "sector": "Financial Services"},
    {"rank": 48, "name": "Archer-Daniels-Midland", "ticker": "ADM", "cik": "0000007084", "fye_month": 12, "sector": "Agriculture/Food"},
    {"rank": 49, "name": "Dow", "ticker": "DOW", "cik": "0001751788", "fye_month": 12, "sector": "Chemicals"},
    {"rank": 50, "name": "Albertsons Cos.", "ticker": "ACI", "cik": "0001646972", "fye_month": 2, "sector": "Retail"},

    # 51-60
    {"rank": 51, "name": "Archer Daniels Midland", "ticker": "ADM", "cik": "0000007084", "fye_month": 12, "sector": "Agriculture/Food"},
    {"rank": 52, "name": "Procter & Gamble", "ticker": "PG", "cik": "0000080424", "fye_month": 6, "sector": "Consumer Goods"},
    {"rank": 53, "name": "Lowe's", "ticker": "LOW", "cik": "0000060667", "fye_month": 1, "sector": "Retail"},
    {"rank": 54, "name": "Energy Transfer", "ticker": "ET", "cik": "0001276187", "fye_month": 12, "sector": "Energy"},
    {"rank": 55, "name": "RTX", "ticker": "RTX", "cik": "0000101829", "fye_month": 12, "sector": "Aerospace/Defense"},
    {"rank": 56, "name": "Albertsons", "ticker": "ACI", "cik": "0001646972", "fye_month": 2, "sector": "Retail"},
    {"rank": 57, "name": "Sysco", "ticker": "SYY", "cik": "0000096021", "fye_month": 6, "sector": "Food Distribution"},
    {"rank": 58, "name": "Progressive", "ticker": "PGR", "cik": "0000080661", "fye_month": 12, "sector": "Insurance"},
    {"rank": 59, "name": "American Express", "ticker": "AXP", "cik": "0000004962", "fye_month": 12, "sector": "Financial Services"},
    {"rank": 60, "name": "Lockheed Martin", "ticker": "LMT", "cik": "0000936468", "fye_month": 12, "sector": "Aerospace/Defense"},

    # 61-70
    {"rank": 61, "name": "MetLife", "ticker": "MET", "cik": "0001099219", "fye_month": 12, "sector": "Insurance"},
    {"rank": 62, "name": "HCA Healthcare", "ticker": "HCA", "cik": "0000860730", "fye_month": 12, "sector": "Healthcare"},
    {"rank": 63, "name": "Prudential Financial", "ticker": "PRU", "cik": "0001137774", "fye_month": 12, "sector": "Financial Services"},
    {"rank": 64, "name": "Boeing", "ticker": "BA", "cik": "0000012927", "fye_month": 12, "sector": "Aerospace/Defense"},
    {"rank": 65, "name": "Caterpillar", "ticker": "CAT", "cik": "0000018230", "fye_month": 12, "sector": "Industrial"},
    {"rank": 66, "name": "Merck", "ticker": "MRK", "cik": "0000310158", "fye_month": 12, "sector": "Healthcare/Pharmaceuticals"},
    {"rank": 67, "name": "Allstate", "ticker": "ALL", "cik": "0000899051", "fye_month": 12, "sector": "Insurance"},
    {"rank": 68, "name": "Pfizer", "ticker": "PFE", "cik": "0000078003", "fye_month": 12, "sector": "Healthcare/Pharmaceuticals"},
    {"rank": 69, "name": "IBM", "ticker": "IBM", "cik": "0000051143", "fye_month": 12, "sector": "Technology"},
    {"rank": 70, "name": "New York Life Insurance", "ticker": "N/A", "cik": "", "fye_month": 12, "sector": "Insurance"},

    # 71-80
    {"rank": 71, "name": "Delta Air Lines", "ticker": "DAL", "cik": "0000027904", "fye_month": 12, "sector": "Airline"},
    {"rank": 72, "name": "Publix Super Markets", "ticker": "N/A", "cik": "", "fye_month": 12, "sector": "Retail"},
    {"rank": 73, "name": "Nationwide", "ticker": "N/A", "cik": "", "fye_month": 12, "sector": "Insurance"},
    {"rank": 74, "name": "TD Synnex", "ticker": "SNX", "cik": "0001754378", "fye_month": 11, "sector": "Technology Distribution"},
    {"rank": 75, "name": "United Airlines Holdings", "ticker": "UAL", "cik": "0000100517", "fye_month": 12, "sector": "Airline"},
    {"rank": 76, "name": "ConocoPhillips", "ticker": "COP", "cik": "0001163165", "fye_month": 12, "sector": "Energy"},
    {"rank": 77, "name": "TJX", "ticker": "TJX", "cik": "0000109198", "fye_month": 1, "sector": "Retail"},
    {"rank": 78, "name": "AbbVie", "ticker": "ABBV", "cik": "0001551152", "fye_month": 12, "sector": "Healthcare/Pharmaceuticals"},
    {"rank": 79, "name": "Enterprise Products Partners", "ticker": "EPD", "cik": "0001061219", "fye_month": 12, "sector": "Energy"},
    {"rank": 80, "name": "Charter Communications", "ticker": "CHTR", "cik": "0001091667", "fye_month": 12, "sector": "Telecommunications"},

    # 81-90
    {"rank": 81, "name": "Performance Food Group", "ticker": "PFGC", "cik": "0001625941", "fye_month": 6, "sector": "Food Distribution"},
    {"rank": 82, "name": "American Airlines Group", "ticker": "AAL", "cik": "0000006201", "fye_month": 12, "sector": "Airline"},
    {"rank": 83, "name": "Capital One Financial", "ticker": "COF", "cik": "0000927628", "fye_month": 12, "sector": "Financial Services"},
    {"rank": 84, "name": "Cisco Systems", "ticker": "CSCO", "cik": "0000858877", "fye_month": 7, "sector": "Technology"},
    {"rank": 85, "name": "HP", "ticker": "HPQ", "cik": "0000047217", "fye_month": 10, "sector": "Technology"},
    {"rank": 86, "name": "Tyson Foods", "ticker": "TSN", "cik": "0000100493", "fye_month": 9, "sector": "Food Processing"},
    {"rank": 87, "name": "Intel", "ticker": "INTC", "cik": "0000050863", "fye_month": 12, "sector": "Technology"},
    {"rank": 88, "name": "Oracle", "ticker": "ORCL", "cik": "0001341439", "fye_month": 5, "sector": "Technology"},
    {"rank": 89, "name": "Broadcom", "ticker": "AVGO", "cik": "0001730168", "fye_month": 10, "sector": "Technology"},
    {"rank": 90, "name": "Deere", "ticker": "DE", "cik": "0000315189", "fye_month": 10, "sector": "Industrial"},

    # 91-100
    {"rank": 91, "name": "Nike", "ticker": "NKE", "cik": "0000320187", "fye_month": 5, "sector": "Consumer Goods"},
    {"rank": 92, "name": "Liberty Mutual Insurance Group", "ticker": "N/A", "cik": "", "fye_month": 12, "sector": "Insurance"},
    {"rank": 93, "name": "Plains GP Holdings", "ticker": "PAGP", "cik": "0001534504", "fye_month": 12, "sector": "Energy"},
    {"rank": 94, "name": "USAA", "ticker": "N/A", "cik": "", "fye_month": 12, "sector": "Financial Services"},
    {"rank": 95, "name": "Bristol-Myers Squibb", "ticker": "BMY", "cik": "0000014272", "fye_month": 12, "sector": "Healthcare/Pharmaceuticals"},
    {"rank": 96, "name": "Ingram Micro Holding", "ticker": "N/A", "cik": "", "fye_month": 12, "sector": "Technology Distribution"},
    {"rank": 97, "name": "General Dynamics", "ticker": "GD", "cik": "0000040533", "fye_month": 12, "sector": "Aerospace/Defense"},
    {"rank": 98, "name": "Coca-Cola", "ticker": "KO", "cik": "0000021344", "fye_month": 12, "sector": "Consumer Goods"},
    {"rank": 99, "name": "TIAA", "ticker": "N/A", "cik": "", "fye_month": 12, "sector": "Financial Services"},
    {"rank": 100, "name": "Travelers", "ticker": "TRV", "cik": "0000086312", "fye_month": 12, "sector": "Insurance"},
]


def compile_fortune_100_json():
    """Compile Fortune 100 2024 data into JSON format."""

    output_data = {
        "metadata": {
            "source": "Fortune 500 2024 (fortune.com)",
            "compiled_date": datetime.now().strftime("%Y-%m-%d"),
            "total_companies": len(FORTUNE_100_2024),
            "notes": [
                "CIK numbers are 10-digit zero-padded format as required by SEC EDGAR",
                "Fiscal year end month (1-12): 1=Jan, 2=Feb, ..., 12=Dec",
                "Private companies (State Farm, New York Life, Publix, etc.) may not have CIKs",
                "Data compiled from Fortune.com 2024 rankings and SEC EDGAR database"
            ]
        },
        "companies": []
    }

    # Count companies with missing CIKs
    missing_ciks = []
    non_calendar_fye = []

    for company in FORTUNE_100_2024:
        company_data = {
            "rank": company["rank"],
            "name": company["name"],
            "ticker": company["ticker"] if company["ticker"] != "N/A" else None,
            "cik": company["cik"] if company["cik"] else None,
            "fiscal_year_end_month": company["fye_month"],
            "sector": company["sector"]
        }

        output_data["companies"].append(company_data)

        # Track missing CIKs
        if not company["cik"]:
            missing_ciks.append(f"#{company['rank']}: {company['name']}")

        # Track non-calendar year companies
        if company["fye_month"] != 12:
            non_calendar_fye.append(
                f"#{company['rank']}: {company['name']} (FYE: Month {company['fye_month']})"
            )

    # Add metadata about completeness
    output_data["metadata"]["companies_with_ciks"] = len(FORTUNE_100_2024) - len(missing_ciks)
    output_data["metadata"]["companies_missing_ciks"] = len(missing_ciks)
    output_data["metadata"]["non_calendar_fiscal_year_companies"] = len(non_calendar_fye)

    return output_data, missing_ciks, non_calendar_fye


def main():
    """Main function to compile and save Fortune 100 data."""
    print("Compiling Fortune 100 2024 data...")

    data, missing_ciks, non_calendar_fye = compile_fortune_100_json()

    # Save to JSON file
    output_path = Path("/Users/masa/Clients/Zach/projects/edgar/data/companies/fortune_100_2024.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\n✓ Saved Fortune 100 2024 data to: {output_path}")
    print(f"\nSummary:")
    print(f"  Total companies: {data['metadata']['total_companies']}")
    print(f"  Companies with CIKs: {data['metadata']['companies_with_ciks']}")
    print(f"  Companies missing CIKs: {data['metadata']['companies_missing_ciks']}")
    print(f"  Non-calendar fiscal year: {data['metadata']['non_calendar_fiscal_year_companies']}")

    if missing_ciks:
        print(f"\nCompanies missing CIKs (likely private):")
        for company in missing_ciks:
            print(f"  - {company}")

    if non_calendar_fye:
        print(f"\nNon-calendar fiscal year companies:")
        for company in non_calendar_fye[:10]:  # Show first 10
            print(f"  - {company}")
        if len(non_calendar_fye) > 10:
            print(f"  ... and {len(non_calendar_fye) - 10} more")


if __name__ == "__main__":
    main()
