import vsCtrl from '@product/controllers/openai-assistants-vector-store'
import asstCtrl from '@product/controllers/openai-assistants'
import { resetHarness, seedCredential, seedShare, makeReq, makeRes, openaiKeys } from '../support/harness'

const CALLER = 'ws_caller'
const OWNER = 'ws_owner'
const OWN_SECRET = 'OWN-OPENAI-SECRET'
const SHARED_SECRET = 'SHARED-OPENAI-SECRET'

const caller = () => ({ id: 'u_caller', activeWorkspaceId: CALLER, activeOrganizationId: 'org_c' })

function assertAllowed(res: any, next: jest.Mock, secret: string) {
    expect(next).not.toHaveBeenCalled()
    expect(res.jsonCalled).toBe(true)
    expect(openaiKeys()).toContain(secret)
}

beforeEach(() => {
    resetHarness()
    // A credential the caller's own workspace owns.
    seedCredential({ id: 'cred_own', workspaceId: CALLER, encryptedData: OWN_SECRET })
})

test('a workspace can read its own vector store', async () => {
    const req = makeReq({ query: { credential: 'cred_own' }, params: { id: 'vs_1' }, user: caller() })
    const res = makeRes()
    const next = jest.fn()
    await vsCtrl.getAssistantVectorStore(req, res, next)
    assertAllowed(res, next, OWN_SECRET)
})

test('a workspace can list assistants with its own credential', async () => {
    const req = makeReq({ query: { credential: 'cred_own' }, user: caller() })
    const res = makeRes()
    const next = jest.fn()
    await asstCtrl.getAllOpenaiAssistants(req, res, next)
    assertAllowed(res, next, OWN_SECRET)
})

test('a workspace can list models with its own credential', async () => {
    const req = makeReq({ query: { credential: 'cred_own' }, user: caller() })
    const res = makeRes()
    const next = jest.fn()
    await asstCtrl.getAssistantModels(req, res, next)
    assertAllowed(res, next, OWN_SECRET)
})

test('a workspace can verify its own credential', async () => {
    const req = makeReq({ body: { credential: 'cred_own' }, user: caller() })
    const res = makeRes()
    const next = jest.fn()
    await asstCtrl.verifyAssistantCredential(req, res, next)
    assertAllowed(res, next, OWN_SECRET)
})

test('a credential shared into the caller workspace still resolves (vector store)', async () => {
    // Owned by another workspace, but explicitly shared to the caller's workspace.
    seedCredential({ id: 'cred_shared', workspaceId: OWNER, encryptedData: SHARED_SECRET })
    seedShare({ workspaceId: CALLER, sharedItemId: 'cred_shared', itemType: 'credential' })
    const req = makeReq({ query: { credential: 'cred_shared' }, params: { id: 'vs_9' }, user: caller() })
    const res = makeRes()
    const next = jest.fn()
    await vsCtrl.getAssistantVectorStore(req, res, next)
    assertAllowed(res, next, SHARED_SECRET)
})

test('a credential shared into the caller workspace still resolves (assistants)', async () => {
    seedCredential({ id: 'cred_shared', workspaceId: OWNER, encryptedData: SHARED_SECRET })
    seedShare({ workspaceId: CALLER, sharedItemId: 'cred_shared', itemType: 'credential' })
    const req = makeReq({ query: { credential: 'cred_shared' }, user: caller() })
    const res = makeRes()
    const next = jest.fn()
    await asstCtrl.getAllOpenaiAssistants(req, res, next)
    assertAllowed(res, next, SHARED_SECRET)
})
