---
name: compress-pdf
description: Shrink a scanned PDF under a size limit by recompressing each full-page image. Use when the user asks to compress a PDF, make a PDF smaller, or get a PDF under a size such as 1 MB or 3 MB. Run /compress-pdf.
---

# Compress a scanned PDF

Use this when a phone or scanner PDF is one photo per page and must fit under a size cap. The original stays in place. The script writes `<name> compressed.pdf` next to it.

## Run

Turn the cap into bytes first. "Under 1 MB" and "less than 3 MB" mean strictly under `N * 1000000` bytes.

```bash
python3 scripts/compress_pdf.py INPUT.pdf --max-bytes 1000000
```

Run that from this skill directory, or pass the script by its absolute path. Pass `--out` when the default name is wrong. The script will not replace the input or an existing output.

Read the report. It prints the output path, the byte size, the JPEG quality, and a scale. Scale `1` means the pixel size is unchanged. `status: already_under_cap` means the original already fits and no new file was written.

## Check the pages

Render every page and look at each image before you say the file is done.

```bash
pdftoppm -png -r 50 RESULT.pdf /tmp/compress-pdf-check
```

Confirm the text, stamps, signatures, and QR codes are still readable. `pdfinfo -f 1 -l N` must show the same page count and the same page size when scale is 1.

If scale is below 1, tell the user the pages were reduced so the file could fit.

## When the script stops

Exit code 2 means the PDF is not one full-page image per page. Stop and tell the user. Leave a text PDF alone.

Exit code 3 means no quality and no modest downscale fits the cap. Report the smallest size the script printed. Ask the user before you go further.

## Tools

Run the script. It calls `pdfinfo`, `pdfimages`, `cjpeg`, `djpeg`, and `ffmpeg`.

Do not install Ghostscript, qpdf, ImageMagick, or Python packages for this job. Do not recompress with `sips`. Its JPEG `formatOptions` made these scans larger. Pandoc, WeasyPrint, and `pdftocairo` rewrite documents. They do not do this size cut.
