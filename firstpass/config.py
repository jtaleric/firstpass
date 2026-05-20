"""Configuration management for FirstPass Agent"""

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


class Config:
    """Configuration handler for FirstPass Agent"""

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize configuration

        Args:
            config_path: Path to YAML configuration file
        """
        # Load environment variables
        load_dotenv()

        # Load YAML config
        self.config_path = Path(config_path)
        with open(self.config_path) as f:
            self._config = yaml.safe_load(f)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation

        Args:
            key: Configuration key (e.g., 'jira.server')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

    @property
    def jira_server(self) -> str:
        """Get JIRA server URL"""
        return str(self.get("jira.server"))

    @property
    def jira_email(self) -> str:
        """Get JIRA email from environment"""
        return os.getenv("JIRA_EMAIL", "")

    @property
    def jira_api_token(self) -> str:
        """Get JIRA API token from environment"""
        return os.getenv("JIRA_API_TOKEN", "")

    @property
    def jira_username(self) -> str:
        """Get JIRA username from environment (alternative auth)"""
        return os.getenv("JIRA_USERNAME", "")

    @property
    def jira_password(self) -> str:
        """Get JIRA password from environment (alternative auth)"""
        return os.getenv("JIRA_PASSWORD", "")

    @property
    def jira_project(self) -> str:
        """Get JIRA project key"""
        return str(self.get("jira.project", "PERFSCALE"))

    @property
    def jira_component(self) -> str:
        """Get JIRA component filter"""
        return str(self.get("jira.component", "CPT_ISSUES"))

    @property
    def release_controller_url(self) -> str:
        """Get Release Controller base URL"""
        return str(self.get("release_controller.base_url"))

    @property
    def gcs_base_url(self) -> str:
        """Get GCS base URL"""
        return str(self.get("gcs.base_url"))

    @property
    def enabled_phases(self) -> list:
        """Get list of enabled phases"""
        result = self.get("phases.enabled", ["phase1"])
        return list(result) if result else ["phase1"]
