"""Run SCT extraction and validate against ground truth."""

import json
from pathlib import Path

from edgar.extractors.sct import SCTExtractor

DATA_DIR = Path("/Users/masa/Projects/edgar/data/e2e_test")
OUTPUT_DIR = Path("/Users/masa/Projects/edgar/output/e2e_test")


def main() -> None:
    """Run extraction and compare to ground truth."""
    print("=== Phase 4: Extraction Execution ===\n")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Load data
    print("1. Loading input data...")
    html = (DATA_DIR / "apple_def14a_raw.html").read_text()

    with open(DATA_DIR / "apple_sct_ground_truth.json") as f:
        ground_truth = json.load(f)

    print(f"   HTML size: {len(html):,} bytes")
    print(f"   Expected executives: {len(ground_truth['executives'])}\n")

    # Step 2: Initialize extractor
    print("2. Initializing SCT Extractor...")
    extractor = SCTExtractor(company="Apple Inc.", cik="0000320193")
    print("   Extractor ready\n")

    # Step 3: Run extraction
    print("3. Running extraction...")
    try:
        result = extractor.extract({"html": html})
        print(f"   Extracted {len(result.executives)} executives\n")
    except Exception as e:
        print(f"   ❌ Extraction failed: {e}")
        return

    # Step 4: Save extracted data
    print("4. Saving extracted data...")
    output_path = OUTPUT_DIR / "apple_sct_extracted.json"
    with open(output_path, "w") as f:
        json.dump(result.model_dump(), f, indent=2)
    print(f"   Saved: {output_path}\n")

    # Step 5: Validate against ground truth
    print("5. Validating against ground truth...")
    accuracy = validate_extraction(result, ground_truth)

    # Step 6: Save validation report
    print("\n6. Saving validation report...")
    report = generate_report(result, ground_truth, accuracy)
    report_path = OUTPUT_DIR / "validation_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"   Saved: {report_path}")

    # Final status
    print("\n=== Phase 4 Complete ===")
    print(f"\nOverall Accuracy: {accuracy['overall']:.1%}")
    if accuracy["overall"] >= 0.95:
        print("✅ PASSED - Accuracy meets 95% threshold")
    else:
        print("⚠️  WARNING - Accuracy below 95% threshold")


def validate_extraction(result, ground_truth: dict) -> dict:
    """Validate extraction results against ground truth."""
    accuracy = {
        "executives_found": 0,
        "executives_expected": len(ground_truth["executives"]),
        "fields_correct": 0,
        "fields_total": 0,
        "compensation_accuracy": [],
        "overall": 0.0,
    }

    # Check executive count
    rules = ground_truth.get("validation_rules", {})
    min_execs = rules.get("min_executives", 5)

    print(f"   Executives: {len(result.executives)} (min: {min_execs})")
    if len(result.executives) >= min_execs:
        print("   ✅ Executive count meets minimum")
        accuracy["executives_found"] = len(result.executives)
    else:
        print("   ❌ Not enough executives found")

    # Check CEO
    ceo_name_pattern = rules.get("ceo_name_contains", "Cook")
    ceo = next((e for e in result.executives if ceo_name_pattern in e.name), None)

    if ceo:
        print(f"   ✅ CEO found: {ceo.name}")

        # Check CEO total compensation
        if ceo.compensation:
            ceo_total = ceo.compensation[0].total
            ceo_min = rules.get("ceo_total_min", 60000000)

            print(f"   CEO Total: ${ceo_total:,.0f} (min: ${ceo_min:,.0f})")
            if ceo_total >= ceo_min:
                print("   ✅ CEO compensation above threshold")
            else:
                print("   ⚠️  CEO compensation below threshold")
    else:
        print(f"   ❌ CEO not found (expected name containing '{ceo_name_pattern}')")

    # Compare each executive
    print("\n   Detailed comparison:")
    for gt_exec in ground_truth["executives"]:
        gt_name = gt_exec["name"]
        # Find matching executive in results
        match = None
        for result_exec in result.executives:
            if name_matches(result_exec.name, gt_name):
                match = result_exec
                break

        if match:
            # Compare compensation values
            if match.compensation and gt_exec.get("compensation"):
                gt_comp = gt_exec["compensation"][0]
                result_comp = match.compensation[0]

                fields_to_check = ["salary", "stock_awards", "non_equity_incentive", "total"]
                correct = 0
                for field in fields_to_check:
                    gt_val = gt_comp.get(field, 0)
                    result_val = getattr(result_comp, field, 0)

                    # Allow 2% tolerance (accounts for rounding in ground truth data)
                    if gt_val == 0:
                        if result_val == 0:
                            correct += 1
                    elif abs(result_val - gt_val) / gt_val < 0.02:
                        correct += 1

                    accuracy["fields_total"] += 1

                accuracy["fields_correct"] += correct
                acc = correct / len(fields_to_check)
                accuracy["compensation_accuracy"].append({"name": gt_name, "accuracy": acc})

                print(f"   {gt_name}: {acc:.0%} accurate")
        else:
            print(f"   {gt_name}: ❌ Not found in results")

    # Calculate overall accuracy
    if accuracy["fields_total"] > 0:
        accuracy["overall"] = accuracy["fields_correct"] / accuracy["fields_total"]

    return accuracy


def name_matches(name1: str, name2: str) -> bool:
    """Check if two names match (handles variations)."""
    import unicodedata

    # Normalize names (convert unicode apostrophes, etc)
    n1 = unicodedata.normalize("NFKD", name1.lower().strip())
    n2 = unicodedata.normalize("NFKD", name2.lower().strip())

    # Replace various apostrophe types with standard one
    # U+2018: LEFT SINGLE QUOTATION MARK
    # U+2019: RIGHT SINGLE QUOTATION MARK
    # U+0060: GRAVE ACCENT
    # U+00B4: ACUTE ACCENT
    for char in ["\u2018", "\u2019", "`", "\u00B4"]:
        n1 = n1.replace(char, "'")
        n2 = n2.replace(char, "'")

    # Check exact match
    if n1 == n2:
        return True

    # Check if one contains the other's last name
    parts1 = n1.split()
    parts2 = n2.split()

    if parts1 and parts2:
        last1 = parts1[-1]
        last2 = parts2[-1]
        if last1 == last2 or last1 in n2 or last2 in n1:
            return True

    return False


def generate_report(result, ground_truth: dict, accuracy: dict) -> dict:
    """Generate validation report."""
    return {
        "phase": "Phase 4: Extraction Execution",
        "status": "PASSED" if accuracy["overall"] >= 0.95 else "FAILED",
        "summary": {
            "executives_extracted": len(result.executives),
            "executives_expected": accuracy["executives_expected"],
            "overall_accuracy": accuracy["overall"],
            "threshold": 0.95,
        },
        "extracted_data": {
            "company": result.company,
            "cik": result.cik,
            "total_compensation": result.total_compensation,
            "executives": [
                {
                    "name": e.name,
                    "title": e.title,
                    "total_2024": e.compensation[0].total if e.compensation else 0,
                }
                for e in result.executives
            ],
        },
        "accuracy_details": accuracy,
        "validation_rules_used": ground_truth.get("validation_rules", {}),
    }


if __name__ == "__main__":
    main()
