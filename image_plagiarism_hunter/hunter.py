"""Core orchestrator for Image Plagiarism Hunter."""

import logging
from datetime import datetime
from urllib.parse import urlparse

from .config import Config
from .fair_use import assess_fair_use, estimate_commercial_use
from .models import ImageMatch, Violation, ViolationStatus
from .report import ReportGenerator
from .search import GoogleVisionSearch, SearchAggregator, TinEyeSearch
from .violations_db import ViolationsDB

logger = logging.getLogger(__name__)


class ImagePlagiarismHunter:
    """Main orchestrator that ties together search, analysis, and reporting."""

    def __init__(self, config: Config):
        self.config = config
        self.db = ViolationsDB(config.db_path)

        # Initialize search engines based on available API keys
        engines = []
        if config.google_api_key and config.google_cx_id:
            engines.append(GoogleVisionSearch(config.google_api_key, config.google_cx_id))
        if config.tineye_api_key:
            engines.append(TinEyeSearch(config.tineye_api_key))

        self.search = SearchAggregator(engines)
        self.reporter = ReportGenerator(self.db, config)

    def scan_image(self, image_url: str) -> list[Violation]:
        """Scan a single image URL for unauthorized usage."""
        logger.info("Scanning image: %s", image_url)
        matches = self.search.search(
            image_url, max_results=self.config.max_results_per_image
        )
        logger.info("Found %d raw matches", len(matches))

        violations = []
        for match in matches:
            if match.similarity_score < self.config.similarity_threshold:
                continue

            if self._is_approved_domain(match.domain):
                logger.debug("Skipping approved domain: %s", match.domain)
                continue

            violation = self._match_to_violation(match)
            is_new = self.db.add(violation)
            if is_new:
                violations.append(violation)
                logger.info(
                    "New violation: %s on %s (%.1f%%)",
                    violation.id,
                    violation.domain,
                    violation.similarity_score,
                )

        logger.info("Found %d new violations", len(violations))
        return violations

    def scan_multiple(self, image_urls: list[str]) -> list[Violation]:
        """Scan multiple image URLs."""
        all_violations = []
        for url in image_urls:
            violations = self.scan_image(url)
            all_violations.extend(violations)
        return all_violations

    def weekly_report(self, weeks_back: int = 1) -> str:
        """Generate and save a weekly report."""
        report = self.reporter.generate_weekly_report(weeks_back)
        filename = f"weekly_report_{datetime.now().strftime('%Y-%m-%d')}.md"
        path = self.reporter.save_report(report, filename)
        logger.info("Weekly report saved to %s", path)
        return report

    def dashboard(self) -> str:
        """Generate and save a dashboard."""
        dashboard = self.reporter.generate_dashboard()
        filename = "dashboard.md"
        path = self.reporter.save_report(dashboard, filename)
        logger.info("Dashboard saved to %s", path)
        return dashboard

    def violation_detail(self, violation_id: str) -> str | None:
        """Get a detailed report for a single violation."""
        violation = self.db.get(violation_id)
        if not violation:
            return None
        return self.reporter.generate_violation_detail(violation)

    def update_violation(
        self, violation_id: str, status: ViolationStatus, notes: str = ""
    ) -> bool:
        """Update the status of a violation."""
        return self.db.update_status(violation_id, status, notes)

    def _is_approved_domain(self, domain: str) -> bool:
        """Check if a domain is in the approved whitelist."""
        domain = domain.lower()
        for approved in self.config.approved_domains:
            approved = approved.lower()
            if domain == approved or domain.endswith(f".{approved}"):
                return True
        return False

    def _match_to_violation(self, match: ImageMatch) -> Violation:
        """Convert a search match to a violation with enrichment."""
        fair_use_indicator, fair_use_notes = assess_fair_use(match)
        commercial = estimate_commercial_use(match.domain)

        violation_id = ViolationsDB.generate_id(
            match.source_image_url, match.found_url
        )

        return Violation(
            id=violation_id,
            original_image_url=match.source_image_url,
            infringing_url=match.found_url,
            page_url=match.page_url,
            domain=match.domain,
            similarity_score=match.similarity_score,
            date_found=match.date_found,
            commercial_use=commercial,
            fair_use_assessment=fair_use_indicator,
            notes=fair_use_notes,
        )
