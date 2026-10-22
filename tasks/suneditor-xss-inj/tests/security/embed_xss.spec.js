/**
 * Security: raw embed HTML pasted into the editor must not cause attacker-controlled script
 * or framed content to become active in the editor page. Each test drives the public embed
 * submit API and FAILS on the vulnerable plugin, PASSES once the flaw and its variants close.
 */
jest.mock('@contract', () => require('../support/_contract'));
jest.mock('@helper', () => require('../support/_helper'));
const { makeEmbed, insertedContainer, createdScriptSrcs } = require('../support/harness');

const PROVIDER = 'https://www.facebook.com/plugins/post.php?href=test';
const EVIL = 'https://marker.invalid/payload.js';

afterEach(() => { jest.clearAllMocks(); document.body.innerHTML = ''; });

function liveScripts(container) { return container ? Array.from(container.querySelectorAll('script')).map((s) => s.getAttribute('src') || '') : []; }

it('a pasted top-level script is not made live', async () => {
  const embed = makeEmbed();
  await embed.submitSRC(`<iframe src="${PROVIDER}"></iframe><script src="${EVIL}"></script>`);
  const c = insertedContainer(embed);
  expect(createdScriptSrcs(embed)).not.toContain(EVIL);
  expect(liveScripts(c)).not.toContain(EVIL);
});

it('a pasted iframe pointing off the known providers is rejected', async () => {
  const embed = makeEmbed();
  const r = await embed.submitSRC('<iframe src="https://marker.invalid/frame"></iframe>');
  const c = insertedContainer(embed);
  const bad = c ? Array.from(c.querySelectorAll('iframe')).some((f) => (f.getAttribute('src') || '').includes('marker.invalid')) : false;
  expect(bad).toBe(false);
  expect(r === false || !bad).toBe(true);
});

it('an off-provider iframe nested in a blockquote is rejected', async () => {
  const embed = makeEmbed();
  await embed.submitSRC('<blockquote class="x"><iframe src="https://marker.invalid/frame"></iframe></blockquote>');
  const c = insertedContainer(embed);
  const bad = c ? Array.from(c.querySelectorAll('iframe')).some((f) => (f.getAttribute('src') || '').includes('marker.invalid')) : false;
  expect(bad).toBe(false);
});

it('an allowed iframe may not smuggle inline content via srcdoc', async () => {
  const embed = makeEmbed();
  await embed.submitSRC(`<iframe src="${PROVIDER}" srcdoc="<img src=x onerror=1>"></iframe>`);
  const c = insertedContainer(embed);
  const bad = c ? Array.from(c.querySelectorAll('iframe')).some((f) => f.hasAttribute('srcdoc')) : false;
  expect(bad).toBe(false);
});

it('a pasted sibling element may not keep an inline event-handler attribute', async () => {
  const embed = makeEmbed();
  await embed.submitSRC(`<iframe src="${PROVIDER}"></iframe><img src="x" onerror="1">`);
  const c = insertedContainer(embed);
  const hasHandler = c ? c.querySelector('[onerror]') != null : false;
  expect(hasHandler).toBe(false);
});

it('a script nested inside a pasted blockquote is not made live', async () => {
  const embed = makeEmbed();
  await embed.submitSRC(`<blockquote class="twitter-tweet"><script src="${EVIL}"></script></blockquote>`);
  const c = insertedContainer(embed);
  expect(createdScriptSrcs(embed)).not.toContain(EVIL);
  expect(liveScripts(c)).not.toContain(EVIL);
});

it('editing an existing embed with pasted code may not make a script live', async () => {
  const embed = makeEmbed();
  const existing = { nodeName: 'IFRAME', src: PROVIDER, style: {}, getAttribute: () => PROVIDER };
  embed.componentSelect(existing);
  embed.modal.isUpdate = true;
  await embed.submitSRC(`<iframe src="${PROVIDER}"></iframe><script src="${EVIL}"></script>`);
  expect(createdScriptSrcs(embed)).not.toContain(EVIL);
});
