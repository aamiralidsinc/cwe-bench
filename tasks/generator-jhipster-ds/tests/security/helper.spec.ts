import { before, describe, it } from 'esmocha';

import { assertDeliveredSafely, installRecorder, loadHelper, type HelperContext } from '../support/harness.ts';

const DATA = 'SkhpcHN0ZXI=';

describe('generated shared helper: opening a stored file', () => {
  const clients = ['angular', 'react', 'vue'] as const;
  const helpers: Record<string, HelperContext> = {};

  before(async () => {
    for (const client of clients) helpers[client] = await loadHelper(client);
  });

  for (const client of clients) {
    it(`the ${client} helper does not render an HTML document type`, () => {
      const recorder = installRecorder();
      try {
        helpers[client].openFile(DATA, 'text/html');
        assertDeliveredSafely(recorder.records, `${client} helper`);
      } finally {
        recorder.restore();
      }
    });

    it(`the ${client} helper does not render an XML image type`, () => {
      const recorder = installRecorder();
      try {
        helpers[client].openFile(DATA, 'image/svg+xml');
        assertDeliveredSafely(recorder.records, `${client} helper`);
      } finally {
        recorder.restore();
      }
    });

    it(`the ${client} helper ignores parameters and case around an XML image type`, () => {
      const recorder = installRecorder();
      try {
        helpers[client].openFile(DATA, ' Image/SVG+XML; charset=utf-8', 'image');
        assertDeliveredSafely(recorder.records, `${client} helper`);
      } finally {
        recorder.restore();
      }
    });

    it(`the ${client} helper does not render an XHTML document type`, () => {
      const recorder = installRecorder();
      try {
        helpers[client].openFile(DATA, 'application/xhtml+xml');
        assertDeliveredSafely(recorder.records, `${client} helper`);
      } finally {
        recorder.restore();
      }
    });
  }
});
