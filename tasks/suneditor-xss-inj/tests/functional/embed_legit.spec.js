/**
 * Functional: legitimate embedding must keep working exactly as before. These pass on both the
 * vulnerable and the fixed plugin, so an over-broad fix that rejects valid embeds is caught.
 */
jest.mock('@contract', () => require('../support/_contract'));
jest.mock('@helper', () => require('../support/_helper'));
const { makeEmbed, insertedContainer } = require('../support/harness');

const PROVIDER = 'https://www.facebook.com/plugins/post.php?href=test';
const TWITTER_WIDGETS = 'https://platform.twitter.com/widgets.js';

afterEach(() => { jest.clearAllMocks(); document.body.innerHTML = ''; });

it('a provider iframe embed code inserts', async () => {
  const embed = makeEmbed();
  const r = await embed.submitSRC(`<iframe src="${PROVIDER}"></iframe>`);
  expect(r).toBe(true);
  expect(embed.$.component.insert).toHaveBeenCalled();
});

it('a provider URL embed inserts', async () => {
  const embed = makeEmbed();
  const r = await embed.submitSRC('https://www.facebook.com/user/posts/123');
  expect(r).toBe(true);
  expect(embed.$.component.insert).toHaveBeenCalled();
});

it('a plain provider blockquote inserts', async () => {
  const embed = makeEmbed();
  const r = await embed.submitSRC('<blockquote class="twitter-tweet">hello</blockquote>');
  expect(r).toBe(true);
  expect(embed.$.component.insert).toHaveBeenCalled();
});

it('a provider blockquote shipped with a loader script still inserts', async () => {
  // Real provider embeds (e.g. Twitter, Instagram) paste a <blockquote> next to a loader
  // <script>. Gating the script is fine, but the embed itself must still be inserted.
  const embed = makeEmbed();
  const r = await embed.submitSRC(`<blockquote class="twitter-tweet">Tweet</blockquote><script src="${TWITTER_WIDGETS}"></script>`);
  expect(r).toBe(true);
  expect(embed.$.component.insert).toHaveBeenCalled();
  const c = insertedContainer(embed);
  expect(c.querySelector('blockquote')).not.toBeNull();
});

it('ordinary markup pasted alongside a provider embed is preserved', async () => {
  const embed = makeEmbed();
  await embed.submitSRC(`<iframe src="${PROVIDER}"></iframe><p class="caption">A caption</p>`);
  const c = insertedContainer(embed);
  const p = c ? c.querySelector('p.caption') : null;
  expect(p).not.toBeNull();
  expect(p.textContent).toBe('A caption');
});
