# staged-path-gate

**Two AI sessions on one working copy share the index, not just the files. "I only `git add`ed my file" is not safe: whatever the other session staged rides along. This repo holds the 30-second reproduction and a ~40-line gate that refuses a commit when the index contains paths you did not plan.**

Article: [2 つの AI セッションが同じ作業コピーを触ると、index まで共有される](https://sumitsuke.jp/lab/two-sessions-one-working-copy/) (Lab, Japanese).

## Reproduction (30 seconds)

```bash
python repro_shared_index.py 3      # throwaway repos; prints files_in_commit for both ways, 3 runs
```

Observed on git 2.53 (`repro_results.csv`), 3/3 identical:

| way | files in commit | still staged |
|---|---|---|
| `git add a.txt; git commit` | `a.txt;b.txt` (2) | — |
| `git commit --only -- a.txt` | `a.txt` (1) | `b.txt` |

`b.txt` was staged by "the other session" before you committed. Plain `git commit` takes the whole index; `--only` records just the paths you name and leaves the rest staged.

## The gate

```bash
python staged_path_gate.py --check docs/a.md src/x.js          # exact file paths (default)
python staged_path_gate.py --check docs/a.md --dir generated/   # --dir allows a directory explicitly
```

Exit 0 = everything staged is in your plan · 1 = unexpected staged paths (listed) · 2 = git failed (outside a repo, etc. — fail-closed).
No state file: you pass the plan on every call, so two sessions sharing one working copy cannot overwrite each other's plan. Call it from `pre-commit` with your own paths.

Poison tests (`gate_poison_log.txt`): planned file → 0 · other directory → 1 · **sibling in the same directory → 1** · `--dir` explicit → 0 · `.bak` next to the planned file → 1 · outside a repo → 2.

## What it does not do

It stops *staging spill-over* only. It cannot stop the other session from overwriting the same file — that is what `git worktree` is for (isolate first; restrict with `--only` and this gate when you cannot; audit with `git status -sb` / `git diff --cached --name-only`).

## License

MIT (`LICENSE`). `repro_results.csv` and `gate_poison_log.txt` are measurement artifacts (CC BY 4.0, credit Sumitsuke Lab).
