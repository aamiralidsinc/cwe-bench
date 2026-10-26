// Location of the project under test.  The verifier restores it at /workspace; a
// local dry-run may point CWE_TASK_ROOT at a checkout.
export const ROOT = process.env.CWE_TASK_ROOT || '/workspace';
