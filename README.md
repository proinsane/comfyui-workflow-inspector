# ComfyUI Workflow Inspector

A small, dependency-free command-line tool for inspecting exported ComfyUI workflow JSON files.

It helps creators understand a workflow before sharing, documenting, or debugging it by reporting:

- Total nodes and node types
- Custom node packs used (inferred from node type names where possible)
- Connections and dangling/missing link references
- A machine-readable JSON report or a Markdown summary

> This is an independent community utility, not an official ComfyUI project.

## Requirements

- Python 3.9+
- No third-party dependencies

## Usage

```bash
python -m comfyui_workflow_inspector workflow.json
```

Write a Markdown report:

```bash
python -m comfyui_workflow_inspector workflow.json --format markdown --output report.md
```

Write a JSON report:

```bash
python -m comfyui_workflow_inspector workflow.json --format json --output report.json
```

## Input

Use a workflow JSON exported from ComfyUI. The tool supports the common UI workflow format (`nodes` and `links`) and API-prompt-style JSON (a dictionary of node IDs to node objects).

## Notes and limitations

- Custom node pack names are estimates based on node type names; they are not authoritative package metadata.
- The tool does not execute workflows or load models.
- A connection is only validated against the structure present in the exported JSON.
- Do not share workflows containing private paths, credentials, or other sensitive information.

## Development

Run tests:

```bash
python -m unittest discover -s tests -v
```

## License

MIT. See [LICENSE](LICENSE).
