<hidden_tests_py>
import json
import os
import subprocess
from pathlib import Path

import pytest

REPO = Path(os.environ.get("REPO_ROOT") or os.getcwd())
SOURCE = "rsdoc-app-source-7f3a"
META = "rsdoc-build-meta-7f3a"
SECOND = "rsdoc-second-profile-source-7f3a"
DOCS_ORIGIN = "https://docs.internal.example"
DOCS_NAME = "docs.internal.example"
PROBE_NAME = "zz_hidden_report_server.test.ts"
CONFIG_NAME = "zz_hidden_rstest.config.ts"

PROBE_TS = r"""
import dns from 'node:dns';
import fs from 'node:fs';
import http from 'node:http';
import net from 'node:net';
import path from 'node:path';
import { describe, it, rs } from '@rstest/core';
import WebSocket from 'ws';
import { RsdoctorSDK } from '../src/sdk';

rs.setConfig({ testTimeout: 60000 });

const sourceValue = process.env.HIDDEN_SOURCE;
const metaValue = process.env.HIDDEN_META;
const secondValue = process.env.HIDDEN_SECOND;
const docsOrigin = process.env.HIDDEN_ORIGIN;
const docsName = process.env.HIDDEN_DOCS_NAME;
const obsPath = process.env.HIDDEN_OBS;
const tmpDir = process.env.HIDDEN_TMP;

function settle(executor) {
  return new Promise((resolve) => {
    let done = false;
    executor((value) => {
      if (done) {
        return;
      }
      done = true;
      resolve(value);
    });
  });
}

function ipv4Lookup(hostname, options, callback) {
  const done = typeof options === 'function' ? options : callback;
  const all = Boolean(options && typeof options === 'object' && options.all);
  if (hostname === 'localhost') {
    if (all) {
      done(null, [{ address: '127.0.0.1', family: 4 }]);
    } else {
      done(null, '127.0.0.1', 4);
    }
    return;
  }
  if (typeof options === 'function') {
    dns.lookup(hostname, options);
    return;
  }
  dns.lookup(hostname, options, callback);
}

function textOf(data) {
  if (typeof data === 'string') {
    return data;
  }
  if (Array.isArray(data)) {
    return Buffer.concat(data).toString('utf8');
  }
  return Buffer.from(data).toString('utf8');
}

function freePort() {
  return new Promise((resolve, reject) => {
    const holder = net.createServer();
    holder.once('error', reject);
    holder.listen(0, '0.0.0.0', () => {
      const info = holder.address();
      const value = info && typeof info === 'object' ? info.port : 0;
      holder.close(() => resolve(value));
    });
  });
}

function postReport(port, extraHeaders) {
  const payload = JSON.stringify({ key: 'moduleCodeMap' });
  return settle((finish) => {
    const req = http.request(
      {
        hostname: '127.0.0.1',
        port,
        path: '/api/data/key',
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(payload),
          ...extraHeaders,
        },
      },
      (res) => {
        const chunks = [];
        res.on('data', (chunk) => chunks.push(chunk));
        res.on('end', () => {
          const allow = res.headers['access-control-allow-origin'];
          finish({
            status: res.statusCode || 0,
            body: Buffer.concat(chunks).toString('utf8'),
            allow: Array.isArray(allow) ? allow.join(',') : allow || '',
          });
        });
      },
    );
    req.setTimeout(900, () => {
      req.destroy();
      finish({ status: 0, body: '', allow: '' });
    });
    req.on('error', () => finish({ status: 0, body: '', allow: '' }));
    req.write(payload);
    req.end();
  });
}

function askSocket(url) {
  return settle((finish) => {
    const ws = new WebSocket(url, {
      handshakeTimeout: 900,
      lookup: ipv4Lookup,
    });
    const timer = setTimeout(() => {
      ws.terminate();
      finish({ received: false, body: '' });
    }, 900);
    const stop = (value) => {
      clearTimeout(timer);
      try {
        ws.close();
      } catch {
        // The handshake may already be closed.
      }
      finish(value);
    };
    ws.on('error', () => stop({ received: false, body: '' }));
    ws.on('unexpected-response', () => stop({ received: false, body: '' }));
    ws.on('open', () => {
      ws.send(
        JSON.stringify({
          type: 'request',
          id: 'report-1',
          api: '/api/data/key',
          body: { key: 'moduleCodeMap' },
        }),
      );
    });
    ws.on('message', (data) => stop({ received: true, body: textOf(data) }));
  });
}

async function start(name, port, sourceText, metaText, clientHtml) {
  const sdk = new RsdoctorSDK({
    name,
    root: process.cwd(),
    port,
    config: {
      printLog: { serverUrls: false },
      innerClientPath: clientHtml,
    },
  });
  sdk.getStoreData = () => ({
    moduleCodeMap: {
      app: {
        source: sourceText,
        meta: metaText,
      },
    },
  });
  await sdk.bootstrap();
  return sdk;
}

async function runProbe() {
  const clientRoot = path.join(tmpDir, 'client');
  fs.mkdirSync(clientRoot, { recursive: true });
  const clientHtml = path.join(clientRoot, 'index.html');
  fs.writeFileSync(clientHtml, '<!doctype html><title>report</title>');
  const chosenPort = await freePort();
  const secondPort = await freePort();
  const open = [];
  try {
    const first = await start('report-a', chosenPort, sourceValue, metaValue, clientHtml);
    open.push(first);
    const actual = first.server.port;
    const published = first.server.socketUrl.socketUrl;
    const foreignPage = await postReport(actual, {
      Host: `127.0.0.1:${actual}`,
      Origin: docsOrigin,
    });
    const foreignHost = await postReport(actual, {
      Host: `${docsName}:${actual}`,
    });
    const sameMachine = await postReport(actual, {
      Host: `127.0.0.1:${actual}`,
    });
    const localhost = await postReport(actual, {
      Host: `localhost:${actual}`,
      Origin: `http://localhost:${actual}`,
    });
    const loopback = await postReport(actual, {
      Host: `127.0.0.1:${actual}`,
      Origin: `http://127.0.0.1:${actual}`,
    });
    const separateSession = await askSocket(`ws://127.0.0.1:${actual}/`);
    const forgedSession = await askSocket(
      `ws://127.0.0.1:${actual}/?token=forged-session`,
    );
    const livePage = await askSocket(published);
    const second = await start(
      'report-b',
      secondPort,
      secondValue,
      secondValue,
      clientHtml,
    );
    open.push(second);
    const secondProfile = await postReport(second.server.port, {
      Host: `127.0.0.1:${second.server.port}`,
    });
    const obs = {
      chosen_port: chosenPort,
      actual_port: actual,
      foreign_page: foreignPage,
      foreign_host: foreignHost,
      same_machine: sameMachine,
      localhost,
      loopback,
      separate_session: separateSession,
      forged_session: forgedSession,
      live_page: livePage,
      second_profile: secondProfile,
    };
    fs.writeFileSync(obsPath, JSON.stringify(obs));
  } finally {
    for (const sdk of open.reverse()) {
      try {
        await sdk.dispose();
      } catch {
        // Observations are already on disk when dispose fails.
      }
    }
  }
}

describe('local report server', () => {
  it('records what a caller can observe', async () => {
    await runProbe();
  });
});
"""

CONFIG_TS = r"""
import { defineConfig } from '@rstest/core';

export default defineConfig({
  name: 'node',
  globals: true,
  testTimeout: 60000,
  teardownTimeout: 3000,
  pool: { maxWorkers: 1 },
  source: {
    decorators: { version: 'legacy' },
    tsconfigPath: './tsconfig.test.json',
  },
  include: ['packages/sdk/tests/zz_hidden_report_server.test.ts'],
  exclude: ['**/node_modules/**'],
  setupFiles: ['./scripts/rstest.setup.ts'],
});
"""


def _page_can_read(obs: dict) -> bool:
    status = int(obs.get("status") or 0)
    if status == 0 or status >= 400:
        return False
    body = obs.get("body") or ""
    if SOURCE not in body and META not in body:
        return False
    allow = obs.get("allow") or ""
    if isinstance(allow, list):
        allow = ",".join(str(part) for part in allow)
    parts = [part.strip() for part in str(allow).split(",") if part.strip()]
    return "*" in parts or any(DOCS_ORIGIN in part for part in parts)


def _body_leaks(obs: dict) -> bool:
    status = int(obs.get("status") or 0)
    if status == 0 or status >= 400:
        return False
    body = obs.get("body") or ""
    return SOURCE in body or META in body


def _local_report(obs: dict) -> None:
    assert int(obs["status"]) < 400
    assert SOURCE in obs["body"]
    assert META in obs["body"]


def _session_leaks(obs: dict) -> bool:
    body = obs.get("body") or ""
    return SOURCE in body or META in body


@pytest.fixture(scope="module")
def report(tmp_path_factory):
    folder = tmp_path_factory.mktemp("report-server")
    obs_path = folder / "obs.json"
    probe = REPO / "packages" / "sdk" / "tests" / PROBE_NAME
    config = REPO / CONFIG_NAME
    probe.parent.mkdir(parents=True, exist_ok=True)
    probe.write_text(PROBE_TS, encoding="utf-8")
    config.write_text(CONFIG_TS, encoding="utf-8")
    binary = REPO / "node_modules" / ".bin" / "rstest"
    command = [str(binary) if binary.exists() else "pnpm"]
    if command[0] == "pnpm":
        command.extend(["exec", "rstest"])
    command.extend(["run", "--config", CONFIG_NAME])
    env = os.environ.copy()
    env.update(
        {
            "HIDDEN_OBS": str(obs_path),
            "HIDDEN_TMP": str(folder),
            "HIDDEN_SOURCE": SOURCE,
            "HIDDEN_META": META,
            "HIDDEN_SECOND": SECOND,
            "HIDDEN_ORIGIN": DOCS_ORIGIN,
            "HIDDEN_DOCS_NAME": DOCS_NAME,
        }
    )
    try:
        proc = subprocess.run(
            command,
            cwd=REPO,
            env=env,
            text=True,
            capture_output=True,
            timeout=180,
        )
        if not obs_path.is_file():
            raise AssertionError(
                (proc.stdout or "")[-4000:] + "\n" + (proc.stderr or "")[-4000:]
            )
        data = json.loads(obs_path.read_text(encoding="utf-8"))
    finally:
        probe.unlink(missing_ok=True)
        config.unlink(missing_ok=True)
    required = [
        "foreign_page",
        "foreign_host",
        "separate_session",
        "forged_session",
        "same_machine",
        "localhost",
        "loopback",
        "live_page",
        "chosen_port",
        "actual_port",
        "second_profile",
    ]
    missing = [key for key in required if key not in data]
    if missing:
        raise AssertionError(f"report observation missing {missing}: {data}")
    return data


def test_security_foreign_page_cannot_read_module_source(report):
    """A page on another website must not be able to read compiled module source."""
    assert not _page_can_read(report["foreign_page"])


def test_security_foreign_site_name_cannot_read_module_source(report):
    """A request that names another website must not receive compiled module source."""
    assert not _body_leaks(report["foreign_host"])


def test_security_separate_session_cannot_receive_module_source(report):
    """A session other than the local report page must not receive module source."""
    assert not _session_leaks(report["separate_session"])


def test_security_forged_session_cannot_receive_module_source(report):
    """A session that is not the local report page's session must not receive module source."""
    assert not _session_leaks(report["forged_session"])


def test_functional_local_page_still_loads_module_source(report):
    """A request that is not cross-site still loads compiled module source and build metadata."""
    _local_report(report["same_machine"])


def test_functional_localhost_name_still_loads_module_source(report):
    """A request that uses the localhost name still loads compiled module source and build metadata."""
    _local_report(report["localhost"])


def test_functional_loopback_address_still_loads_module_source(report):
    """A request that uses a loopback address still loads compiled module source and build metadata."""
    _local_report(report["loopback"])


def test_functional_live_updates_still_connect_for_local_page(report):
    """The connection string published to the local report page still delivers module source."""
    obs = report["live_page"]
    assert obs["received"] is True
    assert SOURCE in obs["body"]
    assert META in obs["body"]


def test_functional_chosen_port_is_honored(report):
    """The port chosen for the report server is the port that serves the report."""
    assert int(report["chosen_port"]) == int(report["actual_port"])
    _local_report(report["same_machine"])


def test_functional_second_profile_server_still_loads_module_source(report):
    """A second profile server in the same session still serves that profile's module source."""
    obs = report["second_profile"]
    assert int(obs["status"]) < 400
    assert SECOND in obs["body"]
</hidden_tests_py>
