#!/usr/bin/env python
"""Run an agy (Antigravity CLI / Gemini) review non-interactively and capture it.

Gives agy a REAL ConPTY with explicit non-zero size (via pywinpty), so it does not
hang or hit the winpty cols=0 assertion. stdout is captured, ANSI-stripped, and
written to an output file -> headless, background, auto-recorded review.

Usage:
  python agy_review.py <prompt_file> <out_file> [model] [print_timeout] [--add-dir DIR ...]
"""
import sys, time, re, shlex
from winpty import PtyProcess

ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b[\(\)][0-9A-Za-z]|\x1b[=>]|[\x00-\x08\x0b\x0c\x0e-\x1f]")

def strip(s):
    return ANSI.sub("", s)

def main():
    # Parse --add-dir pairs from anywhere in argv first, so the positional
    # args (prompt_file, out_file, model, print_timeout) keep their defaults
    # even when --add-dir is supplied without explicit model/timeout.
    argv = sys.argv[1:]
    add_dirs = []
    pos = []
    i = 0
    while i < len(argv):
        if argv[i] == "--add-dir" and i + 1 < len(argv):
            add_dirs.append(argv[i + 1]); i += 2
        else:
            pos.append(argv[i]); i += 1

    prompt_file = pos[0]
    out_file = pos[1]
    model = pos[2] if len(pos) > 2 else "Gemini 3.1 Pro (High)"
    ptimeout = pos[3] if len(pos) > 3 else "5m"

    with open(prompt_file, "r", encoding="utf-8") as f:
        prompt = f.read()

    args = ["agy", "--print-timeout", ptimeout, "--model", model]
    for d in add_dirs:
        args += ["--add-dir", d]
    args += ["-p", prompt]
    cmd = " ".join(shlex.quote(a) for a in args)

    proc = PtyProcess.spawn(cmd, dimensions=(50, 200))
    buf = []
    wall_deadline = time.time() + 360  # hard cap independent of agy's own timeout
    last = time.time()
    while True:
        if time.time() > wall_deadline:
            buf.append("\n[WALL-TIMEOUT]"); break
        try:
            data = proc.read(8192)
        except EOFError:
            break
        if data:
            buf.append(data); last = time.time()
        else:
            if not proc.isalive():
                break
            time.sleep(0.2)

    clean = strip("".join(buf))
    # collapse the leading control noise / blank lines
    clean = "\n".join(line.rstrip() for line in clean.splitlines())
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(clean)
    print("WROTE %d chars -> %s (alive=%s)" % (len(clean), out_file, proc.isalive()))
    try:
        proc.close()
    except Exception:
        pass

if __name__ == "__main__":
    main()
