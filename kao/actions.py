def osc52(text):
    import binascii

    data = text.encode("utf-8")
    b64 = binascii.b2a_base64(data, newline=False)
    return b"\x1b]52;c;" + b64 + b"\a"


def tmux_wrap(seq):
    # DCS passthrough (needs allow-passthrough on); works when set-clipboard is external
    return b"\x1bPtmux;" + seq.replace(b"\x1b", b"\x1b\x1b") + b"\x1b\\"


def yank(text):
    import posix

    seq = osc52(text)
    if b"TMUX" in posix.environ:
        # wrapped only: a second, plain copy once left zsh stuck in a bracketed paste
        seq = tmux_wrap(seq)
    fd = None
    close = False
    try:
        fd = posix.open("/dev/tty", posix.O_WRONLY)
        close = True
    except OSError:
        fd = 2
        close = False
    try:
        posix.write(fd, seq)
    except OSError:
        return "could not write to tty"
    finally:
        if close and fd is not None:
            try:
                posix.close(fd)
            except OSError:
                pass
    return None
