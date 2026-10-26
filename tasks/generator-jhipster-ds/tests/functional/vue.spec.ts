import { before, describe, it } from 'esmocha';

import {
  assertDeliveredSafely,
  assertImageOpened,
  driveVueDetails,
  driveVueList,
  driveVueUpdate,
  entity,
  installRecorder,
  loadVue,
} from '../support/harness.ts';

describe('generated Vue client: legitimate use', () => {
  let ctx: Awaited<ReturnType<typeof loadVue>>;
  before(async () => {
    ctx = await loadVue();
  });

  it('a PNG image still opens inline from the details page', () => {
    const recorder = installRecorder();
    try {
      driveVueDetails(ctx, entity({ imageContentType: 'image/png', anyContentType: 'application/pdf' }));
      assertImageOpened(recorder.records, 'image/png', 'vue details');
    } finally {
      recorder.restore();
    }
  });

  it('a JPEG image still opens inline from the list page', () => {
    const recorder = installRecorder();
    try {
      driveVueList(ctx, entity({ imageContentType: 'image/jpeg', anyContentType: 'application/pdf' }));
      assertImageOpened(recorder.records, 'image/jpeg', 'vue list');
    } finally {
      recorder.restore();
    }
  });

  it('an ordinary document is still delivered', () => {
    const recorder = installRecorder();
    try {
      driveVueDetails(ctx, entity({ imageContentType: 'image/png', anyContentType: 'application/pdf' }));
      assertDeliveredSafely(recorder.records, 'vue details document');
    } finally {
      recorder.restore();
    }
  });

  it('the edit form still opens a stored file', () => {
    const recorder = installRecorder();
    try {
      driveVueUpdate(ctx, entity({ imageContentType: 'image/png', anyContentType: 'image/png' }));
      assertDeliveredSafely(recorder.records, 'vue update');
    } finally {
      recorder.restore();
    }
  });

  it('the composable still reports the stored size', () => {
    const dataUtils = ctx.composable.default();
    const label = dataUtils.byteSize('SkhpcHN0ZXI=');
    if (!/\d+\s*bytes?/i.test(String(label))) throw new Error(`unexpected size label: ${label}`);
  });
});
