from backend.claude_client import analyze_with_claude
from backend.qdrant_client_db import query_chunks
from scripts.dataset import CASES, RAG_CASES
from backend.judge import judge_response
import time

def rag_relevance_eval(case: dict) -> tuple[bool, str]:
    chunks = query_chunks(case['query'], 5)
    ok = case["expect"].lower() in chunks.lower()
    res = f"query={case['query']}  expect={case['expect']}  -> {'found' if ok else 'MISSING'}"
    return ok, res

def eval_check_tools(case: dict) -> tuple[bool, str]:
    tool_used = []
    for event in analyze_with_claude(f"JD: {case['jd']}"):
        if '"stage": "tool"' in event:
            name = event.split('"name": "')[1].split('"')[0]
            tool_used.append(name)

    # assertions
    if not tool_used or tool_used[0] != "extract_requirements":
        return False, f"expect extract_requirements first, got {tool_used}"
    if tool_used.count("search_resume") > 2:
        return False, f"too many resume seaches: {tool_used.count("search_resume")}"
    return True, f"ok: {tool_used}"


def llm_as_judge_check_case(case: dict) -> tuple[bool, str]:
    # We got the response from claude
    result = analyze_with_claude(f"JD: {case['jd']}")
    verdict = judge_response(case['jd'], result)
    passed = verdict['verdict'] == "PASS"
    return passed, verdict['reasoning']


# Deprecated due to enhancement of project, now we use llm_as_judge_check_case()
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
        # ok, msg = llm_as_judge_check_case(case)
        ok, msg = eval_check_tools(case)
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {case['name']:30s} | {msg}")
        if ok:
            passed += 1

        time.sleep(25)   # stay under Voyage 3 RPM between cases
    print(f"\npassed: {passed}/{len(CASES)}")

def run_rag_relevance_eval():
    passed = 0
    for case in RAG_CASES:
        # ok, msg = eval_check_case(case)
        # ok, msg = llm_as_judge_check_case(case)
        ok, msg = rag_relevance_eval(case)
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {case['query']:30s} | {msg}")
        if ok:
            passed += 1

        time.sleep(25)   # stay under Voyage 3 RPM between cases
    print(f"\npassed: {passed}/{len(RAG_CASES)}")

if __name__ == "__main__":
    run_rag_relevance_eval()