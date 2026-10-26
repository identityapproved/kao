import sys


def run(argv, stdin_text=None):
    """Run a helper; return None on success or a one-line error message."""
    import subprocess

    try:
        # wl-copy forks a child that keeps inherited pipes open, so never capture output
        proc = subprocess.run(
            argv,
            input=stdin_text,
            text=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        return "%s: not found" % argv[0]
    if proc.returncode != 0:
        return "%s: failed (exit %d)" % (argv[0], proc.returncode)
    return None


def copy_cmd(text):
    return ["wl-copy"], text


def type_cmd(text):
    return ["wtype", "--", text], None


def _or_exit(err):
    if err:
        print(err, file=sys.stderr)
        raise SystemExit(1)


def copy(text):
    _or_exit(run(*copy_cmd(text)))


def type_text(text):
    _or_exit(run(*type_cmd(text)))
