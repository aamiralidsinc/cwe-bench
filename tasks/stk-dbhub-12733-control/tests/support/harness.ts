import { ConnectorManager } from '../../src/connectors/manager.js';
import { initializeToolRegistry } from '../../src/tools/registry.js';
import { createExecuteSqlToolHandler } from '../../src/tools/execute-sql.js';
import type { SourceConfig } from '../../src/types/config.js';

export interface ToolCall {
  isError: boolean;
  payload: any;
}

let sourcesInUse: SourceConfig[] = [];

function configure(readonly: boolean): void {
  initializeToolRegistry({
    sources: sourcesInUse,
    tools: sourcesInUse.map((s) => ({ name: 'execute_sql', source: s.id, readonly })),
  } as any);
}

/** Connect one or more sources through the real manager and enable the SQL tool on each. */
export async function connectSources(sources: SourceConfig[], readonly: boolean): Promise<ConnectorManager> {
  const manager = new ConnectorManager();
  await manager.connectWithSources(sources);
  sourcesInUse = sources;
  configure(readonly);
  return manager;
}

/** Switch the SQL tool between read-only and writable on the connected sources. */
export function setReadonly(readonly: boolean): void {
  configure(readonly);
}

/** Drive the real `execute_sql` tool handler. */
export async function callExecuteSql(sql: string, sourceId?: string): Promise<ToolCall> {
  const handler = createExecuteSqlToolHandler(sourceId);
  const response: any = await handler({ sql }, {});
  let payload: any = null;
  try {
    payload = JSON.parse(response.content[0].text);
  } catch {
    payload = { raw: response?.content?.[0]?.text };
  }
  return { isError: !!response.isError, payload };
}
