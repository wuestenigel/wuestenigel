"""Command-line interface for Image Plagiarism Hunter."""

import argparse
import logging
import sys

from .config import Config
from .hunter import ImagePlagiarismHunter
from .models import ViolationStatus


def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def cmd_scan(args: argparse.Namespace, hunter: ImagePlagiarismHunter) -> None:
    """Scan image URLs for unauthorized usage."""
    violations = hunter.scan_multiple(args.urls)
    if violations:
        print(f"\nFound {len(violations)} new violation(s):\n")
        for v in violations:
            print(f"  [{v.id}] {v.domain} - {v.similarity_score:.1f}% similarity")
            if v.commercial_use:
                print(f"          ** Commercial use detected **")
            print(f"          Fair use: {v.fair_use_assessment.value}")
            print()
    else:
        print("\nNo new violations found.")


def cmd_report(args: argparse.Namespace, hunter: ImagePlagiarismHunter) -> None:
    """Generate a weekly report."""
    report = hunter.weekly_report(weeks_back=args.weeks)
    if args.print:
        print(report)
    else:
        print("Weekly report generated. Check the reports/ directory.")


def cmd_dashboard(args: argparse.Namespace, hunter: ImagePlagiarismHunter) -> None:
    """Generate the dashboard."""
    dashboard = hunter.dashboard()
    if args.print:
        print(dashboard)
    else:
        print("Dashboard generated. Check the reports/ directory.")


def cmd_detail(args: argparse.Namespace, hunter: ImagePlagiarismHunter) -> None:
    """Show detail for a specific violation."""
    detail = hunter.violation_detail(args.id)
    if detail:
        print(detail)
    else:
        print(f"Violation '{args.id}' not found.")
        sys.exit(1)


def cmd_update(args: argparse.Namespace, hunter: ImagePlagiarismHunter) -> None:
    """Update the status of a violation."""
    try:
        status = ViolationStatus(args.status)
    except ValueError:
        print(f"Invalid status '{args.status}'. Valid options: {[s.value for s in ViolationStatus]}")
        sys.exit(1)

    if hunter.update_violation(args.id, status, notes=args.notes or ""):
        print(f"Violation {args.id} updated to '{status.value}'.")
    else:
        print(f"Violation '{args.id}' not found.")
        sys.exit(1)


def cmd_init(args: argparse.Namespace, hunter: ImagePlagiarismHunter) -> None:
    """Initialize configuration."""
    config = Config()
    config.owner_name = input("Your name: ").strip()
    config.owner_email = input("Your email: ").strip()
    config.owner_address = input("Your address: ").strip()
    config.owner_phone = input("Your phone: ").strip()
    domains = input("Approved domains (comma-separated): ").strip()
    config.approved_domains = [d.strip() for d in domains.split(",") if d.strip()]
    config.google_api_key = input("Google API key (optional): ").strip()
    config.google_cx_id = input("Google CX ID (optional): ").strip()
    config.tineye_api_key = input("TinEye API key (optional): ").strip()
    config.save(args.config)
    print(f"\nConfiguration saved. Run 'image-plagiarism-hunter scan <url>' to start.")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="image-plagiarism-hunter",
        description="Monitor the web for unauthorized use of your images.",
    )
    parser.add_argument("-c", "--config", help="Path to config file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init
    subparsers.add_parser("init", help="Initialize configuration")

    # scan
    scan_parser = subparsers.add_parser("scan", help="Scan image URLs for plagiarism")
    scan_parser.add_argument("urls", nargs="+", help="Image URLs to scan")

    # report
    report_parser = subparsers.add_parser("report", help="Generate weekly report")
    report_parser.add_argument(
        "-w", "--weeks", type=int, default=1, help="Weeks to look back (default: 1)"
    )
    report_parser.add_argument(
        "-p", "--print", action="store_true", help="Print report to stdout"
    )

    # dashboard
    dash_parser = subparsers.add_parser("dashboard", help="Generate dashboard")
    dash_parser.add_argument(
        "-p", "--print", action="store_true", help="Print dashboard to stdout"
    )

    # detail
    detail_parser = subparsers.add_parser("detail", help="Show violation details")
    detail_parser.add_argument("id", help="Violation ID")

    # update
    update_parser = subparsers.add_parser("update", help="Update violation status")
    update_parser.add_argument("id", help="Violation ID")
    update_parser.add_argument(
        "status",
        choices=[s.value for s in ViolationStatus],
        help="New status",
    )
    update_parser.add_argument("-n", "--notes", help="Notes about the update")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    setup_logging(args.verbose)

    config = Config.load(args.config) if args.config else Config.from_env()
    hunter = ImagePlagiarismHunter(config)

    commands = {
        "init": cmd_init,
        "scan": cmd_scan,
        "report": cmd_report,
        "dashboard": cmd_dashboard,
        "detail": cmd_detail,
        "update": cmd_update,
    }

    commands[args.command](args, hunter)


if __name__ == "__main__":
    main()
