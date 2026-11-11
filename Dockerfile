ARG RCLONE_VERSION=1.75.2

# ---- LND (Terminus) ------------------------------------------------------------------------------------------------
# Start9's LND package with one change: lnd and lncli are built from LND's own release tag with one additive patch
# (patches/lnd-terminus.patch, proposed upstream in lightningnetwork/lnd): the funding manager negotiates zero-conf and
# scid-alias channels explicitly with the static-remote-key commitment type, and OpenChannel carries the zero_conf /
# scid_alias flags into a STATIC_REMOTE_KEY open. A node never asked for that channel type behaves as stock LND.
# LND_TAG must be the tag in Start9's "FROM lightninglabs/lnd:" line below; TERMINUS_GO_IMAGE is the Go image of LND's
# own Dockerfile at that tag. terminus/follow-start9.sh sets both. The build stamps "-terminus" into LND's version
# (lncli getinfo → "version": "<x> commit=<tag>-terminus"), which is how the LIJOX adapter package tells this build
# from stock LND. Everything outside this block and the two COPY lines at the end of the file is Start9's file.
ARG LND_TAG=v0.21.6-beta
ARG TERMINUS_GO_IMAGE=golang:1.27.3-alpine

FROM ${TERMINUS_GO_IMAGE} AS terminus-builder
ARG LND_TAG
ENV GODEBUG=netdns=cgo
RUN apk add --no-cache --update alpine-sdk git make gcc
RUN git clone --depth 1 --branch ${LND_TAG} https://github.com/lightningnetwork/lnd /go/src/github.com/lightningnetwork/lnd
COPY patches/lnd-terminus.patch /tmp/lnd-terminus.patch
RUN cd /go/src/github.com/lightningnetwork/lnd \
 && git apply --check /tmp/lnd-terminus.patch \
 && git apply /tmp/lnd-terminus.patch \
 && make release-install COMMIT=${LND_TAG}-terminus \
 && sha256sum /go/bin/lnd /go/bin/lncli
# ---- end of the LND (Terminus) builder ------------------------------------------------------------------------------

# ---- rclone binary fetch ----
FROM alpine:3.24 AS rclone-fetch
RUN apk add --no-cache ca-certificates curl
ARG RCLONE_VERSION
ARG TARGETARCH
ARG RCLONE_SHA256_AMD64=349ac8fba6ff65d6247043f1750cdcb518ec5d500ef91463a10d37c0ccdf3702
ARG RCLONE_SHA256_ARM64=7e1e8d69654941b7b7df84ee74c5f7fb09cce7d5496947fb7bf16b55ff427d10
WORKDIR /out
RUN case "${TARGETARCH}" in \
      amd64) SHA="${RCLONE_SHA256_AMD64}" ;; \
      arm64) SHA="${RCLONE_SHA256_ARM64}" ;; \
      *)     echo "Unsupported architecture: ${TARGETARCH}" && exit 1 ;; \
    esac && \
    curl -fsSL --retry 5 --retry-all-errors --retry-delay 3 \
      "https://downloads.rclone.org/v${RCLONE_VERSION}/rclone-v${RCLONE_VERSION}-linux-${TARGETARCH}.zip" -o rclone.zip && \
    echo "${SHA}  rclone.zip" | sha256sum -c - && \
    unzip -q rclone.zip && \
    install -m 0755 "rclone-v${RCLONE_VERSION}-linux-${TARGETARCH}/rclone" rclone

FROM lightninglabs/lnd:v0.21.6-beta

# The base image's CA store is only as current as its last release.
RUN apk add --no-cache --upgrade ca-certificates ca-certificates-bundle

# curl calls LND's REST API for wallet setup and migration polling; sqlite
# scrubs the migrated database; openssh-client and sshpass import remote wallets;
# flock serializes copies; wireguard-tools and iptables bring up and fence the Clearnet VPN tunnel (startos/vpn.ts).
RUN apk add --no-cache curl sqlite openssh-client sshpass flock wireguard-tools iptables ip6tables

# rclone copies channel.backup to configured providers.
COPY --from=rclone-fetch /out/rclone /usr/local/bin/rclone

# lndinit drives the bolt → SQLite database migration.
COPY --from=lightninglabs/lndinit:v0.1.38-beta-lnd-v0.21.6-beta /bin/lndinit /bin/lndinit

# Continuous off-box copy of channel.backup (see startos/main.ts).
COPY backup-agent.sh /usr/local/bin/backup-agent.sh

# ---- LND (Terminus): the patched binaries replace the stock ones (everything else is Start9's image) ----------------
COPY --from=terminus-builder /go/bin/lnd /bin/lnd
COPY --from=terminus-builder /go/bin/lncli /bin/lncli
