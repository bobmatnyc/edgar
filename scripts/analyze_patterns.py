"""Analyze transformation patterns from extracted SCT data."""

import json
from pathlib import Path

from edgar.services.pattern_analyzer import PatternAnalyzer

DATA_DIR = Path("/Users/masa/Projects/edgar/data/e2e_test")


def main() -> None:
    """Run pattern analysis on extracted SCT data."""
    print("=== Phase 2: Pattern Analysis ===\n")

    # Load data from Phase 1
    print("1. Loading Phase 1 data...")
    raw_html = (DATA_DIR / "apple_def14a_raw.html").read_text()

    with open(DATA_DIR / "apple_sct_extracted.json") as f:
        extracted = json.load(f)

    with open(DATA_DIR / "apple_sct_ground_truth.json") as f:
        ground_truth = json.load(f)

    print(f"   Raw HTML: {len(raw_html):,} bytes")
    print(f"   Extracted: {len(extracted.get('executives', []))} executives")
    print(f"   Ground truth: {len(ground_truth.get('executives', []))} executives\n")

    # Run pattern analysis
    print("2. Analyzing transformation patterns...")
    analyzer = PatternAnalyzer()
    result = analyzer.analyze(raw_html, extracted, ground_truth)

    print(f"   Detected {len(result.patterns)} patterns")
    print(f"   Overall confidence: {result.overall_confidence:.1%}\n")

    # Display patterns by type
    print("3. Pattern Summary:")
    from edgar.services.pattern_analyzer import TransformationPattern

    pattern_types: dict[str, list[TransformationPattern]] = {}
    for p in result.patterns:
        pattern_types.setdefault(p.pattern_type, []).append(p)

    for ptype, patterns in pattern_types.items():
        avg_conf = sum(p.confidence for p in patterns) / len(patterns)
        print(f"   {ptype}: {len(patterns)} patterns (avg conf: {avg_conf:.1%})")
        for p in patterns[:2]:  # Show first 2 of each type
            print(f"      - {p.source_path} → {p.target_field}")

    # Display recommendations
    print("\n4. Implementation Recommendations:")
    for rec in result.recommendations:
        print(f"   • {rec}")

    # Save analysis results
    print("\n5. Saving pattern analysis...")
    output = {
        "patterns": [p.model_dump() for p in result.patterns],
        "overall_confidence": result.overall_confidence,
        "input_schema": result.input_schema,
        "output_schema": result.output_schema,
        "recommendations": result.recommendations,
    }

    output_path = DATA_DIR / "pattern_analysis.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"   Saved: {output_path}")

    # Validation
    print("\n6. Validation:")
    if result.overall_confidence >= 0.85:
        print(f"   ✅ Confidence {result.overall_confidence:.1%} >= 85% threshold")
    else:
        print(f"   ⚠️  Confidence {result.overall_confidence:.1%} < 85% threshold")

    critical_patterns = ["FIELD_MAPPING", "TYPE_CONVERSION"]
    for ptype in critical_patterns:
        if ptype in pattern_types:
            print(f"   ✅ {ptype} patterns detected")
        else:
            print(f"   ❌ Missing {ptype} patterns")

    print("\n=== Phase 2 Complete ===")


if __name__ == "__main__":
    main()
