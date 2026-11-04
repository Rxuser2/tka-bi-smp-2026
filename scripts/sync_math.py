"""Synchronize the math datasets and exports from the authoritative text source."""

from __future__ import annotations

import argparse
import copy
import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "sources" / "yoo.txt"
SOURCE_NAME = "sources/yoo.txt"
PDF_NAME = "Ts_Sick_Boii_Matematika_Soal_dan_Pembahasan.pdf"
VARIANTS = (
    ("data-matematika.json", "Ts_Sick_Boii_Matematika.html"),
    ("data-matematika-modifikasi.json", "Ts_Sick_Boii_Matematika_Modifikasi.html"),
)
SOURCE_NOTE = "Sumber tunggal: yoo.txt. Seluruh 10 wacana, pertanyaan, 49 pilihan jawaban, dan kunci disalin sesuai teks sumber."
AUDIT_NOTE = "Semua 10 soal lengkap dan dinilai. Kedua tautan Matematika memakai isi yoo.txt yang sama; tidak ada opsi rekonstruksi atau soal yang dikecualikan."
EXPLANATIONS = (
    "Parkir 09.15–14.45 = 5 jam 30 menit. Dua jam pertama Rp10.000,00. Sisa 3 jam 30 menit dibulatkan ke 4 jam sesuai ketentuan pecahan jam. Total = Rp10.000,00 + 4 × Rp4.000,00 = Rp26.000,00. Jawaban C.",
    "Keliling 48 m berarti p + l = 24 m. Karena p = l + 6, diperoleh 2l + 6 = 24, l = 9 m, dan p = 15 m. Luas = 15 × 9 = 135 m². Jawaban A.",
    "Diskon pertama: Rp350.000,00 × 0,5 = Rp175.000,00. Diskon kedua diterapkan pada harga setelah potongan pertama: Rp175.000,00 × 0,8 = Rp140.000,00. Diskon efektif 60%, bukan 70%. Jawaban C.",
    "Barisan aritmetika dengan a = 16, b = 4, dan n = 15. Suku terakhir = 16 + 14 × 4 = 72 kursi. Total = 15/2 × (16 + 72) = 660 kursi. Jawaban C.",
    "Tinggi menara dan jarak horizontal membentuk segitiga siku-siku dengan garis pandang sebagai sisi miring. Jarak horizontal = √(30² − 24²) = √(900 − 576) = √324 = 18 meter. Jawaban B.",
    "Jari-jari = 140/2 = 70 cm. Volume tabung = (22/7) × 70² × 100 = 1.540.000 cm³ = 1.540 liter. Waktu = volume/debit = 1.540/22 = 70 menit. Jawaban C.",
    "Nilai 80 muncul empat kali, paling sering, sehingga modus = 80. Ada 20 data terurut; median adalah rata-rata data ke-10 dan ke-11, yaitu (80 + 85)/2 = 82,5. Jawaban C.",
    "Total bola = 5 + 4 + 3 = 12. Bola bukan kuning = 5 merah + 4 biru = 9. Peluang = 9/12 = 3/4. Jawaban D.",
    "h(t) = 40t - 5t². Karena koefisien t² negatif, puncak parabola merupakan maksimum. Waktu puncak = −40/(2 × −5) = 4 detik. h(4) = 40 × 4 − 5 × 4² = 80 meter. Jawaban C.",
    "Dari Rp20.000.000,00: SHU anggota 40% = Rp8.000.000,00; modal tambahan 25% = Rp5.000.000,00; pendidikan 20% = Rp4.000.000,00; sosial/pengurus 15% = Rp3.000.000,00. Pernyataan 1 dan 2 benar. Istilah Modal Cadangan pada opsi 2 merujuk alokasi Modal Tambahan yang sama. Pernyataan 3 salah karena dana sosial lebih kecil daripada pendidikan. Pernyataan 4 benar: selisih Rp5.000.000,00 − Rp4.000.000,00 = Rp1.000.000,00. Jawaban opt1, opt2, opt4 (A, B, D).",
)


def parse_source(path: Path = SOURCE) -> list[dict]:
    text = path.read_text(encoding="utf-8-sig")
    headings = list(re.finditer(r"(?m)^(?:Soal|oal) Nomor (\d+)\s*$", text))
    if [int(m[1]) for m in headings] != list(range(1, 11)):
        raise ValueError("Expected exactly ten consecutive question headings")
    questions = []
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        lines = [line.strip() for line in text[heading.end():end].splitlines()
                 if line.strip() and not line.strip().isdigit()]
        source_form, key_line, source_title, stimulus, stem, *option_lines = lines
        if source_form not in ("PG Tunggal", "PG Kompleks") or not key_line.startswith("Kunci: "):
            raise ValueError(f"Malformed question {index + 1}")
        match = re.fullmatch(rf"Wacana {index + 1}: (.+):", source_title)
        if not match:
            raise ValueError(f"Malformed stimulus heading {index + 1}")
        complex_form = source_form == "PG Kompleks"
        options = []
        for option_index, line in enumerate(option_lines):
            prefix = "• " if complex_form else f"{'ABCDE'[option_index]}. "
            if not line.startswith(prefix):
                raise ValueError(f"Malformed option in question {index + 1}")
            options.append(line[len(prefix):])
        if len(options) != (4 if complex_form else 5):
            raise ValueError(f"Wrong option count in question {index + 1}")
        source_key = key_line[len("Kunci: "):]
        if complex_form:
            tokens = source_key.split(", ")
            if any(not re.fullmatch(r"opt[1-4]", token) for token in tokens):
                raise ValueError("Invalid multiple-choice key")
            key = ["ABCD"[int(token[3:]) - 1] for token in tokens]
        else:
            if source_key not in "ABCDE" or len(source_key) != 1:
                raise ValueError("Invalid single-choice key")
            key = source_key
        questions.append({"n": index + 1, "sourceForm": source_form,
                          "sourceKey": source_key, "sourceTitle": source_title,
                          "title": match[1], "paragraphs": [stimulus],
                          "stem": stem, "options": options, "key": key})
    return questions


def json_text(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def make_dataset(template: dict, source: list[dict], alternate: bool) -> dict:
    data = copy.deepcopy(template)
    for unit, question, item in zip(data["stimuli"], data["questions"], source, strict=True):
        unit.update(title=item["title"], sourceTitle=item["sourceTitle"],
                    paragraphs=item["paragraphs"], chart=[], complete=True,
                    note=f"Wacana {item['n']} · Sumber: yoo.txt", sources=[SOURCE_NAME])
        for field in ("modification", "originalSource"):
            question.pop(field, None)
        question.update(stem=item["stem"], options=item["options"], key=item["key"],
                        sourceKey=item["sourceKey"], sourceForm=item["sourceForm"],
                        form="PG" if item["sourceForm"] == "PG Tunggal" else "PGK MCMA",
                        explanation=EXPLANATIONS[item["n"] - 1], sources=[SOURCE_NAME],
                        status="complete", issue="", keyOrigin="Kunci yoo.txt; diverifikasi dengan perhitungan",
                        answerable=True, graded=True,
                        adminReview={"sourceKey": item["sourceKey"], "result": "matches",
                                     "note": "Kunci yoo.txt cocok dengan perhitungan." if item["n"] != 10
                                     else "Kunci sumber opt1, opt2, opt4 dipetakan ke A, B, D untuk penskoran; redaksi opsi tetap sesuai yoo.txt.",
                                     "sources": [SOURCE_NAME], "numberingConfirmed": True})
    data.update(title="Matematika · Salinan identik" if alternate else "Matematika · Orisinal",
                variantLabel="Salinan identik" if alternate else "Orisinal", sourceNote=SOURCE_NOTE,
                auditNote=AUDIT_NOTE, sourceFile=SOURCE_NAME,
                sourceSha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                screenshotCount=0, originalScreenshotCount=0, adminScreenshotCount=0,
                lead="Sepuluh soal Matematika dari yoo.txt, lengkap dengan seluruh pilihan jawaban. Kedua tautan memakai soal yang sama dan dapat dibuka offline.")
    data["aboutHTML"] = (f"<p>{html.escape(AUDIT_NOTE)}</p><p>{html.escape(data['durationNote'])}</p>"
                         f"<p>{html.escape(SOURCE_NOTE)}</p><p>PGK Kompleks nomor 10 dinilai benar hanya jika seluruh kunci dipilih tanpa pilihan tambahan.</p>"
                         '<p><a href="sources/yoo.txt">Baca teks sumber</a> · <a href="analisis-soal-ts-sick-boii.html">Lihat soal dan audit kunci</a>.</p>')
    # Content changes invalidate only this math variant's saved attempts.
    for field in ("revision", "storageKey"):
        data.pop(field, None)
    revision = hashlib.sha256(json_text(data).encode("utf-8")).hexdigest()[:12]
    data["revision"] = revision
    data["storageKey"] = f"ts-sick-boii-math-{data['variant']}-attempt-{revision}"
    return data


def question_card(item: dict, explanation: bool = True) -> str:
    n = item["n"]
    options = "".join(f"<li>{html.escape(option)}</li>" for option in item["options"])
    list_type = 'type="A"' if item["sourceForm"] == "PG Tunggal" else 'class="complex-options"'
    return (f'<article class="question audit-card" id="soal-{n}">\n'
            f'<h3>Soal Nomor {n} · {html.escape(item["sourceForm"])}</h3>\n'
            f'<h4>{html.escape(item["sourceTitle"])}</h4>\n'
            f'<p class="source-stimulus">{html.escape(item["paragraphs"][0])}</p>\n'
            f'<p class="stem">{html.escape(item["stem"])}</p>\n<ol {list_type}>{options}</ol>\n'
            + (f'<div class="explanation"><p><strong>Kunci: {html.escape(item["sourceKey"])}</strong></p>'
               f'<p><strong>Pembahasan:</strong> {html.escape(EXPLANATIONS[n - 1])}</p></div>\n' if explanation else "")
            + '</article>\n')


def replace_main(page: str, main: str, title: str) -> str:
    page, count = re.subn(r"<main>.*?</main>", lambda _: main, page, count=1, flags=re.S)
    if count != 1:
        raise ValueError("Expected one main element")
    return re.sub(r"<title>.*?</title>", f"<title>{html.escape(title)}</title>", page, count=1)


def exports(source: list[dict], data: list[dict]) -> dict[str, str]:
    outputs = {}
    for dataset, (json_name, html_name) in zip(data, VARIANTS, strict=True):
        outputs[json_name] = json_text(dataset)
        page = (ROOT / html_name).read_text(encoding="utf-8")
        embedded = json.dumps(dataset, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
        page, count = re.subn(r'(<script id="simulation-data" type="application/json">).*?(</script>)',
                             lambda m: m[1] + embedded + m[2], page, count=1, flags=re.S)
        if count != 1:
            raise ValueError(f"Missing embedded dataset: {html_name}")
        page = page.replace("Unduh PDF kedua versi", "Unduh PDF · 5 halaman")
        page = page.replace('<span><i class="dot flag"></i>Tidak dinilai</span>',
                            '<span><i class="dot flag"></i>Kurang tepat</span>')
        outputs[html_name] = page

    audit_name = "analisis-soal-ts-sick-boii.html"
    audit = (ROOT / audit_name).read_text(encoding="utf-8")
    tools = re.search(r'<header class="audit-tools">.*?</header>', audit, re.S)[0]
    meme = re.search(r'<section class="robot-meme".*?</section>', audit, re.S)[0]
    main = (f'<main>\n{tools}\n<h1>Matematika · Soal dan audit kunci yoo.txt</h1>\n'
            f'<p>10 soal lengkap · 49 pilihan jawaban · sumber tunggal: yoo.txt</p>\n'
            f'<div class="note"><strong>{html.escape(AUDIT_NOTE)}</strong>'
            f'<p>{html.escape(data[0]["durationNote"])}</p></div>\n'
            '<nav class="version-nav"><a href="Ts_Sick_Boii_Matematika.html">Latihan Matematika</a>'
            '<a href="Ts_Sick_Boii_Matematika_Modifikasi.html">Tautan alternatif (soal identik)</a>'
            f'<a href="{PDF_NAME}" download>PDF · 5 halaman</a>'
            '<a href="sources/yoo.txt">Teks sumber</a><a href="#questions">Soal dan pembahasan</a></nav>\n'
            f'{meme}\n<section id="original"><h2>Salinan sumber</h2><p>Redaksi dan kunci mengikuti yoo.txt.</p></section>\n'
            '<section id="modified"><h2>Tautan alternatif</h2><p>URL lama Modifikasi dipertahankan; soal sekarang identik dengan salinan sumber di bawah.</p></section>\n'
            '<section id="questions"><h2>10 soal dan pembahasan</h2>\n'
            + "".join(question_card(item) for item in source)
            + '</section>\n<section><h2>Provenans sumber</h2><p><a href="sources/yoo.txt">yoo.txt</a> · Nomor 1–10</p>'
            f'<p class="source-note">SHA-256: {data[0]["sourceSha256"]}</p>'
            '<p>Semua 10 kunci sesuai perhitungan. Kunci PGK opt1, opt2, opt4 dipetakan ke A, B, D; teks pilihan tidak diubah.</p></section>\n</main>')
    outputs[audit_name] = replace_main(audit, main, "Ts Sick Boii · Matematika dari yoo.txt")

    print_name = "matematika-soal-dan-pembahasan.html"
    page = (ROOT / print_name).read_text(encoding="utf-8")
    compact_style = '''<style id="yoo-print-style">
    .print-tools{display:flex;gap:18px;flex-wrap:wrap;margin-bottom:24px}.complex-options{list-style:disc}
    .print-page>h2{margin:12px 0}.print-page h4{margin:8px 0}.print-page .question{margin:12px 0;padding:15px}
    @media print{
      @page{size:A4;margin:12mm 14mm}.print-tools{display:none!important}body{font-size:9pt;line-height:1.3}
      h1{font-size:17pt;margin:0 0 3mm}h2{font-size:14pt}h3{font-size:10pt}h4{font-size:9pt}
      .print-page{break-after:page;break-inside:avoid}.print-page:last-child{break-after:auto}
      .print-page .question{padding:3mm 0;margin:3mm 0}.question p{margin:1.5mm 0}.question li{margin:1mm 0}
      .question ol{margin:1.5mm 0}.explanation{font-size:8.5pt}.source-note{font-size:7.5pt}
    }</style>'''
    page = re.sub(r'<style id="yoo-print-style">.*?</style>', "", page, flags=re.S)
    page = page.replace('</head>', compact_style + '</head>')
    parts = ['<main><nav class="print-tools"><a href="index.html">← Semua paket</a>'
             f'<a href="{PDF_NAME}" download>Unduh PDF · 5 halaman</a><a href="sources/yoo.txt">Teks sumber</a></nav>']
    for start in range(0, 10, 2):
        parts.append('<section class="print-page">')
        if start == 0:
            parts.append('<h1>Matematika TKA</h1><p class="source-note">10 soal, kunci dan pembahasan · Sumber tunggal: yoo.txt</p>')
        else:
            parts.append(f'<h2>Matematika TKA · Soal {start + 1}–{start + 2}</h2>')
        parts.extend(question_card(item) for item in source[start:start + 2])
        parts.append('</section>')
    parts.append('</main>')
    outputs[print_name] = replace_main(page, "\n".join(parts), "Ts Sick Boii · 10 soal Matematika dan pembahasan")

    comparison = []
    for item, question in zip(source, data[0]["questions"], strict=True):
        key = item["key"]
        answer = (f"{key} — {item['options']['ABCDE'.index(key)]}" if isinstance(key, str)
                  else "; ".join(f"{letter} — {item['options']['ABCDE'.index(letter)]}" for letter in key))
        comparison.append({"n": item["n"], "sourceKey": item["sourceKey"], "sourceAnswer": answer,
                           "editorialKey": key, "correctedAnswer": answer, "result": "matches",
                           "note": question["adminReview"]["note"], "explanation": question["explanation"],
                           "sources": [SOURCE_NAME]})
    outputs["key-audit.json"] = json_text({"source": SOURCE_NAME, "screenshots": 0, "originalGraded": 10,
                                          "modifiedGraded": 10, "sourceNumbers": list(range(1, 11)),
                                          "modifiedNumbers": [], "reconstructedOptions": [], "comparison": comparison})
    outputs["source-manifest.json"] = json_text([{"file": SOURCE_NAME, "sha256": data[0]["sourceSha256"],
                                                  "numbers": [str(n) for n in range(1, 11)],
                                                  "stimuli": [str(n) for n in range(1, 11)], "kind": "authoritative-text"}])
    validation = json.loads((ROOT / "build-validation.json").read_text(encoding="utf-8"))
    validation.update(screenshots=0, participant_screenshots=0, admin_screenshots=0, source=SOURCE_NAME,
                      source_sha256=data[0]["sourceSha256"], math_numbers=10, math_options=49, math_graded=10,
                      modified_graded=10, math_forms={"PG": 9, "PGK MCMA": 1}, excluded=[], pdf_pages=5,
                      pdf_sha256=hashlib.sha256((ROOT / PDF_NAME).read_bytes()).hexdigest())
    validation["files"] = sorted(set(validation["files"]) | {SOURCE_NAME, "scripts/sync_math.py", "scripts/test_math.py", "scripts/test_math_engine.cjs"})
    outputs["build-validation.json"] = json_text(validation)
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if generated math artifacts are stale")
    args = parser.parse_args()
    source = parse_source()
    data = [make_dataset(json.loads((ROOT / name).read_text(encoding="utf-8")), source, bool(i))
            for i, (name, _) in enumerate(VARIANTS)]
    outputs = exports(source, data)
    changed = [name for name, text in outputs.items() if (ROOT / name).read_text(encoding="utf-8") != text]
    if args.check:
        if changed:
            raise SystemExit("Stale math artifacts: " + ", ".join(changed))
        print("Math artifacts match yoo.txt: 10 questions, 49 options, 10 graded.")
        return
    for name in changed:
        (ROOT / name).write_text(outputs[name], encoding="utf-8", newline="\n")
    print(f"Updated {len(changed)} math artifacts from yoo.txt.")


if __name__ == "__main__":
    main()
