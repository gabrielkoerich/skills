#!/usr/bin/env python3
"""Shrink a one-image-per-page scan under a byte cap."""

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TOOLS = ("pdfinfo", "pdfimages", "cjpeg", "djpeg", "ffmpeg")
QUALITY_MIN = 35
QUALITY_MAX = 95
SCALE_STEPS = 4
SCALE_FACTOR = 0.85


def die(code, msg):
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def run(cmd):
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode != 0:
        err = proc.stderr.decode("utf-8", "replace").strip()
        die(1, err or f"command failed: {' '.join(cmd)}")
    return proc.stdout.decode("utf-8", "replace")


def jpeg_info(data):
    i = 2
    while i + 10 < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xC0, 0xC1, 0xC2):
            height = int.from_bytes(data[i + 5 : i + 7], "big")
            width = int.from_bytes(data[i + 7 : i + 9], "big")
            components = data[i + 9]
            return width, height, components
        if marker in (0xD8, 0xD9, 0x01) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        if marker == 0x00:
            i += 1
            continue
        seglen = int.from_bytes(data[i + 2 : i + 4], "big")
        i += 2 + seglen
    die(1, "JPEG has no size marker")


def page_geometry(pdf):
    info = run(["pdfinfo", str(pdf)])
    count = re.search(r"^Pages:\s+(\d+)", info, re.M)
    if not count:
        die(1, "pdfinfo did not report a page count")
    if re.search(r"^Encrypted:\s+yes", info, re.M):
        die(1, "PDF is encrypted")
    pages = int(count.group(1))
    detailed = run(["pdfinfo", "-f", "1", "-l", str(pages), str(pdf)])
    sizes = {
        int(num): (float(width), float(height))
        for num, width, height in re.findall(
            r"Page\s+(\d+)\s+size:\s+([\d.]+)\s+x\s+([\d.]+)\s+pts",
            detailed,
        )
    }
    rotations = {
        int(num): int(rot)
        for num, rot in re.findall(r"Page\s+(\d+)\s+rot:\s+(\d+)", detailed)
    }
    if len(sizes) != pages:
        die(1, f"expected {pages} page sizes, got {len(sizes)}")
    return [(sizes[i], rotations.get(i, 0)) for i in range(1, pages + 1)]


def image_rows(pdf):
    text = run(["pdfimages", "-list", str(pdf)])
    rows = []
    for line in text.splitlines():
        match = re.match(r"\s*(\d+)\s+(\d+)\s+image\s+(\d+)\s+(\d+)\s+", line)
        if match:
            rows.append(tuple(int(part) for part in match.groups()))
    return rows


def check_full_page(geometry, rows):
    by_page = {}
    for page, _index, width, height in rows:
        by_page.setdefault(page, []).append((width, height))
    if len(by_page) != len(geometry):
        die(2, "a page has no image, or the image list does not cover every page")
    rotations = []
    for page, ((box_w, box_h), rot) in enumerate(geometry, start=1):
        images = by_page[page]
        if len(images) != 1:
            die(2, f"page {page} has {len(images)} images, this path needs one")
        width, height = images[0]
        same = width == round(box_w) and height == round(box_h)
        if not same:
            die(
                2,
                f"page {page} image is {width}x{height} and the page is {box_w}x{box_h} pts",
            )
        rotations.append(rot)
    return rotations


def extract_images(pdf, raw_dir):
    run(["pdfimages", "-all", str(pdf), str(raw_dir / "page")])
    files = sorted(raw_dir.glob("page-*"), key=lambda path: path.name)
    if not files:
        die(2, "pdfimages wrote no images")
    return files


def to_ppm(src, dest):
    if src.suffix.lower() in {".jpg", ".jpeg"}:
        run(["djpeg", "-outfile", str(dest), str(src)])
        return
    run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(src),
            "-f",
            "image2",
            str(dest),
        ]
    )


def scale_ppm(src, dest, factor):
    filt = f"scale=trunc(iw*{factor}/2)*2:trunc(ih*{factor}/2)*2"
    run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(src),
            "-vf",
            filt,
            "-f",
            "image2",
            str(dest),
        ]
    )


def encode_jpeg(ppm, dest, quality):
    run(
        [
            "cjpeg",
            "-quality",
            str(quality),
            "-optimize",
            "-outfile",
            str(dest),
            str(ppm),
        ]
    )


def build_pdf(jpegs, rotations, dest):
    """jpegs is a list of bytes. Page size is the JPEG pixel size."""

    def obj(num, body):
        return f"{num} 0 obj\n".encode() + body + b"\nendobj\n"

    blobs = []
    count = len(jpegs)
    kids = " ".join(f"{3 + i * 3} 0 R" for i in range(count))
    blobs.append(obj(1, b"<< /Type /Catalog /Pages 2 0 R >>"))
    blobs.append(obj(2, f"<< /Type /Pages /Kids [{kids}] /Count {count} >>".encode()))
    for i, (data, rot) in enumerate(zip(jpegs, rotations)):
        width, height, components = jpeg_info(data)
        if components == 1:
            color = "/DeviceGray"
        elif components == 3:
            color = "/DeviceRGB"
        else:
            die(1, f"page {i + 1} JPEG has {components} components")
        page_num = 3 + i * 3
        content_num = 4 + i * 3
        image_num = 5 + i * 3
        content = f"q\n{width} 0 0 {height} 0 0 cm\n/Im0 Do\nQ\n".encode()
        rotate = f" /Rotate {rot}" if rot else ""
        page = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width} {height}]{rotate} "
            f"/Contents {content_num} 0 R /Resources << /XObject << /Im0 {image_num} 0 R >> >> >>"
        ).encode()
        blobs.append(obj(page_num, page))
        blobs.append(
            f"{content_num} 0 obj\n<< /Length {len(content)} >>\nstream\n".encode()
            + content
            + b"endstream\nendobj\n"
        )
        image = (
            f"<< /Type /XObject /Subtype /Image /Width {width} /Height {height} "
            f"/ColorSpace {color} /BitsPerComponent 8 /Filter /DCTDecode /Length {len(data)} >>"
        )
        # Length is the JPEG byte count, the newline after the stream sits outside that count
        blobs.append(
            f"{image_num} 0 obj\n{image}\nstream\n".encode()
            + data
            + b"\nendstream\nendobj\n"
        )

    header = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    out = bytearray(header)
    offsets = [0]
    for blob in blobs:
        offsets.append(len(out))
        out += blob
    xref_pos = len(out)
    nobj = len(blobs) + 1
    xref = [f"xref\n0 {nobj}\n".encode(), b"0000000000 65535 f \n"]
    for off in offsets[1:]:
        xref.append(f"{off:010d} 00000 n \n".encode())
    trailer = (
        f"trailer\n<< /Size {nobj} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode()
    )
    dest.write_bytes(out + b"".join(xref) + trailer)
    return dest.stat().st_size


def fit(ppms, rotations, max_bytes, work):
    # cjpeg size rises with quality, so the search can step
    best = None
    smallest = None
    lo, hi = QUALITY_MIN, QUALITY_MAX
    while lo <= hi:
        quality = (lo + hi) // 2
        jpegs = []
        for index, ppm in enumerate(ppms):
            jpg = work / f"q{quality}-{index}.jpg"
            encode_jpeg(ppm, jpg, quality)
            jpegs.append(jpg.read_bytes())
        pdf = work / f"q{quality}.pdf"
        size = build_pdf(jpegs, rotations, pdf)
        if smallest is None or size < smallest:
            smallest = size
        if size < max_bytes:
            best = (quality, size, pdf)
            lo = quality + 1
        else:
            hi = quality - 1
    return best, smallest


def main():
    parser = argparse.ArgumentParser(description="Shrink a one-image-per-page scan under a byte cap.")
    parser.add_argument("pdf")
    parser.add_argument("--max-bytes", type=int, required=True)
    parser.add_argument("--out")
    args = parser.parse_args()
    if args.max_bytes < 1:
        die(1, "--max-bytes must be a positive byte count")

    missing = [name for name in TOOLS if shutil.which(name) is None]
    if missing:
        die(1, f"missing tools: {', '.join(missing)}")

    src = Path(args.pdf).expanduser().resolve()
    if not src.is_file():
        die(1, f"file not found: {src}")
    out = (
        Path(args.out).expanduser().resolve()
        if args.out
        else src.with_name(src.stem + " compressed.pdf")
    )
    if out == src:
        die(1, "refusing to replace the input")
    if out.exists():
        die(1, f"output already exists: {out}")

    src_size = src.stat().st_size
    if src_size < args.max_bytes:
        print("status: already_under_cap")
        print(f"bytes: {src_size}")
        print(f"out: {src}")
        return

    geometry = page_geometry(src)
    rotations = check_full_page(geometry, image_rows(src))
    work = Path(tempfile.mkdtemp(prefix="compress-pdf-"))
    try:
        raw_dir = work / "raw"
        raw_dir.mkdir()
        extracted = extract_images(src, raw_dir)
        if len(extracted) != len(geometry):
            die(2, f"found {len(extracted)} images for {len(geometry)} pages")
        ppms = []
        for index, image in enumerate(extracted):
            ppm = work / f"full-{index}.ppm"
            to_ppm(image, ppm)
            ppms.append(ppm)

        best = None
        smallest = None
        scale = 1.0
        current = ppms
        for step in range(SCALE_STEPS + 1):
            found, attempt_smallest = fit(current, rotations, args.max_bytes, work)
            if attempt_smallest is not None and (smallest is None or attempt_smallest < smallest):
                smallest = attempt_smallest
            if found:
                best = found
                scale = 1.0 if step == 0 else SCALE_FACTOR**step
                break
            scale_next = SCALE_FACTOR ** (step + 1)
            current = []
            for index, ppm in enumerate(ppms):
                scaled = work / f"scale{step}-{index}.ppm"
                scale_ppm(ppm, scaled, scale_next)
                current.append(scaled)
        if not best:
            die(3, f"cannot fit under {args.max_bytes} bytes, smallest try was {smallest} bytes")
        quality, size, pdf = best
        shutil.copyfile(pdf, out)
    finally:
        shutil.rmtree(work, ignore_errors=True)

    print("status: compressed")
    print(f"out: {out}")
    print(f"bytes: {size}")
    print(f"quality: {quality}")
    print(f"scale: {scale:g}")
    print(f"pages: {len(geometry)}")


if __name__ == "__main__":
    main()
