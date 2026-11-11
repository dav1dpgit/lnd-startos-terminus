# LND (Terminus) for StartOS

Start9's [`lnd-startos`](https://github.com/Start9Labs/lnd-startos) package (full history) with one change: the `lnd`
and `lncli` binaries are built from LND's own release tag with [`patches/lnd-terminus.patch`](patches/lnd-terminus.patch).
Everything else is Start9's package. Current version: **`0.21.6-beta:4.1`** (LND `v0.21.6-beta`).

**Status: first release, not yet run on an operator's server.** Install it with the publisher on a call.

## Why

A LiJ wallet asks its LIJOX provider for a zero-conf channel with the static-remote-key commitment type and no anchors:
the wallet's side of a force-close then pays a plain P2WPKH output its 12 words reach in any wallet. Stock LND accepts
that channel when the peer opens it, but will not open one itself: the explicit channel-type list pairs zero-conf only
with anchors, and `OpenChannel` drops `zero_conf` / `scid_alias` for `STATIC_REMOTE_KEY`. The patch adds the three
missing cases and carries the two flags. It is additive: a node never asked for that channel type behaves as stock LND.
Proposed upstream: `terminus/upstream-pr.md` (branch `funding-zero-conf-tweakless` on dav1dpgit/lnd). When it lands in a
release Start9 ships, this repository retires and operators go back to Start9's build.

## Download

[Releases](../../releases): `lnd_x86_64.s9pk` for Intel/AMD servers, `lnd_aarch64.s9pk` for ARM, and `SHA256SUMS` with
each file's fingerprint. Check your file before installing:

- Windows (PowerShell): `Get-FileHash .\lnd_x86_64.s9pk -Algorithm SHA256`
- Mac / Linux: `shasum -a 256 lnd_x86_64.s9pk`

## Install

1. Update LND to Start9's newest version first (it must be the version this build's number starts with).
2. Make a StartOS backup. It is for the worst case only: restoring LND from a backup goes through channel recovery,
   which closes its channels.
3. StartOS → **Sideload** → the `.s9pk`. LND keeps its data, its channels and the apps that use it.

**Going back:** install Start9's LND of the same number from the Start9 Registry. It is the same data; nothing is lost.

## The version

Start9's number plus `.1` (Start9's `0.21.6-beta:4` → `0.21.6-beta:4.1`). Same package id (`lnd`), same data, no-op
migrations both ways.

- Every LND app's version rule accepts it (BTCPay, RTL and others name plain LND version ranges).
- Start9's next LND release shows in Updates. Taking it puts the stock binaries back — same data, nothing lost — and
  the LIJOX adapter's "LND (Terminus)" check turns red until the matching Terminus build is installed.
- How to tell the builds apart: `lncli getinfo` → `"version": "… commit=v0.21.6-beta-terminus"`. Start9's reads
  `commit=v0.21.6-beta`.

## What it changes in LND's settings

When this build is installed, or replaces another LND build, it turns on `protocol.zero-conf` and
`protocol.option-scid-alias` (LND → Actions → Channel Settings) — `startos/init/terminusDefaults.ts`. Nothing else.

## How it is made

`terminus/follow-start9.sh` merges a Start9 release tag, checks the patch against LND's tag (`git apply --check`), and
runs `terminus/apply.py`, which writes the builder stage into Start9's Dockerfile (LND's own Go image,
`make release-install COMMIT=<tag>-terminus`), moves Start9's current version into the version list, and sets ours.
`.github/workflows/release.yml` builds both architectures with Start9's shared build workflow and publishes them as a
release. Each CI build is signed with a one-time key.

Security reports: dp@modulo.network.
