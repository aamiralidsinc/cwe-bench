import assistantsRouter from '@product/routes/openai-assistants'
import filesRouter from '@product/routes/openai-assistants-files'
import { resetHarness, seedCredential, makeReq, makeRes, dispatch, sessionUser, expectBlocked } from '../support/harness'

const ATTACKER = 'ws_attacker'
const VICTIM = 'ws_victim'
const SECRET = 'VICTIM-ASSISTANT-SECRET'

const attacker = () => sessionUser(ATTACKER)

async function call(router: any, method: string, url: string, req: any) {
    const res = makeRes()
    const next = jest.fn()
    await dispatch(router, method, url, req, res, next)
    return { res, next }
}

beforeEach(() => {
    resetHarness()
    seedCredential({ id: 'cred_victim', workspaceId: VICTIM, encryptedData: SECRET })
})

test('cross-tenant listing of assistants does not use the foreign credential', async () => {
    const { res, next } = await call(
        assistantsRouter,
        'get',
        '/',
        makeReq({ query: { credential: 'cred_victim' }, user: attacker() })
    )
    expectBlocked(res, next, SECRET)
})

test('cross-tenant read of a single assistant does not use the foreign credential', async () => {
    const { res, next } = await call(
        assistantsRouter,
        'get',
        '/asst_1',
        makeReq({ query: { credential: 'cred_victim' }, user: attacker() })
    )
    expectBlocked(res, next, SECRET)
})

test('cross-tenant assistant file upload does not use the foreign credential', async () => {
    const { res, next } = await call(
        filesRouter,
        'post',
        '/upload/',
        makeReq({ query: { credential: 'cred_victim' }, files: [], user: attacker() })
    )
    expectBlocked(res, next, SECRET)
})
