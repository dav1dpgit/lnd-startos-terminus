import { lndConfFile } from '../fileModels/lnd.conf'
import { sdk } from '../sdk'

// LND (Terminus): when this build is installed, or replaces another LND build (Start9's or an earlier Terminus), turn on
// the two channel settings a LIJOX provider's wallet channels need — zero-conf and option-scid-alias. They are the same
// two switches as LND → Actions → Channel Settings; turning them on lets LND accept and open those channel types and
// changes nothing else. A plain restart (kind null) and a backup restore leave the operator's settings as they are.
//
// The watchtower server is NOT turned on here: it needs the operator to choose the address other nodes reach it on
// (LND → Actions → Watchtower Server). The LIJOX adapter package raises that as a task.
export const terminusDefaults = sdk.setupOnInit(async (effects, kind) => {
  if (kind !== 'install' && kind !== 'update') return
  await lndConfFile.merge(effects, {
    'protocol.option-scid-alias': true,
    'protocol.zero-conf': true,
  })
})
