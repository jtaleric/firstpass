# FirstPass Agent

Multi-Phase Agent for OpenShift Performance Regression Triage. Helps Performance Engineers automatically triage regressions found by CPT (Continuous Performance Testing).

## Overview

FirstPass Agent is a modular framework that processes JIRA tickets through multiple phases:

- **Phase 1**: Monitor payload status using OpenShift Release Controller
- **Phase 2**: LLM-based commit analysis (planned)
- **Phase 3**: TBD - Commit removal regression testing (planned)

## Architecture

The framework is built with modularity in mind:

```
firstpass/
├── framework.py              # Core framework orchestration
├── config.py                 # Configuration management
├── jira_client.py            # JIRA API interactions
├── release_controller.py     # Release Controller API client
└── phases/
    ├── base.py               # Base phase class
    ├── phase1.py             # Phase 1 implementation
    └── phase2.py             # Phase 2 implementation (future)
```

## Phase 1: Payload Status Check

Phase 1 automatically checks if OpenShift payloads have been accepted or rejected:

1. Query JIRA for tickets with status = 'NEW'
2. Extract build URL from JIRA description
3. Fetch build-log.txt from GCS
4. Extract release stream from build log
5. Get payload tag from JIRA "Version Change" field
6. Query Release Controller API for payload phase
7. Take action based on result:
   - **Rejected**: Move to DONE
   - **Accepted**: Add label `phase1_done`, advance to Phase 2
   - **Pending**: Leave in NEW for next cycle

## Installation

1. Clone the repository:
```bash
git clone <repo-url>
cd firstpass
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure credentials:
```bash
cp .env.example .env
# Edit .env with your JIRA credentials
```

4. Configure settings:
```bash
# Edit config.yaml with your JIRA project and preferences
```

## Configuration

### Environment Variables (.env)

```bash
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-jira-api-token
```

### Configuration File (config.yaml)

```yaml
jira:
  server: "https://issues.redhat.com"
  project: "PERFSCALE"
  component: "CPT_ISSUES"  # Only process issues with this component

release_controller:
  base_url: "https://amd64.ocp.releases.ci.openshift.org/api/v1"

phases:
  enabled:
    - phase1
    # - phase2  # Enable when ready

  # Phase 1: Check payload status
  phase1:
    status: "New"  # Query issues with this status
    transition_done: "Done"  # Transition for rejected payloads
    label: "phase1_done"  # Label to add when accepted

  # Phase 2: LLM commit analysis
  phase2:
    status: "In Progress"  # Query issues with this status
    label_required: "phase1_done"  # Only process with this label
    label: "phase2_done"  # Label to add when complete
```

## Usage

### Run All Enabled Phases

```bash
python main.py
```

### Run Specific Phase

```bash
python main.py --phase phase1
```

### Custom Configuration

```bash
python main.py --config my-config.yaml
```

### Dry Run (No JIRA Updates)

```bash
python main.py --dry-run
```

## How It Works

### Phase 1 Example

Given a JIRA ticket with:
- **Description**: Contains build URL like `https://gcsweb-ci.apps.ci.l2s4.p1.openshiftapps.com/gcs/test-platform-results/logs/periodic-ci-openshift-eng-ocp-qe-perfscale-ci-main-aws-5.0-nightly-x86-control-plane-fips-6nodes/2053857063406145536/build-log.txt`
- **Version Change**: `5.0.0-0.nightly-2026-05-11-043758`

The agent will:
1. Fetch the build log
2. Extract stream: `5.0.0-0.nightly`
3. Query: `https://amd64.ocp.releases.ci.openshift.org/api/v1/releasestream/5.0.0-0.nightly/release/5.0.0-0.nightly-2026-05-11-043758`
4. Check `phase` field in response
5. Update JIRA accordingly

## Adding New Phases

To add a new phase:

1. Create a new phase class in `firstpass/phases/`:

```python
from .base import Phase

class Phase2(Phase):
    def get_target_issues(self):
        # Get issues with label 'phase1_done'
        return self.jira_client.get_issues_by_label(
            self.config.jira_project,
            'phase1_done'
        )
    
    def process_issue(self, issue):
        # Your processing logic here
        pass
```

2. Register the phase in `framework.py`:

```python
PHASE_REGISTRY = {
    'phase1': Phase1,
    'phase2': Phase2,  # Add new phase
}
```

3. Enable in `config.yaml`:

```yaml
phases:
  enabled:
    - phase1
    - phase2
```

## Development

### Project Structure

- `main.py` - Entry point
- `firstpass/` - Main package
  - `framework.py` - Orchestrates phases
  - `config.py` - Configuration management
  - `jira_client.py` - JIRA operations
  - `release_controller.py` - Release Controller API
  - `phases/` - Phase implementations

### Adding Features

The framework is designed to be extended:
- Add new phase classes in `phases/`
- Add new clients for external services
- Extend configuration in `config.yaml`

## Troubleshooting

### JIRA Authentication Fails

- Verify your credentials in `.env`
- Check JIRA server URL in `config.yaml`
- Ensure API token has proper permissions

### Build Log Not Found

- Verify the build URL format in JIRA description
- Check GCS URL accessibility
- Ensure network connectivity

### Release Controller API Errors

- Verify the stream and payload tag format
- Check Release Controller API availability
- Review logs for detailed error messages

## License
Apache 2
