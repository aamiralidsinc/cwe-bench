// Minimal offline stand-in for the workspace service: only the shared-items
// lookup used by credential resolution. Backed by the same in-memory
// repositories as the product code, with the real method's semantics (filter
// the share rows by workspace and item type, then load the matching items).
const { Credential } = require('@product/database/entities/Credential')
const { WorkspaceShared } = require('@product/enterprise/database/entities/EnterpriseEntities')

class WorkspaceService {
    constructor() {
        this.dataSource = globalThis.__APPSERVER.AppDataSource
    }

    async getSharedItemsForWorkspace(wsId, itemType) {
        const sharedItems = await this.dataSource.getRepository(WorkspaceShared).find({
            where: { workspaceId: wsId, itemType }
        })
        if (sharedItems.length === 0) return []
        const itemIds = sharedItems.map((item) => item.sharedItemId)
        if (itemType === 'credential') {
            return await this.dataSource.getRepository(Credential).find({
                where: { id: { __op: 'in', value: itemIds } }
            })
        }
        return []
    }

    async setSharedWorkspacesForItem() {
        return { message: 'Updated' }
    }
}

module.exports = { WorkspaceService }
