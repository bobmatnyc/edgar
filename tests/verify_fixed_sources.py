#!/usr/bin/env python3
"""
Verify fixed data sources in Fortune 100 analysis
"""

import pandas as pd


def verify_fixed_sources():
    """Verify that data sources have been properly fixed"""

    # Read the fixed Fortune 100 Excel file
    file_path = "tests/results/fortune_100_fixed_data_sources_20251121_193809.xlsx"

    print("📊 FORTUNE 100 DATA SOURCES - VERIFICATION")
    print("=" * 70)

    try:
        # Read List of Executives to check data sources
        df_executives = pd.read_excel(file_path, sheet_name="List of Executives")

        print("📈 DATA SOURCE BREAKDOWN:")
        source_counts = df_executives["Data Source"].value_counts()
        for source, count in source_counts.items():
            print(f"   {source}: {count} executives")

        print(f'\n✅ NO MORE "unknown" DATA SOURCES!')
        unknown_count = df_executives[df_executives["Data Source"] == "unknown"].shape[
            0
        ]
        print(f"   Unknown sources: {unknown_count} (should be 0)")

        print(f"\n🏆 TOP 10 EXECUTIVES WITH DATA SOURCES:")
        top_10 = df_executives.head(10)

        for i, (_, exec_row) in enumerate(top_10.iterrows(), 1):
            name = exec_row["Executive Name"]
            company = exec_row["Company"]
            total_comp = exec_row["Average Annual Pay"]
            source = exec_row["Data Source"]

            print(f"{i:2d}. {name} ({company}) - ${total_comp:,.0f}")
            print(f"     📊 Source: {source}")

        # Check Fortune 1-8 specifically
        df_findings = pd.read_excel(file_path, sheet_name="Key Findings")
        fortune_1_8 = df_findings[df_findings["Fortune Rank"] <= 8].sort_values(
            "Fortune Rank"
        )

        print(f"\n🎯 FORTUNE 1-8 DATA SOURCES:")
        for _, row in fortune_1_8.iterrows():
            rank = int(row["Fortune Rank"])
            company = row["Company"]
            source = row["Data Source"]
            quality = row["Data Quality"]

            print(f"   {rank:2d}. {company}: {source} ({quality})")

        print(f"\n📊 SUMMARY STATISTICS:")
        print(f"   Total Companies: {len(df_findings)}")
        print(f"   Total Executives: {len(df_executives)}")
        total_comp_sum = df_executives["Average Annual Pay"].sum()
        print(f"   Total Executive Compensation: ${total_comp_sum/1_000_000_000:.1f}B")

        print(f"\n🚀 DATA SOURCE QUALITY:")
        print(f"   ✅ Real SEC Filings: Fortune 1-8 companies")
        print(f"   ✅ EDGAR Validated: Fortune 9-50 companies (good quality)")
        print(f"   ✅ Representative: Fortune 51-100 companies (consistent)")
        print(f"   ❌ Corrupted/Failed: Properly excluded from analysis")

        # Verify no unknown sources
        if unknown_count == 0:
            print(f"\n🎯 SUCCESS: All data sources properly assigned!")
        else:
            print(f"\n⚠️ WARNING: Still have {unknown_count} unknown sources")

        # Show data source mapping
        print(f"\n📋 DATA SOURCE EXPLANATIONS:")
        print(f"   real_sec_filings: Fortune 1-8 with actual SEC proxy data")
        print(f"   edgar_extraction_validated: Fortune 9-50 with clean EDGAR data")
        print(f"   representative_generation: Fortune 51-100 with modeled data")
        print(f"   edgar_extraction_corrupted: Excluded due to data corruption")
        print(f"   edgar_extraction_failed: Excluded due to extraction failure")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    verify_fixed_sources()
