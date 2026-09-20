import unittest
from src.heading import HeadingChunker


class TestHeadingPolicy(unittest.TestCase):
    def test_long_section_preserves_parent_context_and_body(self):
        body = " ".join(f"evidence{i}" for i in range(100))
        chunks = HeadingChunker(180).sections("# Policy\n## Returns\n### Exceptions\n" + body)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(c["content"]) <= 180 for c in chunks))
        self.assertTrue(all(c["section_path"] == "Policy > Returns > Exceptions" for c in chunks))
        recovered = " ".join(c["content"].split("\n\n", 1)[1] for c in chunks)
        self.assertEqual(body.split(), recovered.split())

    def test_sibling_does_not_inherit_previous_heading(self):
        parts = HeadingChunker().sections("---\naudience: seller\n---\n# Policy\n## A\n### Child\nfirst\n## B\nsecond")
        self.assertEqual(parts[1]["section_path"], "Policy > B")
        self.assertNotIn("audience", parts[0]["content"])
        self.assertEqual(len(parts), 2)

    def test_steps_kept_together_when_they_fit(self):
        text = "# Guide\n## Steps\n1. Open\n2. Select\n3. Submit"
        chunks = HeadingChunker().chunk(text)
        self.assertEqual(len(chunks), 1)
        self.assertIn("3. Submit", chunks[0])
