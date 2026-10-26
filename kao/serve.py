import sys


def main(argv=None):
    import json

    from kao import _data
    from kao.search import search

    data = _data.DATA
    out = sys.stdout
    try:
        for line in sys.stdin:
            matches = search(line.rstrip("\n"), data, limit=50)
            obj = [{"text": e[0], "tags": e[2].split(), "category": e[3]} for e in matches]
            out.write(json.dumps(obj, ensure_ascii=False) + "\n")
            out.flush()
    except (BrokenPipeError, KeyboardInterrupt):
        # reader went away (Neovim closed the picker); exit quietly
        sys.stdout = None
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
