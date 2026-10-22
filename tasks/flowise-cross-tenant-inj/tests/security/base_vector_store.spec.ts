import ctrl from '@product/controllers/openai-assistants-vector-store'
import { resetHarness, seedCredential, seedShare, makeReq, makeRes, expectBlocked } from '../support/harness'

const ATTACKER = 'ws_attacker'
const VICTIM = 'ws_victim'
const THIRD = 'ws_third'
const SECRET = 'VICTIM-OPENAI-SECRET'

const attacker = () => ({ id: 'u_attacker', activeWorkspaceId: ATTACKER, activeOrganizationId: 'org_a' })

async function run(name: string, fn: (req: any, res: any, next: jest.Mock) => Promise<unknown>, req: any) {
    const res = makeRes()
    const next = jest.fn()
    await fn(req, res, next)
    try {
        expectBlocked(res, next, SECRET)
    } catch (error) {
        throw new Error(`${name}: ${error instanceof Error ? error.message : String(error)}`)
    }
}

beforeEach(() => {
    resetHarness()
    seedCredential({ id: 'cred_victim', workspaceId: VICTIM, encryptedData: SECRET })
})

// Every route of the module that resolves a caller-supplied credential.
const foreign = { query: { credential: 'cred_victim' }, user: attacker() }

test('cross-tenant read of a vector store does not use the foreign credential', async () => {
    await run('read', ctrl.getAssistantVectorStore, makeReq({ ...foreign, params: { id: 'vs_1' } }))
})

test('cross-tenant list of vector stores does not use the foreign credential', async () => {
    await run('list', ctrl.listAssistantVectorStore, makeReq({ ...foreign }))
})

test('cross-tenant create of a vector store does not use the foreign credential', async () => {
    await run('create', ctrl.createAssistantVectorStore, makeReq({ ...foreign, body: {} }))
})

test('cross-tenant update of a vector store does not use the foreign credential', async () => {
    await run('update', ctrl.updateAssistantVectorStore, makeReq({ ...foreign, params: { id: 'vs_1' }, body: {} }))
})

test('cross-tenant delete of a vector store does not use the foreign credential', async () => {
    await run('delete', ctrl.deleteAssistantVectorStore, makeReq({ ...foreign, params: { id: 'vs_1' } }))
})

test('cross-tenant file upload to a vector store does not use the foreign credential', async () => {
    await run('uploadFiles', ctrl.uploadFilesToAssistantVectorStore, makeReq({ ...foreign, params: { id: 'vs_1' } }))
})

test('cross-tenant file deletion from a vector store does not use the foreign credential', async () => {
    await run(
        'deleteFiles',
        ctrl.deleteFilesFromAssistantVectorStore,
        makeReq({ ...foreign, params: { id: 'vs_1' }, body: { file_ids: [] } })
    )
})

test('a caller with no active workspace cannot use a stored credential', async () => {
    const req = makeReq({
        query: { credential: 'cred_victim' },
        params: { id: 'vs_1' },
        user: { id: 'u_attacker', activeOrganizationId: 'org_a' }
    })
    await run('missing workspace', ctrl.getAssistantVectorStore, req)
})

test('a credential shared into a third workspace is not usable', async () => {
    seedShare({ workspaceId: THIRD, sharedItemId: 'cred_victim', itemType: 'credential' })
    await run('third-workspace share', ctrl.getAssistantVectorStore, makeReq({ ...foreign, params: { id: 'vs_1' } }))
})

test('a share of a different item type does not entitle the caller', async () => {
    seedShare({ workspaceId: ATTACKER, sharedItemId: 'cred_victim', itemType: 'chatflow' })
    await run('wrong item type', ctrl.getAssistantVectorStore, makeReq({ ...foreign, params: { id: 'vs_1' } }))
})

test('an attacker-supplied workspace id does not widen access', async () => {
    const req = makeReq({
        query: { credential: 'cred_victim', workspaceId: VICTIM },
        params: { id: 'vs_1' },
        user: attacker()
    })
    await run('client workspace', ctrl.getAssistantVectorStore, req)
})
