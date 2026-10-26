import { before, describe, it } from 'esmocha';

import {
  assertDeliveredSafely,
  assertImageOpened,
  driveReactDetail,
  driveReactList,
  entity,
  installRecorder,
  loadReact,
} from '../support/harness.ts';

describe('generated React client: legitimate use', () => {
  let ctx: Awaited<ReturnType<typeof loadReact>>;
  before(async () => {
    ctx = await loadReact();
  });

  it('a PNG image still opens inline from the detail page', () => {
    const recorder = installRecorder();
    try {
      driveReactDetail(ctx, entity({ imageContentType: 'image/png', anyContentType: 'application/pdf' }));
      assertImageOpened(recorder.records, 'image/png', 'react detail');
    } finally {
      recorder.restore();
    }
  });

  it('a GIF image still opens inline from the list page', () => {
    const recorder = installRecorder();
    try {
      driveReactList(ctx, entity({ imageContentType: 'image/gif', anyContentType: 'application/pdf' }));
      assertImageOpened(recorder.records, 'image/gif', 'react list');
    } finally {
      recorder.restore();
    }
  });

  it('an ordinary document is still delivered', () => {
    const recorder = installRecorder();
    try {
      driveReactDetail(ctx, entity({ imageContentType: 'image/png', anyContentType: 'application/pdf' }));
      assertDeliveredSafely(recorder.records, 'react detail document');
    } finally {
      recorder.restore();
    }
  });
});
