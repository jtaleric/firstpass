"""Tests for Config class"""

from unittest.mock import patch

from firstpass.config import Config


class TestConfig:
    """Test Config class functionality"""

    def test_load_config_from_file(self, sample_config_file, mock_env_vars):
        """Test loading configuration from YAML file"""
        config = Config(str(sample_config_file))

        assert config.jira_server == "https://test.atlassian.net"
        assert config.jira_project == "TEST"
        assert config.jira_component == "TEST_COMPONENT"

    def test_get_with_dot_notation(self, sample_config_file, mock_env_vars):
        """Test getting nested config values with dot notation"""
        config = Config(str(sample_config_file))

        assert config.get("jira.server") == "https://test.atlassian.net"
        assert config.get("jira.project") == "TEST"
        assert config.get("phases.enabled") == ["phase1", "phase2"]

    def test_get_with_default(self, sample_config_file, mock_env_vars):
        """Test getting config value with default fallback"""
        config = Config(str(sample_config_file))

        assert config.get("nonexistent.key", "default") == "default"
        assert config.get("jira.nonexistent", "fallback") == "fallback"

    def test_jira_credentials_from_env(self, sample_config_file, mock_env_vars):
        """Test reading JIRA credentials from environment"""
        config = Config(str(sample_config_file))

        assert config.jira_email == "test@example.com"
        assert config.jira_api_token == "test-token-123"
        assert config.jira_username == "testuser"
        assert config.jira_password == "testpass"

    @patch("firstpass.config.load_dotenv")
    def test_jira_credentials_empty_when_not_set(
        self, mock_load_dotenv, sample_config_file, clear_env_vars
    ):
        """Test JIRA credentials default to empty string"""
        config = Config(str(sample_config_file))

        assert config.jira_email == ""
        assert config.jira_api_token == ""
        assert config.jira_username == ""
        assert config.jira_password == ""

    def test_release_controller_url(self, sample_config_file, mock_env_vars):
        """Test getting Release Controller URL"""
        config = Config(str(sample_config_file))

        assert config.release_controller_url == "https://test-release-controller.example.com"

    def test_gcs_base_url(self, sample_config_file, mock_env_vars):
        """Test getting GCS base URL"""
        config = Config(str(sample_config_file))

        assert config.gcs_base_url == "https://storage.googleapis.com/test-bucket"

    def test_enabled_phases(self, sample_config_file, mock_env_vars):
        """Test getting enabled phases"""
        config = Config(str(sample_config_file))

        assert config.enabled_phases == ["phase1", "phase2"]

    def test_enabled_phases_default(self, tmp_path, mock_env_vars):
        """Test default enabled phases when not specified"""
        import yaml

        # Create minimal config without phases
        minimal_config = {"jira": {"server": "https://test.example.com"}}
        config_file = tmp_path / "minimal_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(minimal_config, f)

        config = Config(str(config_file))
        assert config.enabled_phases == ["phase1"]

    def test_logging_config(self, sample_config_file, mock_env_vars):
        """Test getting logging configuration"""
        config = Config(str(sample_config_file))

        assert config.get("logging.level") == "INFO"
        assert "asctime" in config.get("logging.format")
