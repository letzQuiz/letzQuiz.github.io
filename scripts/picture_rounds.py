#!/usr/bin/env python3
"""Printable picture rounds for the pub quiz.

Name every image after its answer (e.g. `kimi-antonelli.jpg`, or
`03-kimi-antonelli.jpg`: a leading number is ignored). That name is printed
on the answer key. Each command writes two A4 PDFs in the current folder:
OUT.pdf to hand to the teams and OUT-answers.pdf for the quizmaster.
Images are shuffled, so the file order gives nothing away; pass the same
--seed to get the exact same puzzle again.

  scramble    cut each picture into a grid, shuffle the tiles (--rotate: also spin them)
  split       left half of one picture + right half of the next (give images in pairs)
  blend       two pictures superimposed 50/50 (give images in pairs)
  pixelate    three sheets, from blocky to sharp: hand them out one by one (3-2-1 points)
  zoom        an extreme close-up of one detail
  recolor     "wrong colour" logos: hue turned by 180 degrees (--invert for a negative)
  silhouette  black shape only: logos, landmarks, F1 circuits, countries
  gray        black and white: flags without their colours
  sheet       blank team answer sheet, e.g. for the fact-or-fake betting round

Examples:
  python3 scripts/picture_rounds.py scramble faces/ --grid 4 --out scrambled
  python3 scripts/picture_rounds.py split a.jpg b.jpg c.jpg d.jpg --out two-face
  python3 scripts/picture_rounds.py pixelate albums/ --levels 6,12,28 --out pixels
  python3 scripts/picture_rounds.py sheet --title "Fact or Fake?" --rows 12 \\
      --columns "FACT|FAKE" "Bet:1|2|3" --out fact-or-fake

Needs Pillow: pip install pillow
"""
import argparse
import random
import re
import sys
from pathlib import Path

try:
    from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps, ImageStat
except ImportError:
    sys.exit("This script needs Pillow: pip install pillow")

DPI = 150
PAGE = (round(8.27 * DPI), round(11.69 * DPI))  # A4 portrait
MARGIN = 70
GUTTER = 36
GRIDS = {1: (1, 1), 2: (1, 2), 4: (2, 2), 6: (2, 3), 8: (2, 4),
         9: (3, 3), 12: (3, 4), 16: (4, 4), 20: (4, 5)}
IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tif", ".tiff"}
WORK_SIZE = 900  # long side, in pixels, of every generated picture
FONTS = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]
GREY = (150, 150, 150)
LIGHT = (205, 205, 205)


# ---------------------------------------------------------------- helpers

def font(size):
    for path in FONTS:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # Pillow < 10.1
        return ImageFont.load_default()


def collect(paths):
    """Expand folders into the images they contain."""
    files = []
    for path in paths:
        if path.is_dir():
            files += sorted(p for p in path.iterdir() if p.suffix.lower() in IMAGE_TYPES)
        elif path.is_file():
            files.append(path)
        else:
            sys.exit(f"Not found: {path}")
    if not files:
        sys.exit("No images given.")
    return files


def answer_for(path):
    name = re.sub(r"^\d+[\s._-]*", "", path.stem)
    name = re.sub(r"[_-]+", " ", name).strip() or path.stem
    return name.title() if name.islower() else name


def load(path):
    """Open an image, honour its EXIF rotation and flatten it onto white."""
    img = ImageOps.exif_transpose(Image.open(path))
    if img.mode in ("RGBA", "LA", "PA") or "transparency" in img.info:
        rgba = img.convert("RGBA")
        flat = Image.new("RGB", rgba.size, "white")
        flat.paste(rgba, mask=rgba.getchannel("A"))
        return flat, rgba.getchannel("A")
    return img.convert("RGB"), None


def shrink(img, long_side=WORK_SIZE):
    img = img.copy()
    img.thumbnail((long_side, long_side), Image.Resampling.LANCZOS)
    return img


def derangement(n, rng):
    """A shuffle in which no tile stays where it was."""
    order = list(range(n))
    if n < 2:
        return order
    while True:
        rng.shuffle(order)
        if all(i != v for i, v in enumerate(order)):
            return order


def border_colour(img):
    w, h = img.size
    strips = [img.crop((0, 0, w, 2)), img.crop((0, h - 2, w, h)),
              img.crop((0, 0, 2, h)), img.crop((w - 2, 0, w, h))]
    medians = [ImageStat.Stat(s).median for s in strips]
    return tuple(sorted(m[c] for m in medians)[1] for c in range(3))


# ---------------------------------------------------------- transformations

def scramble(img, grid, rotate, rng, gap=8):
    cols, rows = grid
    img = shrink(img)
    tile = min(img.width // cols, img.height // rows)
    img = ImageOps.fit(img, (tile * cols, tile * rows), centering=(0.5, 0.35))
    tiles = [img.crop((c * tile, r * tile, (c + 1) * tile, (r + 1) * tile))
             for r in range(rows) for c in range(cols)]
    spins = [None, Image.Transpose.ROTATE_90, Image.Transpose.ROTATE_180,
             Image.Transpose.ROTATE_270]
    out = Image.new("RGB", (cols * tile + (cols - 1) * gap,
                            rows * tile + (rows - 1) * gap), "white")
    for slot, source in enumerate(derangement(len(tiles), rng)):
        piece = tiles[source]
        spin = rng.choice(spins) if rotate else None
        if spin is not None:
            piece = piece.transpose(spin)
        r, c = divmod(slot, cols)
        out.paste(piece, (c * (tile + gap), r * (tile + gap)))
    return out


def same_size(a, b, size=(600, 800)):
    return (ImageOps.fit(a, size, centering=(0.5, 0.35)),
            ImageOps.fit(b, size, centering=(0.5, 0.35)))


def split(a, b):
    a, b = same_size(a, b)
    half = a.width // 2
    out = a.copy()
    out.paste(b.crop((half, 0, b.width, b.height)), (half, 0))
    return out


def blend(a, b):
    a, b = same_size(a, b)
    return Image.blend(a, b, 0.5)


def pixelate(img, blocks):
    img = shrink(img)
    w, h = img.size
    small = img.resize((blocks, max(1, round(blocks * h / w))), Image.Resampling.BOX)
    return small.resize((w, h), Image.Resampling.NEAREST)


def zoom(img, fraction, rng):
    side = max(8, int(min(img.size) * fraction))
    cx = rng.uniform(0.3, 0.7) * img.width
    cy = rng.uniform(0.3, 0.7) * img.height
    left = int(min(max(cx - side / 2, 0), img.width - side))
    top = int(min(max(cy - side / 2, 0), img.height - side))
    crop = img.crop((left, top, left + side, top + side))
    return crop.resize((WORK_SIZE, WORK_SIZE), Image.Resampling.LANCZOS)


def recolor(img, invert):
    img = shrink(img)
    if invert:
        return ImageOps.invert(img)
    hue, sat, val = img.convert("HSV").split()
    hue = hue.point(lambda x: (x + 128) % 256)
    return Image.merge("HSV", (hue, sat, val)).convert("RGB")


def silhouette(img, alpha, tolerance):
    img = shrink(img)
    if alpha is not None:
        alpha = alpha.resize(img.size)
        mask = alpha.point(lambda a: 255 if a > 128 else 0)
    else:
        diff = ImageChops.difference(img, Image.new("RGB", img.size, border_colour(img)))
        r, g, b = diff.split()
        strongest = ImageChops.lighter(ImageChops.lighter(r, g), b)
        mask = strongest.point(lambda d: 255 if d > tolerance else 0)
    out = Image.new("RGB", img.size, "white")
    out.paste((0, 0, 0), (0, 0, *img.size), mask)
    return out


def gray(img):
    return ImageOps.grayscale(shrink(img)).convert("RGB")


# ------------------------------------------------------------------ layout

def new_page(title, subtitle, team_box=True):
    page = Image.new("RGB", PAGE, "white")
    draw = ImageDraw.Draw(page)
    draw.text((MARGIN, MARGIN), title, fill="black", font=font(54))
    if subtitle:
        draw.text((MARGIN, MARGIN + 70), subtitle, fill=GREY, font=font(30))
    if team_box:
        label = "Team: ____________________"
        f = font(30)
        width = draw.textlength(label, font=f)
        draw.text((PAGE[0] - MARGIN - width, MARGIN + 18), label, fill="black", font=f)
    return page, draw, MARGIN + 130


def fit_into(img, box_w, box_h):
    scale = min(box_w / img.width, box_h / img.height)
    size = (max(1, int(img.width * scale)), max(1, int(img.height * scale)))
    return img.resize(size, Image.Resampling.LANCZOS)


def wrap(draw, text, f, width):
    words, lines, line = text.split(), [], ""
    for word in words:
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=f) <= width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    return lines + ([line] if line else [])


def render(items, title, subtitle, per_page, team_box=True):
    """items: (number, image, caption or None). Returns a list of pages."""
    cols, rows = GRIDS[per_page]
    pages = []
    for start in range(0, len(items), per_page):
        page, draw, top = new_page(title, subtitle, team_box)
        cell_w = (PAGE[0] - 2 * MARGIN - (cols - 1) * GUTTER) / cols
        cell_h = (PAGE[1] - top - MARGIN - (rows - 1) * GUTTER) / rows
        label_font = font(max(26, min(44, int(cell_h / 9))))
        caption_font = font(max(20, min(30, int(cell_h / 14))))
        for i, (number, img, caption) in enumerate(items[start:start + per_page]):
            r, c = divmod(i, cols)
            x = MARGIN + c * (cell_w + GUTTER)
            y = top + r * (cell_h + GUTTER)
            label_h = label_font.size + 10
            caption_lines = wrap(draw, caption, caption_font, cell_w) if caption else []
            caption_h = len(caption_lines) * (caption_font.size + 6)
            pic = fit_into(img, cell_w, cell_h - label_h - caption_h - 8)
            px = int(x + (cell_w - pic.width) / 2)
            py = int(y + label_h)
            draw.text((x, y), f"{number}.", fill="black", font=label_font)
            page.paste(pic, (px, py))
            draw.rectangle((px - 1, py - 1, px + pic.width, py + pic.height), outline=LIGHT, width=2)
            for k, line in enumerate(caption_lines):
                draw.text((x, py + pic.height + 8 + k * (caption_font.size + 6)),
                          line, fill="black", font=caption_font)
        pages.append(page)
    return pages


def save(pages, path):
    pages[0].save(path, save_all=True, append_images=pages[1:], resolution=DPI)
    print(f"wrote {path} ({len(pages)} page{'s' if len(pages) != 1 else ''})")


def answer_sheet(title, rows, columns, out, note=None, box=None, box_lines=4):
    page, draw, top = new_page(title, note)
    box_h = (60 + box_lines * 70) if box else 0
    specs = []
    for spec in columns:
        header, _, options = spec.partition(":") if ":" in spec else ("", "", spec)
        options = [o.strip() for o in options.split("|")] if "|" in options else []
        header = header or (" / ".join(options) if options else spec)
        specs.append((header.strip(), options))
    weights = [3 if not opts else 1 + len(opts) * 0.4 for _, opts in specs]
    widths = [(PAGE[0] - 2 * MARGIN - 80) * w / sum(weights) for w in weights]
    row_h = min(100, (PAGE[1] - top - MARGIN - 50 - box_h) / rows)
    head_f, cell_f, num_f = font(28), font(max(20, int(row_h * 0.38))), font(max(22, int(row_h * 0.4)))
    x = MARGIN + 80
    for (header, _), width in zip(specs, widths):
        draw.text((x + 10, top), header, fill="black", font=head_f)
        x += width
    y0 = top + 50
    for r in range(rows):
        y = y0 + r * row_h
        draw.line((MARGIN, y, PAGE[0] - MARGIN, y), fill=LIGHT, width=2)
        draw.text((MARGIN, y + (row_h - num_f.size) / 2), f"{r + 1}.", fill="black", font=num_f)
        x = MARGIN + 80
        for (_, options), width in zip(specs, widths):
            draw.line((x, y, x, y + row_h), fill=LIGHT, width=2)
            if options:
                gap = width / len(options)
                for k, opt in enumerate(options):
                    tw = draw.textlength(opt, font=cell_f)
                    draw.text((x + gap * k + (gap - tw) / 2, y + (row_h - cell_f.size) / 2),
                              opt, fill=GREY, font=cell_f)
            x += width
    bottom = y0 + rows * row_h
    draw.line((MARGIN, bottom, PAGE[0] - MARGIN, bottom), fill=LIGHT, width=2)
    if box:
        y = bottom + 40
        draw.text((MARGIN, y), box, fill="black", font=head_f)
        for k in range(box_lines):
            line_y = y + 50 + (k + 1) * 70 - 10
            draw.line((MARGIN, line_y, PAGE[0] - MARGIN, line_y), fill=LIGHT, width=2)
    save([page], f"{out}.pdf")


# --------------------------------------------------------------------- CLI

def main():
    parser = argparse.ArgumentParser(
        description=__doc__.split("\n\n")[0],
        epilog=__doc__.split("\n\n", 1)[1],
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("images", nargs="+", type=Path, help="image files or folders")
    common.add_argument("--out", help="output name, without .pdf (default: the command)")
    common.add_argument("--title", help="title printed on every sheet")
    common.add_argument("--per-page", type=int, choices=sorted(GRIDS), help="pictures per A4 sheet")
    common.add_argument("--seed", type=int, help="reuse a seed to get the same puzzle again")
    common.add_argument("--keep-order", action="store_true", help="don't shuffle the pictures")

    p = sub.add_parser("scramble", parents=[common], help="shuffle the tiles of each picture")
    p.add_argument("--grid", default="4", help="tiles per side, e.g. 3, 4 or 4x5 (cols x rows)")
    p.add_argument("--rotate", action="store_true", help="also rotate tiles (hard mode)")
    sub.add_parser("split", parents=[common], help="left half of A + right half of B")
    sub.add_parser("blend", parents=[common], help="A and B superimposed")
    p = sub.add_parser("pixelate", parents=[common], help="three sheets, blocky to sharp")
    p.add_argument("--levels", default="8,16,32", help="blocks across the width, per sheet")
    p = sub.add_parser("zoom", parents=[common], help="extreme close-up of a detail")
    p.add_argument("--fraction", type=float, default=0.18, help="share of the picture kept (0-1)")
    p = sub.add_parser("recolor", parents=[common], help="wrong-colour logos")
    p.add_argument("--invert", action="store_true", help="negative instead of hue turn")
    p = sub.add_parser("silhouette", parents=[common], help="black shape only")
    p.add_argument("--tolerance", type=int, default=60,
                   help="how different from the background a pixel must be (0-255)")
    sub.add_parser("gray", parents=[common], help="black-and-white pictures")
    p = sub.add_parser("sheet", help="blank team answer sheet")
    p.add_argument("--title", default="Answers")
    p.add_argument("--rows", type=int, default=10)
    p.add_argument("--columns", nargs="+", default=["Answer"],
                   help='column headers; "Header:A|B|C" prints choices to circle')
    p.add_argument("--note", help="small line under the title, e.g. the scoring rules")
    p.add_argument("--box", help="title of a free-writing box under the table")
    p.add_argument("--box-lines", type=int, default=4)
    p.add_argument("--out", default="answer-sheet")

    args = parser.parse_args()
    if args.command == "sheet":
        answer_sheet(args.title, args.rows, args.columns, args.out,
                     args.note, args.box, args.box_lines)
        return

    seed = args.seed if args.seed is not None else random.randrange(10_000)
    rng = random.Random(seed)
    files = collect(args.images)
    out = args.out or args.command
    titles = {"scramble": "Scrambled", "split": "Two-Face", "blend": "Double Vision",
              "pixelate": "Pixel Countdown", "zoom": "Zoom In", "recolor": "Wrong Colours",
              "silhouette": "Silhouettes", "gray": "Fifty Shades of Grey"}
    title = args.title or titles[args.command]

    if args.command in ("split", "blend"):
        if len(files) % 2:
            sys.exit(f"{args.command} needs images in pairs; got {len(files)}.")
        groups = [files[i:i + 2] for i in range(0, len(files), 2)]
    else:
        groups = [[f] for f in files]
    if not args.keep_order:
        rng.shuffle(groups)

    puzzles, keys = [], []
    for n, group in enumerate(groups, 1):
        loaded = [load(f) for f in group]
        answer = " / ".join(answer_for(f) for f in group)
        img, alpha = loaded[0]
        if args.command == "scramble":
            cols, _, rows = args.grid.lower().partition("x")
            grid = (int(cols), int(rows or cols))
            puzzle = scramble(img, grid, args.rotate, rng)
        elif args.command == "split":
            puzzle = split(img, loaded[1][0])
        elif args.command == "blend":
            puzzle = blend(img, loaded[1][0])
        elif args.command == "pixelate":
            levels = [int(x) for x in args.levels.split(",")]
            puzzle = [pixelate(img, b) for b in levels]
        elif args.command == "zoom":
            puzzle = zoom(img, args.fraction, rng)
        elif args.command == "recolor":
            puzzle = recolor(img, args.invert)
        elif args.command == "silhouette":
            puzzle = silhouette(img, alpha, args.tolerance)
        else:
            puzzle = gray(img)
        puzzles.append((n, puzzle))
        reference = puzzle if args.command in ("split", "blend") else shrink(img, 500)
        keys.append((n, reference, answer))

    per_page = args.per_page or (4 if args.command in ("scramble", "split", "blend") else 6)
    if args.command == "pixelate":
        pages = []
        points = len(levels)
        for level in range(len(levels)):
            subtitle = (f"Sheet {level + 1} of {len(levels)} - "
                        f"{points - level} point{'s' if points - level != 1 else ''} if you get it now")
            pages += render([(n, imgs[level], None) for n, imgs in puzzles],
                            title, subtitle, per_page)
    else:
        pages = render([(n, img, None) for n, img in puzzles], title, None, per_page)
    save(pages, f"{out}.pdf")
    save(render(keys, f"{title} - answers", f"seed {seed}", 12, team_box=False),
         f"{out}-answers.pdf")
    print(f"seed {seed} (pass --seed {seed} to regenerate the same puzzle)")


if __name__ == "__main__":
    main()
