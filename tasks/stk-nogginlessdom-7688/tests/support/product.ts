// Product access for the hidden suites. The suites run against the restored
// /workspace; PRODUCT_ROOT exists only so the same files can be exercised
// against a scratch checkout while the task is being built.
const root = process.env['PRODUCT_ROOT'] ?? '/workspace';

const assertions = await import(`${root}/src/assertions/index.ts`);
const snapshots = await import(`${root}/src/assertions/snapshots.ts`);
const client = await import(`${root}/src/assertions/snapshot-client.ts`);
const environment = await import(`${root}/src/assertions/snapshot-environment.ts`);
const manager = await import(`${root}/src/assertions/snapshot-manager.ts`);

export const expect = assertions.expect as (actual: unknown) => any;
export const serialize = snapshots.serialize as (value: unknown) => string;
export const setUpdateMode = snapshots.setUpdateMode as (
  mode: 'all' | 'new' | 'none',
) => void;
export const SnapshotClient = client.SnapshotClient as any;
export const NodeSnapshotEnvironment = environment.NodeSnapshotEnvironment as any;
export const SnapshotManager = manager.SnapshotManager as any;
