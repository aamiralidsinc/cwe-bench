// The credential reference on this path is not taken from the request: it is the
// value already recorded on the stored assistant row the caller is acting on (a
// value a caller can put there through the product's own create/update flow).
// The invariant is about the secret the server would resolve, decrypt and hand
// to the provider, not about where the reference arrived from.
import router from '@product/routes/assistants'
import { Assistant } from '@product/database/entities/Assistant'
import { resetHarness, seedCredential, makeReq, makeRes, dispatch, sessionUser, expectBlocked } from '../support/harness'

const ATTACKER = 'ws_attacker'
const VICTIM = 'ws_victim'
const SECRET = 'VICTIM-ASSISTANT-ROW-SECRET'

const attacker = () => sessionUser(ATTACKER)

const assistantRepo = () => (globalThis as any).__APPSERVER.AppDataSource.getRepository(Assistant)

async function seedAssistant(credentialId: string, workspaceId: string) {
    await assistantRepo().save({
        id: 'asst_1',
        details: JSON.stringify({ id: 'remote_asst_1' }),
        credential: credentialId,
        type: 'ASSISTANT',
        workspaceId
    })
}

async function call(method: string, url: string, req: any) {
    const res = makeRes()
    const next = jest.fn()
    await dispatch(router as any, method, url, req, res, next)
    return { res, next }
}

beforeEach(async () => {
    resetHarness()
    seedCredential({ id: 'cred_victim', workspaceId: VICTIM, encryptedData: SECRET })
    await seedAssistant('cred_victim', ATTACKER)
})

test('a credential recorded on an assistant row is not used across tenants', async () => {
    const { res, next } = await call(
        'delete',
        '/asst_1',
        makeReq({ query: { isDeleteBoth: 'true' }, user: attacker() })
    )
    expectBlocked(res, next, SECRET)
    // The refusal has no side effect: the assistant the caller addressed is still there.
    expect(await assistantRepo().findOneBy({ id: 'asst_1' })).not.toBeNull()
})
