from backend.claude_client import analyze_with_claude
from scripts.dataset import CASES
from backend.judge import judge_response

def llm_as_judge_check_case(case: dict) -> tuple[bool, str]:
    # We got the response from claude
    result = analyze_with_claude(f"JD: {case['jd']}")
    verdict = judge_response(case['jd'], result)
    passed = verdict['verdict'] == "PASS"
    return passed, verdict['reasoning']


# Deprecated due to enhacement of project, now we use llm_as_judge_check_case()
def eval_check_case(case: dict) -> tuple[bool, str]:
    # We got the response from claude
    result = analyze_with_claude(f"JD: {case['jd']}")

    # From response, we extracted score, gaps and bullets
    score = result["match_score"]
    gaps = " ".join(result["gaps"]).lower()
    bullets = " ".join(result["tailored_bullets"]).lower()

    # 1. Score sanity
    low = case.get("expected_score_min", 0)
    high = case.get("expected_score_max", 100)
    if not (low <= score <= high):
        return False, f"Score={score} not in [{low},{high}]"

        # 2. Coverage — expected gap terms should appear in gaps
    for term in case.get("expected_gap_terms", []):
        if term.lower() not in gaps:
            return False, f"gap term '{term}' missing from gaps"

        # 3. Hallucination — gap terms must NOT appear in tailored_bullets
    for term in case.get("expected_gap_terms", []):
        if term.lower() in bullets:
            return False, f"hallucination: '{term}' appears in tailored_bullets"

    return True, f"score={score}, gaps ok, no halluc"

def run_evals():
    passed = 0
    for case in CASES:
        # ok, msg = eval_check_case(case)
        ok, msg = llm_as_judge_check_case(case)
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {case['name']:30s} | {msg}")
        if ok:
            passed += 1
    print(f"\npassed: {passed}/{len(CASES)}")

if __name__ == "__main__":
    run_evals()