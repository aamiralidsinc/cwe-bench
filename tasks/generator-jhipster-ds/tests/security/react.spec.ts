import { before, describe, it } from 'esmocha';

import {
  assertDeliveredSafely,
  driveReactDetail,
  driveReactList,
  entity,
  installRecorder,
  loadReact,
} from '../support/harness.ts';

describe('generated React client: opening a stored file', () => {
  let ctx: Awaited<ReturnType<typeof loadReact>>;
  before(async () => {
    ctx = await loadReact();
  });

  it('an image field with an HTML document type is not rendered as a document', () => {
    const recorder = installRecorder();
    try {
      driveReactDetail(ctx, entity({ imageContentType: 'text/html', anyContentType: 'application/pdf' }));
      assertDeliveredSafely(recorder.records, 'react detail');
    } finally {
      recorder.restore();
    }
  });

  it('an image field with an XML image type is not rendered as a document', () => {
    const recorder = installRecorder();
    try {
      driveReactDetail(ctx, entity({ imageContentType: 'image/svg+xml', anyContentType: 'application/pdf' }));
      assertDeliveredSafely(recorder.records, 'react detail');
    } finally {
      recorder.restore();
    }
  });

  it('an any-type field with an HTML document type is not rendered as a document', () => {
    const recorder = installRecorder();
    try {
      driveReactList(ctx, entity({ imageContentType: 'image/png', anyContentType: 'text/html' }));
      assertDeliveredSafely(recorder.records, 'react list');
    } finally {
      recorder.restore();
    }
  });

  it('a parameterised XML image type in the list is not rendered as a document', () => {
    const recorder = installRecorder();
    try {
      driveReactList(ctx, entity({ imageContentType: 'IMAGE/SVG+XML;charset=UTF-8', anyContentType: 'application/pdf' }));
      assertDeliveredSafely(recorder.records, 'react list');
    } finally {
      recorder.restore();
    }
  });
});
