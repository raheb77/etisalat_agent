# Evaluation Results

Initial evaluation on a 20-question telecom CSR test set.

## Summary

- Total questions: 20
- Passed: 16
- Correct answers: 14
- Handoffs: 3
- Reject / insufficient: 3
- Failed expectations: 4

## Key observations

- The system performs well on direct factual telecom queries such as:
  - porting duration
  - plan pricing
  - SIM replacement fees
  - complaint escalation windows
- High-risk scenarios can trigger handoff behavior, but some legal-style requests still need stronger routing rules.
- The current system is weaker on:
  - formal paraphrases of telecom-policy questions
  - procedural questions where the corpus does not include explicit steps or required documents
  - support/contact questions that are answered correctly but classified too generically, which reduces confidence unnecessarily

## Example failure patterns

- Some domain-specific support questions were answered correctly but received low confidence due to generic or unknown categorization.
- Some legal interpretation requests were not escalated consistently.
- Some formal telecom-policy phrasings were treated too conservatively.

## Conclusion

This first evaluation shows that the system is already useful for grounded factual telecom support queries, but still needs improvement in routing, intent classification, and confidence calibration for support and legal-style questions.