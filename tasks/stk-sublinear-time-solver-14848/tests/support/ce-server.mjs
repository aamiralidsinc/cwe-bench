// Launch the consciousness-explorer MCP server over stdio for the hidden suites.
import { ROOT } from './env.mjs';

const { ConsciousnessExplorer } = await import(ROOT + '/src/consciousness-explorer/index.js');
const explorer = new ConsciousnessExplorer({ enableMCP: true });
await explorer.initialize();
await explorer.startMCPServer(0);
