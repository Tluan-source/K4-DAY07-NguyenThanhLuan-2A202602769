"""Heading-aware chunking for Markdown policies, without external dependencies."""
import re

from .chunking import RecursiveChunker


class HeadingChunker:
    def __init__(self, chunk_size: int = 1400):
        if chunk_size < 100:
            raise ValueError("chunk_size must be at least 100")
        self.chunk_size = chunk_size

    def sections(self, text: str) -> list[dict]:
        text = re.sub(r"\A---\s*\n.*?\n---\s*(?:\n|$)", "", text, count=1, flags=re.S)
        headings: list[tuple[int, str]] = []
        body: list[str] = []
        result = []

        def flush():
            content = "\n".join(body).strip()
            if not content:
                return
            path = " > ".join(title for _, title in headings)
            prefix = path + "\n\n" if path else ""
            # Reserve space for the heading in EVERY descendant chunk.
            if len(prefix) >= self.chunk_size:
                raise ValueError("Heading path exceeds chunk size; increase chunk_size")
            for part in RecursiveChunker(chunk_size=self.chunk_size - len(prefix)).chunk(content):
                result.append({"content": prefix + part, "section_path": path})

        for line in text.splitlines():
            heading = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
            if heading:
                flush()
                body.clear()
                level, title = len(heading[1]), heading[2]
                while headings and headings[-1][0] >= level:
                    headings.pop()
                headings.append((level, title))
            else:
                body.append(line)
        flush()
        return result

    def chunk(self, text: str) -> list[str]:
        return [section["content"] for section in self.sections(text)]
