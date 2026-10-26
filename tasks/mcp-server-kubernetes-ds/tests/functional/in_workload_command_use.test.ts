/**
 * A command line that a request asks to run inside a workload is handed to
 * that workload, not parsed as options of the cluster tool. Its own options,
 * including short ones that begin with a dash, must survive unchanged.
 */
import { afterAll, beforeAll, beforeEach, describe, expect, it } from "vitest";

import { ServerHandle, startServer } from "../helpers";

let server: ServerHandle;

beforeAll(async () => {
  server = await startServer();
});

afterAll(async () => {
  await server.close();
});

beforeEach(() => {
  server.reset();
});

describe("commands run inside a workload", () => {
  it("passes a quiet curl invocation through unchanged", async () => {
    const outcome = await server.callTool("exec_in_pod", {
      name: "mypod",
      command: ["curl", "-s", "-o", "/dev/null", "http://127.0.0.1:8080/health"],
    });

    expect(outcome.refused).toBe(false);
    expect(server.dangerous()).toEqual([]);
    expect(server.kubectl()[0]).toEqual([
      "exec",
      "mypod",
      "-n",
      "default",
      "--",
      "curl",
      "-s",
      "-o",
      "/dev/null",
      "http://127.0.0.1:8080/health",
    ]);
  });

  it("passes a shell command with its own -c through unchanged", async () => {
    const outcome = await server.callTool("exec_in_pod", {
      name: "mypod",
      command: ["sh", "-c", "echo hi"],
    });

    expect(outcome.refused).toBe(false);
    expect(server.dangerous()).toEqual([]);
    expect(server.kubectl()[0]).toEqual(["exec", "mypod", "-n", "default", "--", "sh", "-c", "echo hi"]);
  });

  it("passes a tool's own short socket option through unchanged", async () => {
    const outcome = await server.callTool("exec_in_pod", {
      name: "mypod",
      command: ["redis-cli", "-s", "/tmp/redis.sock", "ping"],
    });

    expect(outcome.refused).toBe(false);
    expect(server.dangerous()).toEqual([]);
    expect(server.kubectl()[0].slice(-4)).toEqual(["redis-cli", "-s", "/tmp/redis.sock", "ping"]);
  });

  it("passes a cronjob command through unchanged", async () => {
    const outcome = await server.callTool("kubectl_create", {
      resourceType: "cronjob",
      name: "collector",
      image: "busybox",
      schedule: "* * * * *",
      command: ["curl", "-s", "http://127.0.0.1:8080/health"],
    });

    expect(outcome.refused).toBe(false);
    expect(server.dangerous()).toEqual([]);
    const argv = server.kubectl().flat();
    expect(argv).toEqual(expect.arrayContaining(["cronjob", "collector", "--", "curl", "-s"]));
  });
});
