import ctrl from '@product/controllers/openai-assistants'
import { resetHarness, seedCredential, makeReq, makeRes, expectBlocked } from '../support/harness'

const ATTACKER = 'ws_attacker'
const VICTIM = 'ws_victim'
const SECRET = 'VICTIM-OPENAI-SECRET'
const attacker = () => ({ id: 'u_attacker', activeWorkspaceId: ATTACKER, activeOrganizationId: 'org_a' })

async function run(fn: (req: any, res: any, next: jest.Mock) => Promise<unknown>, req: any) {
    const res = makeRes()
    const next = jest.fn()
    await fn(req, res, next)
    expectBlocked(res, next, SECRET)
}

beforeEach(() => {
    resetHarness()
    seedCredential({ id: 'cred_victim', workspaceId: VICTIM, encryptedData: SECRET })
})

test('cross-tenant listing of assistants does not use the foreign credential', async () => {
    await run(ctrl.getAllOpenaiAssistants, makeReq({ query: { credential: 'cred_victim' }, user: attacker() }))
})

test('cross-tenant read of a single assistant does not use the foreign credential', async () => {
    await run(
        ctrl.getSingleOpenaiAssistant,
        makeReq({ query: { credential: 'cred_victim' }, params: { id: 'asst_1' }, user: attacker() })
    )
})

test('cross-tenant file upload to an assistant does not use the foreign credential', async () => {
    await run(ctrl.uploadAssistantFiles, makeReq({ query: { credential: 'cred_victim' }, user: attacker() }))
})
