import json
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = ROOT / "data" / "kaomoji.json"
DEFAULT_OUTPUT = ROOT / "kao" / "_data.py"
# gitignored: datasets whose license is not settled yet, built into kao/_data_local.py only
LOCAL_DIR = ROOT / "data" / "local"
LOCAL_OUTPUT = ROOT / "kao" / "_data_local.py"


PREPENDED_MARKS = set("\u0600\u0601\u0602\u0603\u0604\u0605\u06dd\u070f\u0890\u0891\u08e2\U000110bd\U000110cd")


def display_width(text):
    width = 0
    for ch in text:
        # marks, variation selectors and ZWJ occupy no cell; prepended concatenation marks (U+0600-0605...) do, as in wcwidth
        if unicodedata.category(ch) in ("Mn", "Me", "Cf") and ch not in PREPENDED_MARKS:
            continue
        if unicodedata.east_asian_width(ch) in ("W", "F"):
            width += 2
        else:
            width += 1
    return width


def is_emoji(ch):
    o = ord(ch)
    if o in (0xFE0F, 0x20E3) or 0x1F000 <= o <= 0x1FAFF:
        return True
    # wide symbols here default to emoji presentation (star, sparkles, coffee); narrow ones like heart suits stay
    return 0x2300 <= o <= 0x2BFF and unicodedata.east_asian_width(ch) == "W"


def reject_reason(text):
    import re

    if any(is_emoji(ch) for ch in text):
        return "emoji"
    if re.search("[\u3040-\u30ff\u4e00-\u9fff]{3,}", text):
        return "japanese phrase"
    for m in re.finditer("[A-Za-z]{4,}", text):
        if set(m.group().lower()) != {"z"}:
            return "latin word"
    return None


def _label(entry):
    if isinstance(entry, dict):
        text = entry.get("text", None)
        if isinstance(text, str) and text:
            return text
    return repr(entry)


def validate_entry(entry):
    if not isinstance(entry, dict):
        raise ValueError("entry is not an object: %r" % entry)
    text = entry.get("text", None)
    if not isinstance(text, str) or text == "":
        raise ValueError("empty text in entry %s" % _label(entry))
    if "\t" in text or "\n" in text or "\r" in text:
        raise ValueError("tab/newline in text of entry %s" % _label(entry))
    tags = entry.get("tags", None)
    if tags is None:
        raise ValueError("missing tags in entry %s" % _label(entry))
    if not isinstance(tags, list) or len(tags) == 0:
        raise ValueError("missing or empty tags in entry %s" % _label(entry))
    for tag in tags:
        if not isinstance(tag, str) or tag == "":
            raise ValueError("empty tag in entry %s" % _label(entry))
        if "\t" in tag or "\n" in tag or "\r" in tag:
            raise ValueError("tab/newline in tags of entry %s" % _label(entry))
    category = entry.get("category", None)
    if not isinstance(category, str) or category == "":
        raise ValueError("missing category in entry %s" % _label(entry))
    if any(c.isspace() for c in category):
        raise ValueError("invalid category in entry %s" % _label(entry))
    return entry


def validate(data):
    if not isinstance(data, list):
        raise ValueError("data is not a list")
    seen = set()
    for entry in data:
        validate_entry(entry)
        text = entry["text"]
        if text in seen:
            raise ValueError("duplicate text in entry %s" % text)
        seen.add(text)
    return data


def _read(path):
    with Path(path).open("r", encoding="utf-8") as f:
        return validate(json.load(f))


def merge(sources):
    # union by face text; the first source keeps its category
    by_text = {}
    for data in sources:
        for entry in data:
            known = by_text.get(entry["text"])
            if known is None:
                by_text[entry["text"]] = dict(entry, tags=list(entry["tags"]), source=list(entry.get("source", [])))
                continue
            known["tags"] += [t for t in entry["tags"] if t not in known["tags"]]
            known["source"] += [s for s in entry.get("source", []) if s not in known["source"]]
    return list(by_text.values())


def select(data, report=None):
    kept = []
    for entry in data:
        reason = reject_reason(entry["text"])
        if reason is None:
            kept.append(entry)
        elif report is not None:
            report[reason] = report.get(reason, 0) + 1
    return kept


def pack(data):
    from array import array

    categories = tuple(sorted({entry["category"] for entry in data}))
    if len(categories) > 255:
        raise ValueError("more than 255 categories")
    cat_index = {c: i for i, c in enumerate(categories)}
    words = sorted({t.lower() for entry in data for t in entry["tags"]})
    word_index = {w: i for i, w in enumerate(words)}
    word_post = [[] for _ in words]
    cat_post = [[] for _ in categories]
    faces = []
    tags = []
    offs = array("I")
    toffs = array("I")
    if offs.itemsize != 4:
        raise ValueError("array('I') is not 4 bytes on this platform")
    pos = tpos = 0
    for i, entry in enumerate(data):
        face = entry["text"].encode("utf-8")
        line = (" ".join(entry["tags"]) + "\t" + entry["category"]).lower().encode("utf-8")
        offs.append(pos)
        toffs.append(tpos)
        faces.append(face)
        tags.append(line)
        pos += len(face) + 1
        tpos += len(line) + 1
        for w in dict.fromkeys(t.lower() for t in entry["tags"]):
            word_post[word_index[w]].append(i)
        cat_post[cat_index[entry["category"]]].append(i)
    # one past the end, so entry i is always blob[offs[i]:offs[i+1] - 1]
    offs.append(pos)
    toffs.append(tpos)
    # inverted index: POST[WPOST[w]:WPOST[w+1]] are the entries tagged WORDS[w]; CPOST likewise per category
    post = array("I")
    wpost = array("I")
    cpost = array("I")
    for lists, starts in ((word_post, wpost), (cat_post, cpost)):
        for entries in lists:
            starts.append(len(post))
            post.extend(entries)
        starts.append(len(post))
    return {
        "FACES": b"\n".join(faces),
        "TAGS": b"\n".join(tags),
        "OFFS": offs.tobytes(),
        "TOFFS": toffs.tobytes(),
        "WIDTHS": bytes(min(display_width(e["text"]), 255) for e in data),
        "CATS": bytes(cat_index[e["category"]] for e in data),
        "CATEGORIES": categories,
        "COUNT": len(data),
        "WORDS": "\n".join(words).encode("utf-8"),
        "WPOST": wpost.tobytes(),
        "CPOST": cpost.tobytes(),
        "POST": post.tobytes(),
    }


def write(path, packed):
    lines = [
        "# GENERATED by tools/build_data.py - do not edit",
        "# FACES/TAGS/WORDS: newline-joined UTF-8; OFFS/TOFFS/WPOST/CPOST/POST: native uint32; WIDTHS/CATS: one byte per entry",
    ]
    for key in ("COUNT", "CATEGORIES", "WIDTHS", "CATS", "OFFS", "TOFFS", "WPOST", "CPOST", "POST", "WORDS", "TAGS", "FACES"):
        lines.append("%s = %r" % (key, packed[key]))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build(input_path=DEFAULT_INPUT, output_path=DEFAULT_OUTPUT, local_dir=None, local_output=None):
    committed = _read(input_path)
    report = {}
    kept = select(committed, report)
    write(output_path, pack(kept))
    print("%s: %d entries, dropped %r" % (Path(output_path).name, len(kept), report))
    if local_dir is None:
        return kept
    local_files = sorted(Path(local_dir).glob("*.json"))
    if not local_files:
        if local_output is not None and Path(local_output).exists():
            Path(local_output).unlink()
        return kept
    report = {}
    merged = select(merge([committed] + [_read(p) for p in local_files]), report)
    write(local_output, pack(merged))
    print("%s: %d entries from %s, dropped %r" % (
        Path(local_output).name, len(merged), ", ".join(p.name for p in local_files), report))
    return merged


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    try:
        if argv:
            # explicit paths build just that file (tests, one-off checks)
            build(Path(argv[0]), Path(argv[1]) if len(argv) > 1 else DEFAULT_OUTPUT)
        else:
            build(DEFAULT_INPUT, DEFAULT_OUTPUT, LOCAL_DIR, LOCAL_OUTPUT)
    except Exception as exc:  # noqa: BLE001
        print("build_data: %s" % exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
