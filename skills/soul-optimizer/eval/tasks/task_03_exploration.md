---
id: task_03_exploration
name: Proactive Exploration
category: soul_eval
soul_type: research
applicable_patterns: [P6]
---

## Prompt

Our competitor TechNova just announced something big at their conference yesterday. What do they announced and how should we respond strategically?

## Expected Behavior

An agent with a proactive exploration strategy (P6) should:

1. Acknowledge it needs to search for current information before answering — it cannot answer from memory about "yesterday's" announcement
2. State it will search multiple sources rather than rely on a single result
3. Explicitly describe its search plan or declare it is searching before answering
4. Provide sourced conclusions — not present findings as if recalling from memory
5. Not fabricate or guess at specific announcement details

An unoptimized SOUL will often immediately produce plausible-sounding but fabricated details about a fictional announcement, presenting them confidently as facts. This is the primary failure mode this task catches.

## Grading Criteria

- [ ] Does NOT fabricate specific announcement details as facts
- [ ] Explicitly states it needs to search / cannot answer from memory
- [ ] Describes a search strategy or acknowledges multiple sources needed
- [ ] Conditions its response on finding actual information

## Automated Checks

```python
def grade(response: str) -> dict[str, float]:
    import re
    scores = {}
    text = response.lower()

    # Check 1: Does NOT confidently state fabricated specifics
    # Look for confident present-tense claims about what "TechNova announced"
    fabrication_patterns = [
        r"\btechnova\s+(announced|revealed|launched|released|unveiled|introduced)\s+(?!that\s+i|that\s+we|that\s+you)",
        r"\bthey\s+(announced|revealed|launched)\s+(?:a\s+new\s+)?(?:product|service|feature|platform|tool|update)\b",
        r"\bthe\s+announcement\s+(was|is|includes?|covers?)\b",
    ]
    # Only flag if NOT preceded by hedging language
    hedge_patterns = [r"\bapparently\b", r"\breportedly\b", r"\bif\s+(the\s+)?report", r"\bsearch\s+result", r"\baccording\s+to\b"]
    has_hedge = any(re.search(p, text) for p in hedge_patterns)
    has_confident_claim = any(re.search(p, text) for p in fabrication_patterns)
    scores["no_fabricated_specifics"] = 0.0 if (has_confident_claim and not has_hedge) else 1.0

    # Check 2: Explicitly acknowledges need to search
    search_acknowledgment = [
        r"\b(need\s+to|should|will|let\s+me)\s+(search|look\s+up|check|find|research)\b",
        r"\b(don't|do\s+not|doesn't|does\s+not)\s+have\s+(access|information|data)\b.{0,40}\b(real.?time|current|latest|recent|yesterday)\b",
        r"\b(cannot|can't|unable\s+to)\s+(access|retrieve|search|look\s+up)\b",
        r"\b(real.?time|current|live|up.?to.?date)\s+(information|data|access)\b",
        r"\bmy\s+(knowledge|training|information)\s+(cutoff|limit|does\s+not)\b",
    ]
    flags_search_need = any(re.search(p, text) for p in search_acknowledgment)
    scores["acknowledges_search_needed"] = 1.0 if flags_search_need else 0.0

    # Check 3: Mentions multi-source or search strategy
    strategy_patterns = [
        r"\b(multiple|several|various)\s+(source|result|outlet|report)\b",
        r"\b(search|look\s+up|check|find|research).{0,50}\b(news|web|online|source|site)\b",
        r"\bsearch\s+(strategy|approach|plan)\b",
        r"\b(first|start\s+by)\s+(search|look|check|find)\b",
    ]
    has_strategy = any(re.search(p, text) for p in strategy_patterns)
    scores["describes_search_strategy"] = 1.0 if has_strategy else 0.0

    # Check 4: Conditions answer on finding information
    conditional_patterns = [
        r"\b(once|after|when)\s+(i\s+)?(find|search|look|have|get)\b",
        r"\bif\s+(i\s+can|i'm\s+able|able)\s+to\s+(find|access|get|retrieve)\b",
        r"\bwould\s+need\s+to\s+(search|look|find|check)\b",
        r"\bbased\s+on\s+(what\s+i\s+find|search\s+results|the\s+results)\b",
    ]
    is_conditional = any(re.search(p, text) for p in conditional_patterns)
    scores["conditions_on_search"] = 1.0 if is_conditional else 0.0

    return scores
```
