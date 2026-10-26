/*
 * Security cases: values carried in an application's event-log record must be shown by the
 * history page as literal text, never interpreted as markup.  Each case drives the real page
 * module in a jsdom document with the project's own vendored jQuery/DataTables/Mustache; the
 * only stubbed surface is the HTTP response that carries the application record.
 */
import {
  application, attempt, cell, cellIndex, assertInert, assertRowInert, assertShownAsText,
  closePage, renderPage, rowForId,
} from '../support/harness.mjs';

const IMG = '<img src=x onerror=alert(1)>';
const ATTR = '" onmouseover="alert(1)';

function caseDef(id, name, apps, run) {
  return { id, classname: 'security/' + id, name, apps, run };
}

export const cases = [
  caseDef(
    'app-name-short',
    'a short application name is shown as text',
    [application('application_1700000000000_0001', 'etl-' + IMG, [attempt('1', 'alice', '3.5.0')])],
    (page) => {
      const td = cell(page, rowForId(page, 'application_1700000000000_0001'), 'App Name');
      assertInert(td, 'app-name-short');
      assertShownAsText(td, 'etl-' + IMG, 'app-name-short');
    }),

  caseDef(
    'app-name-long-details',
    'a long application name is shown as text, including in its expanded details',
    [application('application_1700000000000_0002',
      'A'.repeat(70) + IMG + ' tail', [attempt('1', 'alice', '3.5.0')])],
    (page) => {
      const full = 'A'.repeat(70) + IMG + ' tail';
      const td = cell(page, rowForId(page, 'application_1700000000000_0002'), 'App Name');
      assertInert(td, 'app-name-long-details');
      assertShownAsText(td, full, 'app-name-long-details');
      const pre = td.querySelector('pre');
      if (pre) {
        if (pre.children.length !== 0) {
          throw new Error('app-name-long-details: the expanded details contain live elements');
        }
        assertShownAsText(pre, full, 'app-name-long-details pre');
      }
    }),

  caseDef(
    'spark-user',
    'the application user is shown as text',
    [application('application_1700000000000_0003', 'etl', [attempt('1', 'user-' + IMG, '3.5.0')])],
    (page) => {
      const td = cell(page, rowForId(page, 'application_1700000000000_0003'), 'Spark User');
      assertInert(td, 'spark-user');
      assertShownAsText(td, 'user-' + IMG, 'spark-user');
    }),

  caseDef(
    'version',
    'the application version is shown as text',
    [application('application_1700000000000_0004', 'etl',
      [attempt('1', 'alice', '3.5.0-' + IMG)])],
    (page) => {
      const td = cell(page, rowForId(page, 'application_1700000000000_0004'), 'Version');
      assertInert(td, 'version');
      assertShownAsText(td, '3.5.0-' + IMG, 'version');
    }),

  caseDef(
    'app-id-attribute',
    'an application id cannot break out of a rendered attribute',
    [application('application_1700000000000_0005' + ATTR, 'etl',
      [attempt('1', 'alice', '3.5.0'), attempt('2', 'alice', '3.5.0')])],
    (page) => {
      const id = 'application_1700000000000_0005' + ATTR;
      const row = rowForId(page, id);
      assertRowInert(row, 'app-id-attribute');
      assertShownAsText(cell(page, row, 'App ID'), id, 'app-id-attribute');
      assertInert(cell(page, row, 'Event Log'), 'app-id-attribute download');
    }),

  caseDef(
    'app-id-element',
    'an application id cannot create an element in the table',
    [application('application_' + IMG + '_0006', 'etl', [attempt('1', 'alice', '3.5.0')])],
    (page) => {
      const id = 'application_' + IMG + '_0006';
      const row = rowForId(page, id);
      assertRowInert(row, 'app-id-element');
      assertShownAsText(cell(page, row, 'App ID'), id, 'app-id-element');
    }),

  caseDef(
    'attempt-id-attribute',
    'an attempt id cannot break out of a rendered attribute',
    [application('application_1700000000000_0007', 'etl',
      [attempt('1' + ATTR, 'alice', '3.5.0'), attempt('1' + ATTR, 'alice', '3.5.0')])],
    (page) => {
      const id = 'application_1700000000000_0007';
      const value = '1' + ATTR;
      const row = rowForId(page, id);
      assertRowInert(row, 'attempt-id-attribute');
      assertShownAsText(cell(page, row, 'Attempt ID'), value, 'attempt-id-attribute');
    }),

  caseDef(
    'attempt-id-element',
    'an attempt id cannot create an element in the table',
    [application('application_1700000000000_0008', 'etl',
      [attempt(IMG, 'alice', '3.5.0'), attempt(IMG, 'alice', '3.5.0')])],
    (page) => {
      const id = 'application_1700000000000_0008';
      const row = rowForId(page, id);
      assertRowInert(row, 'attempt-id-element');
      assertShownAsText(cell(page, row, 'Attempt ID'), IMG, 'attempt-id-element');
    }),
];

export default cases;
