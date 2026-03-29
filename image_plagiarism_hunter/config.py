"""Configuration management for Image Plagiarism Hunter."""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


DEFAULT_CONFIG_PATH = Path.home() / ".image_plagiarism_hunter" / "config.json"
DEFAULT_DB_PATH = Path.home() / ".image_plagiarism_hunter" / "violations.json"


@dataclass
class Config:
    """Configuration for the Image Plagiarism Hunter."""

    # API keys for reverse image search services
    google_api_key: str = ""
    google_cx_id: str = ""  # Custom Search Engine ID
    tineye_api_key: str = ""

    # Owner information for DMCA notices
    owner_name: str = ""
    owner_email: str = ""
    owner_address: str = ""
    owner_phone: str = ""

    # Approved domains that are allowed to use images
    approved_domains: list[str] = field(default_factory=list)

    # Paths
    db_path: str = str(DEFAULT_DB_PATH)
    report_output_dir: str = "reports"

    # Search settings
    similarity_threshold: float = 80.0  # Minimum similarity % to flag
    max_results_per_image: int = 50

    @classmethod
    def load(cls, path: Optional[str] = None) -> "Config":
        """Load configuration from a JSON file."""
        config_path = Path(path) if path else DEFAULT_CONFIG_PATH
        if config_path.exists():
            with open(config_path) as f:
                data = json.load(f)
            return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        return cls()

    def save(self, path: Optional[str] = None) -> None:
        """Save configuration to a JSON file."""
        config_path = Path(path) if path else DEFAULT_CONFIG_PATH
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            json.dump(self.__dict__, f, indent=2)

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        return cls(
            google_api_key=os.environ.get("GOOGLE_API_KEY", ""),
            google_cx_id=os.environ.get("GOOGLE_CX_ID", ""),
            tineye_api_key=os.environ.get("TINEYE_API_KEY", ""),
            owner_name=os.environ.get("IPH_OWNER_NAME", ""),
            owner_email=os.environ.get("IPH_OWNER_EMAIL", ""),
            owner_address=os.environ.get("IPH_OWNER_ADDRESS", ""),
            owner_phone=os.environ.get("IPH_OWNER_PHONE", ""),
        )
