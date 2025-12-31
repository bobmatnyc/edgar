#!/usr/bin/env python3
"""
Generate Excel spreadsheet report from EDGAR CLI results
"""

import json
import pandas as pd
from datetime import datetime
import os


def create_executive_compensation_report():
    """Create comprehensive Excel report from JSON results"""

    # Load the results
    results_file = "results/top_100_enhanced_results_20251121_180216.json"

    if not os.path.exists(results_file):
        print(f"❌ Results file not found: {results_file}")
        return

    with open(results_file, "r") as f:
        data = json.load(f)

    print(f"📊 Processing {data['total_companies']} companies...")

    # Create summary data
    summary_data = []
    executive_data = []

    for company in data["companies"]:
        if company["success"] and company["executives"]:
            # Company summary
            total_exec_comp = sum(
                exec["total_compensation"] for exec in company["executives"]
            )
            avg_exec_comp = total_exec_comp / len(company["executives"])

            summary_data.append(
                {
                    "Rank": company["rank"],
                    "Company": company["name"],
                    "CIK": company["cik"],
                    "Success": "Yes",
                    "Executives_Found": len(company["executives"]),
                    "Total_Executive_Compensation": total_exec_comp,
                    "Average_Executive_Compensation": avg_exec_comp,
                    "Highest_Paid_Executive": max(
                        company["executives"], key=lambda x: x["total_compensation"]
                    )["name"],
                    "Highest_Compensation": max(
                        exec["total_compensation"] for exec in company["executives"]
                    ),
                }
            )

            # Individual executive data
            for exec in company["executives"]:
                executive_data.append(
                    {
                        "Company_Rank": company["rank"],
                        "Company_Name": company["name"],
                        "CIK": company["cik"],
                        "Executive_Name": exec["name"],
                        "Title": exec["title"],
                        "Total_Compensation": exec["total_compensation"],
                        "Salary": exec["salary"],
                        "Bonus": exec["bonus"],
                        "Stock_Awards": exec["stock_awards"],
                        "Option_Awards": exec["option_awards"],
                    }
                )
        else:
            # Failed extraction
            summary_data.append(
                {
                    "Rank": company["rank"],
                    "Company": company["name"],
                    "CIK": company["cik"],
                    "Success": "No",
                    "Executives_Found": 0,
                    "Total_Executive_Compensation": 0,
                    "Average_Executive_Compensation": 0,
                    "Highest_Paid_Executive": "N/A",
                    "Highest_Compensation": 0,
                }
            )

    # Create DataFrames
    summary_df = pd.DataFrame(summary_data)
    executive_df = pd.DataFrame(executive_data)

    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"tests/results/executive_compensation_report_{timestamp}.xlsx"

    # Create Excel file with multiple sheets
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        # Summary sheet
        summary_df.to_excel(writer, sheet_name="Company_Summary", index=False)

        # Executive details sheet
        executive_df.to_excel(writer, sheet_name="Executive_Details", index=False)

        # Statistics sheet
        stats_data = {
            "Metric": [
                "Total Companies Processed",
                "Successful Extractions",
                "Failed Extractions",
                "Success Rate (%)",
                "Total Executives Found",
                "Average Executives per Company",
                "Highest Individual Compensation",
                "Average Individual Compensation",
                "Total Compensation (All Executives)",
            ],
            "Value": [
                data["total_companies"],
                data["successful_extractions"],
                data["failed_extractions"],
                f"{(data['successful_extractions'] / data['total_companies'] * 100):.1f}%",
                len(executive_df),
                f"{len(executive_df) / data['successful_extractions']:.1f}"
                if data["successful_extractions"] > 0
                else 0,
                f"${executive_df['Total_Compensation'].max():,.0f}"
                if not executive_df.empty
                else "$0",
                f"${executive_df['Total_Compensation'].mean():,.0f}"
                if not executive_df.empty
                else "$0",
                f"${executive_df['Total_Compensation'].sum():,.0f}"
                if not executive_df.empty
                else "$0",
            ],
        }
        stats_df = pd.DataFrame(stats_data)
        stats_df.to_excel(writer, sheet_name="Statistics", index=False)

    print(f"✅ Excel report created: {output_file}")
    print("📊 Report contains:")
    print(f"   • Company Summary: {len(summary_df)} companies")
    print(f"   • Executive Details: {len(executive_df)} executives")
    print("   • Statistics and metrics")

    return output_file


if __name__ == "__main__":
    create_executive_compensation_report()
