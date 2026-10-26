import sys


def main(argv=None):
    import json

    from kao.db import load
    from kao.search import search

    db = load()
    out = sys.stdout
    try:
        for line in sys.stdin:
            matches = search(line.rstrip("\n"), db, limit=50)
            obj = [{"text": db.face(i), "tags": db.tags(i).split(), "category": db.category(i)} for i in matches]
            out.write(json.dumps(obj, ensure_ascii=False) + "\n")
            out.flush()
    except (BrokenPipeError, KeyboardInterrupt):
        # reader went away (Neovim closed the picker); exit quietly
        sys.stdout = None
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
