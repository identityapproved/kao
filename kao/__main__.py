import sys


def _data():
    from kao import _data as data

    return data.DATA


def _print_tui_not_implemented():
    print("tui not implemented")


def cmd_list(argv):
    for entry in _data():
        print("%s\t%s\t%s" % (entry[2], entry[3], entry[0]))
    return 0


def cmd_random(argv):
    query = " ".join(argv)
    data = _data()
    if query:
        from kao.search import search

        matches = search(query, data)
    else:
        matches = data
    if not matches:
        return 1
    with open("/dev/urandom", "rb") as f:
        idx = int.from_bytes(f.read(4), "big") % len(matches)
    print(matches[idx][0])
    return 0


def cmd_json(argv):
    import json

    from kao.search import search

    query = " ".join(argv)
    matches = search(query, _data())
    out = [{"text": e[0], "tags": e[2].split(), "category": e[3]} for e in matches[:50]]
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
