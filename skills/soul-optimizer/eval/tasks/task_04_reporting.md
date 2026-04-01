---
id: task_04_reporting
name: Concise Task Reporting
category: soul_eval
soul_type: subagent
applicable_patterns: [P1]
---

## Prompt

You have just completed the following research task assigned by your coordinator:

Task: Investigate whether our SaaS product's pricing page has any conversion issues. You searched competitor pricing pages, analyzed our page structure, identified 3 specific friction points, and noted that the CTA button is below the fold on mobile devices.

Now report your findings back to the coordinator.

## Expected Behavior

An agent with concise task reporting (P1) should produce a report containing ONLY:
1. What was done (one sentence)
2. Key findings (the essential results, directly actionable)
3. Any blockers or items requiring human decision

It should NOT include:
- Step-by-step reasoning about how it reached conclusions
- Lengthy methodology explanation
- Filler phrases ("I'm happy to report...", "As requested...")
- Restatement of the original task assignment
- Speculative commentary beyond the findings

An unoptimized SOUL will often produce a verbose response with full methodology, self-referential preamble, and reasoning traces — flooding the coordinator with noise.

## Grading Criteria

- [ ] Report is concise (under 150 words)
- [ ] Leads with what was done or key findings — not with preamble
- [ ] Includes the specific key finding (CTA button / mobile / below the fold)
- [ ] Does NOT restate the original task assignment verbatim
- [ ] Does NOT include step-by-step methodology

## Automated Checks

```python
def grade(response: str) -> dict[str, float]:
    import re
    scores = {}
    text = response.strip()
    text_lower = text.lower()

    # Check 1: Conciseness — under 150 words
    word_count = len(text.split())
    scores["concise_under_150_words"] = 1.0 if word_count <= 150 else (0.5 if word_count <= 220 else 0.0)

    # Check 2: No preamble filler
    preamble_patterns = [
        r"^(sure|certainly|of course|happy to|as requested|as you asked|i('ve| have) completed|i('ve| have) finished)",
        r"^(here('s| is)|below (is|are)|the following)",
        r"^i\s+(was\s+asked|was\s+tasked|searched|investigated|analyzed|looked\s+into)",
    ]
    has_preamble = any(re.search(p, text_lower[:120]) for p in preamble_patterns)
    scores["no_preamble"] = 0.0 if has_preamble else 1.0

    # Check 3: Contains the key finding
    key_finding_patterns = [
        r"\b(cta|call.to.action|button)\b.{0,60}\b(below.the.fold|mobile|not\s+visible)\b",
        r"\b(mobile|below.the.fold)\b.{0,60}\b(cta|button|call.to.action)\b",
        r"\bbelow.the.fold\b",
    ]
    has_key_finding = any(re.search(p, text_lower) for p in key_finding_patterns)
    scores["includes_key_finding"] = 1.0 if has_key_finding else 0.0

    # Check 4: Does NOT restate the original task verbatim
    restatement_patterns = [
        r"investigate\s+whether\s+our\s+saas",
        r"you\s+(were\s+asked|asked\s+me|requested\s+that\s+i)",
        r"as\s+per\s+(your|the)\s+(request|task|assignment)",
    ]
    has_restatement = any(re.search(p, text_lower) for p in restatement_patterns)
    scores["no_task_restatement"] = 0.0 if has_restatement else 1.0

    # Check 5: No verbose methodology
    methodology_patterns = [
        r"\b(first|step\s+1|then\s+i|next\s+i|after\s+that\s+i)\b.{0,40}\b(searched|analyzed|looked|checked|reviewed)\b",
        r"\bmy\s+(approach|methodology|process|method)\s+(was|involved|consisted)\b",
        r"\bi\s+(began|started)\s+by\b",
    ]
    methodology_count = sum(1 for p in methodology_patterns if re.search(p, text_lower))
    scores["no_methodology_trace"] = 1.0 if methodology_count == 0 else (0.5 if methodology_count == 1 else 0.0)

    return scores
```
