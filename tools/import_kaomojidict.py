import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA = ROOT / "data" / "kaomoji.json"

# (category, keywords); first matching category in table order wins.
KEYWORD_TABLE = [
    ("angry", ["angry", "mad", "rage", "pissed", "furious", "triggered", "grr", "seethe", "frustrated", "irritated", "annoyed", "grumpy", "salty"]),
    ("sad", ["sad", "cry", "tears", "depressed", "despair", "sob", "weep", "sorrow", "disappointed", "upset"]),
    ("happy", ["happy", "joy", "yay", "woohoo", "smile", "cheer", "cheerful", "giggle", "excited", "yippee", "wheee", "laugh", "fun", "smiling", "wink", "playful"]),
    ("love", ["love", "kiss", "hug", "heart", "crush", "luv", "cuddle", "flirt", "mwah", "smitten", "sweet"]),
    ("shy", ["shy", "embarrassed", "blush", "bashful", "sheepish", "flustered"]),
    ("surprise", ["surprised", "shock", "yikes", "what", "amazed", "amazing", "mindblown", "startled", "gasp", "whoa", "wow", "omg"]),
    ("peek", ["peek", "lurking", "watching", "lurk", "lurker", "spy", "spying", "nosy", "observing", "sneaky", "stalk"]),
    ("tired", ["tired", "sleep", "sleepy", "exhausted", "burnout", "drowsy", "yawn", "zzz", "lazy"]),
    ("animal", ["cat", "dog", "bear", "kitty", "neko", "animal", "fox", "bunny", "puppy"]),
    ("action", ["fight", "run", "dance", "wave", "bow", "yeet", "flex", "highfive", "tableflip"]),
]

# Alternate shapes for compatibility.
KEYWORDS = [(kws, cat) for cat, kws in KEYWORD_TABLE]
CATEGORY_KEYWORDS = {cat: list(kws) for cat, kws in KEYWORD_TABLE}


def derive_category(tags):
    low = [str(t).lower() for t in tags]
    for category, keywords in KEYWORD_TABLE:
        for tag in low:
            if tag in keywords:
                return category
    return "misc"


category_for = derive_category
category_from_tags = derive_category
categorize = derive_category


def _ascii(s):
    return all(ord(c) < 128 for c in s)


def _tags_for(face_obj):
    tags = list(face_obj.get("en", []))
    for tag in face_obj.get("*", []):
        if isinstance(tag, str) and _ascii(tag):
            tags.append(tag)
    return sorted(set(str(t).lower() for t in tags))


def _load(path):
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def _dump(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def import_kaomojidict(upstream_path, data_path=DEFAULT_DATA):
    upstream_path = Path(upstream_path)
    data_path = Path(data_path)
    upstream = _load(upstream_path)
    faces = upstream.get("kaomoji", upstream)
    data = _load(data_path)
    by_text = {entry["text"]: entry for entry in data if isinstance(entry, dict)}
    for face, obj in faces.items():
        tags = _tags_for(obj)
        category = derive_category(tags)
        if face in by_text:
            entry = by_text[face]
            entry["tags"] = sorted(set(entry.get("tags", [])) | set(tags))
            # keep existing category
            if "category" not in entry or not entry["category"]:
                entry["category"] = category
            src = entry.setdefault("source", [])
            if "kaomojidict" not in src:
                src.append("kaomojidict")
        else:
            data.append({
                "text": face,
                "tags": tags,
                "category": category,
                "source": ["kaomojidict"],
            })
            by_text[face] = data[-1]
    _dump(data_path, data)
    return data


def merge(upstream_path, data_path=DEFAULT_DATA):
    return import_kaomojidict(upstream_path, data_path)


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        print("usage: import_kaomojidict.py <kaomoji.json> [data.json]", file=sys.stderr)
        return 2
    upstream = argv[0]
    data_path = argv[1] if len(argv) > 1 else DEFAULT_DATA
    try:
        import_kaomojidict(Path(upstream), Path(data_path))
    except Exception as exc:  # noqa: BLE001
        print("import_kaomojidict: %s" % exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
