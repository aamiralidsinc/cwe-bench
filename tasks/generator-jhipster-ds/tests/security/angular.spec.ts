import { before, describe, it } from 'esmocha';

import {
  assertDeliveredSafely,
  driveAngularDetail,
  driveAngularList,
  driveAngularUpdate,
  entity,
  installRecorder,
  loadAngular,
} from '../support/harness.ts';

describe('generated Angular client: opening a stored file', () => {
  let ctx: Awaited<ReturnType<typeof loadAngular>>;
  before(async () => {
    ctx = await loadAngular();
  });

  it('an image field with an HTML document type is not rendered as a document', () => {
    const recorder = installRecorder();
    try {
      driveAngularDetail(ctx, entity({ imageContentType: 'text/html', anyContentType: 'application/pdf' }));
      assertDeliveredSafely(recorder.records, 'angular detail');
    } finally {
      recorder.restore();
    }
  });

  it('an image field with an XML image type is not rendered as a document', () => {
    const recorder = installRecorder();
    try {
      driveAngularDetail(ctx, entity({ imageContentType: 'image/svg+xml', anyContentType: 'application/pdf' }));
      assertDeliveredSafely(recorder.records, 'angular detail');
    } finally {
      recorder.restore();
    }
  });

  it('a parameterised mixed-case XML image type is not rendered as a document', () => {
    const recorder = installRecorder();
    try {
      driveAngularList(ctx, entity({ imageContentType: 'Image/SVG+XML; charset=UTF-8', anyContentType: 'application/pdf' }));
      assertDeliveredSafely(recorder.records, 'angular list');
    } finally {
      recorder.restore();
    }
  });

  it('an any-type field with an HTML document type is not rendered as a document', () => {
    const recorder = installRecorder();
    try {
      driveAngularList(ctx, entity({ imageContentType: 'image/png', anyContentType: 'TEXT/HTML' }));
      assertDeliveredSafely(recorder.records, 'angular list');
    } finally {
      recorder.restore();
    }
  });

  it('an any-type field in the edit form is not rendered as a document', () => {
    const recorder = installRecorder();
    try {
      driveAngularUpdate(ctx, entity({ imageContentType: 'image/png', anyContentType: 'text/html' }));
      assertDeliveredSafely(recorder.records, 'angular update');
    } finally {
      recorder.restore();
    }
  });

  it('an XML image type in the edit form is not rendered as a document', () => {
    const recorder = installRecorder();
    try {
      driveAngularUpdate(ctx, entity({ imageContentType: 'image/png', anyContentType: 'image/svg+xml' }));
      assertDeliveredSafely(recorder.records, 'angular update');
    } finally {
      recorder.restore();
    }
  });
});
