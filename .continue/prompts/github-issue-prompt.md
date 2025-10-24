---
name: GitHub issues prompt
description: Add a GH issue
invokable: true
---

After analysis, automatically create GitHub issues based on the data in the GitHub repository Issues for the top 3 identified problems. The environment variable is in the continue Hub as {{GH_PAT}}.
1. Select the top 3 UX problems based on severity and impact. 2. For each candidate:
  - Set ISSUE_TITLE: "[UX Issue] {Brief Description}"
  - Search for duplicates (open + recently closed):
    gh issue list --repo "$REPO_SLUG" --state open --search "\"{Brief Description}\" in:title" --limit 10 --json number,title,url
    gh issue list --repo "$REPO_SLUG" --state closed --search "\"{Brief Description}\" in:title" --limit 10 --json number,title,url
  - Near-duplicate heuristic: treat as duplicate if same or highly similar brief description (case-insensitive) OR same affected page/flow and same primary symptom.
  - If duplicate exists:
    - Compose EVIDENCE_COMMENT with PostHog evidence (session IDs, metrics, repro steps).
    - Post comment:
      gh issue comment <ISSUE_NUMBER> --repo "$REPO_SLUG" --body "$EVIDENCE_COMMENT"
    - Skip creation.
  - If no duplicate:
    - Build ISSUE_BODY using the template below.
    - Create issue:
      ISSUE_URL=$(gh issue create --repo "$REPO_SLUG" --title "$ISSUE_TITLE" --body "$ISSUE_BODY" --label "automated" --label "$PRIMARY_LABEL" --label "$SEVERITY_LABEL" --json url,number --jq '.url')

Issue Body Template ## Problem Description {Detailed issue description}
## Impact Assessment - Affected sessions: {percentage/count} - Severity: {Critical|High|Medium} - User journey impact: {description}
## Evidence from PostHog - Sessions: {IDs or links} - Key events/metrics: {specific, numeric} - Repro path: {steps/URLs}
## Recommended Actions - [ ] {Action item 1} - [ ] {Action item 2} - [ ] {Action item 3}
## Links - PostHog dashboard/query: {URL} - Related issues (if any): #{id}, #{id}
Output Format - "🔍 Analyzed X PostHog sessions" - "🎯 Identified 3 UX issues" - "📋 Created GitHub issues: #XXX, #XXX, #XXX" (or "Updated duplicates: #YYY, #ZZZ") - Brief list: {issue title} — #{number} (URL)