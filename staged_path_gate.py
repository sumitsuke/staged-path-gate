#!/usr/bin/env python3
"""staged_path_gate.py — 予定外のパスが stage に在れば commit を止める門（T38・「制限」の段）。状態ファイルを持たない。
使い方（毎回、予定を引数で渡す＝同じ作業コピーを共有する別セッションと予定が混ざらない）:
  python staged_path_gate.py --check docs/a.md src/x.js          予定＝ファイルの完全一致（既定）
  python staged_path_gate.py --check docs/a.md --dir generated/   --dir はディレクトリ配下を明示的に許す（同じフォルダの別ファイルも通る＝使うなら承知の上で）
終了コード: 0＝stage が全部予定内／1＝予定外が 1 本以上（一覧を出す）／2＝git が失敗（リポの外・git 無し）＝fail-closed
🔴 止めるのは「他方が先に stage した変更が自分の commit に乗る」こと。他方が同じファイルを上書きすることは止めない（そこは worktree の領域）。
pre-commit から呼ぶなら:  python staged_path_gate.py --check <自分の予定のパス…>
"""
import subprocess, sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # Windows の既定（cp932）では 🔴／✅ の表示で落ちて exit 1 になっていた（2026-09-26）


def git(*args):
    p = subprocess.run(["git", *args], capture_output=True)
    if p.returncode != 0:
        sys.stderr.write("🔴 git failed: " + " ".join(args) + ": " + p.stderr.decode("utf-8", "replace").strip() + "\n")
        sys.exit(2)
    return p.stdout


def norm(p):
    p = p.replace("\\", "/")
    while p.startswith("./"):  # 先頭の「./」だけを外す。lstrip("./") は「.」と「/」をすべて剥がし、.env を env、.config/ を config/ と同じに扱っていた（2026-09-26 外部精査）
        p = p[2:]
    return p


args = sys.argv[1:]
if "--check" not in args:
    print(__doc__); sys.exit(2)
files, dirs, mode = [], [], None
for a in args:
    if a == "--check": mode = "f"; continue
    if a == "--dir": mode = "d"; continue
    (files if mode == "f" else dirs).append(norm(a))
dirs = [d.rstrip("/") + "/" for d in dirs]
git("rev-parse", "--show-toplevel")
staged = [norm(p) for p in git("diff", "--cached", "--name-only", "-z").decode("utf-8", "replace").split("\0") if p]
unexpected = [p for p in staged if p not in files and not any(p.startswith(d) for d in dirs)]
if unexpected:
    print(f"🔴 予定外のパスが stage に {len(unexpected)} 本（予定 {len(files)} ファイル・{len(dirs)} ディレクトリ）")
    for p in unexpected: print("   ", p)
    print("   → 他方の変更なら `git restore --staged <path>`、自分の分なら --check に足す。commit は止める")
    sys.exit(1)
print(f"✅ stage {len(staged)} 本はすべて予定内（{files + dirs}）"); sys.exit(0)
