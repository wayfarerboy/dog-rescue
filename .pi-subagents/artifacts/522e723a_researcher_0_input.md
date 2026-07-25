# Task for researcher

Research additional UK dog rescue websites to add to a Python web scraper project at /Users/alpagan/Documents/dog-rescue. The scraper already monitors:
- Many Tears Rescue (manytearsrescue.org)
- Dogs Trust (dogstrust.org.uk) 
- Second Chance Spaniel Rescue (secondchancespanielrescue.org.uk)

Criteria for adoptable dogs: female, under 1 year old (preferably under 6 months), small or medium size.

Find 5-10 more UK dog rescue sites with online listings. For each site, determine:
1. Full name and adoption listing URL
2. Whether they filter/search by age, gender, size (and how — query params, form POST, GraphQL API)
3. Whether the site is server-rendered HTML (BeautifulSoup-able) or a JavaScript SPA
4. Typical listing format — individual cards, table rows, etc.
5. Whether they show location/centre, breed, age text, status

Focus on rescues with actual searchable listings. Avoid sites that only have a contact form or PDF.

Write a structured research brief to /Users/alpagan/Documents/dog-rescue/docs/research/dog-rescues.md with your findings.

---
**Output:**
Write your findings to exactly this path: /Users/alpagan/Documents/dog-rescue/.pi-subagents/artifacts/outputs/522e723a/research.md
This path is authoritative for this run.
Ignore any other output filename or output path mentioned elsewhere, including output destinations in the base agent prompt, system prompt, or task instructions.

## Acceptance Contract
Acceptance level: attested
Completion is not accepted from prose alone. End with a structured acceptance report.

Criteria:
- criterion-1: Return concrete findings with file paths and severity when applicable

Required evidence: review-findings, residual-risks

Finish with a fenced JSON block tagged `acceptance-report` in this shape:
Use empty arrays when no items apply; array fields contain strings unless object entries are shown.
`criteriaSatisfied[].status` must be exactly one of: satisfied, not-satisfied, not-applicable.
`commandsRun[].result` must be exactly one of: passed, failed, not-run.
`manualNotes` and `notes` are optional strings; an empty string means no note and does not satisfy `manual-notes` evidence.
```acceptance-report
{
  "criteriaSatisfied": [
    {
      "id": "criterion-1",
      "status": "satisfied",
      "evidence": "specific proof"
    }
  ],
  "changedFiles": [
    "src/file.ts"
  ],
  "testsAddedOrUpdated": [
    "test/file.test.ts"
  ],
  "commandsRun": [
    {
      "command": "command",
      "result": "passed",
      "summary": "short result"
    }
  ],
  "validationOutput": [
    "validation output or concise summary"
  ],
  "residualRisks": [
    "none"
  ],
  "noStagedFiles": true,
  "diffSummary": "short description of the diff",
  "reviewFindings": [
    "blocker: file.ts:12 - issue found, or no blockers"
  ],
  "manualNotes": "anything else the parent should know"
}
```