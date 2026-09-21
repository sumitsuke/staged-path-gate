#!/usr/bin/env python3
"""repro_shared_index.py — 最小再現（T38・H3）。同じ作業コピーでは index も共有される:
他方が先に `git add b.txt` した状態で、当方が `git add a.txt; git commit` すると b.txt も commit に乗る。
`git commit --only -- a.txt` なら乗らない（b.txt は stage に残る）。捨てリポで N 回回して files changed を数える。
python repro_shared_index.py [N]   → repro_results.csv（1 行＝1 回 × 2 通り）
"""
import csv, io, os, shutil, subprocess, sys, tempfile

N = int(sys.argv[1]) if len(sys.argv) > 1 else 3


def git(cwd, *args):
    p = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def setup():
    d = tempfile.mkdtemp(prefix="t38_")
    git(d, "init", "-q"); git(d, "config", "user.email", "t@example"); git(d, "config", "user.name", "t")
    git(d, "config", "core.autocrlf", "false")
    for f in ("a.txt", "b.txt"):
        io.open(os.path.join(d, f), "w").write("base\n")
    git(d, "add", "-A"); git(d, "commit", "-qm", "init")
    # 「他方」が b.txt を変えて stage だけしておく／「当方」は a.txt を変える（未 stage）
    io.open(os.path.join(d, "b.txt"), "w").write("other session\n"); git(d, "add", "b.txt")
    io.open(os.path.join(d, "a.txt"), "w").write("my session\n")
    return d


def files_changed(d):
    rc, out, _ = git(d, "show", "--stat", "--format=", "HEAD")
    names = [ln.split("|")[0].strip() for ln in out.splitlines() if "|" in ln]
    return names


rows = []
for i in range(1, N + 1):
    # 通り 1: git add a.txt; git commit
    d = setup(); git(d, "add", "a.txt"); git(d, "commit", "-qm", "mine")
    rows.append({"run": i, "way": "git add a.txt; git commit", "files_in_commit": ";".join(files_changed(d)),
                 "n_files": len(files_changed(d)), "still_staged": git(d, "diff", "--cached", "--name-only")[1]})
    shutil.rmtree(d, ignore_errors=True)
    # 通り 2: git commit --only -- a.txt（a.txt は未 stage のまま）
    d = setup(); git(d, "commit", "-q", "--only", "-m", "mine", "--", "a.txt")
    rows.append({"run": i, "way": "git commit --only -- a.txt", "files_in_commit": ";".join(files_changed(d)),
                 "n_files": len(files_changed(d)), "still_staged": git(d, "diff", "--cached", "--name-only")[1]})
    shutil.rmtree(d, ignore_errors=True)

here = os.path.dirname(os.path.abspath(__file__))
with io.open(os.path.join(here, "repro_results.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print("git", git(".", "--version")[1])
for r in rows:
    print(f"run {r['run']}  {r['way']:<28} files_in_commit={r['files_in_commit']:<12} n={r['n_files']}  still_staged={r['still_staged'] or '-'}")
