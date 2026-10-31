# Repository traffic history

GitHub keeps repository traffic for 14 days. The **Traffic history** workflow
([.github/workflows/traffic-history.yml](../.github/workflows/traffic-history.yml))
collects views and clones once a day and merges them into CSV files on the
data-only `traffic-history` branch, so the history outlives that window. It
does not collect top referrers or popular paths ([visibility](#visibility)).
It is repository analytics, not CI: it builds and tests nothing (#14).

## Schedule

The workflow is scheduled daily at **06:17 UTC** and can be started from
**Actions → Traffic history → Run workflow** on `main`. GitHub runs scheduled
workflows only from the default branch, and may start them late; each
collection records the time it was actually taken. A manual run on any other
branch is skipped.

## Credential setup and renewal

The traffic API needs **Administration: read** on the repository, which the
workflow token cannot have. A GitHub App that you own, installed on this
repository only and holding that single permission, provides it. Each run mints
an installation token from the App's private key: limited to this repository
and to Administration: read, valid for one hour, and revoked when the job ends.
No long-lived token is stored.

1. **Settings → Environments → New environment** `analytics`. Under
   *Deployment branches and tags*, select *Selected branches and tags* and
   allow `main` only. Do this before adding the secret: a run that names a
   missing environment creates it without that restriction.
2. **Settings → Developer settings → GitHub Apps → New GitHub App**:
   - a name, for example `K-CVA traffic`, and the repository URL as homepage;
   - **Webhook**: clear *Active*;
   - **Repository permissions**: **Administration: Read-only**, nothing else
     (*Metadata: Read-only* is added by GitHub);
   - **Where can this GitHub App be installed?** *Only on this account*.
3. On the App's page, note its **Client ID**, then **Generate a private key**;
   a `.pem` file downloads.
4. **Install App** → your account → *Only select repositories*: `K-CVA`.
5. In the `analytics` environment, add the variable **TRAFFIC_APP_CLIENT_ID**
   with the client ID, and the secret **TRAFFIC_APP_PRIVATE_KEY** with the whole
   content of the `.pem` file. Then delete the `.pem` file. Never put the key
   in a file in the repository, an issue, a comment or a chat.
6. Run the workflow manually on `main` and check that it passes and that
   `traffic-history` gains a commit.

**Key rotation:** the key does not expire. Generate a new key on the App's
page, replace the secret, run step 6, then delete the old key there. Do this
at once if the key may have been exposed, or if the workflow is changed by
anyone but the maintainer. Collections missed while the App cannot be used are
lost once they fall outside the 14-day window.

Only the token step receives the private key, and only the fetch step, which
runs `curl` and no repository code, receives the installation token. The merge
script runs without either, and the push uses the workflow token with
`contents: write`.

## Stored data

The `traffic-history` branch holds `README.md` and these files under `data/`.
It is created once as an orphan commit, with the files below empty apart from
their headers (`python tools/traffic_history.py init --data data`), so it has
no history in common with `main`. It is never merged into `main` or a release
branch, and its history is not rewritten. Its creation commit is recorded in
#14.

| File | Key | Contents |
| --- | --- | --- |
| `daily.csv` | `date` | Views and unique views, clones and unique clones per UTC day. `views_collected_at` and `clones_collected_at` give the collection that last changed each pair. |
| `snapshots.csv` | `snapshot_date` | One row per collection day: the first and last day the API reported, the 14-day totals, `collected_at`, the collection that last changed that day's snapshot, and `observed_at`, the latest collection of that day, changed or not. |

The first collections, from 2026-10-27, also stored `referrers.csv` and
`paths.csv`, the top 10 referrers and paths of each collection. Collecting
them stopped once the repository was public (#14, #108); the commit that
removed both files from the branch is recorded in #14. Earlier commits still
hold them, since the branch's history is never rewritten.

### Merge rules

`tools/traffic_history.py` merges each collection idempotently:

- **Overlapping windows:** for every date the collection reports, its values
  replace the stored ones. The newest collection wins, so a day that was
  incomplete when first collected is corrected later. Views and clones are
  merged separately, each with its own collection time, which stays unchanged
  when its values do not change.
- **Older history:** dates the collection does not report keep their values.
  Nothing is deleted.
- **No double counting:** values are replaced, never added. Unique counts are
  never summed across days or windows; a 14-day unique count is only in
  `snapshots.csv`.
- **Same-day runs:** a second collection on the same UTC day replaces that
  day's snapshot only if one of its values changed; otherwise it moves only
  the snapshot's `observed_at`. Merging the same collection again changes
  nothing.
- **Order:** "newest" means the latest collection time. Merging an older
  collection after a newer one, when a saved collection is replayed or a run
  is rebuilt on a newer branch tip, never replaces what the newer one stored;
  it can only fill a date or metric that nothing newer reported. For the
  snapshot, a collection older than the day's `observed_at` is ignored, even
  if its totals differ. For the daily counts, the stored time is that of the
  collection that last *changed* them; a day's counts only grow until the day
  ends, so an older collection replayed later cannot hold different values.

### Zero or unavailable

The API reports each day of its window, days without activity included, as
`0`. So:

- **`0`**: the day was collected and had no activity;
- **no row**: no collection covered the day, either because it is before
  tracking began or because collections stopped for more than 14 days;
- **a blank metric**: one of the two series was not reported for that day.

The step summary of each run lists the dates between the first and the last
stored day that have no row.

### Visibility

The repository is public, and so is the `traffic-history` branch: anyone can
read its CSV files. Branch protection controls writing and deletion, not
reading. The workflow therefore keeps counts only: views, clones and their
unique visitors, per day and over 14 days. It does not collect top referrers
or popular paths, which could name the sites and pages visitors came from.
The data identifies no visitor and is not published through GitHub Pages or
badges. The counts include the maintainer's own visits and every clone made by
CI checkouts.

## Branch protection

The workflow pushes to `traffic-history` directly, so its rules differ from
those of `main` and `release/**`
([GOVERNANCE.md](GOVERNANCE.md#protection-policy-and-verified-controls)). The
traffic ruleset (25782014), configured under #12, applies:

| Rule | `traffic-history` |
| --- | --- |
| Deletion | Blocked. |
| Force pushes | Blocked. |
| Pull request required | No: the workflow commits directly. |
| Required status checks | None. |
| Bypass | None. |

## Failure diagnosis and recovery

Each run fails before anything is written if a response is missing or
invalid, and leaves the history unchanged. Read the failing step:

| Step and message | Cause | Action |
| --- | --- | --- |
| *Create the GitHub App token* fails | The variable or the secret is missing, the run is not in the `analytics` environment, the key was deleted on the App, or the App is not installed on this repository. | Follow the credential setup; rotate the key if it was deleted. |
| *Create the GitHub App token*: permission error | The App does not hold *Administration: read*, or its new permission was not accepted on the installation. | Set the permission on the App and accept it on the installation. |
| *Fetch*: `The GitHub App token is missing` | The token step produced no token. | Read the token step's log. |
| *Fetch*: HTTP 401, 403 or 404 | The token lacks *Administration: read* on this repository. | Check the App's permission and installation. |
| *Fetch*: HTTP 429 or 5xx after retries | Rate limit or GitHub outage. | Run it again later; the next run collects the same 14 days. |
| *Merge*: `ERROR: ...; the history was not changed` | The API returned an unexpected shape, or a history file no longer has the expected layout. | Inspect the response or the named file; a file edited by hand must keep its header and columns. |
| *Commit and push*: `Could not push the history` | `traffic-history` kept moving, or a rule rejected the push. | Check the branch's rules and recent commits, then run again. |
| *Check out traffic-history* fails | The branch does not exist yet, or was deleted. | Create it as described above, or restore it from the last known commit; never recreate it empty over existing history. |

A failed run can always be repeated: the merge is idempotent, and each
collection covers the last 14 days.

If the branch must be repaired, change it with a new commit made with
`python tools/traffic_history.py merge` or by hand, keeping every header.
`python tools/traffic_history.py init --data data` recreates missing files
with their headers and never overwrites an existing one.
