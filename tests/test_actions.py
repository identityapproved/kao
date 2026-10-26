import base64
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class TestActions(unittest.TestCase):
    def test_osc52_exact(self):
        from kao.actions import osc52

        self.assertEqual(osc52("(^_^)"), b"\x1b]52;c;KF5fXik=\x07")

    def test_nonascii_roundtrip(self):
        from kao.actions import osc52

        seq = osc52("(＾▽＾)")
        prefix = b"\x1b]52;c;"
        self.assertTrue(seq.startswith(prefix))
        self.assertTrue(seq.endswith(b"\a"))
        data = base64.b64decode(seq[len(prefix) : -1])
        self.assertEqual(data.decode("utf-8"), "(＾▽＾)")

    def test_tmux_wrap(self):
        from kao.actions import osc52, tmux_wrap

        self.assertEqual(
            tmux_wrap(osc52("(^_^)")),
            b"\x1bPtmux;\x1b\x1b]52;c;KF5fXik=\x07\x1b\\",
        )

    def test_no_subprocess_import(self):
        code = "import sys; sys.path.insert(0, %r); import kao.actions; print('subprocess' in sys.modules)" % str(ROOT)
        proc = subprocess.run(
            [sys.executable, "-I", "-S", "-c", code],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), "False")


if __name__ == "__main__":
    unittest.main()
