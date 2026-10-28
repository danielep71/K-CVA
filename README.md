# traffic-history

Data-only branch of K-CVA. The **Traffic history** workflow on `main` merges
GitHub traffic (views and clones) into the CSV files under `data/` once a
day, keeping it beyond GitHub's 14-day window. Top referrers and popular
paths are no longer collected: this branch is as public as the repository.
Earlier commits still hold the referrers and paths collected before.

Do not merge this branch, base work on it or rewrite its history. The file
layout, the merge rules, the meaning of `0` and of a missing date, and the
recovery steps are in `docs/TRAFFIC.md` on `main`.

| File | Contents |
| --- | --- |
| `data/daily.csv` | Views and clones per UTC day |
| `data/snapshots.csv` | One row per collection day, with the 14-day totals |
