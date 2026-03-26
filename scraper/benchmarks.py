"""Extract benchmark scores from model description text."""

import re


def extract_benchmarks(description: str) -> list[dict]:
    """Extract benchmark name/score pairs from free-text description.

    Supports formats:
    - "BenchName (72.5%)" — parenthesized percentage
    - "BenchName: 89.3%" — colon-separated percentage

    Returns list of dicts: {benchmark_name, score, unit}
    Deduplicates by benchmark_name (first match wins).
    """
    results: dict[str, dict] = {}

    # Pattern 1: "Name (72.5%)"
    for m in re.finditer(r"([\w]+(?:-[\w]+)*)\s*\((\d+\.?\d*)%\)", description):
        name = m.group(1).strip()
        score = float(m.group(2))
        results[name] = {"benchmark_name": name, "score": score, "unit": "%"}

    # Pattern 2: "Name: 72.5%"
    for m in re.finditer(r"([\w]+(?:-[\w]+)*):\s*(\d+\.?\d*)%", description):
        name = m.group(1).strip()
        score = float(m.group(2))
        if name not in results:
            results[name] = {"benchmark_name": name, "score": score, "unit": "%"}

    return list(results.values())
