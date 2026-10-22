import router from '@product/routes/openai-assistants-vector-store'
import {
    resetHarness,
    seedCredential,
    seedShare,
    makeReq,
    makeRes,
    dispatch,
    sessionUser,
    expectBlocked
} from '../support/harness'

const ATTACKER = 'ws_attacker'
const VICTIM = 'ws_victim'
const SECRET = 'VICTIM-OPENAI-SECRET'

const attacker = () => sessionUser(ATTACKER)

async function call(method: string, url: string, req: any) {
    const res = makeRes()
    const next = jest.fn()
    await dispatch(router as any, method, url, req, res, next)
    return { res, next }
}

beforeEach(() => {
    resetHarness()
    seedCredential({ id: 'cred_victim', workspaceId: VICTIM, encryptedData: SECRET })
})

test('cross-tenant read of a vector store does not use the foreign credential', async () => {
    const { res, next } = await call('get', '/vs_1', makeReq({ query: { credential: 'cred_victim' }, user: attacker() }))
    expectBlocked(res, next, SECRET)
})

test('cross-tenant listing of vector stores does not use the foreign credential', async () => {
    const { res, next } = await call('get', '/', makeReq({ query: { credential: 'cred_victim' }, user: attacker() }))
    expectBlocked(res, next, SECRET)
})

test('cross-tenant creation of a vector store does not use the foreign credential', async () => {
    const { res, next } = await call(
        'post',
        '/',
        makeReq({ query: { credential: 'cred_victim' }, body: { name: 'store' }, user: attacker() })
    )
    expectBlocked(res, next, SECRET)
})

test('cross-tenant update of a vector store does not use the foreign credential', async () => {
    const { res, next } = await call(
        'put',
        '/vs_1',
        makeReq({ query: { credential: 'cred_victim' }, body: { name: 'renamed' }, user: attacker() })
    )
    expectBlocked(res, next, SECRET)
})

test('cross-tenant deletion of a vector store does not use the foreign credential', async () => {
    const { res, next } = await call('delete', '/vs_1', makeReq({ query: { credential: 'cred_victim' }, user: attacker() }))
    expectBlocked(res, next, SECRET)
})

test('cross-tenant file upload to a vector store does not use the foreign credential', async () => {
    const { res, next } = await call(
        'post',
        '/vs_1',
        makeReq({ query: { credential: 'cred_victim' }, body: {}, files: [], user: attacker() })
    )
    expectBlocked(res, next, SECRET)
})

test('cross-tenant file deletion from a vector store does not use the foreign credential', async () => {
    const { res, next } = await call(
        'patch',
        '/vs_1',
        makeReq({ query: { credential: 'cred_victim' }, body: { file_ids: ['file_1'] }, user: attacker() })
    )
    expectBlocked(res, next, SECRET)
})

test('a share recorded for another kind of resource does not authorise a credential', async () => {
    seedShare({ workspaceId: ATTACKER, sharedItemId: 'cred_victim', itemType: 'chatflow' })
    const { res, next } = await call('get', '/vs_1', makeReq({ query: { credential: 'cred_victim' }, user: attacker() }))
    expectBlocked(res, next, SECRET)
})

test('a caller with no active workspace cannot use a named credential', async () => {
    const noWorkspace = { id: 'user_no_workspace', activeOrganizationId: 'org_a', isOrganizationAdmin: true }
    const { res, next } = await call('get', '/vs_1', makeReq({ query: { credential: 'cred_victim' }, user: noWorkspace }))
    expectBlocked(res, next, SECRET)
})
