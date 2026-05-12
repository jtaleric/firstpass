# First Pass Agent

Multi-Phase Agent that will help OpenShift Performance Engineers triage regressions found by CPT - Continious Performance Testing.

## Phase 1
In this Phase no LLM is needed. Simply monitoring regressions and the status of the OpenShift Payload.

Here is the logical diagram for Phase 1.

```mermaid
graph TD
    Start([Start Agent Cycle]) --> QueryJira{Query JIRA:<br/>Status = 'NEW'?}

    QueryJira -- No JIRAs Found --> End([End])

    QueryJira -- JIRAs Found --> Iterate[Iterate through JIRA list]

    Iterate --> GetBuildURL[Extract Build URL<br/>from JIRA Description]

    GetBuildURL --> FetchLog[Fetch build-log.txt<br/>from GCS]

    FetchLog --> ExtractStream[Grep for 'Requesting a release'<br/>Extract releasestream]

    ExtractStream --> GetPayloadTag[Extract payload_tag<br/>from JIRA Version Change]

    GetPayloadTag --> ReleaseController["Query Release Controller API:<br/>releasestream/(stream)/release/(payload_tag)"]

    ReleaseController --> Decision{Payload Phase?}

    Decision -- Rejected --> Reject[Move JIRA to 'DONE'<br/>Payload rejected]
    Decision -- Accepted --> Advance[Move JIRA to 'Phase-2']
    Decision -- Pending/Unknown --> Skip[Leave in 'NEW'<br/>Check again next loop]

    Reject --> CheckNext{More JIRAs?}
    Advance --> AddLabel
    Skip --> CheckNext

    AddLabel -- Add JIRA Label phase1_done --> CheckNext

    CheckNext -- Yes --> Iterate
    CheckNext -- No --> End
 ```

### Phase 1 Technical Details
- **Build Log Extraction**: Parse JIRA description to find GCS build-log.txt URL
- **Stream Detection**: Grep for pattern `Requesting a release from https://amd64.ocp.releases.ci.openshift.org/api/v1/releasestream/{stream}/latest`
- **Release Controller API**: Query `https://amd64.ocp.releases.ci.openshift.org/api/v1/releasestream/{stream}/release/{payload_tag}` and check `.phase` field
- **Example**: Stream `5.0.0-0.nightly` + payload `5.0.0-0.nightly-2026-05-11-043758` → Check if accepted/rejected

## Phase 2
In this Phase we will incorporate the LLM to help determine which commits could have caused the regression.

Here is the logical diagram for Phase 2.

```mermaid
graph TD
    Start([Start Agent Cycle]) --> QueryJira{Query JIRA:<br/>Label = 'phase1_done'?}

    QueryJira -- No JIRAs Found --> End([End])

    QueryJira -- JIRAs Found --> Iterate[Iterate through JIRA list]

    Iterate --> ExtractDetails[Extract regression data<br/>and payload information]

    ExtractDetails --> LLMAnalysis[LLM Analysis:<br/>Identify potential commits]

    LLMAnalysis --> AddComment[Add analysis to<br/>JIRA comment]

    AddComment --> AddLabel[Add Label: phase2_done]

    AddLabel --> CheckNext{More JIRAs?}

    CheckNext -- Yes --> Iterate
    CheckNext -- No --> End
```

# Phase 3
WIP 
