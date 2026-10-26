import { before, describe, it } from 'esmocha';

import {
  assertDeliveredSafely,
  driveVueDetails,
  driveVueList,
  driveVueUpdate,
  entity,
  installRecorder,
  loadVue,
} from '../support/harness.ts';

describe('generated Vue client: opening a stored file', () => {
  let ctx: Awaited<ReturnType<typeof loadVue>>;
  before(async () => {
    ctx = await loadVue();
  });

  it('an image field with an HTML document type is not rendered as a document', () => {
    const recorder = installRecorder();
    try {
      driveVueDetails(ctx, entity({ imageContentType: 'text/html', anyContentType: 'application/pdf' }));
      assertDeliveredSafely(recorder.records, 'vue details');
    } finally {
      recorder.restore();
    }
  });

  it('an image field with an XML image type is not rendered as a document', () => {
    const recorder = installRecorder();
    try {
      driveVueDetails(ctx, entity({ imageContentType: 'image/svg+xml', anyContentType: 'application/pdf' }));
      assertDeliveredSafely(recorder.records, 'vue details');
    } finally {
      recorder.restore();
    }
  });

  it('a mixed-case XML image type in the list is not rendered as a document', () => {
    const recorder = installRecorder();
    try {
      driveVueList(ctx, entity({ imageContentType: 'Image/SVG+XML', anyContentType: 'application/pdf' }));
      assertDeliveredSafely(recorder.records, 'vue list');
    } finally {
      recorder.restore();
    }
  });

  it('an any-type field with an HTML document type is not rendered as a document', () => {
    const recorder = installRecorder();
    try {
      driveVueList(ctx, entity({ imageContentType: 'image/png', anyContentType: 'text/html' }));
      assertDeliveredSafely(recorder.records, 'vue list');
    } finally {
      recorder.restore();
    }
  });

  it('an any-type field in the edit form is not rendered as a document', () => {
    const recorder = installRecorder();
    try {
      driveVueUpdate(ctx, entity({ imageContentType: 'image/png', anyContentType: 'text/html' }));
      assertDeliveredSafely(recorder.records, 'vue update');
    } finally {
      recorder.restore();
    }
  });

  it('an XML image type in the edit form is not rendered as a document', () => {
    const recorder = installRecorder();
    try {
      driveVueUpdate(ctx, entity({ imageContentType: 'image/png', anyContentType: 'image/svg+xml; charset=utf-8' }));
      assertDeliveredSafely(recorder.records, 'vue update');
    } finally {
      recorder.restore();
    }
  });
});
