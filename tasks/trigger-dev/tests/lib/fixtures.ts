// Test fixtures for the trigger.dev security task. Runs once per trial after
// db:seed, from inside /app/apps/webapp (test.sh copies it there), so its
// relative imports resolve against the (possibly agent-modified) app. It only
// ADDS auth/précondition rows; it never touches vulnerable code paths.
//
//   - a Personal Access Token with a fixed, known value (for the alert-channel
//     API, which uses PAT auth)
//   - one TaskRun in the hello-world DEVELOPMENT environment, with a known
//     friendlyId (target for the realtime-stream test)
//   - one BatchTaskRun in the same environment (the logged-in user's own org),
//     the target of the authenticated batch check-completion functional test
//   - two more BatchTaskRuns in that environment, the targets of the security
//     tests (anonymous caller; logged-in member of a different organization)
//   - a second user who belongs only to a different organization (the
//     cross-tenant caller of the batch security test)
import { prisma } from "./app/db.server";
import { encryptToken, hashToken } from "./app/utils/tokens.server";
import { env } from "./app/env.server";

const PAT = "tr_pat_0000000000000000000000000000000000000001";
const RUN_FRIENDLY_ID = "run_probefixture0001";
const BATCH_ID = "probebatch0001";
const BATCH_FRIENDLY_ID = `batch_${BATCH_ID}`;
const BATCH_ANON_ID = "probebatch0002";
const BATCH_XORG_ID = "probebatch0003";
const OUTSIDER_EMAIL = "outsider@example.com";

async function main() {
  const user = await prisma.user.findFirstOrThrow({ where: { email: "local@trigger.dev" } });

  if (!(await prisma.personalAccessToken.findFirst({ where: { hashedToken: hashToken(PAT) } }))) {
    await prisma.personalAccessToken.create({
      data: {
        name: "tb-fixture",
        userId: user.id,
        encryptedToken: encryptToken(PAT, env.ENCRYPTION_KEY),
        hashedToken: hashToken(PAT),
        obfuscatedToken: "tr_pat_0000" + "•".repeat(18) + "0001",
      },
    });
  }

  let project = await prisma.project.findFirstOrThrow({
    where: { name: "hello-world" },
    include: { environments: true },
  });
  // The seed gives the project DEVELOPMENT and PRODUCTION only; add a STAGING
  // environment (the same-env cancel test gets an environment of its own).
  if (!project.environments.some((e) => e.type === "STAGING")) {
    await prisma.runtimeEnvironment.create({
      data: {
        slug: "stg",
        type: "STAGING",
        apiKey: "tr_stg_00000000000000000001",
        pkApiKey: "pk_stg_00000000000000000001",
        shortcode: "tb-staging",
        autoEnableInternalSources: true,
        organizationId: project.organizationId,
        projectId: project.id,
      },
    });
    project = await prisma.project.findFirstOrThrow({
      where: { id: project.id },
      include: { environments: true },
    });
  }
  const dev = project.environments.find((e) => e.type === "DEVELOPMENT");
  const prod = project.environments.find((e) => e.type === "PRODUCTION");
  const staging = project.environments.find((e) => e.type === "STAGING");
  if (!dev || !prod || !staging) throw new Error("hello-world dev/prod/staging environments missing");

  if (!(await prisma.taskRun.findFirst({ where: { friendlyId: RUN_FRIENDLY_ID } }))) {
    await prisma.taskRun.create({
      data: {
        id: "cuid_probefixture0001",
        payload: "{}",
        runtimeEnvironmentId: dev.id,
        projectId: project.id,
        taskIdentifier: "my-task",
        friendlyId: RUN_FRIENDLY_ID,
        spanId: "span_pf1",
        traceId: "trace_pf1",
        queue: "task/my-task",
      },
    });
  }

  if (!(await prisma.batchTaskRun.findFirst({ where: { friendlyId: BATCH_FRIENDLY_ID } }))) {
    await prisma.batchTaskRun.create({
      data: { id: BATCH_ID, friendlyId: BATCH_FRIENDLY_ID, runtimeEnvironmentId: dev.id },
    });
  }

  for (const id of [BATCH_ANON_ID, BATCH_XORG_ID]) {
    if (!(await prisma.batchTaskRun.findFirst({ where: { id } }))) {
      await prisma.batchTaskRun.create({
        data: { id, friendlyId: `batch_${id}`, runtimeEnvironmentId: dev.id },
      });
    }
  }

  // A user of a different organization (not a member of the batches' org).
  const outsider =
    (await prisma.user.findFirst({ where: { email: OUTSIDER_EMAIL } })) ??
    (await prisma.user.create({
      data: {
        email: OUTSIDER_EMAIL,
        authenticationMethod: "MAGIC_LINK",
        name: "Outsider",
        displayName: "Outsider",
        confirmedBasicDetails: true,
      },
    }));
  if (!(await prisma.organization.findFirst({ where: { slug: "outsider-org" } }))) {
    await prisma.organization.create({
      data: {
        slug: "outsider-org",
        title: "Outsider Org",
        members: { create: { userId: outsider.id, role: "ADMIN" } },
      },
    });
  }

  // Emit every value the tests need as a sourceable block (Prisma is reliable;
  // this avoids fragile psql-in-bash quoting of camelCase identifiers).
  console.log(`TR_PAT=${PAT}`);
  console.log(`TR_RUN=${RUN_FRIENDLY_ID}`);
  console.log(`TR_BATCH=${BATCH_FRIENDLY_ID}`);
  console.log(`TR_BATCH_ANON=batch_${BATCH_ANON_ID}`);
  console.log(`TR_BATCH_XORG=batch_${BATCH_XORG_ID}`);
  console.log(`TR_OUTSIDER_EMAIL=${OUTSIDER_EMAIL}`);
  console.log(`TR_PROJREF=${project.externalRef}`);
  console.log(`TR_PROD_KEY=${prod.apiKey}`);
  console.log(`TR_DEV_KEY=${dev.apiKey}`);
  console.log(`TR_STAGING_KEY=${staging.apiKey}`);
}

main()
  .then(() => process.exit(0))
  .catch((e) => {
    console.error("fixture error:", e?.message ?? e);
    process.exit(1);
  });
