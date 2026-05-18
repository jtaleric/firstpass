"""Tests for dry-run functionality"""

from unittest.mock import patch

from firstpass.framework import FirstPassFramework


class TestDryRun:
    """Test dry-run mode"""

    @patch("firstpass.framework.JiraClient")
    @patch("firstpass.framework.ReleaseControllerClient")
    def test_dry_run_flag_passed_to_framework(
        self, mock_rc_client, mock_jira_client, sample_config_file, mock_env_vars
    ):
        """Test dry_run flag is stored in framework"""
        framework = FirstPassFramework(str(sample_config_file), dry_run=True)

        assert framework.dry_run is True

    @patch("firstpass.framework.JiraClient")
    @patch("firstpass.framework.ReleaseControllerClient")
    def test_dry_run_flag_passed_to_phases(
        self, mock_rc_client, mock_jira_client, sample_config_file, mock_env_vars
    ):
        """Test dry_run flag is passed to phases"""
        framework = FirstPassFramework(str(sample_config_file), dry_run=True)

        for phase in framework.phases.values():
            assert phase.dry_run is True

    @patch("firstpass.framework.JiraClient")
    @patch("firstpass.framework.ReleaseControllerClient")
    def test_no_dry_run_by_default(
        self, mock_rc_client, mock_jira_client, sample_config_file, mock_env_vars
    ):
        """Test dry_run is False by default"""
        framework = FirstPassFramework(str(sample_config_file))

        assert framework.dry_run is False
        for phase in framework.phases.values():
            assert phase.dry_run is False
