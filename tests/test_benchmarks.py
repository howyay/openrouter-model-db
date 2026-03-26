from scraper.benchmarks import extract_benchmarks


def test_extract_parenthesized_percentage():
    desc = "Leading results on SWE-bench (72.5%) and Terminal-bench (43.2%)."
    results = extract_benchmarks(desc)
    assert {"benchmark_name": "SWE-bench", "score": 72.5, "unit": "%"} in results
    assert {"benchmark_name": "Terminal-bench", "score": 43.2, "unit": "%"} in results


def test_extract_colon_percentage():
    desc = "Scores include MMLU: 89.3% and HellaSwag: 95.1% on standard benchmarks."
    results = extract_benchmarks(desc)
    assert {"benchmark_name": "MMLU", "score": 89.3, "unit": "%"} in results
    assert {"benchmark_name": "HellaSwag", "score": 95.1, "unit": "%"} in results


def test_extract_mixed_formats():
    desc = "Achieves SWE-bench (72.5%) with MMLU: 89.3% performance."
    results = extract_benchmarks(desc)
    assert len(results) == 2


def test_no_benchmarks():
    desc = "A general-purpose language model with no benchmark data."
    results = extract_benchmarks(desc)
    assert results == []


def test_no_duplicates():
    desc = "SWE-bench (72.5%) is great. Also SWE-bench (72.5%) again."
    results = extract_benchmarks(desc)
    swe = [r for r in results if r["benchmark_name"] == "SWE-bench"]
    assert len(swe) == 1


def test_integer_score():
    desc = "Achieves HumanEval (92%) pass rate."
    results = extract_benchmarks(desc)
    assert {"benchmark_name": "HumanEval", "score": 92.0, "unit": "%"} in results
