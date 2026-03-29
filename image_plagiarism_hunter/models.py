"""Data models for Image Plagiarism Hunter."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class ViolationStatus(str, Enum):
    NEW = "new"
    DMCA_SENT = "dmca_sent"
    RESOLVED = "resolved"
    FAIR_USE = "fair_use"
    DISPUTED = "disputed"
    IGNORED = "ignored"


class FairUseIndicator(str, Enum):
    LIKELY_FAIR_USE = "likely_fair_use"
    UNLIKELY_FAIR_USE = "unlikely_fair_use"
    UNCERTAIN = "uncertain"


@dataclass
class ImageMatch:
    """A single match found via reverse image search."""

    source_image_url: str
    found_url: str
    page_url: str
    similarity_score: float
    domain: str
    date_found: str = field(default_factory=lambda: datetime.now().isoformat())
    image_dimensions: Optional[str] = None
    search_engine: str = "unknown"


@dataclass
class Violation:
    """A confirmed unauthorized use of an image."""

    id: str
    original_image_url: str
    infringing_url: str
    page_url: str
    domain: str
    similarity_score: float
    date_found: str
    status: ViolationStatus = ViolationStatus.NEW
    site_contact: Optional[str] = None
    estimated_traffic: Optional[int] = None
    commercial_use: bool = False
    fair_use_assessment: FairUseIndicator = FairUseIndicator.UNCERTAIN
    dmca_sent_date: Optional[str] = None
    resolved_date: Optional[str] = None
    notes: str = ""

    def to_dict(self) -> dict:
        data = {
            "id": self.id,
            "original_image_url": self.original_image_url,
            "infringing_url": self.infringing_url,
            "page_url": self.page_url,
            "domain": self.domain,
            "similarity_score": self.similarity_score,
            "date_found": self.date_found,
            "status": self.status.value,
            "site_contact": self.site_contact,
            "estimated_traffic": self.estimated_traffic,
            "commercial_use": self.commercial_use,
            "fair_use_assessment": self.fair_use_assessment.value,
            "dmca_sent_date": self.dmca_sent_date,
            "resolved_date": self.resolved_date,
            "notes": self.notes,
        }
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Violation":
        data = data.copy()
        data["status"] = ViolationStatus(data.get("status", "new"))
        data["fair_use_assessment"] = FairUseIndicator(
            data.get("fair_use_assessment", "uncertain")
        )
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
