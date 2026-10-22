// Shared helpers for the embed verifier tests. Imported after the module mocks are registered.
const { createMockEditor } = require('@editorMock');
const Embed = require('@product').default;

function makeEmbed(pluginOptions = {}) {
  const embed = new Embed(createMockEditor(), { canResize: true, ...pluginOptions });
  if (embed.inputX) Object.assign(embed.inputX, { value: '' });
  if (embed.inputY) Object.assign(embed.inputY, { value: '' });
  if (embed.proportion) Object.assign(embed.proportion, { checked: false, disabled: false });
  // Approve the embed as an integrator event listener that accepts the paste would.
  embed.$.eventManager.triggerEvent = jest.fn().mockImplementation(async (name, data) => {
    if (name === 'onEmbedInputBefore' && data.handler) data.handler(null);
    return undefined;
  });
  return embed;
}
function insertedContainer(embed) { const c = embed.$.component.insert.mock.calls; return c.length ? c[c.length - 1][0] : null; }
function createdScriptSrcs(embed) { const ce = require('@helper').dom.utils.createElement; return ce.mock.calls.filter((c) => String(c[0]).toLowerCase() === 'script').map((c) => (c[1] && c[1].src) || ''); }
module.exports = { makeEmbed, insertedContainer, createdScriptSrcs, Embed };
