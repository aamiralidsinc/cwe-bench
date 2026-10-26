import { before, describe, it } from 'esmocha';

import { assertImageOpened, installRecorder, loadHelper, type HelperContext } from '../support/harness.ts';

const DATA = 'SkhpcHN0ZXI=';

describe('generated shared helper: legitimate use', () => {
  const clients = ['angular', 'react', 'vue'] as const;
  const helpers: Record<string, HelperContext> = {};

  before(async () => {
    for (const client of clients) helpers[client] = await loadHelper(client);
  });

  for (const client of clients) {
    it(`the ${client} helper still opens a PNG image inline`, () => {
      const recorder = installRecorder();
      try {
        helpers[client].openFile(DATA, 'image/png', 'image');
        assertImageOpened(recorder.records, 'image/png', `${client} helper`);
      } finally {
        recorder.restore();
      }
    });

    it(`the ${client} helper still reports the stored size`, () => {
      const label = helpers[client].byteSize(DATA);
      if (!/\d+\s*bytes?/i.test(String(label))) throw new Error(`unexpected size label: ${label}`);
    });
  }
});
