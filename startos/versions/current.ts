import { VersionInfo } from '@start9labs/start-sdk'

// LND (Terminus) — written by terminus/apply.py from Start9's current version (0.21.8-beta:2); do not edit by hand.
// A plain version just above Start9's, so every LND app's version rule (BTCPay, RTL, ...) accepts it. The data is
// Start9's 0.21.8-beta:2 data unchanged, so both directions are no-ops: Start9's 0.21.8-beta:2 installs back over it, and Start9's
// next release migrates from it as from 0.21.8-beta:2.
const notes = "LND (Terminus) 0.21.8-beta:2.1: Start9's LND package 0.21.8-beta:2 with one additive patch to LND v0.21.8-beta. The patch lets this node open zero-conf, scid-alias channels with the static-remote-key commitment type (no anchors) \u2014 the channel LiJ-class wallets ask their LIJOX provider for. A node never asked for that channel type behaves exactly as Start9's build. Installing or updating this build turns on zero-conf and option-scid-alias (Channel Settings). The LND version line reads \"commit=v0.21.8-beta-terminus\". Update LND from the LIJOX registry: Start9's own LND update puts the stock build back (same data, no loss).\n\nStart9's notes for 0.21.8-beta:2: Requires StartOS 0.4.1 or later. Update Bitcoin first: LND can now read only Bitcoin's RPC credential, not its data directory or wallets.\n\n**Security**\n\n- Nodes migrated from Umbrel get a new wallet password at their next start; record it with Show Credentials.\n- Migrating from Umbrel, myNode or StartOS now shows the origin's SSH host key fingerprint and sends your password only after you confirm it. A migration scheduled before this update has to be set up again in Initialize Wallet.\n- A Pay Invoice request from another service can no longer preset the amount, the fee limit or the confirmation.\n\n**Fixes**\n\n- Start Fresh reports an error when LND fails to create the wallet, instead of showing a seed.\n- Turning off the Clearnet VPN restores the Tor setting for clearnet peers that it changed when it was turned on.\n- An invalid WireGuard configuration is reported by line number, without repeating the line."

export const current = VersionInfo.of({
  version: '0.21.8-beta:2.1',
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
