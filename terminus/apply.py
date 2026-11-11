#!/usr/bin/env python3
"""Turn Start9's lnd-startos files into LND (Terminus).

Run once per Start9 release tag, from the repository root, on a tree whose five files below are Start9's own (after
merging the tag and taking Start9's side of these files). terminus/follow-start9.sh does exactly that.

  Dockerfile                    our builder stage on top, our two COPY lines at the end; LND_TAG = the tag in Start9's
                                "FROM lightninglabs/lnd:" line; TERMINUS_GO_IMAGE = the Go image passed in
  startos/versions/current.ts   Start9's current becomes startos/versions/v<ver>.ts (an "other" version); our
                                current is Start9's number plus ".1" (0.21.5-beta:1 -> 0.21.5-beta:1.1)
  startos/versions/index.ts     imports Start9's current as an other version
  startos/manifest/index.ts     title "LND (Terminus)" and the package repo
  startos/init/index.ts         runs startos/init/terminusDefaults.ts after Start9's seedFiles

Usage: terminus/apply.py <go-image>      e.g. terminus/apply.py golang:1.27.3-alpine
Prints the new version on success. Exits non-zero, changing nothing further, when a file no longer has the shape this
script expects — the daily check then opens an issue instead of building.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path('.')
PACKAGE_REPO = 'https://github.com/dav1dpgit/lnd-startos-terminus'
SUFFIX = '.1'
HEAD_MARK = '# ---- LND (Terminus) ----'
TAIL_MARK = '# ---- LND (Terminus): the patched binaries'


def fail(msg):
    print(f'apply.py: {msg}', file=sys.stderr)
    sys.exit(1)


def read(rel):
    return (ROOT / rel).read_text()


def write(rel, text):
    (ROOT / rel).write_text(text)


def dockerfile(go_image):
    s = read('Dockerfile')
    m = re.search(r'^FROM lightninglabs/lnd:(v[0-9][^\s]*)\s*$', s, re.M)
    if not m:
        fail('Dockerfile: no "FROM lightninglabs/lnd:<tag>" line')
    lnd_tag = m.group(1)
    if not re.fullmatch(r'golang:[0-9.]+-alpine', go_image):
        fail(f'unexpected Go image {go_image!r}')
    head = (ROOT / 'terminus/dockerfile-head.txt').read_text()
    tail = (ROOT / 'terminus/dockerfile-tail.txt').read_text()
    head = head.replace('@LND_TAG@', lnd_tag).replace('@GO_IMAGE@', go_image)
    # strip an earlier copy of our blocks, then put them back
    if HEAD_MARK in s:
        a = s.index(HEAD_MARK)
        end = '# ---- end of the LND (Terminus) builder'
        b = s.index('\n', s.index(end)) + 1
        s = s[:a].rstrip('\n') + '\n\n' + s[b:].lstrip('\n')
    if TAIL_MARK in s:
        s = s[:s.index(TAIL_MARK)].rstrip('\n') + '\n'
    # our block goes just before Start9's first FROM: Start9's own ARGs above it stay global (an ARG after a FROM
    # belongs to that stage), and our builder stage exists before the final stage copies from it
    f = re.search(r'^FROM ', s, re.M)
    if not f:
        fail('Dockerfile: no FROM line')
    lines = s[:f.start()].split('\n')[:-1]     # the lines above the first FROM
    while lines and lines[-1].startswith('#'):  # keep Start9's comment with its FROM
        lines.pop()
    at = sum(len(x) + 1 for x in lines)
    s = s[:at] + head + '\n' + s[at:]
    write('Dockerfile', s.rstrip('\n') + '\n\n' + tail)
    return lnd_tag


def export_name(version):
    # 0.21.5-beta:1 -> v_0_21_5_beta_1 (Start9's own naming of its version files)
    return 'v_' + re.sub(r'[^0-9a-z]+', '_', version.lower()).strip('_')


def file_name(version):
    # 0.21.5-beta:1 -> v0.21.5-beta_1.ts
    return 'v' + version.replace(':', '_') + '.ts'


def versions(lnd_tag):
    cur = read('startos/versions/current.ts')
    if 'LND (Terminus)' in cur:
        fail('startos/versions/current.ts is already ours — take Start9\'s side of it first')
    m = re.search(r"version:\s*'([^']+)'", cur)
    if not m or not re.fullmatch(r'[0-9][0-9a-z.\-]*:[0-9]+', m.group(1)):
        fail('startos/versions/current.ts: no plain Start9 version')
    stock = m.group(1)
    ours = stock + SUFFIX
    name = export_name(stock)
    if not re.search(r'export const current\s*=', cur):
        fail('startos/versions/current.ts: no "export const current"')
    write(f'startos/versions/{file_name(stock)}', re.sub(r'export const current\s*=', f'export const {name} =', cur, count=1))

    notes = (f'LND (Terminus) {ours}: Start9\'s LND package {stock} with one additive patch to LND {lnd_tag}. The patch '
             'lets this node open zero-conf, scid-alias channels with the static-remote-key commitment type (no anchors) '
             '— the channel LiJ-class wallets ask their LIJOX provider for. A node never asked for that channel type '
             'behaves exactly as Start9\'s build. Installing or updating this build turns on zero-conf and '
             'option-scid-alias (Channel Settings). The LND version line reads "commit=' + lnd_tag + '-terminus". '
             'Update LND from the LIJOX registry: Start9\'s own LND update puts the stock build back (same data, no loss).')
    m2 = re.search(r'en_US:\s*`([^`]*)`', cur)
    if m2:
        notes += '\n\nStart9\'s notes for ' + stock + ': ' + m2.group(1)
    notes_js = json.dumps(notes)
    write('startos/versions/current.ts', f"""import {{ VersionInfo }} from '@start9labs/start-sdk'

// LND (Terminus) — written by terminus/apply.py from Start9's current version ({stock}); do not edit by hand.
// A plain version just above Start9's, so every LND app's version rule (BTCPay, RTL, ...) accepts it. The data is
// Start9's {stock} data unchanged, so both directions are no-ops: Start9's {stock} installs back over it, and Start9's
// next release migrates from it as from {stock}.
const notes = {notes_js}

export const current = VersionInfo.of({{
  version: '{ours}',
  releaseNotes: {{
    en_US: notes,
    es_ES: notes,
    de_DE: notes,
    pl_PL: notes,
    fr_FR: notes,
  }},
  migrations: {{
    up: async () => {{}},
    down: async () => {{}},
  }},
}})
""")

    idx = read('startos/versions/index.ts')
    if f"from './{file_name(stock)[:-3]}'" not in idx:
        idx = re.sub(r"(import \{ current \} from './current'\n)",
                     rf"\1import {{ {name} }} from './{file_name(stock)[:-3]}'\n", idx, count=1)
        m3 = re.search(r'other:\s*\[([^\]]*)\]', idx)
        if not m3:
            fail('startos/versions/index.ts: no "other: [...]"')
        items = [x.strip() for x in m3.group(1).split(',') if x.strip()]
        items.append(name)
        idx = idx[:m3.start()] + 'other: [' + ', '.join(items) + ']' + idx[m3.end():]
        write('startos/versions/index.ts', idx)
    return ours


def manifest():
    s = read('startos/manifest/index.ts')
    s2 = re.sub(r"title:\s*'[^']*'", "title: 'LND (Terminus)'", s, count=1)
    s2 = re.sub(r"packageRepo:\s*'[^']*'", f"packageRepo: '{PACKAGE_REPO}'", s2, count=1)
    if "title: 'LND (Terminus)'" not in s2 or PACKAGE_REPO not in s2:
        fail('startos/manifest/index.ts: no title / packageRepo line')
    write('startos/manifest/index.ts', s2)


def init():
    s = read('startos/init/index.ts')
    if 'terminusDefaults' in s:
        return
    if "import { seedFiles } from './seedFiles'\n" not in s or '\n  seedFiles,\n' not in s:
        fail('startos/init/index.ts: no seedFiles import / entry')
    s = s.replace("import { seedFiles } from './seedFiles'\n",
                  "import { seedFiles } from './seedFiles'\nimport { terminusDefaults } from './terminusDefaults'\n", 1)
    s = s.replace('\n  seedFiles,\n', '\n  seedFiles,\n  terminusDefaults,\n', 1)
    write('startos/init/index.ts', s)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        fail('usage: terminus/apply.py <go-image>')
    tag = dockerfile(sys.argv[1])
    version = versions(tag)
    manifest()
    init()
    (ROOT / 'terminus/lnd-tag').write_text(tag + '\n')
    print(version)
