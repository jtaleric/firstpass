"""Core framework for FirstPass Agent"""

import logging
from typing import Dict, Type
from .config import Config
from .jira_client import JiraClient
from .release_controller import ReleaseControllerClient
from .phases.base import Phase
from .phases.phase1 import Phase1
from .phases.phase2 import Phase2

logger = logging.getLogger(__name__)


class FirstPassFramework:
    """Main framework orchestrating all phases"""

    # Registry of available phases
    PHASE_REGISTRY: Dict[str, Type[Phase]] = {
        'phase1': Phase1,
        'phase2': Phase2,
    }

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize framework

        Args:
            config_path: Path to configuration file
        """
        self.config = Config(config_path)
        self._setup_logging()

        # Initialize clients
        self.jira_client = self._init_jira_client()
        self.release_controller_client = self._init_release_controller_client()

        # Initialize phases
        self.phases = self._init_phases()

    def _setup_logging(self):
        """Setup logging configuration"""
        log_level = self.config.get('logging.level', 'INFO')
        log_format = self.config.get('logging.format',
                                     '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        logging.basicConfig(
            level=getattr(logging, log_level),
            format=log_format
        )

    def _init_jira_client(self) -> JiraClient:
        """Initialize JIRA client

        Returns:
            JiraClient instance
        """
        return JiraClient(
            server=self.config.jira_server,
            email=self.config.jira_email,
            api_token=self.config.jira_api_token,
            username=self.config.jira_username,
            password=self.config.jira_password
        )

    def _init_release_controller_client(self) -> ReleaseControllerClient:
        """Initialize Release Controller client

        Returns:
            ReleaseControllerClient instance
        """
        return ReleaseControllerClient(
            base_url=self.config.release_controller_url,
            gcs_base_url=self.config.gcs_base_url
        )

    def _init_phases(self) -> Dict[str, Phase]:
        """Initialize enabled phases

        Returns:
            Dictionary of phase name to phase instance
        """
        phases = {}
        enabled_phases = self.config.enabled_phases

        for phase_name in enabled_phases:
            if phase_name in self.PHASE_REGISTRY:
                phase_class = self.PHASE_REGISTRY[phase_name]
                phases[phase_name] = phase_class(
                    self.config,
                    self.jira_client,
                    self.release_controller_client,
                    phase_name
                )
                logger.info(f"Initialized {phase_name}")
            else:
                logger.warning(f"Phase '{phase_name}' not found in registry")

        return phases

    def run_phase(self, phase_name: str):
        """Run a specific phase

        Args:
            phase_name: Name of phase to run
        """
        if phase_name not in self.phases:
            logger.error(f"Phase '{phase_name}' not enabled or not found")
            return

        phase = self.phases[phase_name]
        phase.run()

    def run_all_phases(self):
        """Run all enabled phases in order"""
        logger.info("Running all enabled phases")

        for phase_name, phase in self.phases.items():
            logger.info(f"=== Running {phase_name} ===")
            phase.run()

    def run(self, phase: str = None):
        """Run the framework

        Args:
            phase: Specific phase to run (optional). If None, runs all phases.
        """
        logger.info("FirstPass Agent starting")

        if phase:
            self.run_phase(phase)
        else:
            self.run_all_phases()

        logger.info("FirstPass Agent complete")
