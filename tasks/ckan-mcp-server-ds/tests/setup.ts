/**
 * Verifier setup: give every name-resolution path a deterministic, offline
 * answer. The hosts list holds names that resolve to loopback (the address a
 * name-based bypass would reach) and names that resolve to a public address
 * (legitimate use). Both getaddrinfo (through /etc/hosts) and c-ares (through a
 * local DNS server) use the same table, so any correct resolution strategy sees
 * the same answers.
 */
import dgram from "node:dgram";
import dns from "node:dns";
import fs from "node:fs";

interface HostEntry {
  ip: string;
  name: string;
}

function readHostsList(): HostEntry[] {
  const file = new URL("./hosts.list", import.meta.url);
  return fs
    .readFileSync(file, "utf8")
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0 && !line.startsWith("#"))
    .map((line) => {
      const [ip, name] = line.split(/\s+/);
      return { ip, name };
    });
}

const entries = readHostsList();

const records: Record<string, string[]> = {};
for (const { ip, name } of entries) {
  records[name] = [...(records[name] ?? []), ip];
}

function ensureHostsEntries(): void {
  try {
    const current = fs.readFileSync("/etc/hosts", "utf8");
    const present = new Set(
      current
        .split("\n")
        .map((line) => line.trim().split(/\s+/).join(" "))
        .filter(Boolean)
    );
    const missing = entries
      .map(({ ip, name }) => `${ip} ${name}`)
      .filter((line) => !present.has(line));
    if (missing.length > 0) {
      fs.appendFileSync("/etc/hosts", "\n" + missing.join("\n") + "\n");
    }
  } catch {
    // Without write access to /etc/hosts only the DNS server below is available;
    // the container runs as root, so this is a guard, not the normal path.
  }
}

function startDnsServer(): Promise<dgram.Socket> {
  const socket = dgram.createSocket("udp4");
  socket.on("message", (msg, rinfo) => {
    try {
      let offset = 12;
      const labels: string[] = [];
      while (offset < msg.length && msg[offset] !== 0) {
        const len = msg[offset];
        labels.push(msg.toString("utf8", offset + 1, offset + 1 + len));
        offset += 1 + len;
      }
      offset += 1;
      const qtype = msg.readUInt16BE(offset);
      const questionEnd = offset + 4;
      const name = labels.join(".").toLowerCase();
      const known = records[name] !== undefined;
      const ips = qtype === 1 ? records[name] ?? [] : [];

      const header = Buffer.alloc(12);
      msg.copy(header, 0, 0, 2); // transaction id
      header.writeUInt16BE(known ? 0x8180 : 0x8183, 2); // NXDOMAIN when unknown
      header.writeUInt16BE(1, 4); // one question
      header.writeUInt16BE(ips.length, 6); // answers
      const question = msg.subarray(12, questionEnd);
      const answers = ips.map((ip) => {
        const answer = Buffer.alloc(16);
        answer.writeUInt16BE(0xc00c, 0);
        answer.writeUInt16BE(1, 2); // A
        answer.writeUInt16BE(1, 4); // IN
        answer.writeUInt32BE(30, 6);
        answer.writeUInt16BE(4, 10);
        ip.split(".").forEach((octet, index) => answer.writeUInt8(Number(octet), 12 + index));
        return answer;
      });
      socket.send(Buffer.concat([header, question, ...answers]), rinfo.port, rinfo.address);
    } catch {
      // Malformed datagram: ignore.
    }
  });

  return new Promise((resolve) => {
    socket.bind(0, "127.0.0.1", () => {
      socket.unref();
      resolve(socket);
    });
  });
}

ensureHostsEntries();
const server = await startDnsServer();
try {
  dns.setServers([`127.0.0.1:${(server.address() as { port: number }).port}`]);
} catch {
  // Older runtimes: getaddrinfo through /etc/hosts still answers.
}

export {};
