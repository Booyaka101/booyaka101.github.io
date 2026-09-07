# booyaka101.github.io

The landing page for my tools, at <https://booyaka101.github.io/>.

It answers three questions with numbers that were measured this morning rather
than written down once: which Home Assistant integrations break next, whether
you can upgrade to ESLint 10 yet, and what actually runs at `npm install` time.

`build.py` reads
[`data/figures.json`](https://github.com/Booyaka101/Booyaka101/blob/main/data/figures.json),
which the profile repo commits every morning after it crawls. Reading that
instead of re-fetching means the site and the profile can't disagree, and the
build is one request plus the repo list. A workflow rebuilds half an hour after
the profile refresh.

    python build.py
