#!/usr/bin/env bash
# Follow Start9's LND package: when Start9 has a release tag newer than the one in terminus/start9-tag, merge it and
# turn it into LND (Terminus) with terminus/apply.py. Run from the repository root on a clean master.
#
# Exit codes: 0 = a new commit was made (prints the new version on the last line); 3 = nothing new; 1 = it needs a
# person (a merge conflict outside the files apply.py writes, or the patch no longer applies to LND's tag). On 1 the
# working tree is reset to where it started.
set -euo pipefail

START9=https://github.com/Start9Labs/lnd-startos
LND=https://github.com/lightningnetwork/lnd
# Start9's files that apply.py rewrites: on a merge we always take Start9's side of them, then apply.py runs.
TRANSFORMED=(Dockerfile startos/versions/current.ts startos/versions/index.ts startos/manifest/index.ts startos/init/index.ts)
# Start9's files this repository does not carry (their release / agent tooling needs Start9's own secrets).
DROPPED=(AGENTS.md CLAUDE.md .github/workflows/release.yml .github/workflows/syncNext.yml
         .github/workflows/tagAndRelease.yml .github/workflows/pr-retarget.yml)

have=$(cat terminus/start9-tag)
newest=$(git ls-remote --tags "$START9" | awk '{print $2}' | grep -v '\^{}' | sed 's#refs/tags/##' \
         | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+-beta_[0-9]+$' | sort -V | tail -1)
[ -n "$newest" ] || { echo "no Start9 release tag found"; exit 1; }
if [ "$newest" = "$have" ] || [ "$(printf '%s\n%s\n' "$have" "$newest" | sort -V | tail -1)" = "$have" ]; then
  echo "up to date with Start9 $have"; exit 3
fi
echo "Start9 $have -> $newest"

start=$(git rev-parse HEAD)
undo() { git merge --abort 2>/dev/null || true; git reset -q --hard "$start"; }

git fetch -q "$START9" "refs/tags/$newest:refs/tags/start9-$newest"
if ! git merge --no-commit --no-ff "start9-$newest" >/dev/null 2>&1; then :; fi
for f in "${TRANSFORMED[@]}"; do git checkout -q "start9-$newest" -- "$f"; done
for f in "${DROPPED[@]}"; do git rm -q --ignore-unmatch -f -- "$f" >/dev/null 2>&1 || true; done
left=$(git diff --name-only --diff-filter=U)
if [ -n "$left" ]; then
  echo "merge conflict outside the transformed files:"; echo "$left"; undo; exit 1
fi

lnd_tag=$(sed -n 's/^FROM lightninglabs\/lnd:\(v[^ ]*\).*/\1/p' Dockerfile | head -1)
[ -n "$lnd_tag" ] || { echo "no lightninglabs/lnd FROM line in Start9's Dockerfile"; undo; exit 1; }
work=$(mktemp -d)
git -c advice.detachedHead=false clone -q --depth 1 --branch "$lnd_tag" "$LND" "$work/lnd"
go_image=$(sed -n 's/^FROM \(golang:[0-9.]*-alpine\).*/\1/p' "$work/lnd/Dockerfile" | head -1)
[ -n "$go_image" ] || { echo "no golang image in LND $lnd_tag's Dockerfile"; undo; exit 1; }
if ! git -C "$work/lnd" apply --check "$PWD/patches/lnd-terminus.patch"; then
  echo "patches/lnd-terminus.patch does not apply to LND $lnd_tag"; undo; exit 1
fi
rm -rf "$work"

if ! version=$(python3 terminus/apply.py "$go_image"); then undo; exit 1; fi
echo "$newest" > terminus/start9-tag
git add -A
git commit -q -m "LND (Terminus) $version: Start9's $newest, LND $lnd_tag with the patch" \
  -m "Merged by terminus/follow-start9.sh; Start9's version files moved and ours written by terminus/apply.py."
echo "$version"
