"""Violation tracking database (JSON file-based)."""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import FairUseIndicator, Violation, ViolationStatus

logger = logging.getLogger(__name__)


class ViolationsDB:
    """Persistent storage for image plagiarism violations."""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self._violations: dict[str, Violation] = {}
        self._load()

    def _load(self) -> None:
        """Load violations from disk."""
        if self.db_path.exists():
            with open(self.db_path) as f:
                data = json.load(f)
            for v_data in data.get("violations", []):
                v = Violation.from_dict(v_data)
                self._violations[v.id] = v
            logger.info("Loaded %d violations from %s", len(self._violations), self.db_path)

    def _save(self) -> None:
        """Persist violations to disk."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "violations": [v.to_dict() for v in self._violations.values()],
            "last_updated": datetime.now().isoformat(),
        }
        with open(self.db_path, "w") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def generate_id(original_url: str, infringing_url: str) -> str:
        """Generate a deterministic ID for a violation."""
        raw = f"{original_url}|{infringing_url}"
        return hashlib.sha256(raw.encode()).hexdigest()[:12]

    def add(self, violation: Violation) -> bool:
        """Add a new violation. Returns True if it was new."""
        if violation.id in self._violations:
            existing = self._violations[violation.id]
            if existing.status == ViolationStatus.RESOLVED:
                # Re-opened violation
                violation.notes = f"Re-detected. Previously resolved on {existing.resolved_date}."
            else:
                return False

        self._violations[violation.id] = violation
        self._save()
        return True

    def get(self, violation_id: str) -> Optional[Violation]:
        return self._violations.get(violation_id)

    def update_status(
        self, violation_id: str, status: ViolationStatus, notes: str = ""
    ) -> bool:
        """Update the status of a violation."""
        v = self._violations.get(violation_id)
        if not v:
            return False

        v.status = status
        if notes:
            v.notes = notes
        if status == ViolationStatus.DMCA_SENT:
            v.dmca_sent_date = datetime.now().isoformat()
        elif status == ViolationStatus.RESOLVED:
            v.resolved_date = datetime.now().isoformat()

        self._save()
        return True

    def get_all(self) -> list[Violation]:
        return list(self._violations.values())

    def get_by_status(self, status: ViolationStatus) -> list[Violation]:
        return [v for v in self._violations.values() if v.status == status]

    def get_new_since(self, since_date: str) -> list[Violation]:
        """Get violations found since a specific date."""
        return [v for v in self._violations.values() if v.date_found >= since_date]

    def get_stats(self) -> dict:
        """Return summary statistics."""
        violations = list(self._violations.values())
        return {
            "total": len(violations),
            "new": sum(1 for v in violations if v.status == ViolationStatus.NEW),
            "dmca_sent": sum(1 for v in violations if v.status == ViolationStatus.DMCA_SENT),
            "resolved": sum(1 for v in violations if v.status == ViolationStatus.RESOLVED),
            "fair_use": sum(1 for v in violations if v.status == ViolationStatus.FAIR_USE),
            "disputed": sum(1 for v in violations if v.status == ViolationStatus.DISPUTED),
            "ignored": sum(1 for v in violations if v.status == ViolationStatus.IGNORED),
            "commercial_count": sum(1 for v in violations if v.commercial_use),
        }
