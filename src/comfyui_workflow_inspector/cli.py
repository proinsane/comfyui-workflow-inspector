"""Command-line interface."""
import argparse
import json
import sys
from pathlib import Path

from .inspector import inspect_workflow, load_workflow, to_markdown


def main():
    parser = argparse.ArgumentParser(description="Inspect an exported ComfyUI workflow JSON file.")
    parser.add_argument("workflow", help="Path to workflow JSON")
    parser.add_argument("--format", choices=("text", "markdown", "json"), default="text")
    parser.add_argument("--output", help="Write report to this file instead of stdout")
    args = parser.parse_args()

    try:
        data = load_workflow(args.workflow)
        report = inspect_workflow(data)
        if args.format == "json":
            rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        elif args.format == "markdown":
            rendered = to_markdown(report, Path(args.workflow).name)
        else:
            rendered = (
                f"Format: {report['format']}\n"
                f"Nodes: {report['node_count']}\n"
                f"Links: {report['link_count'] if report['link_count'] is not None else 'N/A'}\n"
                f"Potential custom node types: {len(report['custom_node_types'])}\n"
                f"Validation findings: "
                f"{len(report['dangling_input_links']) + len(report['links_with_missing_nodes']) + len(report['malformed_links'])}\n"
            )
        if args.output:
            Path(args.output).write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
