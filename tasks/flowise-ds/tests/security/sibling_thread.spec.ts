import router from '@product/routes/openai-assistants'
import { resetHarness, seedCredential, makeReq, makeRes, dispatch, sessionUser, expectBlocked } from '../support/harness'

const ATTACKER = 'ws_attacker'
const VICTIM = 'ws_victim'
const SECRET = 'VICTIM-THREAD-SECRET'

const attacker = () => sessionUser(ATTACKER)

async function call(req: any) {
    const res = makeRes()
    const next = jest.fn()
    await dispatch(router as any, 'post', '/thread', req, res, next)
    return { res, next }
}

beforeEach(() => {
    resetHarness()
    seedCredential({ id: 'cred_victim', workspaceId: VICTIM, encryptedData: SECRET })
})

test('cross-tenant thread creation does not use the foreign credential', async () => {
    const { res, next } = await call(
        makeReq({ body: { credential: 'cred_victim', assistantId: 'asst_1' }, user: attacker() })
    )
    expectBlocked(res, next, SECRET)
})

test('a caller with no active workspace cannot create a thread with a named credential', async () => {
    const noWorkspace = { id: 'user_no_workspace', activeOrganizationId: 'org_a', isOrganizationAdmin: true }
    const { res, next } = await call(
        makeReq({ body: { credential: 'cred_victim', assistantId: 'asst_1' }, user: noWorkspace })
    )
    expectBlocked(res, next, SECRET)
})
