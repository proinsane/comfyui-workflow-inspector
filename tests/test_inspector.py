import unittest
from comfyui_workflow_inspector.inspector import inspect_workflow, to_markdown


class InspectorTests(unittest.TestCase):
    def test_ui_workflow(self):
        data = {
            "nodes": [
                {"id": 1, "type": "CheckpointLoaderSimple", "inputs": []},
                {"id": 2, "type": "CustomSampler", "inputs": [{"link": 99}]},
            ],
            "links": [[1, 1, 0, 2, 0, "MODEL"]],
        }
        report = inspect_workflow(data)
        self.assertEqual(report["node_count"], 2)
        self.assertEqual(report["link_count"], 1)
        self.assertEqual(report["dangling_input_links"][0]["link_id"], 99)
        self.assertIn("CustomSampler", report["custom_node_types"])

    def test_api_workflow(self):
        data = {
            "1": {"class_type": "CheckpointLoaderSimple", "inputs": {}},
            "2": {"class_type": "KSampler", "inputs": {"model": ["1", 0]}},
        }
        report = inspect_workflow(data)
        self.assertEqual(report["format"], "api")
        self.assertEqual(report["node_count"], 2)
        self.assertEqual(report["dangling_input_links"], [])

    def test_markdown_report(self):
        report = inspect_workflow({"nodes": [], "links": []})
        self.assertIn("# Workflow inspection", to_markdown(report))


if __name__ == "__main__":
    unittest.main()
