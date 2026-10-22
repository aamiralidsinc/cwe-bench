import router from '@product/routes/credentials'
import { resetHarness, seedCredential, makeReq, makeRes, dispatch, sessionUser, expectBlocked } from '../support/harness'

const ATTACKER = 'ws_attacker'
const VICTIM = 'ws_victim'
const SECRET = 'VICTIM-CREDENTIAL-SECRET'

const attacker = () => sessionUser(ATTACKER)

async function call(url: string, req: any) {
    const res = makeRes()
    const next = jest.fn()
    await dispatch(router as any, 'post', url, req, res, next)
    return { res, next }
}

beforeEach(() => {
    resetHarness()
    seedCredential({ id: 'cred_victim', workspaceId: VICTIM, encryptedData: SECRET })
})

test('cross-tenant credential connection test does not use the foreign credential', async () => {
    const { res, next } = await call('/cred_victim/test', makeReq({ user: attacker() }))
    expectBlocked(res, next, SECRET)
})

test('a caller with no active workspace cannot test a named credential', async () => {
    const noWorkspace = { id: 'user_no_workspace', activeOrganizationId: 'org_a', isOrganizationAdmin: true }
    const { res, next } = await call('/cred_victim/test', makeReq({ user: noWorkspace }))
    expectBlocked(res, next, SECRET)
})
