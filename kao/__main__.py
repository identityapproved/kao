import sys


def _db():
    from kao.db import load

    return load()


def cmd_list(argv):
    db = _db()
    # whole blobs at once: one decode and split instead of per-entry slices
    faces = db.faces.split(b"\n")
    lines = db.tag_lines.split(b"\n")
    try:
        sys.stdout.flush()
        sys.stdout.buffer.write(b"".join([lines[i] + b"\t" + faces[i] + b"\n" for i in range(db.count)]))
        sys.stdout.buffer.flush()
    except BrokenPipeError:
        # e.g. `kao list | head`
        sys.stdout = None
    return 0


def cmd_random(argv):
    query = " ".join(argv)
    db = _db()
    if query:
        from kao.search import search

        matches = search(query, db)
    else:
        matches = range(db.count)
    if not matches:
        return 1
    with open("/dev/urandom", "rb") as f:
        idx = int.from_bytes(f.read(4), "big") % len(matches)
    print(db.face(matches[idx]))
    return 0


def cmd_json(argv):
    import json

    from kao.search import search

    query = " ".join(argv)
    db = _db()
    matches = search(query, db, limit=50)
    out = [{"text": db.face(i), "tags": db.tags(i).split(), "category": db.category(i)} for i in matches]
    print(json.dumps(out))
    return 0


def cmd_help():
    print("usage: kao [command|query]")
    print("commands:")
    print("  list              list all kaomoji")
    print("  --random [query]  print one random matching face")
    print("  --json [query]    print JSON array of matches")
    print("  --help            show this help")
    print("  --version         show version")
    return 0


def cmd_version():
    print("kao 0.1.0")
    return 0


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        from kao.tui import run

        return run("")

    head = argv[0]
    rest = argv[1:]

    if head in ("-h", "--help"):
        return cmd_help()
    if head == "--version":
        return cmd_version()
    if head == "list":
        if rest:
            print("kao: unexpected argument for list", file=sys.stderr)
            return 2
        return cmd_list(rest)
    if head == "--random":
        return cmd_random(rest)
    if head == "--json":
        return cmd_json(rest)
    if head == "--serve":
        from kao.serve import main

        return main(rest)

    if head.startswith("-"):
        print("kao: unknown option %s" % head, file=sys.stderr)
        return 2

    from kao.tui import run

    return run(" ".join(argv))


if __name__ == "__main__":
    raise SystemExit(main())
