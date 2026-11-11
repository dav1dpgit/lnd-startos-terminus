# The upstream pull request — lightningnetwork/lnd

Branch `funding-zero-conf-tweakless` on the fork (three commits, base = master at ff38b9c, 2026-10-06):

1. `funding: negotiate zero-conf and scid-alias explicitly with the tweakless commitment type` —
   funding/commitment_type_negotiation.go (+52), funding/commitment_type_negotiation_test.go (+95: four table rows,
   three accepted, one refused for a missing remote feature).
2. `rpc: carry zero_conf and scid_alias into an explicit STATIC_REMOTE_KEY open` — rpcserver.go (+14 −2).
3. `docs: release note for zero-conf tweakless channels` — docs/release-notes/release-notes-0.22.0.md (+10; the PR
   number is `XXXXX` until the PR exists — fix it in the branch, force-push, before opening).

Nothing here could be compiled or run in the sandbox (the Go module proxy is not reachable from it); gofmt is clean and
the diff applies to both master and v0.21.4-beta. The fork's CI (and this package's image build) is the first compile.

## Title

funding: negotiate zero-conf and scid-alias channels explicitly with the static remote key (tweakless) commitment type

## Body

### Change Description

`explicitNegotiateCommitmentType` accepts the zero-conf and scid-alias feature bits only together with anchors (and the
script-enforced lease). The fundee side has long tolerated a zero-conf channel without anchors — `funding/manager.go`:
"We don't require anchors here - this is for compatibility with LDK" — so an lnd node can accept such a channel from a
peer that opens it, but cannot open one itself when the peer asks for the static remote key commitment type: the
`OpenChannel` RPC drops `zero_conf` / `scid_alias` for `STATIC_REMOTE_KEY`, and the explicit negotiation returns
`errUnsupportedChannelType`.

This PR adds the three explicit cases — zero-conf + scid-alias + static remote key, zero-conf + static remote key,
scid-alias + static remote key — each resolving to `CommitmentTypeTweakless` after the same `hasFeatures` check the
anchors cases make, and sets the two required bits on a `STATIC_REMOTE_KEY` open the way the `ANCHORS` and
`SCRIPT_ENFORCED_LEASE` cases already do. Callers that do not ask for these types see no change.

Why: an LSP serving LDK-based mobile/browser wallets with JIT zero-conf channels where the wallet's to_remote output
is a plain P2WPKH (recoverable from the wallet's seed without the anchor sweeper machinery). Such wallets request
`static_remote_key` + `zero_conf` + `option_scid_alias` as their channel type today; lnd as the opener cannot offer it.
The change has run in production on an lnd 0.20.1 node as a local patch since 2026-09 with LDK 0.2 wallets as the
fundees.

### Steps to Test

`go test ./funding/ -run TestCommitmentTypeNegotiation` — the four new rows. Manually: with `protocol.zero-conf` and
`protocol.option-scid-alias` on both nodes, `lncli openchannel --zero_conf --scid_alias --channel_type tweakless …` to a
peer advertising the optional bits; before this PR lnd answers `requested channel type not supported`.

### Pull Request Checklist

- [x] Unit tests for the new negotiation cases
- [x] Release notes updated (docs/release-notes/release-notes-0.22.0.md)
- [ ] Integration test (none; the itest harness has no tweakless zero-conf case — happy to add one if the maintainers want it)

## Opening it

1. Fork lightningnetwork/lnd on GitHub (the Fork button), and add the fork to the token's repositories.
2. The branch is pushed to the fork from the sandbox (`git push fork funding-zero-conf-tweakless`).
3. GitHub shows "Compare & pull request" on the fork; title and body as above; base `master`.
4. Expect: a request for an itest, a question about `lncli --channel_type tweakless` naming, and the CI run.
