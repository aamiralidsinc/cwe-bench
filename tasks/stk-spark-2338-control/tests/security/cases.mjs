/*
 * Security cases (control task): the advisory's own route only - an application name carried in
 * the event-log record must be shown as literal text, in a short name and through the expanded
 * details of a long one, whatever markup the name contains.  The real page module is driven in a
 * jsdom document with the project's own vendored jQuery/DataTables/Mustache; only the listing
 * response is stubbed.
 */
import {
  application, attempt, cell, assertInert, assertShownAsText, renderPage, rowForId,
} from '../support/harness.mjs';

const IMG = '<img src=x onerror=alert(1)>';
const SCRIPT = '<script>alert(1)</script>';

function caseDef(id, name, apps, run) {
  return { id, classname: 'security/' + id, name, apps, run };
}

function nameCase(id, label, value) {
  return caseDef(id, label,
    [application('application_1700000000000_0001', value, [attempt('1', 'alice', '3.5.0')])],
    (page) => {
      const td = cell(page, rowForId(page, 'application_1700000000000_0001'), 'App Name');
      assertInert(td, id);
      assertShownAsText(td, value, id);
    });
}

export const cases = [
  nameCase('app-name-element', 'an image element in the application name is shown as text', 'etl-' + IMG),
  nameCase('app-name-script', 'a script element in the application name is shown as text', 'etl-' + SCRIPT),
  nameCase('app-name-nested', 'nested markup in the application name is shown as text',
    'etl-' + '<div><b>' + IMG + '</b></div>'),
  nameCase('app-name-svg', 'an svg element in the application name is shown as text',
    'etl-<svg onload=alert(1)></svg>'),

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
];

export default cases;
