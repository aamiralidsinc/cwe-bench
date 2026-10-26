import { before, describe, it } from 'esmocha';

import {
  assertDeliveredSafely,
  assertImageOpened,
  driveAngularDetail,
  driveAngularList,
  driveAngularUpdate,
  entity,
  installRecorder,
  loadAngular,
} from '../support/harness.ts';

describe('generated Angular client: legitimate use', () => {
  let ctx: Awaited<ReturnType<typeof loadAngular>>;
  before(async () => {
    ctx = await loadAngular();
  });

  it('a PNG image still opens inline from the detail page', () => {
    const recorder = installRecorder();
    try {
      driveAngularDetail(ctx, entity({ imageContentType: 'image/png', anyContentType: 'application/pdf' }));
      assertImageOpened(recorder.records, 'image/png', 'angular detail');
    } finally {
      recorder.restore();
    }
  });

  it('a JPEG image still opens inline from the list page', () => {
    const recorder = installRecorder();
    try {
      driveAngularList(ctx, entity({ imageContentType: 'image/jpeg', anyContentType: 'application/pdf' }));
      assertImageOpened(recorder.records, 'image/jpeg', 'angular list');
    } finally {
      recorder.restore();
    }
  });

  it('an ordinary document is still delivered', () => {
    const recorder = installRecorder();
    try {
      driveAngularDetail(ctx, entity({ imageContentType: 'image/png', anyContentType: 'application/pdf' }));
      assertDeliveredSafely(recorder.records, 'angular detail document');
    } finally {
      recorder.restore();
    }
  });

  it('the edit form still opens a stored file', () => {
    const recorder = installRecorder();
    try {
      driveAngularUpdate(ctx, entity({ imageContentType: 'image/png', anyContentType: 'image/png' }));
      assertDeliveredSafely(recorder.records, 'angular update');
    } finally {
      recorder.restore();
    }
  });

  it('the size label still works', () => {
    const label = ctx.dataUtils.byteSize('SkhpcHN0ZXI=');
    if (!/\d+\s*bytes?/i.test(String(label))) throw new Error(`unexpected size label: ${label}`);
  });
});
