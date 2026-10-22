import vectorStoreRouter from '@product/routes/openai-assistants-vector-store'
import assistantsRouter from '@product/routes/openai-assistants'
import assistantsFileRouter from '@product/routes/openai-assistants-files'
import legacyAssistantsRouter from '@product/routes/assistants'
import oauth2Router from '@product/routes/oauth2'
import credentialsRouter from '@product/routes/credentials'
import { Assistant } from '@product/database/entities/Assistant'
import {
    resetHarness,
    seedCredential,
    seedShare,
    makeReq,
    makeRes,
    dispatch,
    sessionUser,
    apiKeyUser,
    expectAllowed,
    expectProviderUsed
} from '../support/harness'

const CALLER = 'ws_caller'
const OWNER = 'ws_owner'
const OTHER = 'ws_other'
const OWN_SECRET = 'OWN-OPENAI-SECRET'
const SHARED_SECRET = 'SHARED-OPENAI-SECRET'
const OTHER_SECRET = 'OTHER-OPENAI-SECRET'

const caller = () => sessionUser(CALLER)

async function call(router: any, method: string, url: string, req: any) {
    const res = makeRes()
    const next = jest.fn()
    await dispatch(router, method, url, req, res, next)
    return { res, next }
}

function expectDecryptedAndAnswered(res: any, next: jest.Mock, secret: string) {
    expect(next).not.toHaveBeenCalled()
    expect(res.statusCode).toBeLessThan(400)
    expect(res.jsonCalled).toBe(true)
    expect(globalThis.__decryptCalls || []).toContain(secret)
}

beforeEach(() => {
    resetHarness()
    seedCredential({ id: 'cred_own', workspaceId: CALLER, encryptedData: OWN_SECRET })
    seedCredential({ id: 'cred_foreign', workspaceId: OTHER, encryptedData: OTHER_SECRET })
})

test('a workspace can read its own vector store', async () => {
    const { res, next } = await call(
        vectorStoreRouter,
        'get',
        '/vs_1',
        makeReq({ query: { credential: 'cred_own' }, user: caller() })
    )
    expectAllowed(res, next, OWN_SECRET)
    expectProviderUsed(next, OWN_SECRET)
})

test('a workspace can list its own vector stores', async () => {
    const { res, next } = await call(
        vectorStoreRouter,
        'get',
        '/',
        makeReq({ query: { credential: 'cred_own' }, user: caller() })
    )
    expectAllowed(res, next, OWN_SECRET)
})

test('a workspace can create, update and delete a vector store with its own credential', async () => {
    const created = await call(
        vectorStoreRouter,
        'post',
        '/',
        makeReq({ query: { credential: 'cred_own' }, body: { name: 'store' }, user: caller() })
    )
    expectAllowed(created.res, created.next, OWN_SECRET)

    resetHarness()
    seedCredential({ id: 'cred_own', workspaceId: CALLER, encryptedData: OWN_SECRET })
    const updated = await call(
        vectorStoreRouter,
        'put',
        '/vs_1',
        makeReq({ query: { credential: 'cred_own' }, body: { name: 'renamed' }, user: caller() })
    )
    expectAllowed(updated.res, updated.next, OWN_SECRET)

    resetHarness()
    seedCredential({ id: 'cred_own', workspaceId: CALLER, encryptedData: OWN_SECRET })
    const deleted = await call(
        vectorStoreRouter,
        'delete',
        '/vs_1',
        makeReq({ query: { credential: 'cred_own' }, user: caller() })
    )
    expectAllowed(deleted.res, deleted.next, OWN_SECRET)
})

test('a workspace can upload files to and delete files from a vector store with its own credential', async () => {
    const uploaded = await call(
        vectorStoreRouter,
        'post',
        '/vs_1',
        makeReq({
            query: { credential: 'cred_own' },
            body: {},
            files: [{ originalname: 'notes.txt', mimetype: 'text/plain', path: '/tmp/notes.txt' }],
            user: caller()
        })
    )
    expectAllowed(uploaded.res, uploaded.next, OWN_SECRET)

    resetHarness()
    seedCredential({ id: 'cred_own', workspaceId: CALLER, encryptedData: OWN_SECRET })
    const deleted = await call(
        vectorStoreRouter,
        'patch',
        '/vs_1',
        makeReq({ query: { credential: 'cred_own' }, body: { file_ids: ['file_1'] }, user: caller() })
    )
    expectAllowed(deleted.res, deleted.next, OWN_SECRET)
})

test('a credential shared into the caller workspace still resolves for vector stores', async () => {
    seedCredential({ id: 'cred_shared', workspaceId: OWNER, encryptedData: SHARED_SECRET })
    seedShare({ workspaceId: CALLER, sharedItemId: 'cred_shared', itemType: 'credential' })
    const { res, next } = await call(
        vectorStoreRouter,
        'get',
        '/vs_9',
        makeReq({ query: { credential: 'cred_shared' }, user: caller() })
    )
    expectAllowed(res, next, SHARED_SECRET)
})

test('a workspace can list and read assistants with its own credential', async () => {
    const listed = await call(
        assistantsRouter,
        'get',
        '/',
        makeReq({ query: { credential: 'cred_own' }, user: caller() })
    )
    expectAllowed(listed.res, listed.next, OWN_SECRET)

    resetHarness()
    seedCredential({ id: 'cred_own', workspaceId: CALLER, encryptedData: OWN_SECRET })
    const single = await call(
        assistantsRouter,
        'get',
        '/asst_1',
        makeReq({ query: { credential: 'cred_own' }, user: caller() })
    )
    expectAllowed(single.res, single.next, OWN_SECRET)
})

test('a workspace can upload assistant files with its own credential', async () => {
    const { res, next } = await call(
        assistantsFileRouter,
        'post',
        '/upload/',
        makeReq({
            query: { credential: 'cred_own' },
            files: [{ originalname: 'notes.txt', mimetype: 'text/plain', path: '/tmp/notes.txt' }],
            user: caller()
        })
    )
    expectAllowed(res, next, OWN_SECRET)
})

test('a credential shared into the caller workspace still resolves for assistants', async () => {
    seedCredential({ id: 'cred_shared', workspaceId: OWNER, encryptedData: SHARED_SECRET })
    seedShare({ workspaceId: CALLER, sharedItemId: 'cred_shared', itemType: 'credential' })
    const { res, next } = await call(
        assistantsRouter,
        'get',
        '/',
        makeReq({ query: { credential: 'cred_shared' }, user: caller() })
    )
    expectAllowed(res, next, SHARED_SECRET)
})

test('a workspace can start OAuth with its own credential', async () => {
    const { res, next } = await call(
        oauth2Router,
        'post',
        '/authorize/cred_own',
        makeReq({ user: caller() })
    )
    expectDecryptedAndAnswered(res, next, OWN_SECRET)
})

test('a workspace can test its own credential', async () => {
    const { res, next } = await call(credentialsRouter, 'post', '/cred_own/test', makeReq({ user: caller() }))
    expectAllowed(res, next, OWN_SECRET)
    expectProviderUsed(next, OWN_SECRET)
})

test('a workspace can create a thread with its own credential', async () => {
    const { res, next } = await call(
        assistantsRouter,
        'post',
        '/thread',
        makeReq({ body: { credential: 'cred_own', assistantId: 'asst_1' }, user: caller() })
    )
    expectAllowed(res, next, OWN_SECRET)
    expectProviderUsed(next, OWN_SECRET)
})

test('a workspace can delete an assistant whose stored credential it owns', async () => {
    await (globalThis as any).__APPSERVER.AppDataSource.getRepository(Assistant).save({
        id: 'asst_own',
        details: JSON.stringify({ id: 'remote_asst_1' }),
        credential: 'cred_own',
        type: 'ASSISTANT',
        workspaceId: CALLER
    })
    const { res, next } = await call(
        legacyAssistantsRouter,
        'delete',
        '/asst_own',
        makeReq({ query: { isDeleteBoth: 'true' }, user: caller() })
    )
    expectAllowed(res, next, OWN_SECRET)
    expectProviderUsed(next, OWN_SECRET)
})

test('an API-key caller can use its own workspace credential', async () => {
    const { res, next } = await call(
        vectorStoreRouter,
        'get',
        '/vs_1',
        makeReq({
            query: { credential: 'cred_own' },
            user: apiKeyUser(CALLER, 'org_c', ['assistants:view'])
        })
    )
    expectAllowed(res, next, OWN_SECRET)
})

test('the credential management API still returns an owned credential', async () => {
    const { res, next } = await call(credentialsRouter, 'get', '/cred_own', makeReq({ user: caller() }))
    expectDecryptedAndAnswered(res, next, OWN_SECRET)
})

test('the credential management API still refuses another workspace credential', async () => {
    const { res, next } = await call(credentialsRouter, 'get', '/cred_foreign', makeReq({ user: caller() }))
    const error = next.mock.calls.length ? next.mock.calls[0][0] : undefined
    expect(globalThis.__decryptCalls || []).not.toContain(OTHER_SECRET)
    expect(Boolean(error) || res.statusCode >= 400).toBe(true)
})
