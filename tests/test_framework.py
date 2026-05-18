"""Tests for FirstPassFramework"""

from unittest.mock import Mock, patch

from firstpass.framework import FirstPassFramework


class TestFirstPassFramework:
    """Test FirstPassFramework class"""

    @patch("firstpass.framework.JiraClient")
    @patch("firstpass.framework.ReleaseControllerClient")
    def test_framework_initialization(
        self, mock_rc_client, mock_jira_client, sample_config_file, mock_env_vars
    ):
        """Test framework initializes correctly"""
        framework = FirstPassFramework(str(sample_config_file))

        assert framework.config is not None
        assert framework.jira_client is not None
        assert framework.release_controller_client is not None
        assert isinstance(framework.phases, dict)
        assert framework.dry_run is False

    @patch("firstpass.framework.JiraClient")
    @patch("firstpass.framework.ReleaseControllerClient")
    def test_phase_registry(
        self, mock_rc_client, mock_jira_client, sample_config_file, mock_env_vars
    ):
        """Test phase registry contains expected phases"""
        assert "phase1" in FirstPassFramework.PHASE_REGISTRY
        assert "phase2" in FirstPassFramework.PHASE_REGISTRY

    @patch("firstpass.framework.JiraClient")
    @patch("firstpass.framework.ReleaseControllerClient")
    def test_enabled_phases_initialization(
        self, mock_rc_client, mock_jira_client, sample_config_file, mock_env_vars
    ):
        """Test that enabled phases are initialized"""
        framework = FirstPassFramework(str(sample_config_file))

        enabled_phases = framework.config.enabled_phases
        for phase_name in enabled_phases:
            assert phase_name in framework.phases

    @patch("firstpass.framework.JiraClient")
    @patch("firstpass.framework.ReleaseControllerClient")
    def test_jira_client_initialization(
        self, mock_rc_client, mock_jira_client, sample_config_file, mock_env_vars
    ):
        """Test JIRA client is initialized with correct parameters"""
        _ = FirstPassFramework(str(sample_config_file))

        mock_jira_client.assert_called_once()
        call_kwargs = mock_jira_client.call_args.kwargs

        assert call_kwargs["server"] == "https://test.atlassian.net"
        assert call_kwargs["email"] == "test@example.com"
        assert call_kwargs["api_token"] == "test-token-123"

    @patch("firstpass.framework.JiraClient")
    @patch("firstpass.framework.ReleaseControllerClient")
    def test_release_controller_initialization(
        self, mock_rc_client, mock_jira_client, sample_config_file, mock_env_vars
    ):
        """Test Release Controller client is initialized with correct parameters"""
        _ = FirstPassFramework(str(sample_config_file))

        mock_rc_client.assert_called_once()
        call_kwargs = mock_rc_client.call_args.kwargs

        assert call_kwargs["base_url"] == "https://test-release-controller.example.com"
        assert call_kwargs["gcs_base_url"] == "https://storage.googleapis.com/test-bucket"

    @patch("firstpass.framework.JiraClient")
    @patch("firstpass.framework.ReleaseControllerClient")
    def test_run_specific_phase(
        self, mock_rc_client, mock_jira_client, sample_config_file, mock_env_vars
    ):
        """Test running a specific phase"""
        framework = FirstPassFramework(str(sample_config_file))

        # Mock the phase's run method
        for phase in framework.phases.values():
            phase.run = Mock()

        framework.run_phase("phase1")

        # Check that phase1's run was called
        framework.phases["phase1"].run.assert_called_once()

    @patch("firstpass.framework.JiraClient")
    @patch("firstpass.framework.ReleaseControllerClient")
    def test_run_all_phases(
        self, mock_rc_client, mock_jira_client, sample_config_file, mock_env_vars
    ):
        """Test running all phases"""
        framework = FirstPassFramework(str(sample_config_file))

        # Mock the phases' run methods
        for phase in framework.phases.values():
            phase.run = Mock()

        framework.run_all_phases()

        # Check that all phases' run methods were called
        for phase in framework.phases.values():
            phase.run.assert_called_once()

    @patch("firstpass.framework.JiraClient")
    @patch("firstpass.framework.ReleaseControllerClient")
    def test_run_with_specific_phase(
        self, mock_rc_client, mock_jira_client, sample_config_file, mock_env_vars
    ):
        """Test run method with specific phase"""
        framework = FirstPassFramework(str(sample_config_file))

        # Mock the phase's run method
        framework.phases["phase1"].run = Mock()

        framework.run(phase="phase1")

        framework.phases["phase1"].run.assert_called_once()

    @patch("firstpass.framework.JiraClient")
    @patch("firstpass.framework.ReleaseControllerClient")
    def test_run_without_phase(
        self, mock_rc_client, mock_jira_client, sample_config_file, mock_env_vars
    ):
        """Test run method without specifying phase (runs all)"""
        framework = FirstPassFramework(str(sample_config_file))

        # Mock all phases' run methods
        for phase in framework.phases.values():
            phase.run = Mock()

        framework.run()

        # All phases should have been called
        for phase in framework.phases.values():
            phase.run.assert_called_once()
