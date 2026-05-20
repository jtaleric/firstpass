"""Reporting module for analyzing JIRA regressions"""

import logging
import re
from collections import defaultdict
from typing import List, Optional, Tuple

from jira.resources import Issue

from .jira_client import JiraClient

logger = logging.getLogger(__name__)


class RegressionReport:
    """Generate reports on open regressions"""

    def __init__(self, jira_client: JiraClient, project: str, component: str):
        """Initialize report generator

        Args:
            jira_client: JIRA client instance
            project: JIRA project key
            component: Component to filter by
        """
        self.jira_client = jira_client
        self.project = project
        self.component = component

    def extract_version_info(
        self, issue: Issue
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
        """Extract version information from issue

        Args:
            issue: JIRA issue

        Returns:
            Tuple of (short_version, good_version, bad_version, date_extracted, good_date)
            e.g., ("5.0", "5.0.0-nightly-2026-05-17-043758", "5.0.0-nightly-2026-05-18-043758", "2026-05-18", "2026-05-17")
        """
        description = self.jira_client.get_field_value(issue, "description")

        if not description:
            return None, None, None, None, None

        # Pattern: *Version Change:* X → Y or *Version Change:* X -> Y
        # X is the good version, Y is the bad/regression version
        pattern = r"\*?Version Change:?\*?\s*(\S+)\s*(?:→|->)\s*(\S+)"
        match = re.search(pattern, description, re.IGNORECASE)

        if match:
            good_version = match.group(1).strip()
            bad_version = match.group(2).strip()

            # Extract short version (e.g., "5.0" from "5.0.0-nightly-...")
            version_pattern = r"^(\d+\.\d+)"
            version_match = re.match(version_pattern, bad_version)

            if version_match:
                short_version = version_match.group(1)

                # Try to extract dates from nightly versions
                # Format: X.Y.Z-nightly-YYYY-MM-DD-HHMMSS or X.Y.Z-0.nightly-YYYY-MM-DD-HHMMSS
                date_pattern = r"(\d{4}-\d{2}-\d{2})"

                bad_date_match = re.search(date_pattern, bad_version)
                bad_date = bad_date_match.group(1) if bad_date_match else None

                good_date_match = re.search(date_pattern, good_version)
                good_date = good_date_match.group(1) if good_date_match else None

                return short_version, good_version, bad_version, bad_date, good_date

        # Fallback: try to extract from affected versions
        if hasattr(issue.fields, "versions") and issue.fields.versions:
            bad_version = issue.fields.versions[0].name
            version_pattern = r"^(\d+\.\d+)"
            version_match = re.match(version_pattern, bad_version)
            if version_match:
                short_version = version_match.group(1)
                # Try to extract date
                date_pattern = r"(\d{4}-\d{2}-\d{2})"
                date_match = re.search(date_pattern, bad_version)
                bad_date = date_match.group(1) if date_match else None
                return short_version, None, bad_version, bad_date, None

        return None, None, None, None, None

    def extract_metric_name(self, issue: Issue) -> Optional[str]:
        """Extract metric/test name from issue summary

        Args:
            issue: JIRA issue

        Returns:
            Metric name or None
        """
        summary = issue.fields.summary
        if not summary:
            return None

        # Common patterns in regression summaries:
        # "Regression in <metric>"
        # "<metric> regression"
        # "Performance degradation in <metric>"

        # Try to extract metric name from summary
        # This is a simple heuristic - adjust based on your actual JIRA format
        patterns = [
            r"(?:Regression in|regression in)\s+(.+?)(?:\s+for|\s+on|\s+in|$)",
            r"(.+?)\s+regression",
            r"(?:Performance degradation in|degradation in)\s+(.+?)(?:\s+for|\s+on|$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, summary, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # If no pattern matches, just use the summary
        return summary

    def get_open_regressions(self) -> List[Issue]:
        """Get all open regression issues

        Returns:
            List of open JIRA issues
        """
        # Query for open issues (not Done/Closed)
        jql = (
            f"project = {self.project} AND component = {self.component} "
            f"AND status NOT IN (Done, Closed, Resolved)"
        )

        logger.info(f"Querying open regressions with JQL: {jql}")
        return self.jira_client.query_issues(jql, max_results=1000)

    def _format_table(
        self, headers: List[str], rows: List[List[str]], col_widths: Optional[List[int]] = None
    ) -> List[str]:
        """Format data as an aligned table

        Args:
            headers: Column headers
            rows: Data rows
            col_widths: Optional column widths (auto-calculated if not provided)

        Returns:
            List of formatted table lines
        """
        if not rows:
            return []

        # Calculate column widths if not provided
        if col_widths is None:
            col_widths = [len(h) for h in headers]
            for row in rows:
                for i, cell in enumerate(row):
                    col_widths[i] = max(col_widths[i], len(str(cell)))

        # Create format string
        fmt = "  ".join(f"{{:<{w}}}" for w in col_widths)

        # Build table
        lines = []
        lines.append(fmt.format(*headers))
        lines.append("  ".join("-" * w for w in col_widths))

        for row in rows:
            # Ensure all cells are strings
            str_row = [str(cell) if cell is not None else "" for cell in row]
            lines.append(fmt.format(*str_row))

        return lines

    def generate_report(self) -> str:
        """Generate a comprehensive regression report

        Returns:
            Report as formatted string
        """
        issues = self.get_open_regressions()

        if not issues:
            return "No open regressions found."

        # Data structures for aggregation
        by_short_version = defaultdict(list)  # version -> [issues]
        by_full_version = defaultdict(list)  # full_version -> [issues]
        by_date = defaultdict(list)  # date -> [issues]
        metrics_by_date: dict = defaultdict(lambda: defaultdict(list))  # date -> metric -> [issues]

        # Prepare data for table
        all_issue_data = []

        # Process each issue
        for issue in issues:
            short_ver, good_ver, bad_ver, bad_date, good_date = self.extract_version_info(issue)
            metric = self.extract_metric_name(issue)

            # Store for table
            all_issue_data.append(
                {
                    "issue": issue,
                    "short_ver": short_ver,
                    "good_ver": good_ver,
                    "bad_ver": bad_ver,
                    "bad_date": bad_date,
                    "good_date": good_date,
                    "metric": metric,
                }
            )

            if short_ver:
                by_short_version[short_ver].append(issue)

            if bad_ver:
                by_full_version[bad_ver].append(issue)

            if bad_date:
                by_date[bad_date].append(issue)

                if metric:
                    metrics_by_date[bad_date][metric].append(issue)

        # Build report
        report_lines = []
        report_lines.append("=" * 140)
        report_lines.append("OPEN CPT REGRESSIONS REPORT")
        report_lines.append("=" * 140)
        report_lines.append(f"Total open regressions: {len(issues)}\n")
        report_lines.append("-" * 140)
        report_lines.append("SUMMARY: Regression Breakdown")
        report_lines.append("-" * 140)
        report_lines.append("")

        if by_full_version:
            # Sort by count descending, then by version
            sorted_versions = sorted(by_full_version.items(), key=lambda x: (-len(x[1]), x[0]))

            summary_rows = []
            for version, version_issues in sorted_versions:
                count = len(version_issues)
                summary_rows.append([version, str(count)])

            headers = ["Payload Version", "Number of Issues"]
            table_lines = self._format_table(headers, summary_rows)
            report_lines.extend(table_lines)
        else:
            report_lines.append("No payload version information found in issues.")

        # Section 1: By Short Version with detailed table
        report_lines.append("-" * 140)
        report_lines.append("REGRESSIONS BY VERSION")
        report_lines.append("-" * 140)

        if by_short_version:
            for version in sorted(by_short_version.keys()):
                version_issues = by_short_version[version]
                count = len(version_issues)
                report_lines.append(f"\nVersion {version}: {count} regression(s)")
                report_lines.append("-" * 40)

                # Build table for this version
                table_rows = []
                for issue in version_issues:
                    issue_data = next((d for d in all_issue_data if d["issue"] is issue), None)
                    if issue_data:
                        table_rows.append(
                            [
                                str(issue.key),
                                str(issue_data["metric"] or issue.fields.summary[:40]),
                                str(issue_data["good_ver"] or "N/A"),
                                str(issue_data["bad_ver"] or "N/A"),
                                str(issue.fields.status.name),
                            ]
                        )

                # Format and add table
                headers = ["JIRA", "Metric", "Last Known Good", "Bad Version", "Status"]
                table_lines = self._format_table(headers, table_rows)
                report_lines.extend(table_lines)
        else:
            report_lines.append("No version information found in issues.")

        # Section 2: By Payload Version (summary with counts)
        report_lines.append("\n" + "-" * 140)
        report_lines.append("REGRESSIONS BY PAYLOAD VERSION")
        report_lines.append("-" * 140)
        report_lines.append("")

        if by_full_version:
            # Sort by count descending
            sorted_versions = sorted(by_full_version.items(), key=lambda x: len(x[1]), reverse=True)

            table_rows = []
            for version, version_issues in sorted_versions:
                count = len(version_issues)
                # Get unique metrics for this version
                metrics: set = set()
                for issue in version_issues:
                    issue_data = next((d for d in all_issue_data if d["issue"] is issue), None)
                    if issue_data and issue_data["metric"]:
                        metrics.add(str(issue_data["metric"]))

                table_rows.append([version, str(count), ", ".join(list(metrics)[:2]) or "Various"])

            headers = ["Payload Version", "Count", "Sample Metrics"]
            table_lines = self._format_table(headers, table_rows)
            report_lines.extend(table_lines)
        else:
            report_lines.append("No payload version information found in issues.")

        # Section 3: Cross-Version Metrics (metrics appearing across versions on same/nearby dates)
        report_lines.append("\n" + "-" * 140)
        report_lines.append("CROSS-VERSION METRIC ANALYSIS")
        report_lines.append("-" * 140)
        report_lines.append("Metrics appearing across multiple versions around the same time:\n")

        if metrics_by_date:
            # Find metrics that appear on multiple dates or with multiple issues
            metric_appearances: dict = defaultdict(lambda: {"dates": set(), "issues": []})

            for date_str, metrics_dict in metrics_by_date.items():
                for metric, metric_issues in metrics_dict.items():
                    if metric not in metric_appearances:
                        metric_appearances[metric] = {"dates": set(), "issues": []}
                    metric_appearances[metric]["dates"].add(date_str)
                    metric_appearances[metric]["issues"].extend(metric_issues)

            # Filter to metrics appearing multiple times or across dates
            cross_version_metrics = {
                metric: data
                for metric, data in metric_appearances.items()
                if len(data["issues"]) > 1 or len(data["dates"]) > 1
            }

            if cross_version_metrics:
                for metric in sorted(cross_version_metrics.keys()):
                    data = cross_version_metrics[metric]
                    dates = sorted(data["dates"])
                    issue_count = len(data["issues"])

                    report_lines.append(f"\nMetric: {metric}")
                    report_lines.append(
                        f"  Appears in {issue_count} issue(s) across {len(dates)} date(s)"
                    )
                    report_lines.append(f"  Dates: {', '.join(dates)}")
                    report_lines.append("")

                    # Build table for this metric
                    table_rows = []
                    for issue in data["issues"]:
                        issue_data = next((d for d in all_issue_data if d["issue"] is issue), None)
                        if issue_data:
                            table_rows.append(
                                [
                                    str(issue.key),
                                    str(issue_data["short_ver"] or "N/A"),
                                    str(issue_data["good_ver"] or "N/A"),
                                    str(issue_data["bad_ver"] or "N/A"),
                                ]
                            )

                    headers = ["JIRA", "Version", "Last Known Good", "Bad Version"]
                    table_lines = self._format_table(headers, table_rows)
                    report_lines.extend(["  " + line for line in table_lines])
                    report_lines.append("")
            else:
                report_lines.append("No metrics found appearing across multiple versions.")
        else:
            report_lines.append("No date/metric information found in issues.")

        report_lines.append("=" * 140)

        return "\n".join(report_lines)
