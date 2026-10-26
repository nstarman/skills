"""Tiny PDFs for the tests: pages of Helvetica text, optionally a filled rectangle."""

from pathlib import Path


def write_pdf(path, pages):
    """Write `pages` to `path`; each page is a list of text lines, or (lines, (x, y, w, h))."""
    objs = ["<< /Type /Catalog /Pages 2 0 R >>", None, "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    kids = []
    for page in pages:
        lines, rect = page if isinstance(page, tuple) else (page, None)
        ops = ["BT /F1 12 Tf 72 720 Td 14 TL"]
        ops += [f"({line}) Tj T*" for line in lines]
        ops.append("ET")
        if rect:
            ops.append("0 0 0 rg {} {} {} {} re f".format(*rect))
        stream = "\n".join(ops)
        objs.append(f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream")
        objs.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {len(objs)} 0 R >>"
        )
        kids.append(f"{len(objs)} 0 R")
    objs[1] = f"<< /Type /Pages /Kids [{' '.join(kids)}] /Count {len(kids)} >>"

    out = b"%PDF-1.4\n"
    offsets = []
    for i, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n{body}\nendobj\n".encode("latin-1")
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    out += "".join(f"{o:010d} 00000 n \n" for o in offsets).encode()
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    Path(path).write_bytes(out)
