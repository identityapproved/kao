import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from import_kaomojidict import derive_category  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = Path.home() / "downloads" / "kaomojis-gboard.txt"
# license unknown: stays in the gitignored data/local/ until it is settled
DEFAULT_OUTPUT = ROOT / "data" / "local" / "gboard.json"
NOISE = {"kaomoji", "kaomojis"}


def tags_for(label):
    words = label.lower().split()
    tags = [w for w in words if w not in NOISE]
    return tags or words


def read_tsv(path):
    entries = []
    seen = set()
    with Path(path).open("r", encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            line = line.rstrip("\r\n")
            if not line:
                continue
            label, sep, face = line.partition("\t")
            if not sep or not face.strip() or not label.strip() or "\t" in face:
                raise ValueError("%s:%d: expected 'label<TAB>face'" % (path, n))
            if face in seen:
                continue
            seen.add(face)
            tags = tags_for(label)
            entries.append({"text": face, "tags": tags, "category": derive_category(tags), "source": ["gboard"]})
    return entries


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    src = Path(argv[0]) if argv else DEFAULT_INPUT
    out = Path(argv[1]) if len(argv) > 1 else DEFAULT_OUTPUT
    try:
        entries = read_tsv(src)
    except (OSError, ValueError) as exc:
        print("import_gboard: %s" % exc, file=sys.stderr)
        return 1
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("%s: %d entries" % (out, len(entries)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
