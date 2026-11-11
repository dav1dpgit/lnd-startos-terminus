import { VersionInfo } from '@start9labs/start-sdk'

// LND (Terminus) — written by terminus/apply.py from Start9's current version (0.21.6-beta:4); do not edit by hand.
// A plain version just above Start9's, so every LND app's version rule (BTCPay, RTL, ...) accepts it. The data is
// Start9's 0.21.6-beta:4 data unchanged, so both directions are no-ops: Start9's 0.21.6-beta:4 installs back over it, and Start9's
// next release migrates from it as from 0.21.6-beta:4.
const notes = "LND (Terminus) 0.21.6-beta:4.1: Start9's LND package 0.21.6-beta:4 with one additive patch to LND v0.21.6-beta. The patch lets this node open zero-conf, scid-alias channels with the static-remote-key commitment type (no anchors) \u2014 the channel LiJ-class wallets ask their LIJOX provider for. A node never asked for that channel type behaves exactly as Start9's build. Installing or updating this build turns on zero-conf and option-scid-alias (Channel Settings). The LND version line reads \"commit=v0.21.6-beta-terminus\". Update LND from the LIJOX registry: Start9's own LND update puts the stock build back (same data, no loss)."

export const current = VersionInfo.of({
  version: '0.21.6-beta:4.1',
  releaseNotes: {
    en_US: notes,
    es_ES: notes,
    de_DE: notes,
    pl_PL: notes,
    fr_FR: notes,
  },
  migrations: {
    up: async () => {},
    down: async () => {},
  },
})
