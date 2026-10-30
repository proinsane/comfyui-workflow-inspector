"""Core inspection logic for ComfyUI workflow exports."""
from collections import Counter
from pathlib import Path
import json


def load_workflow(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Workflow JSON must contain an object at its top level.")
    return data


def inspect_workflow(data):
    """Return a normalized summary for UI-format or API-prompt workflows."""
    if isinstance(data.get("nodes"), list):
        return _inspect_ui_workflow(data)
    # API prompt format: {"1": {"class_type": "...", "inputs": {...}}, ...}
    if data and all(isinstance(v, dict) for v in data.values()):
        return _inspect_api_workflow(data)
    raise ValueError("Unrecognized workflow format: expected a 'nodes' list or API prompt object.")


def _inspect_ui_workflow(data):
    nodes = data.get("nodes", [])
    links = data.get("links", [])
    node_ids = {str(node.get("id")) for node in nodes if isinstance(node, dict)}
    types = Counter(str(n.get("type", "Unknown")) for n in nodes if isinstance(n, dict))
    link_ids = set()
    malformed_links = []
    for link in links:
        if not isinstance(link, (list, tuple)) or len(link) < 5:
            malformed_links.append(link)
        else:
            link_ids.add(str(link[0]))

    dangling = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        for slot in node.get("inputs", []) or []:
            if isinstance(slot, dict) and slot.get("link") is not None:
                if str(slot["link"]) not in link_ids:
                    dangling.append({
                        "node_id": node.get("id"),
                        "node_type": node.get("type", "Unknown"),
                        "link_id": slot["link"],
                    })

    missing_endpoints = []
    for link in links:
        if isinstance(link, (list, tuple)) and len(link) >= 5:
            # ComfyUI UI link: [link_id, origin_id, origin_slot, target_id, target_slot, ...]
            if str(link[1]) not in node_ids or str(link[3]) not in node_ids:
                missing_endpoints.append(link)

    return {
        "format": "ui",
        "node_count": len(nodes),
        "link_count": len(links),
        "node_types": dict(sorted(types.items())),
        "custom_node_types": sorted(t for t in types if not _looks_builtin(t)),
        "dangling_input_links": dangling,
        "links_with_missing_nodes": missing_endpoints,
        "malformed_links": malformed_links,
    }


def _inspect_api_workflow(data):
    types = Counter()
    broken_inputs = []
    for node_id, node in data.items():
        class_type = str(node.get("class_type", "Unknown"))
        types[class_type] += 1
        inputs = node.get("inputs", {})
        if not isinstance(inputs, dict):
            continue
        for input_name, value in inputs.items():
            # API connections are typically [node_id, output_index].
            if (isinstance(value, list) and len(value) == 2
                    and isinstance(value[0], (str, int))
                    and str(value[0]) not in data):
                broken_inputs.append({
                    "node_id": node_id,
                    "node_type": class_type,
                    "input": input_name,
                    "references_node": value[0],
                })
    return {
        "format": "api",
        "node_count": len(data),
        "link_count": None,
        "node_types": dict(sorted(types.items())),
        "custom_node_types": sorted(t for t in types if not _looks_builtin(t)),
        "dangling_input_links": broken_inputs,
        "links_with_missing_nodes": [],
        "malformed_links": [],
    }


def _looks_builtin(node_type):
    # Heuristic only; custom nodes can use generic names and built-ins can vary by version.
    prefixes = ("KSampler", "CheckpointLoader", "CLIP", "VAEDecode", "VAEEncode",
                "SaveImage", "PreviewImage", "LoadImage", "EmptyLatent", "Conditioning",
                "Primitive", "Reroute", "Note", "MarkdownNote", "UpscaleModelLoader")
    return node_type.startswith(prefixes)


def to_markdown(report, source_name="workflow.json"):
    lines = [
        f"# Workflow inspection: {source_name}", "",
        f"- **Format:** {report['format']}",
        f"- **Nodes:** {report['node_count']}",
        f"- **Links:** {report['link_count'] if report['link_count'] is not None else 'Not available in API format'}",
        "", "## Node types", ""
    ]
    for node_type, count in report["node_types"].items():
        lines.append(f"- `{node_type}`: {count}")
    lines += ["", "## Potential custom node types", ""]
    if report["custom_node_types"]:
        lines.extend(f"- `{name}`" for name in report["custom_node_types"])
    else:
        lines.append("No likely custom node types detected by the built-in heuristic.")
    lines += ["", "## Validation findings", ""]
    findings = [
        ("Dangling or missing input links", report["dangling_input_links"]),
        ("Links referencing missing nodes", report["links_with_missing_nodes"]),
        ("Malformed links", report["malformed_links"]),
    ]
    any_findings = False
    for title, values in findings:
        lines.append(f"### {title}")
        if values:
            any_findings = True
            lines.append(f"Found **{len(values)}**.")
            lines.extend(f"- `{json.dumps(item, ensure_ascii=False)}`" for item in values[:50])
        else:
            lines.append("None detected.")
        lines.append("")
    if not any_findings:
        lines.append("No structural issues detected by these basic checks.")
    lines.append("\n> This report is a structural inspection, not a guarantee that the workflow will execute.")
    return "\n".join(lines) + "\n"
