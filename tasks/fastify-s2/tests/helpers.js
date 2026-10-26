'use strict'

const path = require('node:path')

const WORKSPACE = process.env.WORKSPACE_DIR || '/workspace'

// The product under test. Tests drive it only through its public HTTP surface.
const Fastify = require(path.join(WORKSPACE, 'fastify.js'))

// A request is blocked when the client gets a client error and nothing ran.
function isClientError (res) {
  return typeof res.statusCode === 'number' && res.statusCode >= 400 && res.statusCode < 500
}

// A configuration the server will not apply is refused when the instance never becomes
// ready. Returns true when ready() rejected.
async function refusedAtStartup (app) {
  try {
    await app.ready()
    return false
  } catch (err) {
    return true
  }
}

module.exports = { Fastify, WORKSPACE, isClientError, refusedAtStartup }
