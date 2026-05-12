"""Phase 2: LLM-based commit analysis for regression root cause"""

import logging
from typing import List, Optional
from jira.resources import Issue
from .base import Phase

logger = logging.getLogger(__name__)


class Phase2(Phase):
    """Phase 2: Analyze commits to identify potential regression causes"""

    def get_target_issues(self) -> List[Issue]:
        """Get JIRA issues with status = 'In Progress' and label = 'phase1_done'

        Returns:
            List of JIRA issues
        """
        project = self.config.jira_project
        status = self.get_phase_config('status', 'In Progress')
        label_required = self.get_phase_config('label_required', 'phase1_done')
        component = self.config.jira_component

        # Query for issues with status, label, and component
        jql = f'project = {project} AND status = "{status}" AND labels = "{label_required}"'
        if component:
            jql += f' AND component = "{component}"'
        return self.jira_client.query_issues(jql)

    def process_issue(self, issue: Issue) -> bool:
        """Process a single JIRA issue with LLM analysis

        Args:
            issue: JIRA issue to process

        Returns:
            True if processing was successful, False otherwise
        """
        self.logger.info(f"Processing issue {issue.key}: {issue.fields.summary}")

        # TODO: Phase 2 implementation
        # 1. Extract payload information
        # 2. Get commit range between baseline and regression
        # 3. Use LLM to analyze commits and identify potential causes
        # 4. Add analysis as JIRA comment
        # 5. Add phase2_done label

        self.logger.warning(f"{issue.key}: Phase 2 implementation pending")

        # Placeholder - mark as phase2_done when implemented
        # label = self.get_phase_config('label', 'phase2_done')
        # self.jira_client.add_label(issue, label)

        return True
