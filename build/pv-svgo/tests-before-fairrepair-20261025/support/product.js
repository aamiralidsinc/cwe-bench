'use strict';

// The optimizer's public library entry point (the package's "main"), as a downstream user calls it.
const { optimize } = require('/workspace/lib/svgo-node.js');

const CONFIG = { plugins: ['removeScriptElement'] };

/**
 * Run the document through the optimizer with script removal enabled and return the output.
 * Hostile input must be sanitised, not rejected: a throw is a failed sanitisation, not a refusal.
 *
 * @param {string} svg
 * @returns {string}
 */
exports.sanitize = (svg) => {
  let result;
  try {
    result = optimize(svg, CONFIG);
  } catch (error) {
    throw new Error(
      'the optimizer failed on hostile input instead of removing the dangerous content: ' +
        (error && error.message ? error.message : String(error)),
    );
  }
  if (result == null || typeof result.data !== 'string') {
    throw new Error('the optimizer did not return a document');
  }
  return result.data;
};

exports.optimize = optimize;
exports.CONFIG = CONFIG;
