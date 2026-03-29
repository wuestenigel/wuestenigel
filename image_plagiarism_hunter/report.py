"""Report generation for Image Plagiarism Hunter."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .config import Config
from .dmca import generate_dmca_email_subject, generate_dmca_english, generate_dmca_german
from .models import Violation, ViolationStatus
from .violations_db import ViolationsDB


class ReportGenerator:
    """Generates markdown reports and dashboards for violations."""

    def __init__(self, db: ViolationsDB, config: Config):
        self.db = db
        self.config = config

    def generate_weekly_report(self, weeks_back: int = 1) -> str:
        """Generate a weekly summary report."""
        since = (datetime.now() - timedelta(weeks=weeks_back)).isoformat()
        new_violations = self.db.get_new_since(since)
        resolved = [
            v for v in self.db.get_by_status(ViolationStatus.RESOLVED)
            if v.resolved_date and v.resolved_date >= since
        ]
        pending = self.db.get_by_status(ViolationStatus.NEW)
        dmca_sent = self.db.get_by_status(ViolationStatus.DMCA_SENT)
        stats = self.db.get_stats()

        report = f"""# Image Plagiarism Hunter - Weekly Report

**Report Date:** {datetime.now().strftime('%Y-%m-%d')}
**Period:** Last {weeks_back} week(s)

---

## Summary

| Metric | Count |
|--------|-------|
| New violations found | {len(new_violations)} |
| Cases resolved | {len(resolved)} |
| Pending actions | {len(pending)} |
| DMCA notices sent | {len(dmca_sent)} |
| Total tracked | {stats['total']} |

---

## New Violations Found

"""
        if new_violations:
            report += self._violations_table(new_violations)
        else:
            report += "_No new violations found this period._\n"

        report += "\n---\n\n## Resolved Cases\n\n"
        if resolved:
            report += self._violations_table(resolved)
        else:
            report += "_No cases resolved this period._\n"

        report += "\n---\n\n## Pending Actions\n\n"
        if pending:
            report += self._violations_table(pending)
        else:
            report += "_No pending actions._\n"

        report += "\n---\n\n## DMCA Notices Awaiting Response\n\n"
        if dmca_sent:
            report += self._violations_table(dmca_sent)
        else:
            report += "_No DMCA notices pending._\n"

        return report

    def generate_dashboard(self) -> str:
        """Generate a full dashboard of all active cases."""
        stats = self.db.get_stats()
        all_violations = self.db.get_all()

        active = [
            v for v in all_violations
            if v.status not in (ViolationStatus.RESOLVED, ViolationStatus.IGNORED, ViolationStatus.FAIR_USE)
        ]

        # Sort by commercial impact: commercial first, then by traffic estimate
        active.sort(
            key=lambda v: (not v.commercial_use, -(v.estimated_traffic or 0)),
        )

        dashboard = f"""# Image Plagiarism Hunter - Dashboard

**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Overview

| Status | Count |
|--------|-------|
| New | {stats['new']} |
| DMCA Sent | {stats['dmca_sent']} |
| Resolved | {stats['resolved']} |
| Fair Use | {stats['fair_use']} |
| Disputed | {stats['disputed']} |
| Ignored | {stats['ignored']} |
| **Total** | **{stats['total']}** |

**Commercial use violations:** {stats['commercial_count']}

---

## Active Cases (Prioritized by Commercial Impact)

"""
        if active:
            dashboard += self._detailed_violations_table(active)
        else:
            dashboard += "_No active cases._\n"

        return dashboard

    def generate_violation_detail(self, violation: Violation) -> str:
        """Generate a detailed view for a single violation with DMCA notices."""
        detail = f"""# Violation Detail: {violation.id}

**Status:** {violation.status.value}
**Date Found:** {violation.date_found}

## Original Image
{violation.original_image_url}

## Infringing Usage
- **Image URL:** {violation.infringing_url}
- **Page URL:** {violation.page_url}
- **Domain:** {violation.domain}
- **Similarity:** {violation.similarity_score:.1f}%
- **Commercial Use:** {'Yes' if violation.commercial_use else 'No'}
- **Fair Use Assessment:** {violation.fair_use_assessment.value}
- **Estimated Site Traffic:** {violation.estimated_traffic or 'Unknown'}
- **Site Contact:** {violation.site_contact or 'Unknown'}

## Notes
{violation.notes or '_No notes._'}

---

## DMCA Takedown Notice (English)

```
{generate_dmca_english(violation, self.config)}
```

**Email Subject:** {generate_dmca_email_subject(violation, 'en')}

---

## Abmahnung (German)

```
{generate_dmca_german(violation, self.config)}
```

**E-Mail Betreff:** {generate_dmca_email_subject(violation, 'de')}
"""
        return detail

    def _violations_table(self, violations: list[Violation]) -> str:
        """Render a markdown table of violations."""
        table = "| ID | Domain | Similarity | Status | Date Found | Commercial |\n"
        table += "|-----|--------|-----------|--------|------------|------------|\n"
        for v in violations:
            commercial = "Yes" if v.commercial_use else "No"
            table += (
                f"| `{v.id}` | {v.domain} | {v.similarity_score:.1f}% "
                f"| {v.status.value} | {v.date_found[:10]} | {commercial} |\n"
            )
        return table

    def _detailed_violations_table(self, violations: list[Violation]) -> str:
        """Render a detailed markdown table of violations."""
        table = "| ID | Domain | Similarity | Status | Fair Use | Traffic | Commercial |\n"
        table += "|-----|--------|-----------|--------|----------|---------|------------|\n"
        for v in violations:
            traffic = f"~{v.estimated_traffic:,}" if v.estimated_traffic else "?"
            commercial = "Yes" if v.commercial_use else "No"
            table += (
                f"| `{v.id}` | {v.domain} | {v.similarity_score:.1f}% "
                f"| {v.status.value} | {v.fair_use_assessment.value} "
                f"| {traffic} | {commercial} |\n"
            )
        return table

    def save_report(self, content: str, filename: str) -> str:
        """Save a report to the output directory."""
        output_dir = Path(self.config.report_output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / filename
        path.write_text(content)
        return str(path)
