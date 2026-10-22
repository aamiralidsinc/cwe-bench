import ctrl from '@product/controllers/openai-assistants'
import { resetHarness, seedCredential, makeReq, makeRes, expectBlocked } from '../support/harness'

const ATTACKER = 'ws_attacker'
const VICTIM = 'ws_victim'
const SECRET = 'VICTIM-OPENAI-SECRET'
const attacker = () => ({ id: 'u_attacker', activeWorkspaceId: ATTACKER, activeOrganizationId: 'org_a' })

beforeEach(() => {
    resetHarness()
    seedCredential({ id: 'cred_victim', workspaceId: VICTIM, encryptedData: SECRET })
})

test('cross-tenant model listing does not use the foreign credential', async () => {
    const req = makeReq({ query: { credential: 'cred_victim' }, user: attacker() })
    const res = makeRes()
    const next = jest.fn()
    await ctrl.getAssistantModels(req, res, next)
    expectBlocked(res, next, SECRET)
})
