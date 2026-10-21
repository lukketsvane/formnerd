"""Deterministic page images and a quick, complete review GIF from a final PDF.

The PDF remains the print master. Page PNGs retain enough pixels for phone
zoom; the smaller GIF is for checking the sequence and visual consistency.
All pages are rendered and validated before existing outputs are replaced.
"""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from PIL import Image


_PALETTE = [value for grey in range(256) for value in (grey, grey, grey)]
_PAGE_NAME = re.compile(r"side-(\d+)\.png\Z")


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _publish(stage, output, names):
    """Replace complete outputs, restoring previous files on a publish error."""
    replaced, installed = [], []
    try:
        for name in names:
            target = output / name
            if target.exists():
                backup = stage / ("previous-" + name)
                os.replace(target, backup)
                replaced.append((target, backup))
            os.replace(stage / name, target)
            installed.append(target)
    except Exception:
        for target in reversed(installed):
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
        for target, backup in reversed(replaced):
            os.replace(backup, target)
        raise


def eksporter(pdf, output, pages, page_width=1440, gif_width=768,
              page_ms=650, edge_ms=1400):
    """Export and validate every page; return relative, reproducible metadata.

    ``pages`` is the expected count from the document builder. GIF timing is
    in milliseconds and must be representable in GIF's 10 ms units. A fixed
    256-level grayscale palette preserves antialiasing without dithering or
    per-frame palette changes.
    """
    pdf, output = Path(pdf).resolve(), Path(output).resolve()
    if not pdf.is_file():
        raise ValueError(f"PDF finst ikkje: {pdf}")
    if any(not isinstance(value, int) or value < 1
           for value in (pages, page_width, gif_width, page_ms, edge_ms)):
        raise ValueError("Sidetal, pikselbreidder og visingstider må vere positive heiltal")
    if gif_width > page_width:
        raise ValueError("GIF-breidda kan ikkje vere større enn sidebileta")
    if any(value % 10 or value > 655350 for value in (page_ms, edge_ms)):
        raise ValueError("GIF-tider må vere multiplum av 10 ms, høgst 655350 ms")
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".vising-", dir=output) as temporary:
        stage = Path(temporary)
        images = stage / "sider"
        images.mkdir()
        process = subprocess.run(
            ["pdftoppm", "-scale-to-x", str(page_width), "-scale-to-y", "-1",
             "-png", str(pdf), str(images / "side")],
            capture_output=True, text=True, timeout=300)
        if process.returncode:
            raise RuntimeError("Sideeksport feila: " + process.stderr.strip()[-2000:])
        numbered = sorted((int(match.group(1)), file)
                          for file in images.iterdir()
                          if (match := _PAGE_NAME.fullmatch(file.name)))
        if [number for number, _ in numbered] != list(range(1, pages + 1)):
            raise ValueError(f"Venta {pages} samanhengande sider, fekk {len(numbered)}")
        files = [file for _, file in numbered]
        dimensions = []
        for file in files:
            with Image.open(file) as image:
                image.load()
                dimensions.append(image.size)
                if image.format != "PNG":
                    raise ValueError(f"Ugyldig sidebilete: {file.name}")
        if len(set(dimensions)) != 1 or dimensions[0][0] != page_width:
            raise ValueError(f"Ulike eller uventa sidestorleikar: {sorted(set(dimensions))}")
        width, height = dimensions[0]

        # Build the contact sheet at its delivery size, not as a giant
        # full-resolution intermediate containing every page.
        columns = min(pages, 4)
        rows = math.ceil(pages / columns)
        scale = min(2400 / (columns * width), 2400 / (rows * height), 1)
        thumb_width = max(1, int(width * scale))
        thumb_height = max(1, int(height * scale))
        contact = Image.new("RGB", (columns * thumb_width, rows * thumb_height), "white")
        gif_size = (gif_width, max(1, round(height * gif_width / width)))
        frames = []
        for index, file in enumerate(files):
            with Image.open(file) as image:
                grey = image.convert("L")
                contact.paste(grey.resize((thumb_width, thumb_height), Image.Resampling.LANCZOS),
                              ((index % columns) * thumb_width, (index // columns) * thumb_height))
                grey = grey.resize(gif_size, Image.Resampling.LANCZOS)
                frame = Image.frombytes("P", grey.size, grey.tobytes())
                frame.putpalette(_PALETTE)
                frames.append(frame)
        contact.save(stage / "kontaktark.png")
        durations = [page_ms] * pages
        durations[0] = durations[-1] = edge_ms
        gif = stage / "bla-gjennom.gif"
        frames[0].save(gif, save_all=True, append_images=frames[1:],
                       duration=durations, loop=0, disposal=2,
                       optimize=False, background=255)
        with Image.open(gif) as image:
            if image.n_frames != pages or image.size != gif_size:
                raise ValueError("GIF-en inneheld ikkje alle sidene i rett storleik")
            actual_durations = []
            for index in range(pages):
                image.seek(index)
                actual_durations.append(image.info.get("duration"))
            if actual_durations != durations:
                raise ValueError("GIF-en har uventa visingstider")

        metadata = {
            "pages": pages,
            "png": {"directory": "sider", "width": width, "height": height,
                    "files": [{"file": "sider/" + file.name, "sha256": _sha256(file)} for file in files]},
            "gif": {"file": gif.name, "frames": pages, "width": gif_size[0], "height": gif_size[1],
                    "duration_ms": durations, "total_duration_ms": sum(durations), "loop": 0,
                    "palette": "grayscale-256", "sha256": _sha256(gif)},
            "contact_sheet": {"file": "kontaktark.png", "width": contact.width, "height": contact.height,
                              "sha256": _sha256(stage / "kontaktark.png")},
            "validation": {"complete_page_sequence": True, "uniform_page_dimensions": True,
                           "gif_frame_count_and_timing": True},
        }
        _publish(stage, output, ("sider", "kontaktark.png", "bla-gjennom.gif"))
    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf")
    parser.add_argument("output")
    parser.add_argument("--pages", type=int, required=True)
    parser.add_argument("--page-width", type=int, default=1440)
    parser.add_argument("--gif-width", type=int, default=768)
    parser.add_argument("--page-ms", type=int, default=650)
    parser.add_argument("--edge-ms", type=int, default=1400)
    args = parser.parse_args()
    print(json.dumps(eksporter(args.pdf, args.output, args.pages, args.page_width,
                              args.gif_width, args.page_ms, args.edge_ms),
                     indent=2, ensure_ascii=False))
