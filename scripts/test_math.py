"""Dependency-free checks for the exact math transcription and published artifacts."""

from __future__ import annotations

import hashlib
import json
import re
import unittest
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SOURCE_HASH = "9c458848cc023f11b39cddea9383fa1e1e92ff3b628e691292cc03ae877f5f51"
PDF_HASH = "51e53262d79be3957f0c82112de35ebc1fd823b4283d5e60811cadd852ac7479"
BI_HASHES = {
    "Simulasi_Interaktif_TKA_BI_SMP_2026.html": "f3c67d724af06534c43ea1293ad2b7443c638890f671070acf50e7ece9a4567d",
    "Simulasi_Interaktif_TKA_BI_SMP_2026_Final_Boss.html": "1e5921e232acc991e66b64f7e83ad37f18fd742ec69b63991ed2a0b952467048",
    "Simulasi_Interaktif_TKA_BI_SMP_2026_Paket_2.html": "58397b432c749f246152dc8720016b513bd9b7ec5e7f2920b97fd02b636aca41",
}


@dataclass
class Element:
    tag: str
    attrs: dict = field(default_factory=dict)
    children: list = field(default_factory=list)

    def text(self) -> str:
        return "".join(child.text() if isinstance(child, Element) else child for child in self.children)

    def find(self, tag: str | None = None, **attrs) -> list[Element]:
        matches = [self] if (tag is None or self.tag == tag) and all(self.attrs.get(k) == v for k, v in attrs.items()) else []
        for child in self.children:
            if isinstance(child, Element):
                matches.extend(child.find(tag, **attrs))
        return matches


class Document(HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self, text: str):
        super().__init__(convert_charrefs=True)
        self.root = Element("document")
        self.stack = [self.root]
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        node = Element(tag, dict(attrs))
        self.stack[-1].children.append(node)
        if tag not in self.VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def source_records() -> list[dict]:
    # Independent line-based oracle: not the generation parser.
    lines = (ROOT / "sources/yoo.txt").read_text(encoding="utf-8-sig").splitlines()
    records = []
    for index, line in enumerate(lines):
        if not re.fullmatch(r"(?:Soal|oal) Nomor \d+", line.strip()):
            continue
        n = len(records) + 1
        options = []
        for option in lines[index + 6:]:
            if re.match(r"^[A-E]\. ", option):
                options.append(option[3:].strip())
            elif option.startswith("• "):
                options.append(option[2:].strip())
            else:
                break
        records.append({"n": n, "sourceForm": lines[index + 1], "sourceKey": lines[index + 2][7:],
                        "sourceTitle": lines[index + 3], "stimulus": lines[index + 4],
                        "stem": lines[index + 5], "options": options})
    return records


class MathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = source_records()
        cls.datasets = [json.loads((ROOT / name).read_text(encoding="utf-8"))
                        for name in ("data-matematika.json", "data-matematika-modifikasi.json")]

    def test_authoritative_bytes(self):
        self.assertEqual(hashlib.sha256((ROOT / "sources/yoo.txt").read_bytes()).hexdigest(), SOURCE_HASH)
        self.assertEqual(len(self.source), 10)
        self.assertEqual(sum(len(q["options"]) for q in self.source), 49)

    def test_exact_datasets(self):
        for data in self.datasets:
            self.assertEqual(len(data["stimuli"]), 10)
            self.assertEqual(len(data["questions"]), 10)
            for expected, unit, question in zip(self.source, data["stimuli"], data["questions"], strict=True):
                with self.subTest(variant=data["variant"], n=expected["n"]):
                    self.assertEqual(unit["sourceTitle"], expected["sourceTitle"])
                    self.assertEqual(unit["paragraphs"], [expected["stimulus"]])
                    self.assertEqual(unit["chart"], [])
                    self.assertEqual(question["n"], expected["n"])
                    self.assertEqual(question["stimulus"], unit["id"])
                    for name in ("stem", "options", "sourceKey", "sourceForm"):
                        self.assertEqual(question[name], expected[name])
                    self.assertTrue(question["answerable"] and question["graded"])
                    self.assertEqual(question["status"], "complete")
                    self.assertEqual(question["issue"], "")
                    self.assertNotIn("modification", question)
                    self.assertNotIn("originalSource", question)
            self.assertEqual([q["key"] for q in data["questions"]],
                             ["C", "A", "C", "C", "B", "C", "C", "D", "C", ["A", "B", "D"]])
        self.assertEqual(self.datasets[0]["questions"], self.datasets[1]["questions"])
        self.assertEqual(self.datasets[0]["stimuli"], self.datasets[1]["stimuli"])
        self.assertNotEqual(self.datasets[0]["storageKey"], self.datasets[1]["storageKey"])

    def test_embedded_json_matches(self):
        for name, data in zip(("Ts_Sick_Boii_Matematika.html", "Ts_Sick_Boii_Matematika_Modifikasi.html"), self.datasets, strict=True):
            doc = Document((ROOT / name).read_text(encoding="utf-8")).root
            embedded = doc.find("script", id="simulation-data")
            self.assertEqual(len(embedded), 1)
            self.assertEqual(json.loads(embedded[0].text()), data)

    def test_audit_and_print_exact_text(self):
        for name in ("analisis-soal-ts-sick-boii.html", "matematika-soal-dan-pembahasan.html"):
            doc = Document((ROOT / name).read_text(encoding="utf-8")).root
            self.assertEqual(len(doc.find("article")), 10)
            for expected in self.source:
                card, = doc.find("article", id=f"soal-{expected['n']}")
                self.assertEqual(card.find("h4")[0].text(), expected["sourceTitle"])
                self.assertEqual(card.find("p", **{"class": "source-stimulus"})[0].text(), expected["stimulus"])
                self.assertEqual(card.find("p", **{"class": "stem"})[0].text(), expected["stem"])
                self.assertEqual([li.text() for li in card.find("li")], expected["options"])
                self.assertIn("Kunci: " + expected["sourceKey"], card.text())
            if name.startswith("matematika-"):
                self.assertEqual(len(doc.find("section", **{"class": "print-page"})), 5)

    def test_provenance_and_validation(self):
        manifest = json.loads((ROOT / "source-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(len(manifest), 1)
        self.assertEqual(manifest[0]["sha256"], SOURCE_HASH)
        self.assertEqual(manifest[0]["file"], "sources/yoo.txt")
        validation = json.loads((ROOT / "build-validation.json").read_text(encoding="utf-8"))
        self.assertEqual(validation["excluded"], [])
        self.assertEqual(validation["math_graded"], 10)
        self.assertEqual(validation["modified_graded"], 10)
        self.assertEqual(validation["math_forms"], {"PG": 9, "PGK MCMA": 1})
        self.assertEqual(validation["pdf_sha256"], PDF_HASH)
        audit = json.loads((ROOT / "key-audit.json").read_text(encoding="utf-8"))
        self.assertEqual(audit["reconstructedOptions"], [])
        self.assertEqual([q["sourceKey"] for q in audit["comparison"]], [q["sourceKey"] for q in self.source])

    def test_verified_pdf_unchanged(self):
        content = (ROOT / "Ts_Sick_Boii_Matematika_Soal_dan_Pembahasan.pdf").read_bytes()
        self.assertEqual(hashlib.sha256(content).hexdigest(), PDF_HASH)
        self.assertEqual(len(re.findall(rb"/Type\s*/Page\b", content)), 5)

    def test_bahasa_indonesia_unchanged(self):
        for name, expected in BI_HASHES.items():
            content = (ROOT / name).read_bytes().replace(b"\r\n", b"\n")
            self.assertEqual(hashlib.sha256(content).hexdigest(), expected, name)

    def test_math_links_and_unique_ids(self):
        for name in ("index.html", "Ts_Sick_Boii_Matematika.html", "Ts_Sick_Boii_Matematika_Modifikasi.html",
                     "analisis-soal-ts-sick-boii.html", "matematika-soal-dan-pembahasan.html"):
            doc = Document((ROOT / name).read_text(encoding="utf-8")).root
            ids = [node.attrs["id"] for node in doc.find() if "id" in node.attrs]
            self.assertEqual(len(ids), len(set(ids)), name)
            for node in doc.find("a"):
                url = urlsplit(node.attrs.get("href", ""))
                if url.scheme or url.netloc or not url.path:
                    continue
                self.assertTrue((ROOT / unquote(url.path)).is_file(), (name, url.path))


if __name__ == "__main__":
    unittest.main(verbosity=2)
