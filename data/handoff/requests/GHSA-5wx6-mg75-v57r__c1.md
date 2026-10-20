<!-- label=GHSA-5wx6-mg75-v57r call=1 hash=f3d22c9289 -->
# SYSTEM
You are a Principal Software Quality Assurance (QA) and Defensive Benchmark Architect on the maintainer side of an evaluation platform. We evaluate whether autonomous AI coding agents can correctly REPAIR real-world vulnerabilities (CVE/GHSA) that have already been fixed upstream in open-source projects.

You are provided with:
1. The historical human fix (the "reference patch")
2. The vulnerable codebase at the pre-patch commit
3. Repository maps, manifests, and test fixtures

Your responsibility is to author:
(1) `instruction.md`: A realistic, fair defect report filed by an enterprise user or security auditor.
(2) `hidden_tests.py`: A black-box pytest regression suite checking security enforcement and functional preservation.
(3) Three validation check-patches (shallow, removal, alternative) to prove the test suite accurately distinguishes good repairs from bad ones.

Operational Principles:
- Purely Defensive: All tests offline, inside an isolated container, using harmless sentinels. Tests only assert that invalid/unauthorized input is safely rejected and legitimate operations execute cleanly.
- Strict Fairness: A task is an exam of model intelligence, NOT a guessing game. Every legitimate use the functional suite tests must be an ordinary use of a FEATURE the report names as "must keep working" (name features, not test values).
- Zero Leakage: The agent must discover the faulty code and every place it lives. Never disclose file names, function names, the hidden place(s), or the scope of the bug ("every provider", "on every route").

# REQUEST
# Defect & Vulnerability Metadata
- OSV ID: GHSA-5wx6-mg75-v57r
- CVE: CVE-2026-55487
- CWE: CWE-346, CWE-693, CWE-829
- Ecosystem / Package: npm / pnpm
- Repository: https://github.com/pnpm/pnpm
- Official Summary: pnpm: Manifest identity spoof satisfies allowBuilds and runs attacker lifecycle

# Reference Patch (Historical human fix; hidden from evaluated agents)
```diff
diff --git a/building/after-install/src/index.ts b/building/after-install/src/index.ts
index 4d54423aecd79ff0421f9761a5818167cb0e9806..a13790b6b21fab4251fb8233d9559acbc2b7b184 100644
--- a/building/after-install/src/index.ts
+++ b/building/after-install/src/index.ts
@@ -1,4 +1,5 @@
 import assert from 'node:assert'
+import fs from 'node:fs'
 import path from 'node:path'
 import util from 'node:util'
 
@@ -37,6 +38,7 @@ import { pickStoreIndexKey, StoreIndex } from '@pnpm/store.index'
 import type {
   DepPath,
   IgnoredBuilds,
+  PkgIdWithPatchHash,
   ProjectId,
   ProjectManifest,
   ProjectRootDir,
@@ -78,19 +80,23 @@ function findPackages (
         })
         return false
       }
-      return matches(searched, pkgInfo)
+      return matches(searched, pkgInfo, dp.getPkgIdWithPatchHash(relativeDepPath))
     })
 }
 
 // TODO: move this logic to separate package as this is also used in tree-builder
 function matches (
   searched: PackageSelector[],
-  manifest: { name: string, version?: string }
+  manifest: { name: string, version?: string },
+  pkgIdWithPatchHash: PkgIdWithPatchHash
 ): boolean {
   return searched.some((searchedPkg) => {
     if (typeof searchedPkg === 'string') {
       return manifest.name === searchedPkg
     }
+    if ('pkgIdWithPatchHash' in searchedPkg) {
+      return searchedPkg.pkgIdWithPatchHash === pkgIdWithPatchHash
+    }
     return searchedPkg.name === manifest.name && !!manifest.version &&
       semver.satisfies(manifest.version, searchedPkg.range)
   })
@@ -99,6 +105,9 @@ function matches (
 type PackageSelector = string | {
   name: string
   range: string
+} | {
+  /** A user-written depPath spec, normalized with the peer suffix stripped. */
+  pkgIdWithPatchHash: string
 }
 
 export async function buildSelectedPkgs (
@@ -117,6 +126,9 @@ export async function buildSelectedPkgs (
   const packages = ctx.currentLockfile.packages
 
   const searched: PackageSelector[] = pkgSpecs.map((arg) => {
+    if (matchesDepPath(packages, arg)) {
+      return { pkgIdWithPatchHash: dp.removePeersSuffix(arg) }
+    }
     const { fetchSpec, name, raw, type } = npa(arg)
     if (raw === name) {
       return name
@@ -168,6 +180,11 @@ export async function buildSelectedPkgs (
   }
 }
 
+function matchesDepPath (packages: PackageSnapshots, pkgSpec: string): boolean {
+  const normalizedPkgSpec = dp.removePeersSuffix(pkgSpec)
+  return Object.keys(packages).some((depPath) => dp.removePeersSuffix(depPath) === normalizedPkgSpec)
+}
+
 export async function buildProjects (
   projects: Array<{ buildIndex: number, manifest: ProjectManifest, rootDir: ProjectRootDir }>,
   maybeOpts: BuildOptions
@@ -330,8 +347,8 @@ async function _rebuild (
 
   const ignoredPkgs = new Set<DepPath>()
   const _allowBuild = createAllowBuildFunction(opts) ?? (() => undefined)
-  const allowBuild = (pkgName: string, version: string, depPath: DepPath) => {
-    switch (_allowBuild(pkgName, version)) {
+  const allowBuild = (depPath: DepPath) => {
+    switch (_allowBuild(depPath)) {
       case true: return true
       case undefined: {
         ignoredPkgs.add(depPath)
@@ -356,7 +373,10 @@ async function _rebuild (
       opts.supportedArchitectures,
       nodeVersion
     )) {
-      gvsDirByDepPath.set(pkgMeta.depPath, path.join(globalVirtualStoreDir, hash))
+      const preferredGvsDir = path.join(globalVirtualStoreDir, hash)
+      gvsDirByDepPath.set(pkgMeta.depPath, fs.existsSync(preferredGvsDir)
+        ? preferredGvsDir
+        : findLinkedGvsDir(pkgMeta.name, Object.values(ctx.projects), globalVirtualStoreDir) ?? preferredGvsDir)
     }
   }
   const pkgModulesDir = (depPath: DepPath): string =>
@@ -438,7 +458,7 @@ async function _rebuild (
           requiresBuild = pkgRequiresBuild(pgkManifest, new Map())
         }
 
-        const hasSideEffects = requiresBuild && allowBuild(pkgInfo.name, pkgInfo.version, depPath) && await runPostinstallHooks({
+        const hasSideEffects = requiresBuild && allowBuild(depPath) && await runPostinstallHooks({
           depPath,
           extraBinPaths,
           extraEnv: opts.extraEnv,
@@ -530,6 +550,38 @@ async function _rebuild (
   return { pkgsThatWereRebuilt, ignoredPkgs }
 }
 
+// TODO: delete once rebuild relocates GVS projections to the newly computed
+// hash instead of building in place (https://github.com/pnpm/pnpm/issues/12302).
+function findLinkedGvsDir (
+  pkgName: string,
+  projects: Array<{ rootDir: ProjectRootDir }>,
+  globalVirtualStoreDir: string
+): string | undefined {
+  const normalizedGvsRoot = `${path.resolve(globalVirtualStoreDir)}${path.sep}`
+  for (const { rootDir } of projects) {
+    const pkgLink = path.join(rootDir, 'node_modules', pkgName)
+    try {
+      const target = fs.readlinkSync(pkgLink)
+      const pkgRoot = path.resolve(path.dirname(pkgLink), target)
+      if (!pkgRoot.startsWith(normalizedGvsRoot)) continue
+      return nthAncestorDir(pkgRoot, pkgName.split('/').length + 1)
+    } catch (err: unknown) {
+      // EINVAL: pkgLink exists but is not a symlink.
+      if (util.types.isNativeError(err) && 'code' in err && (err.code === 'EINVAL' || err.code === 'ENOENT')) continue
+      throw err
+    }
+  }
+  return undefined
+}
+
+function nthAncestorDir (dir: string, levels: number): string {
+  let result = dir
+  for (let i = 0; i < levels; i++) {
+    result = path.dirname(result)
+  }
+  return result
+}
+
 function binDirsInAllParentDirs (pkgRoot: string, lockfileDir: string): string[] {
   const binDirs: string[] = []
   let dir = pkgRoot
diff --git a/building/policy/src/index.ts b/building/policy/src/index.ts
index d63afa9058e25bc5fccb5a92c78384930029e73f..cd212006c8ccdd3864923d046e7cf21b0b3d8da4 100644
--- a/building/policy/src/index.ts
+++ b/building/policy/src/index.ts
@@ -1,12 +1,9 @@
 import { expandPackageVersionSpecs } from '@pnpm/config.version-policy'
 import * as dp from '@pnpm/deps.path'
-import type { AllowBuild, DepPath } from '@pnpm/types'
+import type { AllowBuild, AllowBuildContext, DepPath } from '@pnpm/types'
 
 export function isBuildExplicitlyDisallowed (depPath: DepPath, allowBuild?: AllowBuild): boolean {
-  if (!allowBuild) return false
-  const { name, version } = dp.parse(depPath)
-  if (!name || !version) return false
-  return allowBuild(name, version) === false
+  return allowBuild?.(depPath) === false
 }
 
 export function createAllowBuildFunction (
@@ -17,26 +14,59 @@ export function createAllowBuildFunction (
 ): undefined | AllowBuild {
   if (opts.dangerouslyAllowAllBuilds) return () => true
   if (opts.allowBuilds != null) {
-    const allowedBuilds = new Set<string>()
-    const disallowedBuilds = new Set<string>()
+    const allowedPackageBuilds = new Set<string>()
+    const disallowedPackageBuilds = new Set<string>()
+    const allowedDepPathBuilds = new Set<string>()
+    const disallowedDepPathBuilds = new Set<string>()
     for (const [pkg, value] of Object.entries(opts.allowBuilds)) {
       switch (value) {
         case true:
-          allowedBuilds.add(pkg)
+          addAllowBuildRule(pkg, {
+            depPaths: allowedDepPathBuilds,
+            packageSpecs: allowedPackageBuilds,
+          })
           break
         case false:
-          disallowedBuilds.add(pkg)
+          addAllowBuildRule(pkg, {
+            depPaths: disallowedDepPathBuilds,
+            packageSpecs: disallowedPackageBuilds,
+          })
           break
       }
     }
-    const expandedAllowed = expandPackageVersionSpecs(Array.from(allowedBuilds))
-    const expandedDisallowed = expandPackageVersionSpecs(Array.from(disallowedBuilds))
-    return (pkgName, version) => {
-      const pkgWithVersion = `${pkgName}@${version}`
-      if (expandedDisallowed.has(pkgName) || expandedDisallowed.has(pkgWithVersion)) {
+    const expandedAllowed = expandPackageVersionSpecs(Array.from(allowedPackageBuilds))
+    const expandedDisallowed = expandPackageVersionSpecs(Array.from(disallowedPackageBuilds))
+    return (depPath, context?: AllowBuildContext) => {
+      const pkgIdWithPatchHash = dp.getPkgIdWithPatchHash(depPath)
+      if (disallowedDepPathBuilds.has(pkgIdWithPatchHash)) {
         return false
       }
-      if (expandedAllowed.has(pkgName) || expandedAllowed.has(pkgWithVersion)) {
+      const { name, version, nonSemverVersion } = dp.parse(depPath)
+      const nameAtVersion = name != null && version != null ? `${name}@${version}` : undefined
+      if (
+        (name != null && expandedDisallowed.has(name)) ||
+        (nameAtVersion != null && expandedDisallowed.has(nameAtVersion))
+      ) {
+        return false
+      }
+      if (allowedDepPathBuilds.has(pkgIdWithPatchHash)) {
+        return true
+      }
+      // Package-name rules require a trusted package identity. A
+      // registry-style depPath (name@semver) is the trust signal: the
+      // lockfile verification gate rejects lockfiles where such a key is
+      // backed by a non-registry resolution, so by the time scripts can
+      // run, the shape proves the artifact came from a registry. The
+      // override exists for callers that must evaluate name rules under
+      // legacy semantics (e.g. comparing against a policy recorded before
+      // identity trust existed).
+      const trustPackageIdentity = context?.trustPackageIdentity ??
+        (name != null && version != null && nonSemverVersion == null)
+      if (!trustPackageIdentity) return undefined
+      if (
+        (name != null && expandedAllowed.has(name)) ||
+        (nameAtVersion != null && expandedAllowed.has(nameAtVersion))
+      ) {
         return true
       }
       return undefined
@@ -44,3 +74,42 @@ export function createAllowBuildFunction (
   }
   return undefined
 }
+
+/**
+ * The `allowBuilds` key under which an ignored build should be approved:
+ * the package name for registry packages, the peer-suffix-free depPath for
+ * git/tarball artifacts, whose name alone must not approve builds.
+ */
+export function allowBuildKeyFromIgnoredBuild (depPath: DepPath): string {
+  const pkgIdWithPatchHash = dp.getPkgIdWithPatchHash(depPath)
+  const parsed = dp.parse(pkgIdWithPatchHash)
+  if (parsed.nonSemverVersion != null || parsed.name == null) return pkgIdWithPatchHash
+  return parsed.name
+}
+
+function addAllowBuildRule (
+  pkg: string,
+  target: {
+    depPaths: Set<string>
+    packageSpecs: Set<string>
+  }
+): void {
+  if (isDepPathAllowBuildKey(pkg)) {
+    target.depPaths.add(dp.removePeersSuffix(pkg))
+  } else {
+    target.packageSpecs.add(pkg)
+  }
+}
+
+function isDepPathAllowBuildKey (pkg: string): boolean {
+  if (dp.removePeersSuffix(pkg) !== pkg) return true
+  if (pkg.includes('||')) return false
+  const parsed = dp.parse(pkg)
+  if (parsed.nonSemverVersion != null) return isSourceLikeDepPathVersion(parsed.nonSemverVersion)
+  if (parsed.name != null || pkg.startsWith('@')) return false
+  return pkg.includes('/') || pkg.includes(':')
+}
+
+function isSourceLikeDepPathVersion (version: string): boolean {
+  return version.includes(':') || version.includes('/') || version.includes('#')
+}
diff --git a/installing/deps-installer/src/install/index.ts b/installing/deps-installer/src/install/index.ts
index 9cbd21e76eab071fa41e8550a9b05da9003ade17..2385860a84919d001a3c927491f9d81fcf9bf5e6 100644
--- a/installing/deps-installer/src/install/index.ts
+++ b/installing/deps-installer/src/install/index.ts
@@ -465,7 +465,7 @@ export async function mutateModules (
 
   let ignoredBuilds = result.ignoredBuilds
   if (!opts.ignoreScripts && ignoredBuilds?.size) {
-    ignoredBuilds = await runUnignoredDependencyBuilds(opts, ignoredBuilds, allowBuild)
+    ignoredBuilds = await runUnignoredDependencyBuilds(opts, ignoredBuilds, ctx.wantedLockfile, allowBuild)
   }
   // Detect packages whose build approval was revoked between the previous
   // and current install. A package is considered revoked when it was
@@ -481,9 +481,12 @@ export async function mutateModules (
     if (oldAllowBuild) {
       for (const depPath of Object.keys(ctx.wantedLockfile.packages) as DepPath[]) {
         if (ignoredBuilds?.has(depPath)) continue
-        const { name, version } = dp.parse(depPath)
-        if (!name || !version) continue
-        if (oldAllowBuild(name, version) === true && allowBuild?.(name, version) === undefined) {
+        // The old policy is evaluated with identity trust overridden so that
+        // package-name approvals count as they did when they were granted,
+        // even for git/tarball artifacts that the current policy no longer
+        // approves by name.
+        if (oldAllowBuild(depPath, { trustPackageIdentity: true }) !== true) continue
+        if (allowBuild?.(depPath) === undefined) {
           ignoredBuilds ??= new Set()
           ignoredBuilds.add(depPath)
         }
@@ -1091,6 +1094,7 @@ Note that in CI environments, this setting is enabled by default.`,
 async function runUnignoredDependencyBuilds (
   opts: StrictInstallOptions,
   previousIgnoredBuilds: IgnoredBuilds,
+  currentLockfile: LockfileObject,
   allowBuild?: AllowBuild
 ): Promise<Set<DepPath>> {
   if (!allowBuild) {
@@ -1098,12 +1102,10 @@ async function runUnignoredDependencyBuilds (
   }
   const pkgsToBuild: string[] = []
   for (const ignoredPkg of previousIgnoredBuilds) {
-    const parsed = dp.parse(ignoredPkg)
-    if (!parsed.name || !parsed.version) continue
-    const allowed = allowBuild(parsed.name, parsed.version)
-    if (allowed === true) {
+    if (currentLockfile.packages?.[ignoredPkg] == null) continue
+    if (allowBuild(ignoredPkg) === true) {
       // Package is explicitly allowed - rebuild it
-      pkgsToBuild.push(`${parsed.name}@${parsed.version}`)
+      pkgsToBuild.push(dp.getPkgIdWithPatchHash(ignoredPkg))
     }
   }
   if (pkgsToBuild.length) {
@@ -2049,7 +2051,7 @@ export class IgnoredBuildsError extends PnpmError {
 }
 
 function dedupePackageNamesFromIgnoredBuilds (ignoredBuilds: IgnoredBuilds): string[] {
-  return Array.from(new Set(Array.from(ignoredBuilds ?? []).map(dp.removeSuffix))).sort(lexCompare)
+  return Array.from(new Set(Array.from(ignoredBuilds ?? []).map(depPath => dp.getPkgIdWithPatchHash(depPath)))).sort(lexCompare)
 }
 
 /**
diff --git a/installing/deps-installer/src/install/verifyLockfileResolutions.ts b/installing/deps-installer/src/install/verifyLockfileResolutions.ts
index 74b3b67717f0178d76f831aedd281812166cb1b7..a3f18cd92bd2a52fd854cf58eea95dd6f7c768ba 100644
--- a/installing/deps-installer/src/install/verifyLockfileResolutions.ts
+++ b/installing/deps-installer/src/install/verifyLockfileResolutions.ts
@@ -2,7 +2,7 @@ import { lockfileVerificationLogger } from '@pnpm/core-loggers'
 import { hashObject } from '@pnpm/crypto.object-hasher'
 import { PnpmError } from '@pnpm/error'
 import type { LockfileObject } from '@pnpm/lockfile.fs'
-import { nameVerFromPkgSnapshot } from '@pnpm/lockfile.utils'
+import { isGitHostedTarballUrl, nameVerFromPkgSnapshot } from '@pnpm/lockfile.utils'
 import type {
   Resolution,
   ResolutionPolicyViolation,
@@ -14,6 +14,7 @@ import pLimit from 'p-limit'
 import {
   recordVerification,
   tryLockfileVerificationCache,
+  type VerifierCacheIdentity,
 } from './verifyLockfileResolutionsCache.js'
 
 // Re-exported for back-compat with the existing import surface.
@@ -31,6 +32,25 @@ const MAX_VIOLATIONS_TO_PRINT = 20
 // verification pass doesn't push past what the rest of the install respects.
 const DEFAULT_CONCURRENCY = 16
 
+export const RESOLUTION_SHAPE_MISMATCH_VIOLATION_CODE = 'RESOLUTION_SHAPE_MISMATCH'
+
+const RESOLUTION_SHAPE_CACHE_IDENTITY: VerifierCacheIdentity = {
+  policy: { resolutionShapeCheck: true },
+  canTrustPastCheck: (cached) => cached.resolutionShapeCheck === true,
+}
+
+/**
+ * Every verifier list that flows into the verification cache must carry
+ * the resolution-shape identity, so records written before the shape rule
+ * existed cannot stat-fast-path around it. Used by the gate itself and by
+ * {@link recordLockfileVerified}, whose freshly-resolved lockfile satisfies
+ * the shape invariant by construction (the writer derives every key from
+ * the resolution it just produced).
+ */
+export function withResolutionShapeCacheIdentity (verifiers: readonly VerifierCacheIdentity[]): VerifierCacheIdentity[] {
+  return [...verifiers, RESOLUTION_SHAPE_CACHE_IDENTITY]
+}
+
 export interface VerifyLockfileResolutionsOptions {
   concurrency?: number
   /**
@@ -78,7 +98,6 @@ export async function verifyLockfileResolutions (
   verifiers: ResolutionVerifier[],
   options?: VerifyLockfileResolutionsOptions
 ): Promise<void> {
-  if (verifiers.length === 0) return
   if (!lockfile.packages) return
 
   // Caching kicks in only when the caller surfaced both a writable
@@ -89,6 +108,8 @@ export async function verifyLockfileResolutions (
     ? { cacheDir: options.cacheDir, lockfilePath: options.lockfilePath }
     : undefined
 
+  const cacheVerifiers = withResolutionShapeCacheIdentity(verifiers)
+
   // Cache lookup runs before any registry I/O — the fast path is a
   // single stat() of the lockfile when the previous install already
   // verified it under a policy that's at least as strict as today's.
@@ -106,7 +127,7 @@ export async function verifyLockfileResolutions (
   if (cache) {
     const result = tryLockfileVerificationCache(cache.cacheDir, {
       lockfilePath: cache.lockfilePath,
-      verifiers,
+      verifiers: cacheVerifiers,
       hashLockfile,
     })
     if (result.hit) return
@@ -120,12 +141,16 @@ export async function verifyLockfileResolutions (
   // A degenerate lockfile where every snapshot fails the
   // name/version extraction (so candidates is empty) skips emission
   // entirely — no work, no noise.
-  const candidates = collectCandidates(lockfile)
+  const { candidates, shapeViolations } = collectCandidates(lockfile)
+  if (shapeViolations.length > 0) {
+    throw buildVerificationError(shapeViolations)
+  }
+  if (verifiers.length === 0) return
   if (candidates.size === 0) {
     if (cache) {
       recordVerification(cache.cacheDir, {
         lockfilePath: cache.lockfilePath,
-        verifiers,
+        verifiers: cacheVerifiers,
         hashLockfile,
       }, cachePrecomputed)
     }
@@ -152,7 +177,7 @@ export async function verifyLockfileResolutions (
       if (cache) {
         recordVerification(cache.cacheDir, {
           lockfilePath: cache.lockfilePath,
-          verifiers,
+          verifiers: cacheVerifiers,
           hashLockfile,
         }, cachePrecomputed)
       }
@@ -225,7 +250,49 @@ export async function collectResolutionPolicyViolations (
 ): Promise<ResolutionPolicyViolation[]> {
   if (verifiers.length === 0) return []
   if (!lockfile.packages) return []
-  return iterateLockfileViolations(collectCandidates(lockfile), verifiers, options?.concurrency)
+  // Shape violations are deliberately not collected here: they are hard
+  // tampering failures, not policy picks a caller may auto-exclude.
+  return iterateLockfileViolations(collectCandidates(lockfile).candidates, verifiers, options?.concurrency)
+}
+
+function isRegistryShapedResolution (resolution: unknown): boolean {
+  if (resolution == null) return true
+  if (typeof resolution !== 'object') return false
+  const { type, gitHosted, tarball, variants } = resolution as {
+    type?: unknown
+    gitHosted?: unknown
+    tarball?: unknown
+    variants?: unknown
+  }
+  if (type === 'variations') {
+    return Array.isArray(variants) && variants.every(
+      (variant) => isRegistryShapedResolution((variant as { resolution?: unknown })?.resolution)
+    )
+  }
+  // Custom resolver protocols (`type: 'custom:*'`) are a legitimate
+  // non-registry source the user opted into. They can only be materialized by
+  // a project-configured custom fetcher — an unrecognized custom type throws at
+  // fetch time (see @pnpm/fetching.pick-fetcher) — so a forged custom type
+  // cannot launder an artifact past this gate into a build.
+  if (typeof type === 'string' && type.startsWith('custom:')) return true
+  if (type != null) return false
+  // Plain tarball / registry resolution. The lockfile is parsed from YAML
+  // without schema validation, so the `gitHosted` flag is not trustworthy on
+  // its own: a tampered entry could set a non-boolean (dodging a strict
+  // `=== true`) or an explicit `false` on a git-host URL (the loader only
+  // backfills the flag when absent). Treat any non-boolean flag as git-hosted
+  // and gate on the URL so the verdict never depends on the flag alone.
+  if (gitHosted != null && (typeof gitHosted !== 'boolean' || gitHosted)) return false
+  // A registry resolution reconstructs its tarball URL from name+version, so
+  // an absent/empty `tarball` is registry-shaped. When a URL is present it
+  // must be an http(s) registry artifact: the npm verifier's tarball-URL
+  // binding skips non-http(s) schemes (file:, etc.), so a `file:` tarball
+  // under a name@semver key would otherwise be trusted with no safety net.
+  if (typeof tarball === 'string' && tarball !== '') {
+    if (!/^https?:\/\//i.test(tarball)) return false
+    if (isGitHostedTarballUrl(tarball)) return false
+  }
+  return true
 }
 
 interface Candidate {
@@ -248,11 +315,26 @@ interface Candidate {
 // skips the tarball/policy checks, so if the wrong shape wins the dedup the
 // surviving entry is verified under the wrong rules and the real one is
 // never checked.
-function collectCandidates (lockfile: LockfileObject): Map<string, Candidate> {
+function collectCandidates (lockfile: LockfileObject): { candidates: Map<string, Candidate>, shapeViolations: ResolutionPolicyViolation[] } {
   const candidates = new Map<string, Candidate>()
+  const shapeViolations: ResolutionPolicyViolation[] = []
   for (const [depPath, snapshot] of Object.entries(lockfile.packages ?? {})) {
     const { name, version, nonSemverVersion } = nameVerFromPkgSnapshot(depPath as DepPath, snapshot)
     if (!name || !version) continue
+    // A registry-style depPath (name@semver) must be backed by a
+    // registry-shaped resolution: the allowBuilds policy derives a
+    // trusted package identity from that key shape, which is only sound
+    // while this invariant holds. The check is offline, so it applies
+    // even when no policy verifiers are active.
+    if (nonSemverVersion == null && !isRegistryShapedResolution(snapshot.resolution)) {
+      shapeViolations.push({
+        name,
+        version,
+        resolution: snapshot.resolution as Resolution,
+        code: RESOLUTION_SHAPE_MISMATCH_VIOLATION_CODE,
+        reason: 'a registry-style dependency path is backed by a non-registry resolution',
+      })
+    }
     const key = `${name}@${version}@${nonSemverVersion ?? ''}@${JSON.stringify(snapshot.resolution)}`
     candidates.set(key, {
       name,
@@ -261,7 +343,7 @@ function collectCandidates (lockfile: LockfileObject): Map<string, Candidate> {
       resolution: snapshot.resolution as Resolution,
     })
   }
-  return candidates
+  return { candidates, shapeViolations }
 }
 
 async function iterateLockfileViolations (
diff --git a/installing/deps-restorer/src/linkHoistedModules.ts b/installing/deps-restorer/src/linkHoistedModules.ts
index 169ddb7ed1590beb687304f6a6281bd0fbd8221f..9c6c84c96d54ad9a5d73f53ec22b695af404cc6a 100644
--- a/installing/deps-restorer/src/linkHoistedModules.ts
+++ b/installing/deps-restorer/src/linkHoistedModules.ts
@@ -135,7 +135,7 @@ async function linkAllPkgsInOrder (
         depNode.requiresBuild = filesResponse.requiresBuild
         let sideEffectsCacheKey: string | undefined
         if (opts.sideEffectsCacheRead && filesResponse.sideEffectsMaps && !isEmpty(filesResponse.sideEffectsMaps)) {
-          if (opts.allowBuild?.(depNode.name, depNode.version) === true) {
+          if (opts.allowBuild?.(depNode.depPath) === true) {
             sideEffectsCacheKey = calcDepState(graph, opts.depsStateCache, dir, {
               includeDepGraphHash: !opts.ignoreScripts && depNode.requiresBuild, // true when is built
               patchFileHash: depNode.patch?.hash,
diff --git a/pacquet/crates/git-fetcher/src/fetcher/tests.rs b/pacquet/crates/git-fetcher/src/fetcher/tests.rs
index b00472af3ba7333566a8ac2ea691129b8c7e7566..2a5b64b885141548cde2a5429a900b05dd5701e1 100644
--- a/pacquet/crates/git-fetcher/src/fetcher/tests.rs
+++ b/pacquet/crates/git-fetcher/src/fetcher/tests.rs
@@ -1,5 +1,5 @@
 use super::{GitFetcher, exec_git_with, extract_host, is_valid_commit_hash, should_use_shallow};
-use crate::error::GitFetcherError;
+use crate::{error::GitFetcherError, prepare_package::AllowBuildRef};
 use pacquet_executor::ScriptsPrependNodePath;
 use pacquet_reporter::SilentReporter;
 use pacquet_store_dir::StoreDir;
@@ -47,8 +47,8 @@ fn make_bare_repo_with_prepare_script(tmp: &Path, prepare_script: &str) -> (Path
     (bare, commit)
 }
 
-fn allow_all_builds<'a>() -> &'a (dyn Fn(&str, &str) -> bool + Send + Sync) {
-    &|_, _| true
+fn allow_all_builds<'a>() -> AllowBuildRef<'a> {
+    &|_| true
 }
 
 /// Create a tiny bare git repo whose single commit ships a
@@ -77,8 +77,8 @@ fn make_bare_repo(tmp: &Path) -> (PathBuf, String) {
     (bare, commit)
 }
 
-fn deny_all_builds<'a>() -> &'a (dyn Fn(&str, &str) -> bool + Send + Sync) {
-    &|_, _| false
+fn deny_all_builds<'a>() -> AllowBuildRef<'a> {
+    &|_| false
 }
 
 #[test]
@@ -659,10 +659,9 @@ async fn fetcher_runs_prepare_when_allow_build_returns_true() {
     let repo_url = format!("file://{}", bare.display());
 
     // Targeted allow_build that returns true for *this* package only —
-    // catches a regression where the gate ignores the (name, version)
-    // pair and falls through to default-allow or default-deny.
-    let allow_x_only: &(dyn Fn(&str, &str) -> bool + Send + Sync) =
-        &|name, version| name == "x" && version == "1.0.0";
+    // catches a regression where the gate ignores the dep path and
+    // falls through to default-allow or default-deny.
+    let allow_x_only: AllowBuildRef<'_> = &|dep_path| dep_path == "x@1.0.0";
 
     let received = GitFetcher {
         repo: &repo_url,
@@ -699,6 +698,95 @@ async fn fetcher_runs_prepare_when_allow_build_returns_true() {
     );
 }
 
+#[tokio::test(flavor = "multi_thread")]
+async fn fetcher_rejects_untrusted_manifest_identity() {
+    let tmp = tempdir().unwrap();
+    let (bare, commit) = make_bare_repo_with_prepare_script(
+        tmp.path(),
+        r#"node -e "require('fs').writeFileSync('BUILD_RAN.marker', 'ok')""#,
+    );
+    let store_root = tempdir().unwrap();
+    let store_dir = StoreDir::from(store_root.path().to_path_buf());
+    let repo_url = format!("file://{}", bare.display());
+    let allow_registry_artifacts_only: AllowBuildRef<'_> = &|dep_path| !dep_path.contains("://");
+
+    let err = GitFetcher {
+        repo: &repo_url,
+        commit: &commit,
+        path: None,
+        git_shallow_hosts: &[],
+        allow_build: allow_registry_artifacts_only,
+        ignore_scripts: false,
+        unsafe_perm: true,
+        user_agent: None,
+        scripts_prepend_node_path: ScriptsPrependNodePath::Never,
+        script_shell: None,
+        node_execpath: None,
+        npm_execpath: None,
+        store_dir: &store_dir,
+        package_id: "x@git+file:///tmp/repo.git#abc123",
+        requester: "/test",
+        store_index_writer: None,
+        files_index_file: "x@git+file:///tmp/repo.git#abc123\tbuilt",
+        git_bin: None,
+    }
+    .run::<SilentReporter>()
+    .await
+    .unwrap_err();
+
+    match err {
+        GitFetcherError::Prepare(crate::error::PreparePackageError::NotAllowed {
+            name,
+            version,
+        }) => {
+            assert_eq!(name, "x");
+            assert_eq!(version, "1.0.0");
+        }
+        other => panic!("expected NotAllowed, got {other:?}"),
+    }
+}
+
+#[tokio::test(flavor = "multi_thread")]
+async fn fetcher_allows_untrusted_manifest_identity_by_dep_path() {
+    let tmp = tempdir().unwrap();
+    let (bare, commit) = make_bare_repo_with_prepare_script(
+        tmp.path(),
+        r#"node -e "require('fs').writeFileSync('BUILD_RAN.marker', 'ok')""#,
+    );
+    let store_root = tempdir().unwrap();
+    let store_dir = StoreDir::from(store_root.path().to_path_buf());
+    let repo_url = format!("file://{}", bare.display());
+    let package_id = "x@git+file:///tmp/repo.git#abc123";
+    let allow_dep_path: AllowBuildRef<'_> = &|dep_path| dep_path == package_id;
+
+    let received = GitFetcher {
+        repo: &repo_url,
+        commit: &commit,
+        path: None,
+        git_shallow_hosts: &[],
+        allow_build: allow_dep_path,
+        ignore_scripts: false,
+        unsafe_perm: true,
+        user_agent: None,
+        scripts_prepend_node_path: ScriptsPrependNodePath::Never,
+        script_shell: None,
+        node_execpath: None,
+        npm_execpath: None,
+        store_dir: &store_dir,
+        package_id,
+        requester: "/test",
+        store_index_writer: None,
+        files_index_file: "x@git+file:///tmp/repo.git#abc123\tbuilt",
+        git_bin: None,
+    }
+    .run::<SilentReporter>()
+    .await
+    .unwrap();
+
+    assert!(received.built);
+    assert!(received.cas_paths.contains_key("BUILD_RAN.marker"));
+}
+
 /// Write a `git` shim shell script to `dir/git` that:
 ///
 /// - Appends every invocation to `$PACQUET_GIT_SHIM_LOG` as one
diff --git a/pacquet/crates/git-fetcher/src/prepare_package.rs b/pacquet/crates/git-fetcher/src/prepare_package.rs
index d5159d5ace9374c6c41cf910a2b91289e1176452..278f0af2d7a2c5eb0f16ac76c6cd3e4bf156eaad 100644
--- a/pacquet/crates/git-fetcher/src/prepare_package.rs
+++ b/pacquet/crates/git-fetcher/src/prepare_package.rs
@@ -32,20 +32,20 @@ use std::{
 /// nor Yarn run it for git-hosted deps.
 const PREPUBLISH_SCRIPTS: &[&str] = &["prepublish", "prepack", "publish"];
 
-/// Closure shape used to ask the install policy whether a package
-/// (`name`, `version`) is allowed to run lifecycle scripts. Mirrors
-/// upstream's `opts.allowBuild?.(name, version)` at
-/// [`index.ts:36`](https://github.com/pnpm/pnpm/blob/94240bc046/exec/prepare-package/src/index.ts#L36).
+/// Closure shape used to ask the install policy whether the package at
+/// a dep path is allowed to run lifecycle scripts.
 ///
 /// We pass a closure rather than `&AllowBuildPolicy` so the
 /// `pacquet-git-fetcher` crate stays free of a back-edge into
 /// `pacquet-package-manager`. The caller adapts whatever policy
 /// structure it has into this shape.
-pub type AllowBuildFn<'a> = Box<dyn Fn(&str, &str) -> bool + Send + Sync + 'a>;
+pub type AllowBuildFn<'a> = Box<dyn Fn(&str) -> bool + Send + Sync + 'a>;
+pub type AllowBuildRef<'a> = &'a (dyn Fn(&str) -> bool + Send + Sync);
 
 /// Caller-supplied context for [`prepare_package`].
 pub struct PreparePackageOptions<'a> {
     pub allow_build: AllowBuildFn<'a>,
+    pub dep_path: &'a str,
     pub ignore_scripts: bool,
     pub unsafe_perm: bool,
     pub user_agent: Option<&'a str>,
@@ -96,11 +96,13 @@ pub fn prepare_package<Reporter: self::Reporter>(
     }
 
     // `allowBuild` check before any spawn. Upstream throws when
-    // `opts.allowBuild?.(name, version)` is missing or false, with
-    // GIT_DEP_PREPARE_NOT_ALLOWED.
+    // `opts.allowBuild?.(depPath)` is missing or false, with
+    // GIT_DEP_PREPARE_NOT_ALLOWED. The manifest comes from the fetched
+    // artifact itself, so its name and version only feed the error
+    // message; the dep path is the gated identity.
     let name = manifest.get("name").and_then(Value::as_str).unwrap_or("");
     let version = manifest.get("version").and_then(Value::as_str).unwrap_or("");
-    if !(opts.allow_build)(name, version) {
+    if !(opts.allow_build)(opts.dep_path) {
         return Err(PreparePackageError::NotAllowed {
             name: name.to_string(),
             version: version.to_string(),
diff --git a/pacquet/crates/git-fetcher/src/prepare_package/tests.rs b/pacquet/crates/git-fetcher/src/prepare_package/tests.rs
index e396ce97949963b381b96fff411c3971072ec98b..e51c782852753fcff5fe452e0e4d210ade19eb92 100644
--- a/pacquet/crates/git-fetcher/src/prepare_package/tests.rs
+++ b/pacquet/crates/git-fetcher/src/prepare_package/tests.rs
@@ -31,7 +31,8 @@ fn write_manifest(dir: &Path, manifest: &serde_json::Value) {
 fn opts<'a>(allow: bool, ignore_scripts: bool) -> PreparePackageOptions<'a> {
     static EMPTY_BIN_PATHS: &[std::path::PathBuf] = &[];
     PreparePackageOptions {
-        allow_build: Box::new(move |_name, _version| allow),
+        allow_build: Box::new(move |_dep_path| allow),
+        dep_path: "x@https://example.com/x.tgz",
         ignore_scripts,
         unsafe_perm: true,
         user_agent: None,
@@ -44,6 +45,40 @@ fn opts<'a>(allow: bool, ignore_scripts: bool) -> PreparePackageOptions<'a> {
     }
 }
 
+fn opts_allow_registry_artifacts_only<'a>() -> PreparePackageOptions<'a> {
+    static EMPTY_BIN_PATHS: &[std::path::PathBuf] = &[];
+    PreparePackageOptions {
+        allow_build: Box::new(move |dep_path| !dep_path.contains("://")),
+        dep_path: "x@https://example.com/x.tgz",
+        ignore_scripts: false,
+        unsafe_perm: true,
+        user_agent: None,
+        scripts_prepend_node_path: ScriptsPrependNodePath::Never,
+        script_shell: None,
+        node_execpath: None,
+        npm_execpath: None,
+        extra_bin_paths: EMPTY_BIN_PATHS,
+        extra_env: empty_env(),
+    }
+}
+
+fn opts_allow_dep_path<'a>(dep_path: &'a str) -> PreparePackageOptions<'a> {
+    static EMPTY_BIN_PATHS: &[std::path::PathBuf] = &[];
+    PreparePackageOptions {
+        allow_build: Box::new(move |actual_dep_path| actual_dep_path == dep_path),
+        dep_path,
+        ignore_scripts: false,
+        unsafe_perm: true,
+        user_agent: None,
+        scripts_prepend_node_path: ScriptsPrependNodePath::Never,
+        script_shell: None,
+        node_execpath: None,
+        npm_execpath: None,
+        extra_bin_paths: EMPTY_BIN_PATHS,
+        extra_env: empty_env(),
+    }
+}
+
 #[test]
 fn package_should_be_built_false_for_empty_scripts() {
     let dir = tempdir().unwrap();
@@ -143,6 +178,50 @@ fn prepare_rejects_when_allow_build_returns_false() {
     }
 }
 
+#[test]
+fn prepare_rejects_untrusted_manifest_identity() {
+    let dir = tempdir().unwrap();
+    write_manifest(
+        dir.path(),
+        &json!({
+            "name": "naughty", "version": "1.0.0",
+            "scripts": { "prepare": "tsc" },
+        }),
+    );
+
+    let err =
+        prepare_package::<SilentReporter>(&opts_allow_registry_artifacts_only(), dir.path(), None)
+            .unwrap_err();
+    match err {
+        PreparePackageError::NotAllowed { name, version } => {
+            assert_eq!(name, "naughty");
+            assert_eq!(version, "1.0.0");
+        }
+        other => panic!("expected NotAllowed, got {other:?}"),
+    }
+}
+
+#[test]
+fn prepare_allows_untrusted_manifest_identity_by_dep_path() {
+    let dir = tempdir().unwrap();
+    write_manifest(
+        dir.path(),
+        &json!({
+            "name": "trusted-name",
+            "version": "1.0.0",
+            "scripts": { "prepack": r#"node -e "require('fs').writeFileSync('built.txt', 'ok')""# },
+        }),
+    );
+
+    let dep_path = "trusted-name@git+https://example.com/org/repo.git#abc123";
+    let result =
+        prepare_package::<SilentReporter>(&opts_allow_dep_path(dep_path), dir.path(), None)
+            .expect("depPath-specific allow should permit prepare");
+
+    assert!(result.should_be_built);
+    assert!(dir.path().join("built.txt").exists());
+}
+
 #[test]
 fn safe_join_path_rejects_escapes() {
     let dir = tempdir().unwrap();
diff --git a/pacquet/crates/lockfile-verification/src/verify_lockfile_resolutions.rs b/pacquet/crates/lockfile-verification/src/verify_lockfile_resolutions.rs
index 8abf3ccbc14c9d7b8e35ba84e8fbc1b827d43a75..9791b1e9c2d71bd11f67f1b5c3ca023398211bf1 100644
--- a/pacquet/crates/lockfile-verification/src/verify_lockfile_resolutions.rs
+++ b/pacquet/crates/lockfile-verification/src/verify_lockfile_resolutions.rs
@@ -19,12 +19,12 @@
 use std::{collections::BTreeMap, path::Path, sync::Arc, time::Instant};
 
 use futures_util::{StreamExt, stream::FuturesUnordered};
-use pacquet_lockfile::{Lockfile, LockfileResolution, PkgName};
+use pacquet_lockfile::{Lockfile, LockfileResolution, PkgName, is_git_hosted_tarball_url};
 use pacquet_reporter::{
     LockfileVerificationLog, LockfileVerificationMessage, LogEvent, LogLevel, Reporter,
 };
 use pacquet_resolving_resolver_base::{
-    ResolutionPolicyViolation, ResolutionVerification, ResolutionVerifier, VerifyCtx,
+    ResolutionPolicyViolation, ResolutionVerification, ResolutionVerifier, VerifyCtx, VerifyFuture,
 };
 use tokio::sync::Semaphore;
 
@@ -82,7 +82,7 @@ pub async fn verify_lockfile_resolutions<Reporter: self::Reporter>(
     verifiers: &[Arc<dyn ResolutionVerifier>],
     opts: &VerifyLockfileResolutionsOptions<'_>,
 ) -> Result<(), VerifyError> {
-    if verifiers.is_empty() || lockfile.packages.is_none() {
+    if lockfile.packages.is_none() {
         return Ok(());
     }
 
@@ -93,6 +93,8 @@ pub async fn verify_lockfile_resolutions<Reporter: self::Reporter>(
     // logic via the same code path).
     let cache_inputs = opts.cache_dir.zip(opts.lockfile_path);
 
+    let cache_verifiers = with_resolution_shape_cache_identity(verifiers);
+
     // Memoised content hash. Used by both the lookup (when the
     // stat-shortcut doesn't apply) and the recorder (after the
     // gate passes). The closure is `FnMut` so multiple lazy calls
@@ -109,15 +111,25 @@ pub async fn verify_lockfile_resolutions<Reporter: self::Reporter>(
 
     let mut cache_precomputed: CachePrecomputed = CachePrecomputed::default();
     if let Some((cache_dir, lockfile_path)) = cache_inputs {
-        let result =
-            try_lockfile_verification_cache(cache_dir, lockfile_path, verifiers, &mut hash_once);
+        let result = try_lockfile_verification_cache(
+            cache_dir,
+            lockfile_path,
+            &cache_verifiers,
+            &mut hash_once,
+        );
         if result.hit {
             return Ok(());
         }
         cache_precomputed = result.precomputed;
     }
 
-    let candidates = collect_candidates(lockfile);
+    let (candidates, shape_violations) = collect_candidates(lockfile);
+    if !shape_violations.is_empty() {
+        return Err(build_verification_error(shape_violations));
+    }
+    if verifiers.is_empty() {
+        return Ok(());
+    }
     let lockfile_path_str = opts.lockfile_path.map(|path| path.to_string_lossy().into_owned());
     if candidates.is_empty() {
         // Persist the success so the next install can stat-only the
@@ -128,7 +140,7 @@ pub async fn verify_lockfile_resolutions<Reporter: self::Reporter>(
             record_verification(
                 cache_dir,
                 lockfile_path,
-                verifiers,
+                &cache_verifiers,
                 &mut hash_once,
                 cache_precomputed,
             );
@@ -161,7 +173,7 @@ pub async fn verify_lockfile_resolutions<Reporter: self::Reporter>(
             record_verification(
                 cache_dir,
                 lockfile_path,
-                verifiers,
+                &cache_verifiers,
                 &mut hash_once,
                 cache_precomputed,
             );
@@ -184,10 +196,98 @@ pub async fn collect_resolution_policy_violations(
     if verifiers.is_empty() || lockfile.packages.is_none() {
         return Vec::new();
     }
-    let candidates = collect_candidates(lockfile);
+    // Shape violations are deliberately not collected here: they are
+    // hard tampering failures, not policy picks a caller may
+    // auto-exclude.
+    let (candidates, _shape_violations) = collect_candidates(lockfile);
     run_fan_out(candidates, verifiers, concurrency).await
 }
 
+pub const RESOLUTION_SHAPE_MISMATCH_VIOLATION_CODE: &str = "RESOLUTION_SHAPE_MISMATCH";
+
+/// Cache-key participant for the offline resolution-shape pass: a
+/// record written before the rule existed lacks the flag, so
+/// `can_trust_past_check` rejects it and forces a re-verification.
+/// `verify` is never invoked — the identity is appended only to the
+/// verifier lists handed to the cache lookup and recorder.
+struct ResolutionShapeCacheIdentity {
+    policy: serde_json::Map<String, serde_json::Value>,
+}
+
+fn resolution_shape_cache_identity() -> Arc<dyn ResolutionVerifier> {
+    let mut policy = serde_json::Map::new();
+    policy.insert("resolutionShapeCheck".to_string(), serde_json::Value::Bool(true));
+    Arc::new(ResolutionShapeCacheIdentity { policy })
+}
+
+/// Every verifier list that flows into the verification cache must
+/// carry the resolution-shape identity, so records written before the
+/// shape rule existed cannot stat-fast-path around it. Used by the
+/// gate itself and by [`crate::record_lockfile_verified()`], whose
+/// freshly-resolved lockfile satisfies the shape invariant by
+/// construction (the writer derives every key from the resolution it
+/// just produced).
+pub(crate) fn with_resolution_shape_cache_identity(
+    verifiers: &[Arc<dyn ResolutionVerifier>],
+) -> Vec<Arc<dyn ResolutionVerifier>> {
+    verifiers.iter().cloned().chain(std::iter::once(resolution_shape_cache_identity())).collect()
+}
+
+impl ResolutionVerifier for ResolutionShapeCacheIdentity {
+    fn verify<'a>(
+        &'a self,
+        _resolution: &'a LockfileResolution,
+        _ctx: VerifyCtx<'a>,
+    ) -> VerifyFuture<'a> {
+        Box::pin(async { ResolutionVerification::Ok })
+    }
+
+    fn policy(&self) -> &serde_json::Map<String, serde_json::Value> {
+        &self.policy
+    }
+
+    fn can_trust_past_check(&self, cached: &serde_json::Map<String, serde_json::Value>) -> bool {
+        cached.get("resolutionShapeCheck") == Some(&serde_json::Value::Bool(true))
+    }
+}
+
+/// Mirrors upstream's `isRegistryShapedResolution`: a plain tarball
+/// resolution is registry-shaped because the npm verifier unconditionally
+/// binds explicit tarball URLs of semver-keyed entries to the registry's
+/// own `dist.tarball`. A git-hosted tarball is not — and trust is gated on
+/// the tarball URL rather than the `gitHosted` flag alone, so a tampered
+/// entry that clears the flag (`gitHosted: false`) on a git-host URL is
+/// still rejected.
+fn is_registry_shaped_resolution(resolution: &LockfileResolution) -> bool {
+    match resolution {
+        LockfileResolution::Registry(_) => true,
+        LockfileResolution::Tarball(tarball) => {
+            // The tarball URL must be an http(s) registry artifact and not
+            // git-hosted. The npm verifier's tarball-URL binding skips
+            // non-http(s) schemes (file:, etc.), so a `file:` tarball under a
+            // name@semver key would otherwise be trusted with no safety net.
+            is_http_tarball_url(&tarball.tarball)
+                && tarball.git_hosted != Some(true)
+                && !is_git_hosted_tarball_url(&tarball.tarball)
+        }
+        LockfileResolution::Variations(variations) => variations
+            .variants
+            .iter()
+            .all(|variant| is_registry_shaped_resolution(&variant.resolution)),
+        LockfileResolution::Directory(_)
+        | LockfileResolution::Git(_)
+        | LockfileResolution::Binary(_) => false,
+    }
+}
+
+/// Whether a tarball URL uses an http(s) scheme — the only schemes a
+/// registry artifact is served over. Case-insensitive to reject a
+/// tampered uppercase scheme.
+fn is_http_tarball_url(url: &str) -> bool {
+    let lower = url.to_ascii_lowercase();
+    lower.starts_with("https://") || lower.starts_with("http://")
+}
+
 /// One `(name, version, resolution)` tuple deduplicated from
 /// `lockfile.packages`. Mirrors upstream's inline `Candidate`
 /// interface.
@@ -207,14 +307,34 @@ struct Candidate {
 /// `BTreeMap` over a serialized key gives deterministic iteration
 /// order for tests; the fan-out runs across the value iter so order
 /// doesn't affect correctness, only the reproducibility of failures.
-fn collect_candidates(lockfile: &Lockfile) -> Vec<Candidate> {
+fn collect_candidates(lockfile: &Lockfile) -> (Vec<Candidate>, Vec<ResolutionPolicyViolation>) {
     let Some(packages) = lockfile.packages.as_ref() else {
-        return Vec::new();
+        return (Vec::new(), Vec::new());
     };
     let mut deduped: BTreeMap<String, Candidate> = BTreeMap::new();
+    let mut shape_violations = Vec::new();
     for (key, metadata) in packages {
         let name = key.name.clone();
         let version = key.suffix.version().to_string();
+        // A registry-style dep path (`name@semver`, no `runtime:`-style
+        // prefix) must be backed by a registry-shaped resolution: the
+        // allowBuilds policy derives a trusted package identity from
+        // that key shape, which is only sound while this invariant
+        // holds. The check is offline, so it applies even when no
+        // policy verifiers are active.
+        if key.suffix.prefix() == pacquet_lockfile::Prefix::None
+            && matches!(key.suffix.version(), pacquet_lockfile::VersionPart::Semver(_))
+            && !is_registry_shaped_resolution(&metadata.resolution)
+        {
+            shape_violations.push(ResolutionPolicyViolation {
+                name: name.clone(),
+                version: version.clone(),
+                resolution: metadata.resolution.clone(),
+                code: RESOLUTION_SHAPE_MISMATCH_VIOLATION_CODE,
+                reason: "a registry-style dependency path is backed by a non-registry resolution"
+                    .to_string(),
+            });
+        }
         // Every `LockfileResolution` variant derives `Serialize`, and
         // the wire shape never contains non-string keys or non-finite
         // numbers — the only way this `expect` could fire is a future
@@ -230,7 +350,7 @@ fn collect_candidates(lockfile: &Lockfile) -> Vec<Candidate> {
             resolution: metadata.resolution.clone(),
         });
     }
-    deduped.into_values().collect()
+    (deduped.into_values().collect(), shape_violations)
 }
 
 /// Run every active verifier against every candidate with a
diff --git a/pacquet/crates/lockfile-verification/src/verify_lockfile_resolutions/tests.rs b/pacquet/crates/lockfile-verification/src/verify_lockfile_resolutions/tests.rs
index 370889d24aa2a8a171cd919c1930650ffb45550c..331ab7b47bffaec5988d0bb0f42014bcd46d7ccd 100644
--- a/pacquet/crates/lockfile-verification/src/verify_lockfile_resolutions/tests.rs
+++ b/pacquet/crates/lockfile-verification/src/verify_lockfile_resolutions/tests.rs
@@ -527,3 +527,181 @@ async fn ctx_borrows_have_expected_lifetimes() {
     .await;
     assert!(result.is_ok());
 }
+
+#[tokio::test]
+async fn rejects_registry_style_key_backed_by_git_resolution_even_with_no_verifiers() {
+    let lockfile = parse(
+        "lockfileVersion: '9.0'
+
+importers:
+
+  .:
+    dependencies:
+      acme:
+        specifier: ^1.0.0
+        version: 1.0.0
+
+packages:
+
+  acme@1.0.0:
+    resolution: {type: git, repo: https://example.com/acme.git, commit: 0123456789abcdef0123456789abcdef01234567}
+
+snapshots:
+
+  acme@1.0.0: {}
+",
+    );
+    let err = verify_lockfile_resolutions::<SilentReporter>(
+        &lockfile,
+        &[],
+        &VerifyLockfileResolutionsOptions::default(),
+    )
+    .await
+    .expect_err("registry-style key with a git resolution must be rejected");
+    let VerifyError::ResolutionShapeMismatch { count, breakdown } = err else {
+        panic!("expected ResolutionShapeMismatch, got {err:?}");
+    };
+    assert_eq!(count, 1);
+    assert!(breakdown.contains("acme@1.0.0"), "breakdown: {breakdown}");
+}
+
+#[tokio::test]
+async fn accepts_artifact_keys_with_non_registry_resolutions() {
+    let lockfile = parse(
+        "lockfileVersion: '9.0'
+
+importers:
+
+  .:
+    dependencies:
+      acme:
+        specifier: github:org/acme
+        version: git+https://example.com/acme.git#0123456789abcdef0123456789abcdef01234567
+
+packages:
+
+  acme@git+https://example.com/acme.git#0123456789abcdef0123456789abcdef01234567:
+    resolution: {type: git, repo: https://example.com/acme.git, commit: 0123456789abcdef0123456789abcdef01234567}
+    version: 1.0.0
+
+snapshots:
+
+  acme@git+https://example.com/acme.git#0123456789abcdef0123456789abcdef01234567: {}
+",
+    );
+    verify_lockfile_resolutions::<SilentReporter>(
+        &lockfile,
+        &[],
+        &VerifyLockfileResolutionsOptions::default(),
+    )
+    .await
+    .expect("artifact-keyed git entry passes the structural gate");
+}
+
+#[tokio::test]
+async fn rejects_git_host_tarball_when_git_hosted_flag_is_cleared() {
+    // A tampered lockfile sets gitHosted: false on a codeload URL under a
+    // semver key to dodge the flag-only check; the URL must still flag it.
+    let lockfile = parse(
+        "lockfileVersion: '9.0'
+
+importers:
+
+  .:
+    dependencies:
+      acme:
+        specifier: ^1.0.0
+        version: 1.0.0
+
+packages:
+
+  acme@1.0.0:
+    resolution: {integrity: sha512-deadbeef, tarball: 'https://codeload.github.com/org/acme/tar.gz/abc123', gitHosted: false}
+
+snapshots:
+
+  acme@1.0.0: {}
+",
+    );
+    let err = verify_lockfile_resolutions::<SilentReporter>(
+        &lockfile,
+        &[],
+        &VerifyLockfileResolutionsOptions::default(),
+    )
+    .await
+    .expect_err("git-host tarball under a semver key must be rejected regardless of the flag");
+    let VerifyError::ResolutionShapeMismatch { count, .. } = err else {
+        panic!("expected ResolutionShapeMismatch, got {err:?}");
+    };
+    assert_eq!(count, 1);
+}
+
+#[tokio::test]
+async fn rejects_semver_key_backed_by_non_http_tarball() {
+    // A file: tarball under a semver key is not registry-backed and the npm
+    // verifier skips non-http(s) tarballs, so the shape pass must reject it.
+    let lockfile = parse(
+        "lockfileVersion: '9.0'
+
+importers:
+
+  .:
+    dependencies:
+      acme:
+        specifier: ^1.0.0
+        version: 1.0.0
+
+packages:
+
+  acme@1.0.0:
+    resolution: {integrity: sha512-deadbeef, tarball: 'file:///tmp/evil.tgz'}
+
+snapshots:
+
+  acme@1.0.0: {}
+",
+    );
+    let err = verify_lockfile_resolutions::<SilentReporter>(
+        &lockfile,
+        &[],
+        &VerifyLockfileResolutionsOptions::default(),
+    )
+    .await
+    .expect_err("file: tarball under a semver key must be rejected");
+    assert!(matches!(err, VerifyError::ResolutionShapeMismatch { .. }), "got {err:?}");
+}
+
+#[tokio::test]
+async fn rejects_git_host_tarball_with_uppercased_host() {
+    // Hostnames are case-insensitive; an uppercased codeload host with
+    // gitHosted: false must still be rejected under a semver key.
+    let lockfile = parse(
+        "lockfileVersion: '9.0'
+
+importers:
+
+  .:
+    dependencies:
+      acme:
+        specifier: ^1.0.0
+        version: 1.0.0
+
+packages:
+
+  acme@1.0.0:
+    resolution: {integrity: sha512-deadbeef, tarball: 'https://CODELOAD.GITHUB.COM/org/acme/tar.gz/abc123', gitHosted: false}
+
+snapshots:
+
+  acme@1.0.0: {}
+",
+    );
+    let err = verify_lockfile_resolutions::<SilentReporter>(
+        &lockfile,
+        &[],
+        &VerifyLockfileResolutionsOptions::default(),
+    )
+    .await
+    .expect_err("uppercased git-host tarball must be rejected");
+    assert!(matches!(err, VerifyError::ResolutionShapeMismatch { .. }), "got {err:?}");
+}
diff --git a/pacquet/crates/package-manager/src/build_modules.rs b/pacquet/crates/package-manager/src/build_modules.rs
index b7202945121af4d2e8d09b830299df77b8af5428..37f303a341c873566412b7464fb0d469020eaf83 100644
--- a/pacquet/crates/package-manager/src/build_modules.rs
+++ b/pacquet/crates/package-manager/src/build_modules.rs
@@ -6,6 +6,7 @@ use crate::{
 use derive_more::{Display, Error};
 use miette::Diagnostic;
 use pacquet_config::Config;
+use pacquet_deps_path::remove_suffix;
 use pacquet_executor::{
     LifecycleScriptError, RunPostinstallHooks, ScriptsPrependNodePath, run_postinstall_hooks,
 };
@@ -84,6 +85,8 @@ pub enum BuildModulesError {
 pub struct AllowBuildPolicy {
     expanded_allowed: HashSet<String>,
     expanded_disallowed: HashSet<String>,
+    allowed_dep_paths: HashSet<String>,
+    disallowed_dep_paths: HashSet<String>,
     dangerously_allow_all: bool,
 }
 
@@ -99,7 +102,29 @@ impl AllowBuildPolicy {
         expanded_disallowed: HashSet<String>,
         dangerously_allow_all: bool,
     ) -> Self {
-        Self { expanded_allowed, expanded_disallowed, dangerously_allow_all }
+        Self {
+            expanded_allowed,
+            expanded_disallowed,
+            allowed_dep_paths: HashSet::new(),
+            disallowed_dep_paths: HashSet::new(),
+            dangerously_allow_all,
+        }
+    }
+
+    pub fn new_with_dep_paths(
+        expanded_allowed: HashSet<String>,
+        expanded_disallowed: HashSet<String>,
+        allowed_dep_paths: HashSet<String>,
+        disallowed_dep_paths: HashSet<String>,
+        dangerously_allow_all: bool,
+    ) -> Self {
+        Self {
+            expanded_allowed,
+            expanded_disallowed,
+            allowed_dep_paths,
+            disallowed_dep_paths,
+            dangerously_allow_all,
+        }
     }
 
     /// Build the policy from a resolved [`Config`]. Reads
@@ -120,16 +145,32 @@ impl AllowBuildPolicy {
     pub fn from_config(config: &Config) -> Result<Self, VersionPolicyError> {
         let mut allowed_specs: Vec<&str> = Vec::new();
         let mut disallowed_specs: Vec<&str> = Vec::new();
+        let mut allowed_dep_paths = HashSet::new();
+        let mut disallowed_dep_paths = HashSet::new();
         for (spec, &value) in &config.allow_builds {
-            if value {
-                allowed_specs.push(spec);
+            if is_dep_path_allow_build_key(spec) {
+                if value {
+                    allowed_dep_paths.insert(normalize_build_dep_path(spec));
+                } else {
+                    disallowed_dep_paths.insert(normalize_build_dep_path(spec));
+                }
             } else {
-                disallowed_specs.push(spec);
+                if value {
+                    allowed_specs.push(spec);
+                } else {
+                    disallowed_specs.push(spec);
+                }
             }
         }
         let expanded_allowed = expand_package_version_specs(allowed_specs)?;
         let expanded_disallowed = expand_package_version_specs(disallowed_specs)?;
-        Ok(Self::new(expanded_allowed, expanded_disallowed, config.dangerously_allow_all_builds))
+        Ok(Self::new_with_dep_paths(
+            expanded_allowed,
+            expanded_disallowed,
+            allowed_dep_paths,
+            disallowed_dep_paths,
+            config.dangerously_allow_all_builds,
+        ))
     }
 
     /// Check whether a package is allowed to run build scripts.
@@ -146,18 +187,34 @@ impl AllowBuildPolicy {
     /// lookup means `*` wildcards in specs do NOT match real
     /// package names — see [`expand_package_version_specs`] for
     /// the rationale.
-    pub fn check(&self, name: &str, version: &str) -> Option<bool> {
+    pub fn check(&self, dep_path: &str) -> Option<bool> {
         if self.dangerously_allow_all {
             return Some(true);
         }
 
+        let normalized_dep_path = normalize_build_dep_path(dep_path);
+        if self.disallowed_dep_paths.contains(&normalized_dep_path) {
+            return Some(false);
+        }
+        let (name, version) = parse_name_version_from_key(&normalized_dep_path);
         let name_at_version = format!("{name}@{version}");
-        if self.expanded_disallowed.contains(name)
+        if self.expanded_disallowed.contains(&name)
             || self.expanded_disallowed.contains(&name_at_version)
         {
             return Some(false);
         }
-        if self.expanded_allowed.contains(name) || self.expanded_allowed.contains(&name_at_version)
+        if self.allowed_dep_paths.contains(&normalized_dep_path) {
+            return Some(true);
+        }
+        // Package-name rules require a trusted package identity. A
+        // registry-style dep path (`name@semver`) is the trust signal: the
+        // lockfile verification gate rejects lockfiles where such a key is
+        // backed by a non-registry resolution, so by the time scripts can
+        // run, the shape proves the artifact came from a registry.
+        if node_semver::Version::parse(&version).is_err() {
+            return None;
+        }
+        if self.expanded_allowed.contains(&name) || self.expanded_allowed.contains(&name_at_version)
         {
             return Some(true);
         }
@@ -166,6 +223,33 @@ impl AllowBuildPolicy {
     }
 }
 
+/// Strips the peer suffix (and, matching [`PkgVerPeer::without_peer`]'s
+/// lumped suffix handling, the patch hash) so config keys compare equal
+/// to the `metadata_key.to_string()` form used at the runtime call sites.
+///
+/// [`PkgVerPeer::without_peer`]: pacquet_lockfile::PkgVerPeer::without_peer
+pub(crate) fn normalize_build_dep_path(dep_path: &str) -> String {
+    remove_suffix(dep_path).to_string()
+}
+
+fn is_dep_path_allow_build_key(spec: &str) -> bool {
+    if normalize_build_dep_path(spec) != spec {
+        return true;
+    }
+    if spec.contains("||") {
+        return false;
+    }
+    let (_, version) = parse_name_version_from_key(spec);
+    if version.is_empty() {
+        return !spec.starts_with('@') && (spec.contains('/') || spec.contains(':'));
+    }
+    node_semver::Version::parse(&version).is_err() && is_source_like_dep_path_version(&version)
+}
+
+fn is_source_like_dep_path_version(version: &str) -> bool {
+    version.contains(':') || version.contains('/') || version.contains('#')
+}
+
 /// Run lifecycle scripts for all packages that require a build.
 ///
 /// Ports the core of `buildModules` from
@@ -547,7 +631,8 @@ fn build_one_snapshot<Reporter: self::Reporter>(
     // `ignoreScripts = true; break` pattern.
     let mut should_run_scripts = requires_build;
     if requires_build {
-        match allow_build_policy.check(&name, &version) {
+        let dep_path = metadata_key.to_string();
+        match allow_build_policy.check(&dep_path) {
             Some(false) => {
                 should_run_scripts = false;
             }
@@ -560,10 +645,7 @@ fn build_one_snapshot<Reporter: self::Reporter>(
                 // the end of `BuildModules::run` for the safety
                 // argument (BTreeSet insertion is atomic from the
                 // data-structure's POV).
-                ignored_builds
-                    .lock()
-                    .unwrap_or_else(|e| e.into_inner())
-                    .insert(metadata_key.to_string());
+                ignored_builds.lock().unwrap_or_else(|e| e.into_inner()).insert(dep_path);
                 should_run_scripts = false;
             }
             Some(true) => {}
diff --git a/pacquet/crates/package-manager/src/build_modules/tests.rs b/pacquet/crates/package-manager/src/build_modules/tests.rs
index 5f8f9472709ba9ce35e2039a2b078b3d2baf18c6..dcbb7bb5948a91962fb26104854113ad5180466b 100644
--- a/pacquet/crates/package-manager/src/build_modules/tests.rs
+++ b/pacquet/crates/package-manager/src/build_modules/tests.rs
@@ -21,26 +21,19 @@ use tempfile::tempdir;
 /// Build an [`AllowBuildPolicy`] from a list of `(spec, allowed)`
 /// pairs, mirroring how `pnpm-workspace.yaml`'s `allowBuilds` map
 /// would arrive at the policy. Each spec is parsed through
-/// [`crate::expand_package_version_specs`] so version unions
-/// (`foo@1.0.0 || 2.0.0`) work the same way they do at runtime.
+/// [`AllowBuildPolicy::from_config`] so version unions and depPath
+/// keys work the same way they do at runtime.
 /// Panics on any parse failure — test inputs must be valid.
 fn policy_from_specs<const LEN: usize>(
     entries: [(&str, bool); LEN],
     dangerously_allow_all: bool,
 ) -> AllowBuildPolicy {
-    use crate::expand_package_version_specs;
-    let mut allowed_specs: Vec<&str> = Vec::new();
-    let mut disallowed_specs: Vec<&str> = Vec::new();
+    let mut config = Config::new();
+    config.dangerously_allow_all_builds = dangerously_allow_all;
     for (spec, value) in entries {
-        if value {
-            allowed_specs.push(spec);
-        } else {
-            disallowed_specs.push(spec);
-        }
+        config.allow_builds.insert(spec.to_string(), value);
     }
-    let expanded_allowed = expand_package_version_specs(allowed_specs).expect("valid specs");
-    let expanded_disallowed = expand_package_version_specs(disallowed_specs).expect("valid specs");
-    AllowBuildPolicy::new(expanded_allowed, expanded_disallowed, dangerously_allow_all)
+    AllowBuildPolicy::from_config(&config).expect("valid specs")
 }
 
 #[test]
@@ -74,25 +67,55 @@ fn parse_key_without_leading_slash() {
 #[test]
 fn default_policy_denies_all() {
     let policy = AllowBuildPolicy::default();
-    assert_eq!(policy.check("any-package", "1.0.0"), None);
+    assert_eq!(policy.check("any-package@1.0.0"), None);
 }
 
 #[test]
 fn explicit_allow() {
     let policy = policy_from_specs([("@pnpm.e2e/install-script-example", true)], false);
-    assert_eq!(policy.check("@pnpm.e2e/install-script-example", "1.0.0"), Some(true));
+    assert_eq!(policy.check("@pnpm.e2e/install-script-example@1.0.0"), Some(true));
+}
+
+#[test]
+fn explicit_allow_requires_registry_style_dep_path() {
+    let policy = policy_from_specs([("@pnpm.e2e/install-script-example", true)], false);
+    assert_eq!(
+        policy.check("@pnpm.e2e/install-script-example@git+https://example.com/x.git#abc123"),
+        None,
+    );
+    assert_eq!(policy.check("@pnpm.e2e/install-script-example@1.0.0"), Some(true));
+}
+
+#[test]
+fn explicit_allow_by_dep_path_allows_untrusted_package_identity() {
+    let policy = policy_from_specs(
+        [("foo@git+https://github.com/org/foo.git#abc123", true), ("foo", true)],
+        false,
+    );
+    assert_eq!(
+        policy.check("foo@git+https://github.com/org/foo.git#abc123(react@19.0.0)"),
+        Some(true),
+    );
+    assert_eq!(policy.check("foo@git+https://github.com/attacker/foo.git#abc123"), None);
+}
+
+#[test]
+fn explicit_allow_by_tarball_dep_path_allows_untrusted_package_identity() {
+    let policy = policy_from_specs([("foo@https://example.com/foo.tgz", true)], false);
+
+    assert_eq!(policy.check("foo@https://example.com/foo.tgz"), Some(true));
 }
 
 #[test]
 fn explicit_deny() {
     let policy = policy_from_specs([("@pnpm.e2e/bad-package", false)], false);
-    assert_eq!(policy.check("@pnpm.e2e/bad-package", "1.0.0"), Some(false));
+    assert_eq!(policy.check("@pnpm.e2e/bad-package@1.0.0"), Some(false));
 }
 
 #[test]
 fn unlisted_returns_none() {
     let policy = policy_from_specs([("@pnpm.e2e/allowed", true)], false);
-    assert_eq!(policy.check("@pnpm.e2e/not-listed", "1.0.0"), None);
+    assert_eq!(policy.check("@pnpm.e2e/not-listed@1.0.0"), None);
 }
 
 /// Upstream checks `expandedDisallowed` before `expandedAllowed`
@@ -106,8 +129,8 @@ fn unlisted_returns_none() {
 fn disallow_bare_name_wins_over_allow_exact_version() {
     let policy =
         policy_from_specs([("@pnpm.e2e/pkg@1.0.0", true), ("@pnpm.e2e/pkg", false)], false);
-    assert_eq!(policy.check("@pnpm.e2e/pkg", "1.0.0"), Some(false));
-    assert_eq!(policy.check("@pnpm.e2e/pkg", "2.0.0"), Some(false));
+    assert_eq!(policy.check("@pnpm.e2e/pkg@1.0.0"), Some(false));
+    assert_eq!(policy.check("@pnpm.e2e/pkg@2.0.0"), Some(false));
 }
 
 /// The converse: a bare-name allow combined with an exact-version
@@ -117,27 +140,33 @@ fn disallow_bare_name_wins_over_allow_exact_version() {
 fn disallow_exact_version_with_allow_bare_name() {
     let policy =
         policy_from_specs([("@pnpm.e2e/pkg", true), ("@pnpm.e2e/pkg@1.0.0", false)], false);
-    assert_eq!(policy.check("@pnpm.e2e/pkg", "1.0.0"), Some(false));
-    assert_eq!(policy.check("@pnpm.e2e/pkg", "2.0.0"), Some(true));
+    assert_eq!(policy.check("@pnpm.e2e/pkg@1.0.0"), Some(false));
+    assert_eq!(policy.check("@pnpm.e2e/pkg@2.0.0"), Some(true));
 }
 
 #[test]
 fn empty_rules_denies_all() {
     let policy = policy_from_specs([], false);
-    assert_eq!(policy.check("any-package", "1.0.0"), None);
+    assert_eq!(policy.check("any-package@1.0.0"), None);
 }
 
 #[test]
 fn dangerously_allow_all_builds() {
     let policy = policy_from_specs([], true);
-    assert_eq!(policy.check("any-package", "1.0.0"), Some(true));
-    assert_eq!(policy.check("other-package", "2.0.0"), Some(true));
+    assert_eq!(policy.check("any-package@1.0.0"), Some(true));
+    assert_eq!(policy.check("other-package@2.0.0"), Some(true));
+}
+
+#[test]
+fn dangerously_allow_all_allows_artifact_dep_paths() {
+    let policy = policy_from_specs([], true);
+    assert_eq!(policy.check("anything@git+https://example.com/x.git#abc123"), Some(true));
 }
 
 #[test]
 fn dangerously_allow_all_overrides_deny() {
     let policy = policy_from_specs([("@pnpm.e2e/pkg", false)], true);
-    assert_eq!(policy.check("@pnpm.e2e/pkg", "1.0.0"), Some(true));
+    assert_eq!(policy.check("@pnpm.e2e/pkg@1.0.0"), Some(true));
 }
 
 /// Mirrors upstream's
@@ -148,11 +177,11 @@ fn dangerously_allow_all_overrides_deny() {
 #[test]
 fn allow_via_version_union() {
     let policy = policy_from_specs([("foo", true), ("qar@1.0.0 || 2.0.0", true)], false);
-    assert_eq!(policy.check("foo", "1.0.0"), Some(true));
-    assert_eq!(policy.check("bar", "1.0.0"), None);
-    assert_eq!(policy.check("qar", "1.0.0"), Some(true));
-    assert_eq!(policy.check("qar", "2.0.0"), Some(true));
-    assert_eq!(policy.check("qar", "1.1.0"), None);
+    assert_eq!(policy.check("foo@1.0.0"), Some(true));
+    assert_eq!(policy.check("bar@1.0.0"), None);
+    assert_eq!(policy.check("qar@1.0.0"), Some(true));
+    assert_eq!(policy.check("qar@2.0.0"), Some(true));
+    assert_eq!(policy.check("qar@1.1.0"), None);
 }
 
 /// Mirrors upstream's
@@ -165,8 +194,8 @@ fn allow_via_version_union() {
 #[test]
 fn wildcard_name_in_allow_builds_does_not_match_real_package() {
     let policy = policy_from_specs([("is-*", true)], false);
-    assert_eq!(policy.check("is-odd", "1.0.0"), None);
-    assert_eq!(policy.check("is-positive", "1.0.0"), None);
+    assert_eq!(policy.check("is-odd@1.0.0"), None);
+    assert_eq!(policy.check("is-positive@1.0.0"), None);
 }
 
 /// `from_config` propagates `expand_package_version_specs` errors —
@@ -201,7 +230,7 @@ fn from_config_propagates_name_pattern_in_version_union() {
 #[test]
 fn empty_config_denies_all() {
     let policy = AllowBuildPolicy::from_config(&Config::new()).expect("empty config never errors");
-    assert_eq!(policy.check("anything", "1.0.0"), None);
+    assert_eq!(policy.check("anything@1.0.0"), None);
 }
 
 #[test]
@@ -212,9 +241,9 @@ fn from_config_consumes_allow_builds_and_dangerously_allow_all_builds() {
     config.allow_builds.insert("@pnpm.e2e/bad-package".to_string(), false);
 
     let policy = AllowBuildPolicy::from_config(&config).expect("valid specs");
-    assert_eq!(policy.check("@pnpm.e2e/install-script-example", "1.0.0"), Some(true));
-    assert_eq!(policy.check("@pnpm.e2e/bad-package", "1.0.0"), Some(false));
-    assert_eq!(policy.check("@pnpm.e2e/unrelated", "1.0.0"), None);
+    assert_eq!(policy.check("@pnpm.e2e/install-script-example@1.0.0"), Some(true));
+    assert_eq!(policy.check("@pnpm.e2e/bad-package@1.0.0"), Some(false));
+    assert_eq!(policy.check("@pnpm.e2e/unrelated@1.0.0"), None);
 }
 
 fn name(text: &str) -> PkgName {

# (13 test/doc file(s) of the upstream fix omitted here)

# ... 36 more source file(s) changed in this fix, listed instead of shown to save space (the same kind of change unless the line says otherwise):
- building/commands/package.json: +1 -0; first added line: "@pnpm/building.policy": "workspace:*",
- building/commands/src/policy/approveBuilds.ts: +2 -2; first added line: import { allowBuildKeyFromIgnoredBuild } from '@pnpm/building.policy'
- building/commands/src/policy/getAutomaticallyIgnoredBuilds.ts: +2 -2; first added line: import { allowBuildKeyFromIgnoredBuild } from '@pnpm/building.policy'
- building/commands/tsconfig.json: +3 -0; first added line: },
- building/during-install/src/index.ts: +1 -1; first added line: const allowed = allowBuild(node.depPath)
- core/types/src/config.ts: +7 -1; first added line: import type { DepPath } from './misc.js'
- deps/graph-builder/src/lockfileToDepGraph.ts: +1 -1; first added line: opts.allowBuild?.(depPath) === true
- deps/graph-hasher/src/index.ts: +4 -4; first added line: entries: Iterable<PkgMeta>,
- deps/path/src/index.ts: +9 -6; first added line: export function removePeersSuffix (relDepPath: string): string {
- exec/prepare-package/src/index.ts: +9 -4; first added line: import type { AllowBuild, DepPath, PackageManifest } from '@pnpm/types'
- fetching/git-fetcher/package.json: +1 -0; first added line: "@pnpm/resolving.git-resolver": "workspace:*",
- fetching/git-fetcher/src/index.ts: +2 -0; first added line: import { createGitHostedPkgId } from '@pnpm/resolving.git-resolver'
- fetching/git-fetcher/tsconfig.json: +3 -0; first added line: {
- fetching/tarball-fetcher/src/gitHostedTarballFetcher.ts: +9 -0; first added line: pkgResolutionId: createGitHostedTarballPkgResolutionId(resolution),
- installing/commands/package.json: +1 -0; first added line: "@pnpm/building.policy": "workspace:*",
- installing/commands/src/handleIgnoredBuilds.ts: +2 -2; first added line: import { allowBuildKeyFromIgnoredBuild } from '@pnpm/building.policy'
- installing/commands/tsconfig.json: +3 -0; first added line: {
- installing/deps-installer/src/install/link.ts: +1 -1; first added line: if (opts.allowBuild?.(depNode.depPath) === true) {
- installing/deps-installer/src/install/recordLockfileVerified.ts: +2 -1; first added line: import { withResolutionShapeCacheIdentity } from './verifyLockfileResolutions.js'
- installing/deps-restorer/src/index.ts: +1 -1; first added line: if (opts.allowBuild?.(depNode.depPath) === true) {
- lockfile/fs/src/lockfileFormatConverters.ts: +1 -13; first added line: import { isGitHostedTarballUrl } from '@pnpm/lockfile.utils'
- lockfile/utils/src/index.ts: +1 -1; first added line: export { isGitHostedTarballUrl, toLockfileResolution } from './toLockfileResolution.js'
- lockfile/utils/src/toLockfileResolution.ts: +9 -4; first added line: // Schemes and hostnames are case-insensitive, so match against a lowercased
- pacquet/crates/git-fetcher/src/fetcher.rs: +4 -3; first added line: prepare_package::{AllowBuildRef, PreparePackageOptions, PreparedPackage, prepare_package},
- pacquet/crates/git-fetcher/src/tarball_fetcher.rs: +4 -3; first added line: prepare_package::{AllowBuildRef, PreparePackageOptions, PreparedPackage, prepare_package},
- pacquet/crates/git-fetcher/src/tarball_fetcher/tests.rs: +6 -3; first added line: use crate::{
- pacquet/crates/lockfile-verification/src/errors.rs: +14 -0; first added line: /// Every violation tripped `RESOLUTION_SHAPE_MISMATCH` — a
- pacquet/crates/lockfile-verification/src/lib.rs: +2 -2; first added line: RESOLUTION_SHAPE_MISMATCH_VIOLATION_CODE, VerifyLockfileResolutionsOptions,
- pacquet/crates/lockfile-verification/src/record_lockfile_verified.rs: +5 -2; first added line: use crate::{
- pacquet/crates/lockfile/src/resolution.rs: +12 -7; first added line: /// resolutions written by older pnpm versions, and to gate trust on the
- pacquet/crates/package-manager/src/install_package_by_snapshot.rs: +1 -1; first added line: |dep_path: &str| allow_build_policy.check(dep_path).unwrap_or(false);
- pacquet/crates/package-manager/src/virtual_store_layout.rs: +1 -6; first added line: .filter(|key| policy.check(&key.without_peer().to_string()) == Some(true))
- pacquet/crates/package-manager/src/virtual_store_layout/tests.rs: +36 -1; first added line: use std::{
- pnpm-lock.yaml: +10 -0; first added line: shell-quote: 1.8.4
- pnpm-workspace.yaml: +2 -0; first added line: # GHSA-w7jw-789q-3m8p / CVE-2026-9277: 1.8.4 patches critical shell-quote vulnerabilities in <=1.8.3.
- resolving/git-resolver/src/createGitHostedPkgId.ts: +12 -1; first added line: const normalizedRepo = normalizeGitRepoForPkgResolutionId(repo)

Pre-Patch Source Files (Vulnerable state of files modified by patch)
### .changeset/tough-allow-builds-identities.md
[new file in patch, binary, or unreadable in pre-patch tree]

### building/after-install/src/index.ts
```
import assert from 'node:assert'
import path from 'node:path'
import util from 'node:util'

import { linkBins } from '@pnpm/bins.linker'
import { pkgRequiresBuild } from '@pnpm/building.pkg-requires-build'
import { createAllowBuildFunction } from '@pnpm/building.policy'
import {
  LAYOUT_VERSION,
  WANTED_LOCKFILE,
} from '@pnpm/constants'
import { skippedOptionalDependencyLogger } from '@pnpm/core-loggers'
import { calcDepState, type DepsStateCache, findRuntimeNodeVersion, iterateHashedGraphNodes, iteratePkgMeta, lockfileToDepGraph } from '@pnpm/deps.graph-hasher'
import { graphSequencer } from '@pnpm/deps.graph-sequencer'
import * as dp from '@pnpm/deps.path'
import { PnpmError } from '@pnpm/error'
import {
  runLifecycleHooksConcurrently,
  runPostinstallHooks,
} from '@pnpm/exec.lifecycle'
import { getContext, type PnpmContext } from '@pnpm/installing.context'
import { writeModulesManifest } from '@pnpm/installing.modules-yaml'
import type { TarballResolution } from '@pnpm/lockfile.types'
import {
  type LockfileObject,
  nameVerFromPkgSnapshot,
  packageIsIndependent,
  type PackageSnapshots,
} from '@pnpm/lockfile.utils'
import { lockfileWalker, type LockfileWalkerStep } from '@pnpm/lockfile.walker'
import { logger, streamParser } from '@pnpm/logger'
import npa from '@pnpm/npm-package-arg'
import { safeReadPackageJsonFromDir } from '@pnpm/pkg-manifest.reader'
import type { PackageFilesIndex } from '@pnpm/store.cafs'
import { createStoreController } from '@pnpm/store.connection-manager'
import { pickStoreIndexKey, StoreIndex } from '@pnpm/store.index'
import type {
  DepPath,
  IgnoredBuilds,
  ProjectId,
  ProjectManifest,
  ProjectRootDir,
} from '@pnpm/types'
import { hardLinkDir } from '@pnpm/worker'
import pLimit from 'p-limit'
import { runGroups } from 'run-groups'
import semver from 'semver'

import {
  type BuildOptions,
  extendBuildOptions,
  type StrictBuildOptions,
} from './extendBuildOptions.js'

export type { BuildOptions }

// Serializes builds of a shared GVS projection across concurrent per-project
// rebuilds: the first build proceeds, concurrent ones await it and reuse the
// result. Keyed by the absolute projection directory.
const gvsBuildLocks = new Map<string, Promise<void>>()

function findPackages (
  packages: PackageSnapshots,
  searched: PackageSelector[],
  opts: {
    prefix: string
  }
): DepPath[] {
  return (Object.keys(packages) as DepPath[])
    .filter((relativeDepPath) => {
      const pkgLockfile = packages[relativeDepPath]
      const pkgInfo = nameVerFromPkgSnapshot(relativeDepPath, pkgLockfile)
      if (!pkgInfo.name) {
        logger.warn({
          message: `Skipping ${relativeDepPath} because cannot get the package name from ${WANTED_LOCKFILE}.
            Try to run \`pnpm update --depth 100\` to create a new ${WANTED_LOCKFILE} with all the necessary info.`,
          prefix: opts.prefix,
        })
        return false
      }
      return matches(searched, pkgInfo)
    })
}

// TODO: move this logic to separate package as this is also used in tree-builder
function matches (
  searched: PackageSelector[],
  manifest: { name: string, version?: string }
): boolean {
  return searched.some((searchedPkg) => {
    if (typeof searchedPkg === 'string') {
      return manifest.name === searchedPkg
    }
    return searchedPkg.name === manifest.name && !!manifest.version &&
      semver.satisfies(manifest.version, searchedPkg.range)
  })
}

type PackageSelector = string | {
  name: string
  range: string
}

export async function buildSelectedPkgs (
  projects: Array<{ buildIndex: number, manifest: ProjectManifest, rootDir: ProjectRootDir }>,
  pkgSpecs: string[],
  maybeOpts: BuildOptions
): Promise<{ ignoredBuilds?: IgnoredBuilds }> {
  const reporter = maybeOpts?.reporter
  if ((reporter != null) && typeof reporter === 'function') {
    streamParser.on('data', reporter)
  }
  const opts = await extendBuildOptions(maybeOpts)
  const ctx = await getContext({ ...opts, allProjects: projects })

  if (ctx.currentLockfile?.packages == null) return {}
  const packages = ctx.currentLockfile.packages

  const searched: PackageSelector[] = pkgSpecs.map((arg) => {
    const { fetchSpec, name, raw, type } = npa(arg)
    if (raw === name) {
      return name
    }
    if (type !== 'version' && type !== 'range') {
      throw new Error(`Invalid argument - ${arg}. Rebuild can only select by version or range`)
    }
    return {
      name,
      range: fetchSpec,
    }
  })

  let pkgs = [] as string[]
  for (const { rootDir } of projects) {
    pkgs = [
      ...pkgs,
      ...findPackages(packages, searched, { prefix: rootDir }),
    ]
  }

  const { ignoredPkgs } = await _rebuild(
    {
      pkgsToRebuild: new Set(pkgs),
      ...ctx,
    },
    opts
  )
  await writeModulesManifest(ctx.rootModulesDir, {
    prunedAt: new Date().toUTCString(),
    ...ctx.modulesFile,
    hoistedDependencies: ctx.hoistedDependencies,
    hoistPattern: ctx.hoistPattern,
    included: ctx.include,
    ignoredBuilds: mergeIgnoredBuilds(ctx.modulesFile?.ignoredBuilds, ignoredPkgs, pkgs as DepPath[]),
    layoutVersion: LAYOUT_VERSION,
    packageManager: `${opts.packageManager.name}@${opts.packageManager.version}`,
    pendingBuilds: ctx.pendingBuilds,
    publicHoistPattern: ctx.publicHoistPattern,
    registries: ctx.registries,
    skipped: Array.from(ctx.skipped),
    storeDir: ctx.modulesFile?.storeDir ?? ctx.storeDir,
    virtualStoreDir: ctx.modulesFile?.virtualStoreDir ?? ctx.virtualStoreDir,
    virtualStoreDirMaxLength: ctx.modulesFile?.virtualStoreDirMaxLength ?? ctx.virtualStoreDirMaxLength,
    allowBuilds: opts.allowBuilds,
  })
  return {
    ignoredBuilds: ignoredPkgs,
  }
}

export async function buildProjects (
  projects: Array<{ buildIndex: number, manifest: ProjectManifest, rootDir: ProjectRootDir }>,
  maybeOpts: BuildOptions
): Promise<void> {
  const reporter = maybeOpts?.reporter
  if ((reporter != null) && typeof reporter === 'function') {
    streamParser.on('data', reporter)
  }
  const opts = await extendBuildOptions(maybeOpts)
  const ctx = await getContext({ ...opts, allProjects: projects })

  let idsToRebuild: string[] = []

  if (opts.pending) {
    idsToRebuild = ctx.pendingBuilds
  } else if ((ctx.currentLockfile?.packages) != null) {
    idsToRebuild = Object.keys(ctx.currentLockfile.packages)
  }

  const { pkgsThatWereRebuilt, ignoredPkgs } = await _rebuild(
    {
      pkgsToRebuild: new Set(idsToRebuild),
      ...ctx,
    },
    opts
  )

  ctx.pendingBuilds = ctx.pendingBuilds.filter((depPath) => !pkgsThatWereRebuilt.has(depPath))

  const store = await createStoreController(opts)
  const scriptsOpts = {
    extraBinPaths: ctx.extraBinPaths,
    extraNodePaths: ctx.extraNodePaths,
    extraEnv: opts.extraEnv,
    preferSymlinkedExecutables: opts.preferSymlinkedExecutables,
    scriptsPrependNodePath: opts.scriptsPrependNodePath,
    scriptShell: opts.scriptShell,
    shellEmulator: opts.shellEmulator,
    storeController: store.ctrl,
    unsafePerm: opts.unsafePerm || false,
    userAgent: opts.userAgent,
  }
  await runLifecycleHooksConcurrently(
    ['preinstall', 'install', 'postinstall', 'prepublish', 'prepare'],
    Object.values(ctx.projects),
    opts.childConcurrency || 5,
    scriptsOpts
  )
  for (const { id, manifest } of Object.values(ctx.projects)) {
    if (((manifest?.scripts) != null) && (!opts.pending || ctx.pendingBuilds.includes(id))) {
      ctx.pendingBuilds.splice(ctx.pendingBuilds.indexOf(id), 1)
    }
  }

  await writeModulesManifest(ctx.rootModulesDir, {
    prunedAt: new Date().toUTCString(),
    ...ctx.modulesFile,
    hoistedDependencies: ctx.hoistedDependencies,
    hoistPattern: ctx.hoistPattern,
    included: ctx.include,
    ignoredBuilds: ignoredPkgs,
    layoutVersion: LAYOUT_VERSION,
    packageManager: `${opts.packageManager.name}@${opts.packageManager.version}`,
    pendingBuilds: ctx.pendingBuilds,
    publicHoistPattern: ctx.publicHoistPattern,
    registries: ctx.registries,
    skipped: Array.from(ctx.skipped),
    storeDir: ctx.storeDir,
    virtualStoreDir: ctx.virtualStoreDir,
    virtualStoreDirMaxLength: ctx.virtualStoreDirMaxLength,
  })
}

function getSubgraphToBuild (
  step: LockfileWalkerStep,
  nodesToBuildAndTransitive: Set<DepPath>,
  opts: {
    pkgsToRebuild: Set<string>
  }
): boolean {
  let currentShouldBeBuilt = false
  for (const { depPath, next } of step.dependencies) {
    if (nodesToBuildAndTransitive.has(depPath)) {
      currentShouldBeBuilt = true
    }

    const childShouldBeBuilt = getSubgraphToBuild(next(), nodesToBuildAndTransitive, opts) ||
      opts.pkgsToRebuild.has(depPath)
    if (childShouldBeBuilt) {
      nodesToBuildAndTransitive.add(depPath)
      currentShouldBeBuilt = true
    }
  }
  for (const depPath of step.missing) {
    // It might make sense to fail if the depPath is not in the skipped list from .modules.yaml
    // However, the skipped list currently contains package IDs, not dep paths.
    logger.debug({ message: `No entry for "${depPath}" in ${WANTED_LOCKFILE}` })
  }
  return currentShouldBeBuilt
}

const limitLinking = pLimit(16)

async function _rebuild (
  ctx: {
    pkgsToRebuild: Set<string>
    skipped: Set<string>
    virtualStoreDir: string
    rootModulesDir: string
    currentLockfile: LockfileObject
    projects: Record<string, { id: ProjectId, rootDir: ProjectRootDir }>
    extraBinPaths: string[]
    extraNodePaths: string[]
  } & Pick<PnpmContext, 'modulesFile'>,
  opts: StrictBuildOptions
): Promise<{ pkgsThatWereRebuilt: Set<string>, ignoredPkgs: IgnoredBuilds }> {
  const depGraph = lockfileToDepGraph(ctx.currentLockfile, opts.supportedArchitectures)
  const depsStateCache: DepsStateCache = {}
  // Resolved `engines.runtime` Node version (when one is pinned) —
  // every side-effects-cache key computed below is anchored to it so
  // the prefix tracks the script-runner Node rather than pnpm's own
  // `process.version`.
  const nodeVersion = findRuntimeNodeVersion(Object.keys(depGraph))
  const pkgsThatWereRebuilt = new Set<string>()
  const graph = new Map()
  const pkgSnapshots: PackageSnapshots = ctx.currentLockfile.packages ?? {}

  const nodesToBuildAndTransitive = new Set<DepPath>()
  getSubgraphToBuild(
    lockfileWalker(
      ctx.currentLockfile,
      Object.values(ctx.projects).map(({ id }) => id),
      {
        include: {
          dependencies: opts.production,
          devDependencies: opts.development,
          optionalDependencies: opts.optional,
        },
      }
    ).step,
    nodesToBuildAndTransitive,
    { pkgsToRebuild: ctx.pkgsToRebuild }
  )
  const nodesToBuildAndTransitiveArray = Array.from(nodesToBuildAndTransitive)

  for (const depPath of nodesToBuildAndTransitiveArray) {
    const pkgSnapshot = pkgSnapshots[depPath]
    graph.set(depPath, Object.entries({ ...pkgSnapshot.dependencies, ...pkgSnapshot.optionalDependencies })
      .map(([pkgName, reference]) => dp.refToRelative(reference, pkgName))
      .filter((childRelDepPath) => childRelDepPath && nodesToBuildAndTransitive.has(childRelDepPath)))
  }
  const graphSequencerResult = graphSequencer(
    graph,
    nodesToBuildAndTransitiveArray
  )
  const chunks = graphSequencerResult.chunks as DepPath[][]
  const warn = (message: string) => {
    logger.info({ message, prefix: opts.dir })
  }

  const ignoredPkgs = new Set<DepPath>()
  const _allowBuild = createAllowBuildFunction(opts) ?? (() => undefined)
  const allowBuild = (pkgName: string, version: string, depPath: DepPath) => {
    switch (_allowBuild(pkgName, version)) {
      case true: return true
      case undefined: {
        ignoredPkgs.add(depPath)
        break
      }
    }
    return false
  }
  const builtDepPaths = new Set<string>()
  const storeIndex = opts.skipIfHasSideEffectsCache ? new StoreIndex(opts.storeDir) : undefined

  // Under GVS, packages live at `<globalVirtualStoreDir>/<hash>/node_modules/<name>`,
  // not the classic virtualStoreDir layout. The hash is computed with the same inputs
  // as the installer so rebuild resolves the exact directory the install created.
  const gvsDirByDepPath = new Map<DepPath, string>()
  if (opts.enableGlobalVirtualStore) {
    const globalVirtualStoreDir = opts.globalVirtualStoreDir ?? path.join(opts.storeDir, 'links')
    for (const { hash, pkgMeta } of iterateHashedGraphNodes(
      depGraph,
      iteratePkgMeta(ctx.currentLockfile, depGraph),
      _allowBuild,
      opts.supportedArchitectures,
      nodeVersion
    )) {
      gvsDirByDepPath.set(pkgMeta.depPath, path.join(globalVirtualStoreDir, hash))
    }
  }
  const pkgModulesDir = (depPath: DepPath): string =>
    gvsDirByDepPath.has(depPath)
      ? path.join(gvsDirByDepPath.get(depPath)!, 'node_modules')
      : path.join(ctx.virtualStoreDir, dp.depPathToFilename(depPath, opts.virtualStoreDirMaxLength), 'node_modules')

  const groups = chunks.map((chunk) => chunk.filter((depPath) => ctx.pkgsToRebuild.has(depPath) && !ctx.skipped.has(depPath)).map((depPath) =>
    async () => {
      const pkgSnapshot = pkgSnapshots[depPath]
      const pkgInfo = nameVerFromPkgSnapshot(depPath, pkgSnapshot)
      const pkgRoots = opts.nodeLinker === 'hoisted'
        ? (ctx.modulesFile?.hoistedLocations?.[depPath] ?? []).map((hoistedLocation) => path.join(opts.lockfileDir, hoistedLocation))
        : [path.join(pkgModulesDir(depPath), pkgInfo.name)]
      if (pkgRoots.length === 0) {
        if (pkgSnapshot.optional) return
        throw new PnpmError('MISSING_HOISTED_LOCATIONS', `${depPath} is not found in hoistedLocations inside node_modules/.modules.yaml`, {
          hint: 'If you installed your node_modules with pnpm older than v7.19.0, you may need to remove it and run "pnpm install"',
        })
      }
      const pkgRoot = pkgRoots[0]
      // If another project is already building this shared projection, wait for it
      // and reuse the result instead of racing on the same directory.
      const gvsDir = gvsDirByDepPath.get(depPath)
      if (gvsDir != null) {
        const inFlight = gvsBuildLocks.get(gvsDir)
        if (inFlight != null) {
          await inFlight.catch(() => {})
          pkgsThatWereRebuilt.add(depPath)
          return
        }
      }
      let releaseGvsLock: (() => void) | undefined
      if (gvsDir != null) {
        let resolveLock!: () => void
        gvsBuildLocks.set(gvsDir, new Promise<void>((resolve) => {
          resolveLock = resolve
        }))
        releaseGvsLock = () => {
          gvsBuildLocks.delete(gvsDir)
          resolveLock()
        }
      }
      try {
        const extraBinPaths = ctx.extraBinPaths
        if (opts.nodeLinker !== 'hoisted') {
          const modules = pkgModulesDir(depPath)
          const binPath = path.join(pkgRoot, 'node_modules', '.bin')
          await linkBins(modules, binPath, { extraNodePaths: ctx.extraNodePaths, warn })
        } else {
          extraBinPaths.push(...binDirsInAllParentDirs(pkgRoot, opts.lockfileDir))
        }
        const resolution = (pkgSnapshot.resolution as TarballResolution)
        let sideEffectsCacheKey: string | undefined
        // Match the resolver-supplied pkg.id used by the writer in
        // @pnpm/installing.package-requester: that's the tarball URL for
        // git-hosted packages (nonSemverVersion) and `name@version` otherwise.
        const pkgId = pkgInfo.nonSemverVersion ?? `${pkgInfo.name}@${pkgInfo.version}`
        if (opts.skipIfHasSideEffectsCache && (resolution.gitHosted || resolution.integrity)) {
          const filesIndexFile = pickStoreIndexKey(resolution, pkgId, { built: true })
          const pkgFilesIndex = storeIndex!.get(filesIndexFile) as PackageFilesIndex | undefined
          if (pkgFilesIndex) {
            sideEffectsCacheKey = calcDepState(depGraph, depsStateCache, depPath, {
              includeDepGraphHash: true,
              supportedArchitectures: opts.supportedArchitectures,
              nodeVersion,
            })
            if (pkgFilesIndex.sideEffects?.has(sideEffectsCacheKey)) {
              pkgsThatWereRebuilt.add(depPath)
              return
            }
          }
        }
        let requiresBuild = true
        const pgkManifest = await safeReadPackageJsonFromDir(pkgRoot)
        if (pgkManifest != null) {
          // This won't return the correct result for packages with binding.gyp as we don't pass the filesIndex to the function.
          // However, currently rebuild doesn't work for such packages at all, which should be fixed.
          requiresBuild = pkgRequiresBuild(pgkManifest, new Map())
        }

        const hasSideEffects = requiresBuild && allowBuild(pkgInfo.name, pkgInfo.version, depPath) && await runPostinstallHooks({
          depPath,
          extraBinPaths,
          extraEnv: opts.extraEnv,
          optional: pkgSnapshot.optional === true,
          pkgRoot,
          rootModulesDir: ctx.rootModulesDir,
          scriptsPrependNodePath: opts.scriptsPrependNodePath,
          shellEmulator: opts.shellEmulator,
          unsafePerm: opts.unsafePerm || false,
          userAgent: opts.userAgent,
        })
        if (hasSideEffects && (opts.sideEffectsCacheWrite ?? true) && (resolution.gitHosted || resolution.integrity)) {
          builtDepPaths.add(depPath)
          const filesIndexFile = pickStoreIndexKey(resolution, pkgId, { built: true })
          try {
            if (!sideEffectsCacheKey) {
              sideEffectsCacheKey = calcDepState(depGraph, depsStateCache, depPath, {
                includeDepGraphHash: true,
                nodeVersion,
              })
            }
            await opts.storeController.upload(pkgRoot, {
              sideEffectsCacheKey,
              filesIndexFile,
            })
          } catch (err: unknown) {
            assert(util.types.isNativeError(err))
            logger.warn({
              error: err,
              message: `An error occurred while uploading ${pkgRoot}`,
              prefix: opts.lockfileDir,
            })
          }
        }
        pkgsThatWereRebuilt.add(depPath)
      } catch (err: unknown) {
        assert(util.types.isNativeError(err))
        if (pkgSnapshot.optional) {
          // TODO: add parents field to the log
          skippedOptionalDependencyLogger.debug({
            details: err.toString(),
            package: {
              id: pkgSnapshot.id ?? depPath,
              name: pkgInfo.name,
              version: pkgInfo.version,
            },
            prefix: opts.dir,
            reason: 'build_failure',
          })
          return
        }
        throw err
      } finally {
        releaseGvsLock?.()
      }
      if (pkgRoots.length > 1) {
        await hardLinkDir(pkgRoot, pkgRoots.slice(1))
      }
    }
  ))

  await runGroups(opts.childConcurrency || 5, groups)
  storeIndex?.close()

  if (builtDepPaths.size > 0) {
    // It may be optimized because some bins were already linked before running lifecycle scripts
    await Promise.all(
      (Object
        .keys(pkgSnapshots) as DepPath[])
        .filter((depPath) => !packageIsIndependent(pkgSnapshots[depPath]))
        .map(async (depPath) => limitLinking(async () => {
          const pkgSnapshot = pkgSnapshots[depPath]
          const pkgInfo = nameVerFromPkgSnapshot(depPath, pkgSnapshot)
          const modules = pkgModulesDir(depPath)
          const binPath = path.join(modules, pkgInfo.name, 'node_modules', '.bin')
          return linkBins(modules, binPath, { warn })
        }))
    )
    await Promise.all(Object.values(ctx.projects).map(async ({ rootDir }) => limitLinking(async () => {
      const modules = path.join(rootDir, 'node_modules')
      const binPath = path.join(modules, '.bin')
      return linkBins(modules, binPath, {
        allowExoticManifests: true,
        warn,
      })
    })))
  }

  return { pkgsThatWereRebuilt, ignoredPkgs }
}

function binDirsInAllParentDirs (pkgRoot: string, lockfileDir: string): string[] {
  const binDirs: string[] = []
  let dir = pkgRoot
  do {
    if (!(path.dirname(dir)[0] === '@')) {
      binDirs.push(path.join(dir, 'node_modules/.bin'))
    }
    dir = path.dirname(dir)
  } while (path.relative(dir, lockfileDir) !== '')
  binDirs.push(path.join(lockfileDir, 'node_modules/.bin'))
  return binDirs
}

/**
 * Merge new ignoredBuilds from a selective rebuild with existing ones.
 * Keeps existing entries for packages that weren't part of this rebuild.
 */
function mergeIgnoredBuilds (
  existing: IgnoredBuilds | undefined,
  newIgnored: IgnoredBuilds,
  rebuiltPkgs: DepPath[]
): IgnoredBuilds | undefined {
  if (!existing?.size && !newIgnored.size) return undefined
  const rebuiltSet = new Set<DepPath>(rebuiltPkgs)
  const merged = new Set<DepPath>()
  if (existing) {
    for (const depPath of existing) {
      if (!rebuiltSet.has(depPath)) {
        merged.add(depPath)
      }
    }
  }
  for (const depPath of newIgnored) {
    merged.add(depPath)
  }
  return merged.size ? merged : undefined
}

```

### building/commands/package.json
```
{
  "name": "@pnpm/building.commands",
  "version": "1100.1.2",
  "description": "Commands for rebuilding and managing dependency builds",
  "keywords": [
    "pnpm",
    "pnpm11",
    "rebuild"
  ],
  "license": "MIT",
  "funding": "https://opencollective.com/pnpm",
  "repository": "https://github.com/pnpm/pnpm/tree/main/building/commands",
  "homepage": "https://github.com/pnpm/pnpm/tree/main/building/commands#readme",
  "bugs": {
    "url": "https://github.com/pnpm/pnpm/issues"
  },
  "type": "module",
  "main": "lib/index.js",
  "types": "lib/index.d.ts",
  "exports": {
    ".": "./lib/index.js"
  },
  "files": [
    "lib",
    "!*.map"
  ],
  "scripts": {
    "lint": "eslint \"src/**/*.ts\" \"test/**/*.ts\"",
    "test": "pn compile && pn --filter=pnpm compile && pn .test",
    "prepublishOnly": "tsgo --build",
    "compile": "tsgo --build && pn lint --fix",
    ".test": "cross-env NODE_OPTIONS=\"$NODE_OPTIONS --experimental-vm-modules --disable-warning=ExperimentalWarning --disable-warning=DEP0169\" jest"
  },
  "dependencies": {
    "@inquirer/prompts": "catalog:",
    "@pnpm/building.after-install": "workspace:*",
    "@pnpm/cli.command": "workspace:*",
    "@pnpm/cli.common-cli-options-help": "workspace:*",
    "@pnpm/cli.utils": "workspace:*",
    "@pnpm/config.reader": "workspace:*",
    "@pnpm/config.writer": "workspace:*",
    "@pnpm/deps.path": "workspace:*",
    "@pnpm/error": "workspace:*",
    "@pnpm/installing.commands": "workspace:*",
    "@pnpm/installing.modules-yaml": "workspace:*",
    "@pnpm/prepare-temp-dir": "workspace:*",
    "@pnpm/store.connection-manager": "workspace:*",
    "@pnpm/types": "workspace:*",
    "@pnpm/util.lex-comparator": "catalog:",
    "@pnpm/workspace.projects-sorter": "workspace:*",
    "chalk": "catalog:",
    "p-limit": "catalog:",
    "ramda": "catalog:",
    "render-help": "catalog:"
  },
  "peerDependencies": {
    "@pnpm/logger": "catalog:"
  },
  "devDependencies": {
    "@jest/globals": "catalog:",
    "@pnpm/assert-project": "workspace:*",
    "@pnpm/building.commands": "workspace:*",
    "@pnpm/constants": "workspace:*",
    "@pnpm/crypto.object-hasher": "workspace:*",
    "@pnpm/logger": "workspace:*",
    "@pnpm/prepare": "workspace:*",
    "@pnpm/store.cafs": "workspace:*",
    "@pnpm/store.index": "workspace:*",
    "@pnpm/test-fixtures": "workspace:*",
    "@pnpm/test-ipc-server": "workspace:*",
    "@pnpm/testing.command-defaults": "workspace:*",
    "@pnpm/testing.registry-mock": "workspace:*",
    "@pnpm/workspace.projects-filter": "workspace:*",
    "@types/ramda": "catalog:",
    "execa": "catalog:",
    "load-json-file": "catalog:",
    "read-yaml-file": "catalog:",
    "write-package": "catalog:",
    "write-yaml-file": "catalog:"
  },
  "engines": {
    "node": ">=22.13"
  },
  "jest": {
    "preset": "@pnpm/jest-config/with-registry"
  }
}

```

### building/commands/src/policy/approveBuilds.ts
```
import { checkbox, confirm } from '@inquirer/prompts'
import type { CommandHandlerMap } from '@pnpm/cli.command'
import type { Config, ConfigContext } from '@pnpm/config.reader'
import { writeSettings } from '@pnpm/config.writer'
import { parse } from '@pnpm/deps.path'
import { PnpmError } from '@pnpm/error'
import { install } from '@pnpm/installing.commands'
import { type StrictModules, writeModulesManifest } from '@pnpm/installing.modules-yaml'
import { globalInfo } from '@pnpm/logger'
import { lexCompare } from '@pnpm/util.lex-comparator'
import chalk from 'chalk'
import { renderHelp } from 'render-help'

import { rebuild, type RebuildCommandOpts } from '../build/index.js'
import { getAutomaticallyIgnoredBuilds } from './getAutomaticallyIgnoredBuilds.js'

export type ApproveBuildsCommandOpts = Pick<Config, 'modulesDir' | 'dir' | 'allowBuilds' | 'enableGlobalVirtualStore'> & Pick<ConfigContext, 'rootProjectManifest' | 'rootProjectManifestDir'> & {
  all?: boolean
  global?: boolean
  /**
   * When set, overrides the target directory for writeSettings.
   * Used by the global-install flow to point allowBuilds updates at the
   * global pnpm-workspace.yaml while keeping workspaceDir unset so the
   * install itself targets only the single install directory.
   */
  settingsDir?: string
}

export const commandNames = ['approve-builds']

export const recursiveByDefault = true

export function help (): string {
  return renderHelp({
    description: 'Approve dependencies for running scripts during installation',
    usages: [
      'pnpm approve-builds',
      'pnpm approve-builds [<pkg> ...] [!<pkg> ...]',
    ],
    descriptionLists: [
      {
        title: 'Options',

        list: [
          {
            description: 'Approve all pending dependencies without interactive prompts',
            name: '--all',
          },
        ],
      },
    ],
  })
}

export function cliOptionsTypes (): Record<string, unknown> {
  return {
    all: Boolean,
    global: Boolean,
  }
}

export function rcOptionsTypes (): Record<string, unknown> {
  return {}
}

export async function handler (opts: ApproveBuildsCommandOpts & RebuildCommandOpts, params: string[] = [], commands?: CommandHandlerMap): Promise<void> {
  if (opts.global) {
    throw new PnpmError(
      'APPROVE_BUILDS_NOT_SUPPORTED_WITH_GLOBAL',
      '"approve-builds" is not supported with global packages',
      {
        hint: 'Use --allow-build when installing globally, e.g. "pnpm add -g --allow-build=<pkg> <pkg>". ' +
          'pnpm will also prompt to allow builds interactively during global install.',
      }
    )
  }
  if (opts.all && params.length) {
    throw new PnpmError(
      'APPROVE_BUILDS_ALL_WITH_ARGS',
      'Cannot use --all with positional arguments'
    )
  }
  const {
    automaticallyIgnoredBuilds,
    modulesDir,
    modulesManifest,
  } = await getAutomaticallyIgnoredBuilds(opts)
  if (!automaticallyIgnoredBuilds?.length) {
    globalInfo('There are no packages awaiting approval')
    return
  }
  const denied: string[] = []
  const approved: string[] = []
  const unknown: string[] = []
  for (const p of params) {
    const name = p.startsWith('!') ? p.slice(1) : p
    if (!automaticallyIgnoredBuilds.includes(name)) {
      unknown.push(name)
    } else if (p.startsWith('!')) {
      denied.push(name)
    } else {
      approved.push(name)
    }
  }
  if (unknown.length) {
    throw new PnpmError(
      'APPROVE_BUILDS_UNKNOWN_PACKAGES',
      `The following packages are not awaiting approval: ${unknown.join(', ')}`
    )
  }
  const contradictions = approved.filter((p) => denied.includes(p))
  if (contradictions.length) {
    throw new PnpmError(
      'APPROVE_BUILDS_CONTRADICTING_ARGS',
      `The following packages are both approved and denied: ${contradictions.join(', ')}`
    )
  }
  let buildPackages: string[] = []
  if (params.length) {
    buildPackages = sortUniqueStrings([...approved])
  } else if (opts.all) {
    buildPackages = sortUniqueStrings([...automaticallyIgnoredBuilds])
  } else {
    try {
      const buildPackagesValues = await checkbox({
        choices: sortUniqueStrings([...automaticallyIgnoredBuilds]).map((name) => ({
          name,
          value: name,
        })),
        message: 'Choose which packages to build ' +
          `(Press ${chalk.cyan('<space>')} to select, ` +
          `${chalk.cyan('<a>')} to toggle all, ` +
          `${chalk.cyan('<i>')} to invert selection)`,
        required: false,
        theme: {
          icon: { checked: '●', unchecked: '○', cursor: '❯' },
          style: {
            highlight: chalk.bgBlack.whiteBright,
          },
          keybindings: ['vim'],
        },
      })
      buildPackages = buildPackagesValues
    } catch (err) {
      if (err instanceof Error && err.name === 'ExitPromptError') {
        process.exit(0)
      }
      throw err
    }
  }
  const allowBuilds: Record<string, boolean | string> = { ...opts.allowBuilds }
  if (params.length) {
    for (const pkg of approved) {
      allowBuilds[pkg] = true
    }
    for (const pkg of denied) {
      allowBuilds[pkg] = false
    }
  } else {
    const ignoredPackages = automaticallyIgnoredBuilds.filter((automaticallyIgnoredBuild) => !buildPackages.includes(automaticallyIgnoredBuild))
    for (const pkg of ignoredPackages) {
      allowBuilds[pkg] = false
    }
    for (const pkg of buildPackages) {
      allowBuilds[pkg] = true
    }
  }
  if (!opts.all && !params.length) {
    if (buildPackages.length) {
      let isConfirmed: boolean
      try {
        isConfirmed = await confirm({
          message: `The next packages will now be built: ${buildPackages.join(', ')}.\nDo you approve?`,
          default: false,
        })
      } catch (err) {
        if (err instanceof Error && err.name === 'ExitPromptError') {
          process.exit(0)
        }
        throw err
      }
      if (!isConfirmed) {
        return
      }
    } else {
      globalInfo('All packages were added to allowBuilds with value false.')
    }
  }
  await writeSettings({
    ...opts,
    workspaceDir: opts.settingsDir ?? opts.workspaceDir ?? opts.rootProjectManifestDir,
    updatedSettings: { allowBuilds },
  })
  if (modulesManifest?.ignoredBuilds) {
    if (params.length) {
      const decided = new Set([...approved, ...denied])
      for (const depPath of Array.from(modulesManifest.ignoredBuilds)) {
        const name = parse(depPath).name ?? depPath
        if (decided.has(name)) {
          modulesManifest.ignoredBuilds.delete(depPath)
        }
      }
      if (!modulesManifest.ignoredBuilds.size) {
        delete modulesManifest.ignoredBuilds
      }
    } else {
      delete modulesManifest.ignoredBuilds
    }
    await writeModulesManifest(modulesDir, modulesManifest as StrictModules)
  }
  if (buildPackages.length) {
    if (opts.enableGlobalVirtualStore) {
      await install.handler({
        ...opts,
        allowBuilds,
        frozenLockfile: true,
        optimisticRepeatInstall: false,
      } as any, [], commands) // eslint-disable-line @typescript-eslint/no-explicit-any
      return
    }
    return rebuild.handler({
      ...opts,
      allowBuilds,
    }, buildPackages)
  }
}

function sortUniqueStrings (array: string[]): string[] {
  return Array.from(new Set(array)).sort(lexCompare)
}

```

### building/commands/src/policy/getAutomaticallyIgnoredBuilds.ts
```
import path from 'node:path'

import { parse } from '@pnpm/deps.path'
import { type Modules, readModulesManifest } from '@pnpm/installing.modules-yaml'

import type { IgnoredBuildsCommandOpts } from './ignoredBuilds.js'

export interface GetAutomaticallyIgnoredBuildsResult {
  automaticallyIgnoredBuilds: string[] | null
  modulesDir: string
  modulesManifest: Modules | null
}

export async function getAutomaticallyIgnoredBuilds (opts: IgnoredBuildsCommandOpts): Promise<GetAutomaticallyIgnoredBuildsResult> {
  const modulesDir = getModulesDir(opts)
  const modulesManifest = await readModulesManifest(modulesDir)
  let automaticallyIgnoredBuilds: null | string[]
  if (modulesManifest?.ignoredBuilds) {
    const ignoredPkgNames = new Set<string>()
    for (const depPath of modulesManifest.ignoredBuilds) {
      ignoredPkgNames.add(parse(depPath).name ?? depPath)
    }
    automaticallyIgnoredBuilds = Array.from(ignoredPkgNames)
  } else {
    automaticallyIgnoredBuilds = null
  }
  return {
    automaticallyIgnoredBuilds,
    modulesDir,
    modulesManifest,
  }
}

function getModulesDir (opts: IgnoredBuildsCommandOpts): string {
  return opts.modulesDir ?? path.join(opts.lockfileDir ?? opts.dir, 'node_modules')
}

```

### building/commands/tsconfig.json
```
{
  "extends": "@pnpm/tsconfig",
  "compilerOptions": {
    "outDir": "lib",
    "rootDir": "src"
  },
  "include": [
    "src/**/*.ts",
    "../../__typings__/**/*.d.ts"
  ],
  "references": [
    {
      "path": "../../__utils__/assert-project"
    },
    {
      "path": "../../__utils__/prepare"
    },
    {
      "path": "../../__utils__/prepare-temp-dir"
    },
    {
      "path": "../../__utils__/test-fixtures"
    },
    {
      "path": "../../__utils__/test-ipc-server"
    },
    {
      "path": "../../cli/command"
    },
    {
      "path": "../../cli/common-cli-options-help"
    },
    {
      "path": "../../cli/utils"
    },
    {
      "path": "../../config/reader"
    },
    {
      "path": "../../config/writer"
    },
    {
      "path": "../../core/constants"
    },
    {
      "path": "../../core/error"
    },
    {
      "path": "../../core/logger"
    },
    {
      "path": "../../core/types"
    },
    {
      "path": "../../crypto/object-hasher"
    },
    {
      "path": "../../deps/path"
    },
    {
      "path": "../../installing/commands"
    },
    {
      "path": "../../installing/modules-yaml"
    },
    {
      "path": "../../store/cafs"
    },
    {
      "path": "../../store/connection-manager"
    },
    {
      "path": "../../store/index"
    },
    {
      "path": "../../testing/command-defaults"
    },
    {
      "path": "../../testing/registry-mock"
    },
    {
      "path": "../../workspace/projects-filter"
    },
    {
      "path": "../../workspace/projects-sorter"
    },
    {
      "path": "../after-install"
    }
  ]
}

```

### building/during-install/src/index.ts
```
import assert from 'node:assert'
import fs from 'node:fs/promises'
import path from 'node:path'
import util from 'node:util'

import { linkBins, linkBinsOfPackages } from '@pnpm/bins.linker'
import { getWorkspaceConcurrency } from '@pnpm/config.reader'
import { skippedOptionalDependencyLogger } from '@pnpm/core-loggers'
import { calcDepState, type DepsStateCache, findRuntimeNodeVersion } from '@pnpm/deps.graph-hasher'
import { PnpmError } from '@pnpm/error'
import { runPostinstallHooks } from '@pnpm/exec.lifecycle'
import { logger } from '@pnpm/logger'
import { applyPatchToDir } from '@pnpm/patching.apply-patch'
import { safeReadPackageJsonFromDir } from '@pnpm/pkg-manifest.reader'
import type { StoreController } from '@pnpm/store.controller-types'
import type {
  AllowBuild,
  DependencyManifest,
  DepPath,
  IgnoredBuilds,
} from '@pnpm/types'
import { hardLinkDir } from '@pnpm/worker'
import pDefer, { type DeferredPromise } from 'p-defer'
import { pickBy } from 'ramda'
import { runGroups } from 'run-groups'

import { buildSequence, type DependenciesGraph, type DependenciesGraphNode } from './buildSequence.js'

export type { DepsStateCache }

export async function buildModules<T extends string> (
  depGraph: DependenciesGraph<T>,
  rootDepPaths: T[],
  opts: {
    allowBuild?: AllowBuild
    childConcurrency?: number
    depsToBuild?: Set<string>
    depsStateCache: DepsStateCache
    extraBinPaths?: string[]
    extraNodePaths?: string[]
    extraEnv?: Record<string, string>
    ignoreScripts?: boolean
    lockfileDir: string
    optional: boolean
    preferSymlinkedExecutables?: boolean
    unsafePerm: boolean
    userAgent: string
    scriptsPrependNodePath?: boolean | 'warn-only'
    scriptShell?: string
    shellEmulator?: boolean
    sideEffectsCacheWrite: boolean
    storeController: StoreController
    rootModulesDir: string
    hoistedLocations?: Record<string, string[]>
    enableGlobalVirtualStore?: boolean
  }
): Promise<{ ignoredBuilds?: IgnoredBuilds }> {
  if (!rootDepPaths.length) return {}
  const warn = (message: string) => {
    logger.warn({ message, prefix: opts.lockfileDir })
  }
  // postinstall hooks

  // Resolved `engines.runtime` Node version (when the project pins
  // one) so each per-snapshot side-effects-cache key reflects the
  // script-runner Node. Computed once over the install-wide graph
  // and threaded into [`buildDependency`] via [`buildDepOpts`].
  const nodeVersion = findRuntimeNodeVersion(Object.keys(depGraph))
  const buildDepOpts = {
    ...opts,
    builtHoistedDeps: opts.hoistedLocations ? {} : undefined,
    nodeVersion,
    warn,
  }
  const chunks = buildSequence<T>(depGraph, rootDepPaths)
  if (!chunks.length) return {}
  const ignoredBuilds = new Set<DepPath>()
  const allowBuild = opts.allowBuild ?? (() => undefined)
  const groups = chunks.map((chunk) => {
    chunk = chunk.filter((depPath) => {
      const node = depGraph[depPath]
      return (node.requiresBuild || node.patch != null) && !node.isBuilt
    })
    if (opts.depsToBuild != null) {
      chunk = chunk.filter((depPath) => opts.depsToBuild!.has(depPath))
    }

    return chunk.map((depPath) =>
      () => {
        let ignoreScripts = Boolean(buildDepOpts.ignoreScripts)
        if (!ignoreScripts) {
          const node = depGraph[depPath]
          if (node.requiresBuild) {
            const allowed = allowBuild(node.name, node.version)
            switch (allowed) {
              case false:
              // Explicitly disallowed - don't report as ignored
                ignoreScripts = true
                break
              case undefined:
              // Not in allowlist - report as ignored
                ignoredBuilds.add(node.depPath)
                ignoreScripts = true
                break
            }
            // allowed === true means build is permitted
          }
        }
        return buildDependency(depPath, depGraph, {
          ...buildDepOpts,
          ignoreScripts,
        })
      }
    )
  })
  const patchErrors: Error[] = []
  const groupsWithPatchErrors = groups.map((group) =>
    group.map((task) => async () => {
      try {
        await task()
      } catch (err: unknown) {
        if (util.types.isNativeError(err) && 'code' in err && err.code === 'ERR_PNPM_PATCH_FAILED') {
          patchErrors.push(err)
        } else {
          throw err
        }
      }
    })
  )
  await runGroups(getWorkspaceConcurrency(opts.childConcurrency), groupsWithPatchErrors)
  if (patchErrors.length > 0) {
    throw patchErrors[0]
  }
  return { ignoredBuilds }
}

async function buildDependency<T extends string> (
  depPath: T,
  depGraph: DependenciesGraph<T>,
  opts: {
    extraBinPaths?: string[]
    extraNodePaths?: string[]
    extraEnv?: Record<string, string>
    depsStateCache: DepsStateCache
    ignoreScripts?: boolean
    lockfileDir: string
    optional: boolean
    preferSymlinkedExecutables?: boolean
    rootModulesDir: string
    scriptsPrependNodePath?: boolean | 'warn-only'
    scriptShell?: string
    shellEmulator?: boolean
    sideEffectsCacheWrite: boolean
    storeController: StoreController
    unsafePerm: boolean
    userAgent?: string
    hoistedLocations?: Record<string, string[]>
    builtHoistedDeps?: Record<string, DeferredPromise<void>>
    enableGlobalVirtualStore?: boolean
    /** Resolved `engines.runtime` Node version — see [`buildModules`]. */
    nodeVersion?: string
    warn: (message: string) => void
  }
): Promise<void> {
  const depNode = depGraph[depPath]
  if (!depNode.filesIndexFile) return
  if (opts.builtHoistedDeps) {
    if (opts.builtHoistedDeps[depNode.depPath]) {
      await opts.builtHoistedDeps[depNode.depPath].promise
      return
    }
    opts.builtHoistedDeps[depNode.depPath] = pDefer()
  }
  let buildSucceeded = false
  try {
    await linkBinsOfDependencies(depNode, depGraph, opts)
    let isPatched = false
    if (depNode.patch) {
      if (!depNode.patch.patchFilePath) {
        throw new PnpmError('PATCH_FILE_PATH_MISSING',
          `Cannot apply patch for ${depPath}: patch file path is missing`,
          { hint: 'Ensure the package is listed in patchedDependencies configuration' }
        )
      }
      isPatched = applyPatchToDir({ patchedDir: depNode.dir, patchFilePath: depNode.patch.patchFilePath })
    }
    const hasSideEffects = !opts.ignoreScripts && await runPostinstallHooks({
      depPath,
      extraBinPaths: opts.extraBinPaths,
      extraEnv: opts.extraEnv,
      initCwd: opts.lockfileDir,
      optional: depNode.optional,
      pkgRoot: depNode.dir,
      rootModulesDir: opts.rootModulesDir,
      scriptsPrependNodePath: opts.scriptsPrependNodePath,
      scriptShell: opts.scriptShell,
      shellEmulator: opts.shellEmulator,
      unsafePerm: opts.unsafePerm || false,
      userAgent: opts.userAgent,
    })
    // Remove the .pnpm-needs-build marker before uploading side effects,
    // so it doesn't get cached as part of the package's side effects diff.
    if (opts.enableGlobalVirtualStore) {
      await fs.unlink(path.join(depNode.dir, '.pnpm-needs-build')).catch(() => {})
    }
    if ((isPatched || hasSideEffects) && opts.sideEffectsCacheWrite) {
      try {
        const sideEffectsCacheKey = calcDepState(depGraph, opts.depsStateCache, depPath, {
          patchFileHash: depNode.patch?.hash,
          includeDepGraphHash: hasSideEffects,
          nodeVersion: opts.nodeVersion,
        })
        await opts.storeController.upload(depNode.dir, {
          sideEffectsCacheKey,
          filesIndexFile: depNode.filesIndexFile,
        })
      } catch (err: unknown) {
        assert(util.types.isNativeError(err))
        logger.warn({
          error: err,
          message: `An error occurred while uploading ${depNode.dir}`,
          prefix: opts.lockfileDir,
        })
      }
    }
    buildSucceeded = true
  } catch (err: unknown) {
    assert(util.types.isNativeError(err))
    // In GVS mode, remove the entire hash directory so the next install
    // sees the directory is absent, re-fetches, and re-builds.
    if (opts.enableGlobalVirtualStore) {
      const hashDir = path.resolve(depNode.dir, '../..')
      await fs.rm(hashDir, { recursive: true, force: true })
    }
    if (depNode.optional) {
      // TODO: add parents field to the log
      skippedOptionalDependencyLogger.debug({
        details: err.toString(),
        package: {
          id: depNode.dir,
          name: depNode.name,
          version: depNode.version,
        },
        prefix: opts.lockfileDir,
        reason: 'build_failure',
      })
      return
    }
    throw err
  } finally {
    if (buildSucceeded) {
      const hoistedLocationsOfDep = opts.hoistedLocations?.[depNode.depPath]
      if (hoistedLocationsOfDep) {
        // There is no need to build the same package in every location.
        // We just copy the built package to every location where it is present.
        const currentHoistedLocation = path.relative(opts.lockfileDir, depNode.dir)
        const nonBuiltHoistedDeps = hoistedLocationsOfDep?.filter((hoistedLocation) => hoistedLocation !== currentHoistedLocation)
        await hardLinkDir(depNode.dir, nonBuiltHoistedDeps)
      }
    }
    if (opts.builtHoistedDeps) {
      opts.builtHoistedDeps[depNode.depPath].resolve()
    }
  }
}

export async function linkBinsOfDependencies<T extends string> (
  depNode: DependenciesGraphNode<T>,
  depGraph: DependenciesGraph<T>,
  opts: {
    extraNodePaths?: string[]
    optional: boolean
    preferSymlinkedExecutables?: boolean
    warn: (message: string) => void
  }
): Promise<void> {
  const childrenToLink: Record<string, T> = opts.optional
    ? depNode.children
    : pickBy((child, childAlias) => !depNode.optionalDependencies.has(childAlias), depNode.children)

  const binPath = path.join(depNode.dir, 'node_modules/.bin')

  const pkgNodes = [
    ...Object.entries(childrenToLink)
      .map(([alias, childDepPath]) => ({ alias, dep: depGraph[childDepPath] }))
      .filter(({ alias, dep }) => {
        if (!dep) {
          // TODO: Try to reproduce this issue with a test in @pnpm/installing.deps-installer
          logger.debug({ message: `Failed to link bins of "${alias}" to "${binPath}". This is probably not an issue.` })
          return false
        }
        return dep.hasBin && dep.installable !== false
      })
      .map(({ dep }) => dep),
    depNode,
  ]
  const pkgs = await Promise.all(pkgNodes
    .map(async (dep) => ({
      location: dep.dir,
      manifest: ((await dep.fetching?.())?.bundledManifest ?? (await safeReadPackageJsonFromDir(dep.dir))) as DependencyManifest ?? {},
    }))
  )

  await linkBinsOfPackages(pkgs, binPath, {
    extraNodePaths: opts.extraNodePaths,
    preferSymlinkedExecutables: opts.preferSymlinkedExecutables,
  })

  // link also the bundled dependencies` bins
  if (depNode.hasBundledDependencies) {
    const bundledModules = path.join(depNode.dir, 'node_modules')
    await linkBins(bundledModules, binPath, {
      extraNodePaths: opts.extraNodePaths,
      preferSymlinkedExecutables: opts.preferSymlinkedExecutables,
      warn: opts.warn,
    })
  }
}

```

### building/policy/src/index.ts
```
import { expandPackageVersionSpecs } from '@pnpm/config.version-policy'
import * as dp from '@pnpm/deps.path'
import type { AllowBuild, DepPath } from '@pnpm/types'

export function isBuildExplicitlyDisallowed (depPath: DepPath, allowBuild?: AllowBuild): boolean {
  if (!allowBuild) return false
  const { name, version } = dp.parse(depPath)
  if (!name || !version) return false
  return allowBuild(name, version) === false
}

export function createAllowBuildFunction (
  opts: {
    dangerouslyAllowAllBuilds?: boolean
    allowBuilds?: Record<string, boolean | string>
  }
): undefined | AllowBuild {
  if (opts.dangerouslyAllowAllBuilds) return () => true
  if (opts.allowBuilds != null) {
    const allowedBuilds = new Set<string>()
    const disallowedBuilds = new Set<string>()
    for (const [pkg, value] of Object.entries(opts.allowBuilds)) {
      switch (value) {
        case true:
          allowedBuilds.add(pkg)
          break
        case false:
          disallowedBuilds.add(pkg)
          break
      }
    }
    const expandedAllowed = expandPackageVersionSpecs(Array.from(allowedBuilds))
    const expandedDisallowed = expandPackageVersionSpecs(Array.from(disallowedBuilds))
    return (pkgName, version) => {
      const pkgWithVersion = `${pkgName}@${version}`
      if (expandedDisallowed.has(pkgName) || expandedDisallowed.has(pkgWithVersion)) {
        return false
      }
      if (expandedAllowed.has(pkgName) || expandedAllowed.has(pkgWithVersion)) {
        return true
      }
      return undefined
    }
  }
  return undefined
}

```

### core/types/src/config.ts
```
export type PackageVersionPolicy = (pkgName: string) => boolean | string[]

export type AllowBuild = (pkgName: string, pkgVersion: string) => boolean | undefined

export type TrustPolicy = 'no-downgrade' | 'off'

```

### deps/graph-builder/src/lockfileToDepGraph.ts
```
import fs from 'node:fs'
import path from 'node:path'

import { packageIsInstallable } from '@pnpm/config.package-is-installable'
import { WANTED_LOCKFILE } from '@pnpm/constants'
import {
  progressLogger,
} from '@pnpm/core-loggers'
import * as dp from '@pnpm/deps.path'
import type { IncludedDependencies } from '@pnpm/installing.modules-yaml'
import type { LockfileObject, LockfileResolution } from '@pnpm/lockfile.fs'
import {
  packageIdFromSnapshot,
  pkgSnapshotToResolution,
} from '@pnpm/lockfile.utils'
import { logger } from '@pnpm/logger'
import { getPatchInfo, type PatchGroupRecord } from '@pnpm/patching.config'
import type { PatchInfo } from '@pnpm/patching.types'
import type {
  FetchResponse,
  PkgRequestFetchResult,
  StoreController,
} from '@pnpm/store.controller-types'
import type {
  AllowBuild,
  DepPath,
  PkgIdWithPatchHash,
  ProjectId,
  Registries,
  SupportedArchitectures,
} from '@pnpm/types'
import { pathExists } from 'path-exists'
import { equals, isEmpty } from 'ramda'

import { iteratePkgsForVirtualStore } from './iteratePkgsForVirtualStore.js'

const brokenModulesLogger = logger('_broken_node_modules')

export interface DependenciesGraphNode {
  alias?: string // this is populated in HoistedDepGraphOnly
  hasBundledDependencies: boolean
  modules: string
  name: string
  version: string
  fetching?: () => Promise<PkgRequestFetchResult>
  forceImportPackage?: boolean // Used to force re-imports from the store of local tarballs that have changed.
  dir: string
  children: Record<string, string>
  optionalDependencies: Set<string>
  optional: boolean
  depPath: DepPath // this option is only needed for saving pendingBuild when running with --ignore-scripts flag
  pkgIdWithPatchHash: PkgIdWithPatchHash
  isBuilt?: boolean
  requiresBuild?: boolean
  hasBin: boolean
  filesIndexFile?: string
  patch?: PatchInfo
  resolution: LockfileResolution
}

export interface DependenciesGraph {
  [depPath: string]: DependenciesGraphNode
}

export interface LockfileToDepGraphOptions {
  allowBuild?: AllowBuild
  autoInstallPeers: boolean
  enableGlobalVirtualStore?: boolean
  engineStrict: boolean
  force: boolean
  importerIds: ProjectId[]
  include: IncludedDependencies
  includeUnchangedDeps?: boolean
  ignoreScripts: boolean
  /**
   * When true, skip fetching local dependencies (file: protocol pointing to directories).
   * This is useful for `pnpm fetch` which only downloads packages from the registry
   * and doesn't need local packages that won't be available (e.g., in Docker builds).
   */
  ignoreLocalPackages?: boolean
  lockfileDir: string
  nodeVersion: string
  pnpmVersion: string
  patchedDependencies?: PatchGroupRecord
  registries: Registries
  sideEffectsCacheRead: boolean
  skipped: Set<DepPath>
  storeController: StoreController
  storeDir: string
  globalVirtualStoreDir: string
  virtualStoreDir: string
  supportedArchitectures?: SupportedArchitectures
  virtualStoreDirMaxLength: number
}

export interface DirectDependenciesByImporterId {
  [importerId: string]: { [alias: string]: string }
}

export interface DepHierarchy {
  [depPath: string]: Record<string, DepHierarchy>
}

export interface LockfileToDepGraphResult {
  directDependenciesByImporterId: DirectDependenciesByImporterId
  graph: DependenciesGraph
  hierarchy?: DepHierarchy
  hoistedLocations?: Record<string, string[]>
  symlinkedDirectDependenciesByImporterId?: DirectDependenciesByImporterId
  prevGraph?: DependenciesGraph
  injectionTargetsByDepPath: Map<string, string[]>
}

/**
 * Generate a dependency graph from lockfiles.
 *
 * If a current lockfile is provided, this function only includes new or changed
 * packages in the graph. In other words, the graph returned will be a set
 * subtraction of the packages in the wanted lockfile minus the current
 * lockfile. This behavior can be configured with the `includeUnchangedDeps`
 * option.
 */
export async function lockfileToDepGraph (
  lockfile: LockfileObject,
  currentLockfile: LockfileObject | null,
  opts: LockfileToDepGraphOptions
): Promise<LockfileToDepGraphResult> {
  const {
    graph,
    locationByDepPath,
    injectionTargetsByDepPath,
  } = await buildGraphFromPackages(lockfile, currentLockfile, opts)

  const _getChildrenPaths = getChildrenPaths.bind(null, {
    force: opts.force,
    graph,
    lockfileDir: opts.lockfileDir,
    registries: opts.registries,
    sideEffectsCacheRead: opts.sideEffectsCacheRead,
    skipped: opts.skipped,
    storeController: opts.storeController,
    storeDir: opts.storeDir,
    virtualStoreDir: opts.virtualStoreDir,
    virtualStoreDirMaxLength: opts.virtualStoreDirMaxLength,
    locationByDepPath,
  } satisfies GetChildrenPathsContext)

  for (const node of Object.values(graph)) {
    const pkgSnapshot = lockfile.packages![node.depPath]
    const allDeps = {
      ...pkgSnapshot.dependencies,
      ...(opts.include.optionalDependencies ? pkgSnapshot.optionalDependencies : {}),
    }
    const peerDeps = pkgSnapshot.peerDependencies ? new Set(Object.keys(pkgSnapshot.peerDependencies)) : null
    node.children = _getChildrenPaths(allDeps, peerDeps, '.')
  }

  const directDependenciesByImporterId: DirectDependenciesByImporterId = {}
  for (const importerId of opts.importerIds) {
    const projectSnapshot = lockfile.importers[importerId]
    const rootDeps = {
      ...(opts.include.devDependencies ? projectSnapshot.devDependencies : {}),
      ...(opts.include.dependencies ? projectSnapshot.dependencies : {}),
      ...(opts.include.optionalDependencies ? projectSnapshot.optionalDependencies : {}),
    }
    directDependenciesByImporterId[importerId] = _getChildrenPaths(rootDeps, null, importerId)
  }

  return { graph, directDependenciesByImporterId, injectionTargetsByDepPath }
}

async function buildGraphFromPackages (
  lockfile: LockfileObject,
  currentLockfile: LockfileObject | null,
  opts: LockfileToDepGraphOptions
): Promise<{
  graph: DependenciesGraph
  locationByDepPath: Record<string, string>
  injectionTargetsByDepPath: Map<string, string[]>
}> {
  const currentPackages = currentLockfile?.packages ?? {}
  const graph: DependenciesGraph = {}
  const locationByDepPath: Record<string, string> = {}
  // Only populated for directory deps (injected workspace packages)
  const injectionTargetsByDepPath = new Map<string, string[]>()

  const _getPatchInfo = getPatchInfo.bind(null, opts.patchedDependencies)
  const promises: Array<Promise<void>> = []
  const pkgSnapshotsWithLocations = iteratePkgsForVirtualStore(lockfile, opts)

  for (const { dirInVirtualStore, pkgMeta } of pkgSnapshotsWithLocations) {
    promises.push((async () => {
      const { pkgIdWithPatchHash, name: pkgName, version: pkgVersion, depPath, pkgSnapshot } = pkgMeta
      if (opts.skipped.has(depPath)) return

      const pkg = {
        name: pkgName,
        version: pkgVersion,
        engines: pkgSnapshot.engines,
        cpu: pkgSnapshot.cpu,
        os: pkgSnapshot.os,
        libc: pkgSnapshot.libc,
      }

      const packageId = packageIdFromSnapshot(depPath, pkgSnapshot)
      if (!opts.force && packageIsInstallable(packageId, pkg, {
        engineStrict: opts.engineStrict,
        lockfileDir: opts.lockfileDir,
        nodeVersion: opts.nodeVersion,
        optional: pkgSnapshot.optional === true,
        supportedArchitectures: opts.supportedArchitectures,
      }) === false) {
        opts.skipped.add(depPath)
        return
      }

      const isDirectoryDep = 'directory' in pkgSnapshot.resolution && pkgSnapshot.resolution.directory != null
      if (isDirectoryDep && opts.ignoreLocalPackages) {
        logger.info({
          message: `Skipping local dependency ${pkgName}@${pkgVersion} (file: protocol)`,
          prefix: opts.lockfileDir,
        })
        return
      }

      const depIsPresent = !isDirectoryDep &&
        currentPackages[depPath] &&
        equals(currentPackages[depPath].dependencies, pkgSnapshot.dependencies)

      const depIntegrityIsUnchanged = isIntegrityEqual(pkgSnapshot.resolution, currentPackages[depPath]?.resolution)

      const modules = path.join(dirInVirtualStore, 'node_modules')
      const dir = path.join(modules, pkgName)
      locationByDepPath[depPath] = dir
      // Track directory deps for injected workspace packages
      if (isDirectoryDep) {
        injectionTargetsByDepPath.set(depPath, [dir])
      }

      // In GVS mode, packages that are allowed to build may have a .pnpm-needs-build
      // marker indicating a previous build failed or was interrupted. When the
      // marker is present, skip the fast path to force a re-fetch/re-import/re-build.
      const mightNeedBuild = opts.enableGlobalVirtualStore &&
        opts.allowBuild?.(pkgName, pkgVersion) === true

      let dirExists: boolean | undefined
      if (
        depIsPresent &&
        depIntegrityIsUnchanged &&
        isEmpty(currentPackages[depPath].optionalDependencies ?? {}) &&
        isEmpty(pkgSnapshot.optionalDependencies ?? {}) &&
        !opts.includeUnchangedDeps
      ) {
        dirExists = await pathExists(dir)
        if (dirExists) {
          if (!(mightNeedBuild && fs.existsSync(path.join(dir, '.pnpm-needs-build')))) return
        } else {
          brokenModulesLogger.debug({ missing: dir })
        }
      }

      let fetchResponse!: Partial<FetchResponse>
      if (depIsPresent && depIntegrityIsUnchanged && equals(currentPackages[depPath].optionalDependencies, pkgSnapshot.optionalDependencies)) {
        if (dirExists ?? await pathExists(dir)) {
          if (!(mightNeedBuild && fs.existsSync(path.join(dir, '.pnpm-needs-build')))) {
            fetchResponse = {}
          }
        } else {
          brokenModulesLogger.debug({ missing: dir })
        }
      }

      if (!fetchResponse && opts.enableGlobalVirtualStore && !isDirectoryDep
        && !opts.force) {
        if (dirExists ?? await pathExists(dir)) {
          if (!(mightNeedBuild && fs.existsSync(path.join(dir, '.pnpm-needs-build')))) {
            fetchResponse = {}
          }
        }
      }

      if (!fetchResponse) {
        const resolution = pkgSnapshotToResolution(depPath, pkgSnapshot, opts.registries)
        progressLogger.debug({ packageId, requester: opts.lockfileDir, status: 'resolved' })

        try {
          fetchResponse = await opts.storeController.fetchPackage({
            allowBuild: opts.allowBuild,
            force: false,
            lockfileDir: opts.lockfileDir,
            ignoreScripts: opts.ignoreScripts,
            pkg: { name: pkgName, version: pkgVersion, id: packageId, resolution },
            supportedArchitectures: opts.supportedArchitectures,
          })
        } catch (err) {
          if (pkgSnapshot.optional) return
          throw err
        }
      }

      graph[dir] = {
        children: {},
        pkgIdWithPatchHash,
        resolution: pkgSnapshot.resolution,
        depPath,
        dir,
        fetching: fetchResponse.fetching,
        filesIndexFile: fetchResponse.filesIndexFile,
        forceImportPackage: !depIntegrityIsUnchanged,
        hasBin: pkgSnapshot.hasBin === true,
        hasBundledDependencies: pkgSnapshot.bundledDependencies != null,
        modules,
        name: pkgName,
        version: pkgVersion,
        optional: !!pkgSnapshot.optional,
        optionalDependencies: new Set(Object.keys(pkgSnapshot.optionalDependencies ?? {})),
        patch: _getPatchInfo(pkgName, pkgVersion),
      }
    })())
  }
  await Promise.all(promises)
  return { graph, locationByDepPath, injectionTargetsByDepPath }
}

interface GetChildrenPathsContext {
  graph: DependenciesGraph
  force: boolean
  registries: Registries
  virtualStoreDir: string
  storeDir: string
  skipped: Set<DepPath>
  lockfileDir: string
  sideEffectsCacheRead: boolean
  storeController: StoreController
  locationByDepPath: Record<string, string>
  virtualStoreDirMaxLength: number
}

function getChildrenPaths (
  ctx: GetChildrenPathsContext,
  allDeps: { [alias: string]: string },
  peerDeps: Set<string> | null,
  importerId: string
): { [alias: string]: string } {
  const children: { [alias: string]: string } = {}
  for (const [alias, ref] of Object.entries(allDeps)) {
    const childDepPath = dp.refToRelative(ref, alias)
    if (childDepPath === null) {
      children[alias] = path.resolve(ctx.lockfileDir, importerId, ref.slice(5))
      continue
    }
    const childRelDepPath = dp.refToRelative(ref, alias)!
    if (ctx.locationByDepPath[childRelDepPath]) {
      children[alias] = ctx.locationByDepPath[childRelDepPath]
    } else if (ctx.graph[childRelDepPath]) {
      children[alias] = ctx.graph[childRelDepPath].dir
    } else if (ref.startsWith('file:')) {
      children[alias] = path.resolve(ctx.lockfileDir, ref.slice(5))
    } else if (!ctx.skipped.has(childRelDepPath) && ((peerDeps == null) || !peerDeps.has(alias))) {
      throw new Error(`${childRelDepPath} not found in ${WANTED_LOCKFILE}`)
    }
  }
  return children
}

function isIntegrityEqual (resolutionA?: LockfileResolution, resolutionB?: LockfileResolution) {
  // The LockfileResolution type is a union, but it doesn't have a "tag"
  // field to perform a discriminant match on. Using a type assertion is
  // required to get the integrity field.
  const integrityA = (resolutionA as ({ integrity?: string } | undefined))?.integrity
  const integrityB = (resolutionB as ({ integrity?: string } | undefined))?.integrity

  return integrityA === integrityB
}

```

### deps/graph-hasher/src/index.ts
```
import { hashObject, hashObjectWithoutSorting } from '@pnpm/crypto.object-hasher'
import { getPkgIdWithPatchHash, refToRelative } from '@pnpm/deps.path'
import { engineName } from '@pnpm/engine.runtime.system-version'
import type { LockfileObject, LockfileResolution, PackageSnapshot } from '@pnpm/lockfile.types'
import { nameVerFromPkgSnapshot } from '@pnpm/lockfile.utils'
import { resolvePlatformSelector, selectPlatformVariant } from '@pnpm/resolving.resolver-base'
import type { AllowBuild, DepPath, PkgIdWithPatchHash, SupportedArchitectures } from '@pnpm/types'
import { familySync } from 'detect-libc'

/**
 * Strip the `node@runtime:` prefix and any peer-context suffix `(...)`
 * from a single snapshot key, returning the bare Node version (e.g.
 * `"22.11.0"`) — or `undefined` if the key isn't a Node runtime pin.
 *
 * Peer-suffixed (`node@runtime:22.11.0(node@22.11.0)`) and bare
 * (`node@runtime:22.11.0`) forms must reduce to the same answer; the
 * pacquet side relies on the same rule for GVS-hash parity.
 */
function extractRuntimeNodeVersion (snapshotKey: string): string | undefined {
  const prefix = 'node@runtime:'
  if (!snapshotKey.startsWith(prefix)) return undefined
  const versionWithPeers = snapshotKey.slice(prefix.length)
  const parenAt = versionWithPeers.indexOf('(')
  return parenAt === -1 ? versionWithPeers : versionWithPeers.slice(0, parenAt)
}

/**
 * Scan an iterable of lockfile snapshot keys for the resolved
 * `engines.runtime` / `devEngines.runtime` Node version and return
 * its bare version string (e.g. `"22.11.0"`), or `undefined` when
 * no snapshot pins a runtime.
 *
 * Pnpm's runtime resolver writes the pinned Node into the lockfile as
 * a snapshot with key `node@runtime:<version>[(<peers>)]`
 * (see [`engine/runtime/node-resolver/src/index.ts`](https://github.com/pnpm/pnpm/blob/29a42efc3b/engine/runtime/node-resolver/src/index.ts)).
 * The first such key found is treated as authoritative. This is fine
 * as an install-wide fallback (project-pin in the typical case), but
 * snapshots that pin their own Node still need
 * {@link readSnapshotRuntimePin} to get a per-snapshot result.
 *
 * Callers typically pass `Object.keys(lockfile.packages ?? {})` — the
 * in-memory `LockfileObject` merges the on-disk `packages:` and
 * `snapshots:` sections under a single `packages` field, so its keys
 * include every snapshot key the install will hash.
 */
export function findRuntimeNodeVersion (snapshotKeys: Iterable<string>): string | undefined {
  for (const key of snapshotKeys) {
    const version = extractRuntimeNodeVersion(key)
    if (version != null) return version
  }
  return undefined
}

/**
 * Read a single graph node's own `engines.runtime` Node pin from its
 * `children` map. The resolver desugars `engines.runtime` declared on
 * a dependency's manifest into `dependencies.node: 'runtime:<version>'`
 * (see [`installing/deps-resolver/src/resolveDependencies.ts`](https://github.com/pnpm/pnpm/blob/29a42efc3b/installing/deps-resolver/src/resolveDependencies.ts)),
 * which then becomes a `children.node` entry pointing at the
 * `node@runtime:<version>[(peers)]` snapshot key.
 *
 * Returns the bare version (e.g. `"22.11.0"`) when this snapshot pins
 * its own Node — or `undefined` when it doesn't and the caller should
 * fall back to the install-wide pin / host probe.
 *
 * Per-snapshot resolution matters because the bin linker routes
 * lifecycle-script spawns for a pinning package through *that
 * package's* downloaded Node — anchoring the snapshot's GVS engine
 * hash to an install-wide value would produce the wrong
 * side-effects-cache key for cross-pinning installs.
 */
export function readSnapshotRuntimePin (
  children: Record<string, string> | undefined
): string | undefined {
  const ref = children?.node
  return ref != null ? extractRuntimeNodeVersion(ref) : undefined
}

export type DepsGraph<T extends string> = Record<T, DepsGraphNode<T>>

export interface DepsGraphNode<T extends string> {
  children: { [alias: string]: T }
  pkgIdWithPatchHash?: PkgIdWithPatchHash
  resolution?: LockfileResolution
  // The full package ID is a unique fingerprint based on the package’s
  // integrity checksum, patch information, and other resolution data.
  fullPkgId?: string
}

export interface DepsStateCache {
  [depPath: string]: string
}

export function calcDepState<T extends string> (
  depsGraph: DepsGraph<T>,
  cache: DepsStateCache,
  depPath: string,
  opts: {
    patchFileHash?: string
    includeDepGraphHash: boolean
    supportedArchitectures?: SupportedArchitectures
    /**
     * Install-wide fallback `engines.runtime` / `devEngines.runtime`
     * Node version (e.g. `"22.11.0"`). Used only when the snapshot at
     * `depPath` doesn't itself pin a Node: per-snapshot pins take
     * precedence so the side-effects-cache key reflects the actual
     * script-runner Node the bin linker would spawn for the package
     * (see {@link readSnapshotRuntimePin}). Typically computed once
     * per install via {@link findRuntimeNodeVersion} over the
     * lockfile's snapshot keys.
     */
    nodeVersion?: string
  }
): string {
  const ownPin = readSnapshotRuntimePin(depsGraph[depPath as T]?.children)
  let result = engineName(ownPin ?? opts.nodeVersion)
  if (opts.includeDepGraphHash) {
    const depGraphHash = calcDepGraphHash(depsGraph, cache, new Set(), depPath, opts.supportedArchitectures)
    result += `;deps=${depGraphHash}`
  }
  if (opts.patchFileHash) {
    result += `;patch=${opts.patchFileHash}`
  }
  return result
}

function calcDepGraphHash<T extends string> (
  depsGraph: DepsGraph<T>,
  cache: DepsStateCache,
  parents: Set<string>,
  depPath: T,
  supportedArchitectures?: SupportedArchitectures
): string {
  if (cache[depPath]) return cache[depPath]
  const node = depsGraph[depPath]
  if (!node) return ''
  if (!node.fullPkgId) {
    if (!node.pkgIdWithPatchHash) {
      throw new Error(`pkgIdWithPatchHash is not defined for ${depPath} in depsGraph`)
    }
    if (!node.resolution) {
      throw new Error(`resolution is not defined for ${depPath} in depsGraph`)
    }
    node.fullPkgId = createFullPkgId(node.pkgIdWithPatchHash, node.resolution, supportedArchitectures)
  }
  const deps: Record<string, string> = {}
  if (Object.keys(node.children).length && !parents.has(node.fullPkgId)) {
    const nextParents = new Set([...Array.from(parents), node.fullPkgId])
    for (const alias in node.children) {
      if (Object.hasOwn(node.children, alias)) {
        const childId = node.children[alias]
        deps[alias] = calcDepGraphHash(depsGraph, cache, nextParents, childId, supportedArchitectures)
      }
    }
  }
  cache[depPath] = hashObject({
    id: node.fullPkgId,
    deps,
  })
  return cache[depPath]
}

export interface PkgMeta {
  depPath: DepPath
  name: string
  version: string
}

export type PkgMetaIterator<T extends PkgMeta> = IterableIterator<T>

export interface HashedDepPath<T extends PkgMeta> {
  pkgMeta: T
  hash: string
}

export function * iterateHashedGraphNodes<T extends PkgMeta> (
  graph: DepsGraph<DepPath>,
  pkgMetaIterator: PkgMetaIterator<T>,
  allowBuild?: AllowBuild,
  supportedArchitectures?: SupportedArchitectures,
  /**
   * Install-wide fallback `engines.runtime` / `devEngines.runtime`
   * Node version. Used only for snapshots that don't pin their own
   * Node; pinning snapshots get resolved per-snapshot via
   * {@link readSnapshotRuntimePin} so the GVS engine hash matches
   * the Node the bin linker would actually spawn for each package
   * (see [`bins/linker/src/index.ts`](https://github.com/pnpm/pnpm/blob/29a42efc3b/bins/linker/src/index.ts)).
   * Typically obtained via {@link findRuntimeNodeVersion} over the
   * lockfile's snapshot keys. `undefined` falls back to
   * {@link engineName}'s default (system `node --version`, with
   * `process.version` as a last resort).
   */
  nodeVersion?: string
): IterableIterator<HashedDepPath<T>> {
  let builtDepPaths: Set<DepPath> | undefined
  let entries: Iterable<T>
  if (allowBuild != null) {
    const pkgMetaList = Array.from(pkgMetaIterator)
    builtDepPaths = computeBuiltDepPaths(pkgMetaList, allowBuild)
    entries = pkgMetaList
  } else {
    entries = pkgMetaIterator
  }
  const ctx = {
    graph,
    cache: {},
    builtDepPaths,
    buildRequiredCache: builtDepPaths !== undefined ? {} : undefined,
    supportedArchitectures,
    nodeVersion,
  }
  for (const pkgMeta of entries) {
    yield {
      hash: calcGraphNodeHash(ctx, pkgMeta),
      pkgMeta,
    }
  }
}

export function calcGraphNodeHash<T extends PkgMeta> (
  { graph, cache, builtDepPaths, buildRequiredCache, supportedArchitectures, nodeVersion }: {
    graph: DepsGraph<DepPath>
    cache: DepsStateCache
    builtDepPaths?: Set<DepPath>
    buildRequiredCache?: Record<string, boolean>
    supportedArchitectures?: SupportedArchitectures
    /** See [`iterateHashedGraphNodes`]'s `nodeVersion` parameter. */
    nodeVersion?: string
  },
  pkgMeta: T
): string {
  const { name, version, depPath } = pkgMeta
  // When builtDepPaths is provided (derived from the allowBuilds config),
  // we only include the engine name for packages that are allowed to build
  // or transitively depend on a package that is allowed to build.
  // This makes GVS hashes engine-agnostic for pure-JS packages,
  // so they survive Node.js upgrades and architecture changes.
  const includeEngine = builtDepPaths === undefined ||
    transitivelyRequiresBuild(graph, builtDepPaths, buildRequiredCache ??= {}, depPath, new Set())
  // A snapshot that declares `engines.runtime` carries the desugared
  // `node@runtime:<version>` pin as a child; that's the Node the bin
  // linker spawns for its lifecycle scripts, so it has to drive the
  // engine portion of the hash too. Non-pinning siblings fall through
  // to the install-wide value.
  const ownPin = readSnapshotRuntimePin(graph[depPath]?.children)
  const engine = includeEngine ? engineName(ownPin ?? nodeVersion) : null
  const deps = calcDepGraphHash(graph, cache, new Set(), depPath, supportedArchitectures)
  const hexDigest = hashObjectWithoutSorting({ engine, deps }, { encoding: 'hex' })
  return formatGlobalVirtualStorePath(name, version, hexDigest)
}

export function calcLeafGlobalVirtualStorePath (fullPkgId: string, name: string, version: string): string {
  const depsHash = hashObject({ id: fullPkgId, deps: {} })
  const hexDigest = hashObjectWithoutSorting({ engine: null, deps: depsHash }, { encoding: 'hex' })
  return formatGlobalVirtualStorePath(name, version, hexDigest)
}

/**
 * `subdepIds` maps each direct child's alias to its full pkg id
 * (`${name}@${version}:${integrity}`). Each child contributes a leaf hash
 * (no transitive walk) to the parent's hash, so the resulting path differs
 * whenever the set or versions of children change. One level deep only —
 * use {@link calcGraphNodeHash} when full graph traversal is needed.
 */
export function calcGlobalVirtualStorePathWithSubdeps (
  fullPkgId: string,
  name: string,
  version: string,
  subdepIds: Record<string, string>
): string {
  const childHashes: Record<string, string> = {}
  for (const [alias, childFullPkgId] of Object.entries(subdepIds)) {
    childHashes[alias] = hashObject({ id: childFullPkgId, deps: {} })
  }
  const depsHash = hashObject({ id: fullPkgId, deps: childHashes })
  const hexDigest = hashObjectWithoutSorting({ engine: null, deps: depsHash }, { encoding: 'hex' })
  return formatGlobalVirtualStorePath(name, version, hexDigest)
}

// Use @/ prefix for unscoped packages to maintain uniform 4-level directory depth
// Scoped: @scope/pkg/version/hash
// Unscoped: @/pkg/version/hash
function formatGlobalVirtualStorePath (name: string, version: string, hexDigest: string): string {
  const prefix = name.startsWith('@') ? '' : '@/'
  return `${prefix}${name}/${version}/${hexDigest}`
}

export interface PkgMetaAndSnapshot extends PkgMeta {
  pkgSnapshot: PackageSnapshot
  pkgIdWithPatchHash: PkgIdWithPatchHash
}

export function * iteratePkgMeta (lockfile: LockfileObject, graph: DepsGraph<DepPath>): PkgMetaIterator<PkgMetaAndSnapshot> {
  if (lockfile.packages == null) {
    return
  }
  for (const depPath in lockfile.packages) {
    if (!Object.hasOwn(lockfile.packages, depPath)) {
      continue
    }
    const pkgSnapshot = lockfile.packages[depPath as DepPath]
    const { name, version } = nameVerFromPkgSnapshot(depPath, pkgSnapshot)
    yield {
      name,
      version,
      depPath: depPath as DepPath,
      pkgIdWithPatchHash: graph[depPath as DepPath]?.pkgIdWithPatchHash ?? getPkgIdWithPatchHash(depPath as DepPath),
      pkgSnapshot,
    }
  }
}

export function lockfileToDepGraph (
  lockfile: LockfileObject,
  supportedArchitectures?: SupportedArchitectures
): DepsGraph<DepPath> {
  const graph: DepsGraph<DepPath> = {}
  if (lockfile.packages != null) {
    for (const [depPath, pkgSnapshot] of Object.entries(lockfile.packages)) {
      const children = lockfileDepsToGraphChildren({
        ...pkgSnapshot.dependencies,
        ...pkgSnapshot.optionalDependencies,
      })
      graph[depPath as DepPath] = {
        children,
        fullPkgId: createFullPkgId(getPkgIdWithPatchHash(depPath as DepPath), pkgSnapshot.resolution, supportedArchitectures),
      }
    }
  }
  return graph
}

function computeBuiltDepPaths (
  entries: Iterable<{ depPath: DepPath; name: string; version: string }>,
  allowBuild: AllowBuild
): Set<DepPath> {
  const builtDepPaths = new Set<DepPath>()
  for (const { depPath, name, version } of entries) {
    if (allowBuild(name, version) === true) {
      builtDepPaths.add(depPath)
    }
  }
  return builtDepPaths
}

function transitivelyRequiresBuild<T extends string> (
  graph: DepsGraph<T>,
  builtDepPaths: Set<T>,
  cache: Record<string, boolean>,
  depPath: T,
  parents: Set<T>
): boolean {
  if (depPath in cache) return cache[depPath]
  if (builtDepPaths.has(depPath)) {
    cache[depPath] = true
    return true
  }
  const node = graph[depPath]
  if (!node) {
    cache[depPath] = false
    return false
  }
  if (parents.has(depPath)) {
    return false
  }
  const nextParents = new Set([...parents, depPath])
  for (const childDepPath of Object.values(node.children) as T[]) {
    if (transitivelyRequiresBuild(graph, builtDepPaths, cache, childDepPath, nextParents)) {
      cache[depPath] = true
      return true
    }
  }
  cache[depPath] = false
  return false
}

function lockfileDepsToGraphChildren (deps: Record<string, string>): Record<string, DepPath> {
  const children: Record<string, DepPath> = {}
  for (const [alias, reference] of Object.entries(deps)) {
    const depPath = refToRelative(reference, alias)
    if (depPath) {
      children[alias] = depPath
    }
  }
  return children
}

function createFullPkgId (
  pkgIdWithPatchHash: PkgIdWithPatchHash,
  resolution: LockfileResolution,
  supportedArchitectures?: SupportedArchitectures
): string {
  if ('integrity' in resolution && resolution.integrity != null) {
    return `${pkgIdWithPatchHash}:${resolution.integrity}`
  }
  if ('type' in resolution && resolution.type === 'variations') {
    // Variations resolutions list every platform variant for a runtime (e.g. all
    // OS/arch combinations for a Node.js version). Hashing the whole object
    // would be identical across hosts, so two projects that install different
    // variants of the same runtime would collide on the same virtual store
    // directory — the first install would "win" and subsequent installs with
    // different --os/--cpu/--libc would silently reuse the cached variant.
    // Incorporate the chosen variant's integrity instead so each variant gets
    // its own entry in the global virtual store.
    const selector = resolvePlatformSelector(supportedArchitectures, {
      platform: process.platform,
      arch: process.arch,
      libc: familySync(),
    })
    const variant = selectPlatformVariant(resolution.variants, selector)
    const chosenResolution = variant?.resolution
    if (chosenResolution && 'integrity' in chosenResolution && chosenResolution.integrity != null) {
      return `${pkgIdWithPatchHash}:${chosenResolution.integrity}`
    }
  }
  return `${pkgIdWithPatchHash}:${hashObject(resolution)}`
}

```

### deps/path/src/index.ts
```
import { createShortHash } from '@pnpm/crypto.hash'
import type { DepPath, PkgId, PkgIdWithPatchHash, PkgResolutionId, Registries } from '@pnpm/types'
import semver from 'semver'

export function isAbsolute (dependencyPath: string): boolean {
  return dependencyPath[0] !== '/'
}

export function indexOfDepPathSuffix (depPath: string): { peersIndex: number, patchHashIndex: number } {
  if (!depPath.endsWith(')')) return { peersIndex: -1, patchHashIndex: -1 }
  let open = 1
  for (let i = depPath.length - 2; i >= 0; i--) {
    if (depPath[i] === '(') {
      open--
    } else if (depPath[i] === ')') {
      open++
    } else if (!open) {
      if (depPath.substring(i + 1).startsWith('(patch_hash=')) {
        return {
          patchHashIndex: i + 1,
          peersIndex: depPath.indexOf('(', i + 2),
        }
      }
      return {
        patchHashIndex: -1,
        peersIndex: i + 1,
      }
    }
  }
  return { peersIndex: -1, patchHashIndex: -1 }
}

export interface ParsedDepPath {
  id: string
  peerDepGraphHash: string
}

export function parseDepPath (relDepPath: string): ParsedDepPath {
  const { peersIndex } = indexOfDepPathSuffix(relDepPath)
  if (peersIndex !== -1) {
    return {
      id: relDepPath.substring(0, peersIndex),
      peerDepGraphHash: relDepPath.substring(peersIndex),
    }
  }
  return {
    id: relDepPath,
    peerDepGraphHash: '',
  }
}

export function removeSuffix (relDepPath: string): string {
  const { peersIndex, patchHashIndex } = indexOfDepPathSuffix(relDepPath)
  if (patchHashIndex !== -1) {
    return relDepPath.substring(0, patchHashIndex)
  }
  if (peersIndex !== -1) {
    return relDepPath.substring(0, peersIndex)
  }
  return relDepPath
}

export function getPkgIdWithPatchHash (depPath: DepPath): PkgIdWithPatchHash {
  let pkgId: string = depPath
  const { peersIndex: sepIndex } = indexOfDepPathSuffix(pkgId)
  if (sepIndex !== -1) {
    pkgId = pkgId.substring(0, sepIndex)
  }
  return pkgId as PkgIdWithPatchHash
}

export function tryGetPackageId (relDepPath: DepPath): PkgId {
  let pkgId: string = relDepPath
  const { peersIndex, patchHashIndex } = indexOfDepPathSuffix(pkgId)
  const sepIndex = patchHashIndex === -1 ? peersIndex : patchHashIndex
  if (sepIndex !== -1) {
    pkgId = pkgId.substring(0, sepIndex)
  }
  if (pkgId.includes(':')) {
    const newPkgId = pkgId.substring(pkgId.indexOf('@', 1) + 1)
    // TODO: change the format of package ID to always start with the package name.
    // not only in the case of "runtime:"
    if (!newPkgId.startsWith('runtime:')) {
      pkgId = newPkgId
    }
  }
  return pkgId as PkgId
}

export function getRegistryByPackageName (registries: Registries, packageName: string): string {
  if (packageName[0] !== '@') return registries.default
  const scope = packageName.substring(0, packageName.indexOf('/'))
  return registries[scope] || registries.default
}

export function refToRelative (
  reference: string,
  pkgName: string
): DepPath | null {
  if (reference.startsWith('link:')) {
    return null
  }
  if (reference[0] === '@') return reference as DepPath
  const atIndex = reference.indexOf('@')
  if (atIndex === -1) return `${pkgName}@${reference}` as DepPath
  const colonIndex = reference.indexOf(':')
  const bracketIndex = reference.indexOf('(')
  if ((colonIndex === -1 || atIndex < colonIndex) && (bracketIndex === -1 || atIndex < bracketIndex)) return reference as DepPath
  return `${pkgName}@${reference}` as DepPath
}

export interface DependencyPath {
  name?: string
  peerDepGraphHash?: string
  version?: string
  nonSemverVersion?: PkgResolutionId
  patchHash?: string
}

export function parse (dependencyPath: string): DependencyPath {
  // eslint-disable-next-line: strict-type-predicates
  if (typeof dependencyPath !== 'string') {
    throw new TypeError(`Expected \`dependencyPath\` to be of type \`string\`, got \`${
      // eslint-disable-next-line: strict-type-predicates
      dependencyPath === null ? 'null' : typeof dependencyPath
    }\``)
  }
  const sepIndex = dependencyPath.indexOf('@', 1)
  if (sepIndex === -1) {
    return {}
  }
  const name = dependencyPath.substring(0, sepIndex)
  let version = dependencyPath.substring(sepIndex + 1)
  if (version) {
    let peerDepGraphHash: string | undefined
    let patchHash: string | undefined
    const { peersIndex, patchHashIndex } = indexOfDepPathSuffix(version)
    if (peersIndex !== -1 || patchHashIndex !== -1) {
      if (peersIndex === -1) {
        patchHash = version.substring(patchHashIndex)
        version = version.substring(0, patchHashIndex)
      } else if (patchHashIndex === -1) {
        peerDepGraphHash = version.substring(peersIndex)
        version = version.substring(0, peersIndex)
      } else {
        patchHash = version.substring(patchHashIndex, peersIndex)
        peerDepGraphHash = version.substring(peersIndex)
        version = version.substring(0, patchHashIndex)
      }
    }
    if (semver.valid(version)) {
      return {
        name,
        peerDepGraphHash,
        version,
        patchHash,
      }
    }
    return {
      name,
      nonSemverVersion: version as PkgResolutionId,
      peerDepGraphHash,
      patchHash,
    }
  }
  return {}
}

export function depPathToFilename (depPath: string, maxLengthWithoutHash: number): string {
  let filename = depPathToFilenameUnescaped(depPath).replace(/[\\/:*?"<>|#]/g, '+')
  if (filename.includes('(')) {
    filename = filename
      .replace(/\)$/, '')
      .replace(/\)\(|\(|\)/g, '_')
  }
  if (filename.length > maxLengthWithoutHash || filename !== filename.toLowerCase() && !filename.startsWith('file+')) {
    return `${filename.substring(0, maxLengthWithoutHash - 33)}_${createShortHash(filename)}`
  }
  return filename
}

function depPathToFilenameUnescaped (depPath: string): string {
  if (!depPath.startsWith('file:')) {
    if (depPath[0] === '/') {
      depPath = depPath.substring(1)
    }
    const index = depPath.indexOf('@', 1)
    if (index === -1) return depPath
    return `${depPath.substring(0, index)}@${depPath.slice(index + 1)}`
  }
  return depPath.replace(':', '+')
}

// Peer ID or stringified peer dependency graph
export type PeerId = { name: string, version: string } | string

export function createPeerDepGraphHash (peerIds: PeerId[], maxLength: number = 1000): string {
  let dirName = peerIds.map(
    (peerId) => {
      if (typeof peerId !== 'string') {
        return `${peerId.name}@${peerId.version}`
      }
      if (peerId[0] === '/') {
        return peerId.substring(1)
      }
      return peerId
    }
  ).sort().join(')(')
  if (dirName.length > maxLength) {
    dirName = createShortHash(dirName)
  }
  return `(${dirName})`
}

const RUNTIME_DEP_PATH_RE = /^(?:node|bun|deno)@runtime:/

export function isRuntimeDepPath (depPath: DepPath): boolean {
  return RUNTIME_DEP_PATH_RE.test(depPath)
}

```

### exec/prepare-package/src/index.ts
```
import assert from 'node:assert'
import fs from 'node:fs'
import path from 'node:path'
import util from 'node:util'

import { PnpmError } from '@pnpm/error'
import { runLifecycleHook, type RunLifecycleHookOptions } from '@pnpm/exec.lifecycle'
import { safeReadPackageJsonFromDir } from '@pnpm/pkg-manifest.reader'
import type { AllowBuild, PackageManifest } from '@pnpm/types'
import { rimraf } from '@zkochan/rimraf'
import { preferredPM } from 'preferred-pm'

// We don't run prepublishOnly to prepare the dependency.
// This might be counterintuitive as prepublishOnly is where a lot of packages put their build scripts.
// However, neither npm nor Yarn run prepublishOnly of git-hosted dependencies (checked on npm v10 and Yarn v3).
const PREPUBLISH_SCRIPTS = [
  'prepublish',
  'prepack',
  'publish',
]

export interface PreparePackageOptions {
  allowBuild?: AllowBuild
  ignoreScripts?: boolean
  unsafePerm?: boolean
  userAgent?: string
}

export async function preparePackage (opts: PreparePackageOptions, gitRootDir: string, subDir: string): Promise<{ shouldBeBuilt: boolean, pkgDir: string }> {
  const pkgDir = safeJoinPath(gitRootDir, subDir)
  const manifest = await safeReadPackageJsonFromDir(pkgDir)
  if (manifest?.scripts == null || !packageShouldBeBuilt(manifest, pkgDir)) return { shouldBeBuilt: false, pkgDir }
  if (opts.ignoreScripts) return { shouldBeBuilt: true, pkgDir }
  // Check if the package is allowed to run build scripts
  // If allowBuild is undefined or returns false, block the build
  if (!opts.allowBuild?.(manifest.name, manifest.version)) {
    throw new PnpmError(
      'GIT_DEP_PREPARE_NOT_ALLOWED',
      `The git-hosted package "${manifest.name}@${manifest.version}" needs to execute build scripts but is not in the "allowBuilds" allowlist.`,
      {
        hint: `Add the package to "allowBuilds" in your project's pnpm-workspace.yaml to allow it to run scripts. For example:
allowBuilds:
  ${manifest.name}: true`,
      }
    )
  }
  const pm = (await preferredPM(gitRootDir))?.name ?? 'npm'
  const execOpts: RunLifecycleHookOptions = {
    depPath: `${manifest.name}@${manifest.version}`,
    pkgRoot: pkgDir,
    rootModulesDir: pkgDir, // We don't need this property but there is currently no way to not set it.
    unsafePerm: Boolean(opts.unsafePerm),
    userAgent: opts.userAgent,
  }
  try {
    const installScriptName = `${pm}-install`
    manifest.scripts[installScriptName] = `${pm} install`
    await runLifecycleHook(installScriptName, manifest, execOpts)
    for (const scriptName of PREPUBLISH_SCRIPTS) {
      if (manifest.scripts[scriptName] == null || manifest.scripts[scriptName] === '') continue
      let newScriptName
      if (pm !== 'pnpm') {
        newScriptName = `${pm}-run-${scriptName}`
        manifest.scripts[newScriptName] = `${pm} run ${scriptName}`
      } else {
        newScriptName = scriptName
      }
      // eslint-disable-next-line no-await-in-loop
      await runLifecycleHook(newScriptName, manifest, execOpts)
    }
  } catch (err: unknown) {
    assert(util.types.isNativeError(err))
    Object.assign(err, {
      code: 'ERR_PNPM_PREPARE_PACKAGE',
    })
    throw err
  }
  await rimraf(path.join(pkgDir, 'node_modules'))
  return { shouldBeBuilt: true, pkgDir }
}

function packageShouldBeBuilt (manifest: PackageManifest, pkgDir: string): boolean {
  if (manifest.scripts == null) return false
  const scripts = manifest.scripts
  if (scripts.prepare != null && scripts.prepare !== '') return true
  const hasPrepublishScript = PREPUBLISH_SCRIPTS.some((scriptName) => scripts[scriptName] != null && scripts[scriptName] !== '')
  if (!hasPrepublishScript) return false
  const mainFile = manifest.main ?? 'index.js'
  return !fs.existsSync(path.join(pkgDir, mainFile))
}

function safeJoinPath (root: string, sub: string): string {
  const joined = path.join(root, sub)
  // prevent the dir traversal attack
  const relative = path.relative(root, joined)
  if (relative.startsWith('..')) {
    throw new PnpmError('INVALID_PATH', `Path "${sub}" should be a sub directory`)
  }
  if (!fs.existsSync(joined) || !fs.lstatSync(joined).isDirectory()) {
    throw new PnpmError('INVALID_PATH', `Path "${sub}" is not a directory`)
  }
  return joined
}

```

### fetching/git-fetcher/package.json
```
{
  "name": "@pnpm/fetching.git-fetcher",
  "version": "1101.0.11",
  "description": "A fetcher for git-hosted packages",
  "keywords": [
    "pnpm",
    "pnpm11",
    "fetcher"
  ],
  "license": "MIT",
  "funding": "https://opencollective.com/pnpm",
  "repository": "https://github.com/pnpm/pnpm/tree/main/fetching/git-fetcher",
  "homepage": "https://github.com/pnpm/pnpm/tree/main/fetching/git-fetcher#readme",
  "bugs": {
    "url": "https://github.com/pnpm/pnpm/issues"
  },
  "type": "module",
  "main": "lib/index.js",
  "types": "lib/index.d.ts",
  "exports": {
    ".": "./lib/index.js"
  },
  "files": [
    "lib",
    "!*.map"
  ],
  "scripts": {
    "test": "pn compile && pn .test",
    "lint": "eslint \"src/**/*.ts\" \"test/**/*.ts\"",
    "prepublishOnly": "tsgo --build",
    "compile": "tsgo --build && pn lint --fix",
    ".test": "cross-env NODE_OPTIONS=\"$NODE_OPTIONS --experimental-vm-modules --disable-warning=ExperimentalWarning --disable-warning=DEP0169\" jest"
  },
  "dependencies": {
    "@pnpm/error": "workspace:*",
    "@pnpm/exec.prepare-package": "workspace:*",
    "@pnpm/fetching.fetcher-base": "workspace:*",
    "@pnpm/fs.packlist": "workspace:*",
    "@pnpm/store.index": "workspace:*",
    "@zkochan/rimraf": "catalog:",
    "execa": "catalog:"
  },
  "peerDependencies": {
    "@pnpm/logger": "catalog:",
    "@pnpm/worker": "workspace:^"
  },
  "devDependencies": {
    "@jest/globals": "catalog:",
    "@pnpm/fetching.git-fetcher": "workspace:*",
    "@pnpm/logger": "workspace:*",
    "@pnpm/store.cafs": "workspace:*",
    "@pnpm/store.create-cafs-store": "workspace:*",
    "@pnpm/types": "workspace:*",
    "@pnpm/util.lex-comparator": "catalog:",
    "tempy": "catalog:"
  },
  "engines": {
    "node": ">=22.13"
  },
  "jest": {
    "preset": "@pnpm/jest-config"
  }
}

```

### fetching/git-fetcher/src/index.ts
```
import assert from 'node:assert'
import path from 'node:path'
import { URL } from 'node:url'
import util from 'node:util'

import { PnpmError } from '@pnpm/error'
import { preparePackage } from '@pnpm/exec.prepare-package'
import type { GitFetcher } from '@pnpm/fetching.fetcher-base'
import { packlist } from '@pnpm/fs.packlist'
import { globalWarn } from '@pnpm/logger'
import type { StoreIndex } from '@pnpm/store.index'
import { addFilesFromDir } from '@pnpm/worker'
import { rimraf } from '@zkochan/rimraf'
import { safeExeca as execa } from 'execa'

export interface CreateGitFetcherOptions {
  gitShallowHosts?: string[]
  storeIndex: StoreIndex
  unsafePerm?: boolean
  userAgent?: string
  ignoreScripts?: boolean
}

export function createGitFetcher (createOpts: CreateGitFetcherOptions): { git: GitFetcher } {
  const allowedHosts = new Set(createOpts?.gitShallowHosts ?? [])
  const ignoreScripts = createOpts.ignoreScripts ?? false

  const gitFetcher: GitFetcher = async (cafs, resolution, opts) => {
    if (!isValidCommitHash(resolution.commit)) {
      throw new PnpmError('INVALID_GIT_COMMIT', `Invalid git commit hash "${resolution.commit}" for repository "${resolution.repo}". Expected a 40-character hexadecimal SHA.`)
    }
    const tempLocation = await cafs.tempDir()
    if (allowedHosts.size > 0 && shouldUseShallow(resolution.repo, allowedHosts)) {
      await execGit(['init'], { cwd: tempLocation })
      await execGit(['remote', 'add', 'origin', resolution.repo], { cwd: tempLocation })
      await execGit(['fetch', '--depth', '1', 'origin', resolution.commit], { cwd: tempLocation })
    } else {
      await execGit(['clone', resolution.repo, tempLocation])
    }
    await execGit(['checkout', resolution.commit], { cwd: tempLocation })
    const receivedCommit = await execGit(['rev-parse', 'HEAD'], { cwd: tempLocation })
    if (receivedCommit.trim() !== resolution.commit) {
      throw new PnpmError('GIT_CHECKOUT_FAILED', `received commit ${receivedCommit.trim()} does not match expected value ${resolution.commit}`)
    }
    let pkgDir: string
    try {
      const prepareResult = await preparePackage({
        allowBuild: opts.allowBuild,
        ignoreScripts: createOpts.ignoreScripts,
        unsafePerm: createOpts.unsafePerm,
        userAgent: createOpts.userAgent,
      }, tempLocation, resolution.path ?? '')
      pkgDir = prepareResult.pkgDir
      if (ignoreScripts && prepareResult.shouldBeBuilt) {
        globalWarn(`The git-hosted package fetched from "${resolution.repo}" has to be built but the build scripts were ignored.`)
      }
    } catch (err: unknown) {
      assert(util.types.isNativeError(err))
      err.message = `Failed to prepare git-hosted package fetched from "${resolution.repo}": ${err.message}`
      throw err
    }
    // removing /.git to make directory integrity calculation faster
    await rimraf(path.join(tempLocation, '.git'))
    const files = await packlist(pkgDir)
    // Important! We cannot remove the temp location at this stage.
    // Even though we have the index of the package,
    // the linking of files to the store is in progress.
    return addFilesFromDir({
      storeDir: cafs.storeDir,
      storeIndex: createOpts.storeIndex,
      dir: pkgDir,
      files,
      filesIndexFile: opts.filesIndexFile,
      readManifest: opts.readManifest,
      pkg: opts.pkg,
    })
  }

  return {
    git: gitFetcher,
  }
}

function isValidCommitHash (commit: string): boolean {
  return /^[0-9a-f]{40}$/i.test(commit)
}

function shouldUseShallow (repoUrl: string, allowedHosts: Set<string>): boolean {
  try {
    const { host } = new URL(repoUrl)
    if (allowedHosts.has(host)) {
      return true
    }
  } catch {
    // URL might be malformed
  }
  return false
}

function prefixGitArgs (): string[] {
  return process.platform === 'win32' ? ['-c', 'core.longpaths=true'] : []
}

async function execGit (args: string[], opts?: object): Promise<string> {
  const fullArgs = prefixGitArgs().concat(args || [])
  const { stdout } = await execa('git', fullArgs, opts)
  return stdout as string
}

```

### fetching/git-fetcher/tsconfig.json
```
{
  "extends": "@pnpm/tsconfig",
  "compilerOptions": {
    "outDir": "lib",
    "rootDir": "src"
  },
  "include": [
    "src/**/*.ts",
    "../../__typings__/**/*.d.ts"
  ],
  "references": [
    {
      "path": "../../core/error"
    },
    {
      "path": "../../core/logger"
    },
    {
      "path": "../../core/types"
    },
    {
      "path": "../../exec/prepare-package"
    },
    {
      "path": "../../fs/packlist"
    },
    {
      "path": "../../store/cafs"
    },
    {
      "path": "../../store/create-cafs-store"
    },
    {
      "path": "../../store/index"
    },
    {
      "path": "../../worker"
    },
    {
      "path": "../fetcher-base"
    }
  ]
}

```

### fetching/tarball-fetcher/src/gitHostedTarballFetcher.ts
```
import assert from 'node:assert'
import util from 'node:util'

import { preparePackage } from '@pnpm/exec.prepare-package'
import type { FetchFunction, FetchOptions } from '@pnpm/fetching.fetcher-base'
import { packlist } from '@pnpm/fs.packlist'
import { globalWarn } from '@pnpm/logger'
import type { Cafs, FilesMap } from '@pnpm/store.cafs-types'
import type { StoreIndex } from '@pnpm/store.index'
import type { BundledManifest } from '@pnpm/types'
import { addFilesFromDir } from '@pnpm/worker'

interface Resolution {
  integrity?: string
  registry?: string
  tarball: string
  path?: string
}

export interface CreateGitHostedTarballFetcher {
  ignoreScripts?: boolean
  storeIndex: StoreIndex
  unsafePerm?: boolean
}

export function createGitHostedTarballFetcher (fetchRemoteTarball: FetchFunction, fetcherOpts: CreateGitHostedTarballFetcher): FetchFunction {
  const fetch = async (cafs: Cafs, resolution: Resolution, opts: FetchOptions) => {
    const rawFilesIndexFile = `${opts.filesIndexFile}\traw`
    const { filesMap, manifest, requiresBuild, integrity } = await fetchRemoteTarball(cafs, resolution, {
      ...opts,
      filesIndexFile: rawFilesIndexFile,
    })
    // Flush any queued store index writes so that the raw files index entry
    // written during tarball extraction is visible to subsequent reads.
    fetcherOpts.storeIndex.flush()
    try {
      const prepareResult = await prepareGitHostedPkg(filesMap, cafs, rawFilesIndexFile, opts.filesIndexFile, fetcherOpts, opts, resolution)
      if (prepareResult.ignoredBuild) {
        globalWarn(`The git-hosted package fetched from "${resolution.tarball}" has to be built but the build scripts were ignored.`)
      }
      return {
        filesMap: prepareResult.filesMap,
        manifest: prepareResult.manifest ?? manifest,
        requiresBuild,
        // Propagate the raw tarball integrity so the lockfile pins it and
        // future installs detect a tampered tarball from the git host.
        integrity,
      }
    } catch (err: unknown) {
      assert(util.types.isNativeError(err))
      err.message = `Failed to prepare git-hosted package fetched from "${resolution.tarball}": ${err.message}`
      throw err
    }
  }

  return fetch as FetchFunction
}

interface PrepareGitHostedPkgResult {
  filesMap: FilesMap
  manifest?: BundledManifest
  ignoredBuild: boolean
}

async function prepareGitHostedPkg (
  filesMap: FilesMap,
  cafs: Cafs,
  rawFilesIndexFile: string,
  filesIndexFile: string,
  opts: CreateGitHostedTarballFetcher,
  fetcherOpts: FetchOptions,
  resolution: Resolution
): Promise<PrepareGitHostedPkgResult> {
  const tempLocation = await cafs.tempDir()
  cafs.importPackage(tempLocation, {
    filesResponse: {
      filesMap,
      resolvedFrom: 'remote',
      requiresBuild: false,
    },
    force: true,
  })
  const { shouldBeBuilt, pkgDir } = await preparePackage({
    ...opts,
    allowBuild: fetcherOpts.allowBuild,
  }, tempLocation, resolution.path ?? '')
  const files = await packlist(pkgDir)
  const { storeIndex } = opts
  if (!resolution.path && files.length === filesMap.size) {
    if (!shouldBeBuilt) {
      const data = storeIndex.get(rawFilesIndexFile)
      if (data) {
        storeIndex.set(filesIndexFile, data)
        storeIndex.delete(rawFilesIndexFile)
      }
      return {
        filesMap,
        ignoredBuild: false,
      }
    }
    if (opts.ignoreScripts) {
      storeIndex.delete(rawFilesIndexFile)
      return {
        filesMap,
        ignoredBuild: true,
      }
    }
  }
  storeIndex.delete(rawFilesIndexFile)
  // Important! We cannot remove the temp location at this stage.
  // Even though we have the index of the package,
  // the linking of files to the store is in progress.
  return {
    ...await addFilesFromDir({
      storeDir: cafs.storeDir,
      storeIndex: opts.storeIndex,
      dir: pkgDir,
      files,
      filesIndexFile,
      pkg: fetcherOpts.pkg,
      readManifest: fetcherOpts.readManifest,
    }),
    ignoredBuild: Boolean(opts.ignoreScripts),
  }
}

```

### installing/commands/package.json
```
{
  "name": "@pnpm/installing.commands",
  "version": "1100.7.2",
  "description": "Commands for installation",
  "keywords": [
    "pnpm",
    "pnpm11"
  ],
  "license": "MIT",
  "funding": "https://opencollective.com/pnpm",
  "repository": "https://github.com/pnpm/pnpm/tree/main/installing/commands",
  "homepage": "https://github.com/pnpm/pnpm/tree/main/installing/commands#readme",
  "bugs": {
    "url": "https://github.com/pnpm/pnpm/issues"
  },
  "type": "module",
  "main": "lib/index.js",
  "types": "lib/index.d.ts",
  "exports": {
    ".": "./lib/index.js"
  },
  "files": [
    "lib",
    "!*.map"
  ],
  "scripts": {
    "start": "tsgo --watch",
    "lint": "eslint \"src/**/*.ts\" \"test/**/*.ts\"",
    "test": "pn compile && pn .test",
    "prepublishOnly": "tsgo --build",
    "compile": "tsgo --build && pn lint --fix",
    ".test": "cross-env NODE_OPTIONS=\"$NODE_OPTIONS --experimental-vm-modules --disable-warning=ExperimentalWarning --disable-warning=DEP0169\" jest"
  },
  "dependencies": {
    "@inquirer/prompts": "catalog:",
    "@pnpm/building.after-install": "workspace:*",
    "@pnpm/catalogs.types": "workspace:*",
    "@pnpm/cli.command": "workspace:*",
    "@pnpm/cli.common-cli-options-help": "workspace:*",
    "@pnpm/cli.utils": "workspace:*",
    "@pnpm/colorize-semver-diff": "catalog:",
    "@pnpm/config.matcher": "workspace:*",
    "@pnpm/config.pick-registry-for-package": "workspace:*",
    "@pnpm/config.reader": "workspace:*",
    "@pnpm/config.writer": "workspace:*",
    "@pnpm/constants": "workspace:*",
    "@pnpm/deps.inspection.outdated": "workspace:*",
    "@pnpm/deps.path": "workspace:*",
    "@pnpm/deps.security.signatures": "workspace:*",
    "@pnpm/deps.status": "workspace:*",
    "@pnpm/error": "workspace:*",
    "@pnpm/fs.graceful-fs": "workspace:*",
    "@pnpm/fs.read-modules-dir": "workspace:*",
    "@pnpm/global.commands": "workspace:*",
    "@pnpm/hooks.pnpmfile": "workspace:*",
    "@pnpm/installing.context": "workspace:*",
    "@pnpm/installing.dedupe.check": "workspace:*",
    "@pnpm/installing.deps-installer": "workspace:*",
    "@pnpm/installing.env-installer": "workspace:*",
    "@pnpm/lockfile.fs": "workspace:*",
    "@pnpm/lockfile.types": "workspace:*",
    "@pnpm/network.auth-header": "workspace:*",
    "@pnpm/network.fetch": "workspace:*",
    "@pnpm/pkg-manifest.reader": "workspace:*",
    "@pnpm/pkg-manifest.utils": "workspace:*",
    "@pnpm/resolving.npm-resolver": "workspace:*",
    "@pnpm/resolving.parse-wanted-dependency": "workspace:*",
    "@pnpm/resolving.resolver-base": "workspace:*",
    "@pnpm/semver-diff": "catalog:",
    "@pnpm/store.connection-manager": "workspace:*",
    "@pnpm/store.controller": "workspace:*",
    "@pnpm/types": "workspace:*",
    "@pnpm/util.lex-comparator": "catalog:",
    "@pnpm/workspace.project-manifest-reader": "workspace:*",
    "@pnpm/workspace.project-manifest-writer": "workspace:*",
    "@pnpm/workspace.projects-filter": "workspace:*",
    "@pnpm/workspace.projects-graph": "workspace:*",
    "@pnpm/workspace.projects-reader": "workspace:*",
    "@pnpm/workspace.projects-sorter": "workspace:*",
    "@pnpm/workspace.root-finder": "workspace:*",
    "@pnpm/workspace.state": "workspace:*",
    "@pnpm/workspace.workspace-manifest-writer": "workspace:*",
    "@yarnpkg/core": "catalog:",
    "@yarnpkg/lockfile": "catalog:",
    "@yarnpkg/parsers": "catalog:",
    "@zkochan/rimraf": "catalog:",
    "@zkochan/table": "catalog:",
    "chalk": "catalog:",
    "ci-info": "catalog:",
    "get-npm-tarball-url": "catalog:",
    "is-subdir": "catalog:",
    "load-json-file": "catalog:",
    "normalize-path": "catalog:",
    "p-filter": "catalog:",
    "p-limit": "catalog:",
    "ramda": "catalog:",
    "render-help": "catalog:",
    "version-selector-type": "catalog:"
  },
  "peerDependencies": {
    "@pnpm/logger": "catalog:"
  },
  "devDependencies": {
    "@jest/globals": "catalog:",
    "@pnpm/assert-project": "workspace:*",
    "@pnpm/installing.commands": "workspace:*",
    "@pnpm/installing.modules-yaml": "workspace:*",
    "@pnpm/logger": "workspace:*",
    "@pnpm/prepare": "workspace:*",
    "@pnpm/store.index": "workspace:*",
    "@pnpm/test-fixtures": "workspace:*",
    "@pnpm/test-ipc-server": "workspace:*",
    "@pnpm/testing.command-defaults": "workspace:*",
    "@pnpm/testing.mock-agent": "workspace:*",
    "@pnpm/testing.registry-mock": "workspace:*",
    "@pnpm/worker": "workspace:*",
    "@pnpm/workspace.projects-filter": "workspace:*",
    "@types/normalize-path": "catalog:",
    "@types/proxyquire": "catalog:",
    "@types/ramda": "catalog:",
    "@types/yarnpkg__lockfile": "catalog:",
    "@types/zkochan__table": "catalog:",
    "delay": "catalog:",
    "jest-diff": "catalog:",
    "path-name": "catalog:",
    "proxyquire": "catalog:",
    "read-yaml-file": "catalog:",
    "symlink-dir": "catalog:",
    "tempy": "catalog:",
    "write-json-file": "catalog:",
    "write-package": "catalog:",
    "write-yaml-file": "catalog:"
  },
  "engines": {
    "node": ">=22.13"
  },
  "jest": {
    "preset": "@pnpm/jest-config/with-registry"
  }
}

```

### installing/commands/src/handleIgnoredBuilds.ts
```
import { writeSettings } from '@pnpm/config.writer'
import { parse } from '@pnpm/deps.path'
import {
  IgnoredBuildsError,
} from '@pnpm/installing.deps-installer'
import type { IgnoredBuilds } from '@pnpm/types'
import { lexCompare } from '@pnpm/util.lex-comparator'

export interface HandleIgnoredBuildsOpts {
  allowBuilds?: Record<string, boolean | string>
  rootProjectManifestDir?: string
  workspaceDir?: string
  strictDepBuilds?: boolean
}

export async function handleIgnoredBuilds (
  opts: HandleIgnoredBuildsOpts,
  ignoredBuilds: IgnoredBuilds | undefined
): Promise<void> {
  if (!ignoredBuilds?.size) return
  await writeIgnoredBuildsToAllowBuilds(opts, ignoredBuilds)
  if (opts.strictDepBuilds) {
    throw new IgnoredBuildsError(ignoredBuilds)
  }
}

async function writeIgnoredBuildsToAllowBuilds (
  opts: Pick<HandleIgnoredBuildsOpts, 'allowBuilds' | 'rootProjectManifestDir' | 'workspaceDir'>,
  ignoredBuilds: IgnoredBuilds
): Promise<void> {
  const packageNames = packageNamesFromIgnoredBuilds(ignoredBuilds)
  const newEntries: Record<string, string> = {}
  for (const name of packageNames) {
    if (opts.allowBuilds?.[name] == null) {
      newEntries[name] = 'set this to true or false'
    }
  }
  if (Object.keys(newEntries).length && opts.rootProjectManifestDir) {
    await writeSettings({
      rootProjectManifestDir: opts.rootProjectManifestDir,
      workspaceDir: opts.workspaceDir ?? opts.rootProjectManifestDir,
      updatedSettings: {
        allowBuilds: { ...opts.allowBuilds, ...newEntries },
      },
    })
  }
}

function packageNamesFromIgnoredBuilds (ignoredBuilds: IgnoredBuilds): string[] {
  return Array.from(new Set(Array.from(ignoredBuilds).map((dp) => parse(dp).name ?? dp))).sort(lexCompare)
}

```

### installing/commands/tsconfig.json
```
{
  "extends": "@pnpm/tsconfig",
  "compilerOptions": {
    "outDir": "lib",
    "rootDir": "src"
  },
  "include": [
    "src/**/*.ts",
    "../../__typings__/**/*.d.ts"
  ],
  "references": [
    {
      "path": "../../__utils__/assert-project"
    },
    {
      "path": "../../__utils__/prepare"
    },
    {
      "path": "../../__utils__/test-fixtures"
    },
    {
      "path": "../../__utils__/test-ipc-server"
    },
    {
      "path": "../../building/after-install"
    },
    {
      "path": "../../catalogs/types"
    },
    {
      "path": "../../cli/command"
    },
    {
      "path": "../../cli/common-cli-options-help"
    },
    {
      "path": "../../cli/utils"
    },
    {
      "path": "../../config/matcher"
    },
    {
      "path": "../../config/pick-registry-for-package"
    },
    {
      "path": "../../config/reader"
    },
    {
      "path": "../../config/writer"
    },
    {
      "path": "../../core/constants"
    },
    {
      "path": "../../core/error"
    },
    {
      "path": "../../core/logger"
    },
    {
      "path": "../../core/types"
    },
    {
      "path": "../../deps/inspection/outdated"
    },
    {
      "path": "../../deps/path"
    },
    {
      "path": "../../deps/security/signatures"
    },
    {
      "path": "../../deps/status"
    },
    {
      "path": "../../fs/graceful-fs"
    },
    {
      "path": "../../fs/read-modules-dir"
    },
    {
      "path": "../../global/commands"
    },
    {
      "path": "../../hooks/pnpmfile"
    },
    {
      "path": "../../lockfile/fs"
    },
    {
      "path": "../../lockfile/types"
    },
    {
      "path": "../../network/auth-header"
    },
    {
      "path": "../../network/fetch"
    },
    {
      "path": "../../pkg-manifest/reader"
    },
    {
      "path": "../../pkg-manifest/utils"
    },
    {
      "path": "../../resolving/npm-resolver"
    },
    {
      "path": "../../resolving/parse-wanted-dependency"
    },
    {
      "path": "../../resolving/resolver-base"
    },
    {
      "path": "../../store/connection-manager"
    },
    {
      "path": "../../store/controller"
    },
    {
      "path": "../../store/index"
    },
    {
      "path": "../../testing/command-defaults"
    },
    {
      "path": "../../testing/mock-agent"
    },
    {
      "path": "../../testing/registry-mock"
    },
    {
      "path": "../../worker"
    },
    {
      "path": "../../workspace/project-manifest-reader"
    },
    {
      "path": "../../workspace/project-manifest-writer"
    },
    {
      "path": "../../workspace/projects-filter"
    },
    {
      "path": "../../workspace/projects-graph"
    },
    {
      "path": "../../workspace/projects-reader"
    },
    {
      "path": "../../workspace/projects-sorter"
    },
    {
      "path": "../../workspace/root-finder"
    },
    {
      "path": "../../workspace/state"
    },
    {
      "path": "../../workspace/workspace-manifest-writer"
    },
    {
      "path": "../context"
    },
    {
      "path": "../dedupe/check"
    },
    {
      "path": "../deps-installer"
    },
    {
      "path": "../env-installer"
    },
    {
      "path": "../modules-yaml"
    }
  ]
}

```

### installing/deps-installer/src/install/index.ts
```
import path from 'node:path'

import { linkBins, linkBinsOfPackages } from '@pnpm/bins.linker'
import { buildSelectedPkgs } from '@pnpm/building.after-install'
import { buildModules, type DepsStateCache, linkBinsOfDependencies } from '@pnpm/building.during-install'
import { createAllowBuildFunction, isBuildExplicitlyDisallowed } from '@pnpm/building.policy'
import { parseCatalogProtocol } from '@pnpm/catalogs.protocol-parser'
import { type CatalogResultMatcher, matchCatalogResolveResult, resolveFromCatalog } from '@pnpm/catalogs.resolver'
import type { Catalogs } from '@pnpm/catalogs.types'
import {
  LAYOUT_VERSION,
  LOCKFILE_MAJOR_VERSION,
  LOCKFILE_VERSION,
  WANTED_LOCKFILE,
} from '@pnpm/constants'
import {
  ignoredScriptsLogger,
  stageLogger,
  summaryLogger,
} from '@pnpm/core-loggers'
import { hashObjectNullableWithPrefix } from '@pnpm/crypto.object-hasher'
import * as dp from '@pnpm/deps.path'
import { PnpmError } from '@pnpm/error'
import {
  makeNodeRequireOption,
  runLifecycleHook,
  runLifecycleHooksConcurrently,
  type RunLifecycleHooksConcurrentlyOptions,
} from '@pnpm/exec.lifecycle'
import { getContext, type PnpmContext } from '@pnpm/installing.context'
import {
  type DependenciesGraph,
  type DependenciesGraphNode,
  getWantedDependencies,
  type PinnedVersion,
  resolveDependencies,
  type UpdateMatchingFunction,
  type WantedDependency,
} from '@pnpm/installing.deps-resolver'
import { extendProjectsWithTargetDirs, headlessInstall, type InstallationResultStats } from '@pnpm/installing.deps-restorer'
import { writeModulesManifest } from '@pnpm/installing.modules-yaml'
import {
  type CatalogSnapshots,
  cleanGitBranchLockfiles,
  getWantedLockfileName,
  isEmptyLockfile,
  type LockfileObject,
  type ProjectSnapshot,
  readWantedLockfileFile,
  writeCurrentLockfile,
  writeLockfiles,
  writeWantedLockfile,
} from '@pnpm/lockfile.fs'
import { getPreferredVersionsFromLockfileAndManifests } from '@pnpm/lockfile.preferred-versions'
import {
  calcPatchHashes,
  createOverridesMapFromParsed,
  getOutdatedLockfileSetting,
} from '@pnpm/lockfile.settings-checker'
import { writePnpFile } from '@pnpm/lockfile.to-pnp'
import { allProjectsAreUpToDate, satisfiesPackageManifest } from '@pnpm/lockfile.verification'
import { globalInfo, logger, streamParser } from '@pnpm/logger'
import { groupPatchedDependencies, type PatchGroupRecord } from '@pnpm/patching.config'
import { createVersionSpecFromResolvedVersion, getAllDependenciesFromManifest, getAllUniqueSpecs } from '@pnpm/pkg-manifest.utils'
import { parseWantedDependency } from '@pnpm/resolving.parse-wanted-dependency'
import type {
  PreferredVersions,
  ResolutionPolicyViolation,
} from '@pnpm/resolving.resolver-base'
import type {
  AllowBuild,
  DependenciesField,
  DependencyManifest,
  DepPath,
  IgnoredBuilds,
  PeerDependencyIssues,
  ProjectId,
  ProjectManifest,
  ProjectRootDir,
  ReadPackageHook,
} from '@pnpm/types'
import { lexCompare } from '@pnpm/util.lex-comparator'
import { safeReadProjectManifestOnly } from '@pnpm/workspace.project-manifest-reader'
import { isSubdir } from 'is-subdir'
import pLimit from 'p-limit'
import { clone, isEmpty, map as mapValues, pipeWith, props } from 'ramda'
import semver from 'semver'

import { parseWantedDependencies } from '../parseWantedDependencies.js'
import { removeDeps } from '../uninstall/removeDeps.js'
import { CatalogVersionMismatchError } from './checkCompatibility/CatalogVersionMismatchError.js'
import { checkCustomResolverForceResolve } from './checkCustomResolverForceResolve.js'
import {
  extendOptions,
  type InstallOptions,
  type ProcessedInstallOptions as StrictInstallOptions,
} from './extendInstallOptions.js'
import { linkPackages } from './link.js'
import { reportPeerDependencyIssues } from './reportPeerDependencyIssues.js'
import { validateModules } from './validateModules.js'
import { verifyLockfileResolutions } from './verifyLockfileResolutions.js'
import { writeLockfilesAndRecordVerified } from './writeLockfilesAndRecordVerified.js'
import { writeWantedLockfileAndRecordVerified } from './writeWantedLockfileAndRecordVerified.js'

class LockfileConfigMismatchError extends PnpmError {
  constructor (outdatedLockfileSettingName: string) {
    super('LOCKFILE_CONFIG_MISMATCH',
      `Cannot proceed with the frozen installation. The current "${outdatedLockfileSettingName!}" configuration doesn't match the value found in the lockfile`, {
        hint: 'Update your lockfile using "pnpm install --no-frozen-lockfile"',
      })
  }
}

const BROKEN_LOCKFILE_INTEGRITY_ERRORS = new Set([
  'ERR_PNPM_UNEXPECTED_PKG_CONTENT_IN_STORE',
  'ERR_PNPM_TARBALL_INTEGRITY',
])

const DEV_PREINSTALL = 'pnpm:devPreinstall'

interface InstallMutationOptions {
  update?: boolean
  updateToLatest?: boolean
  updateMatching?: UpdateMatchingFunction
  updatePackageManifest?: boolean
}

export interface InstallDepsMutation extends InstallMutationOptions {
  mutation: 'install'
  pruneDirectDependencies?: boolean
}

export interface InstallSomeDepsMutation extends InstallMutationOptions {
  allowNew?: boolean
  dependencySelectors: string[]
  mutation: 'installSome'
  peer?: boolean
  pruneDirectDependencies?: boolean
  pinnedVersion?: PinnedVersion
  targetDependenciesField?: DependenciesField
}

export interface UninstallSomeDepsMutation {
  mutation: 'uninstallSome'
  dependencyNames: string[]
  targetDependenciesField?: DependenciesField
}

export type DependenciesMutation = InstallDepsMutation | InstallSomeDepsMutation | UninstallSomeDepsMutation

type Opts = Omit<InstallOptions, 'allProjects'> & {
  preferredVersions?: PreferredVersions
  pruneDirectDependencies?: boolean
  binsDir?: string
} & InstallMutationOptions

export interface InstallResult {
  /**
   * A partial of new or updated catalog config entries. A change will be
   * produced if a dependency using the catalog protocol was newly added or
   * updated during this install. To obtain the full catalog, callers should
   * merge this object with the current catalog configs in pnpm-workspace.yaml.
   */
  updatedCatalogs: Catalogs | undefined
  updatedManifest: ProjectManifest
  ignoredBuilds: IgnoredBuilds | undefined
  /** Forwarded from {@link MutateModulesResult.resolutionPolicyViolations}. */
  resolutionPolicyViolations: ResolutionPolicyViolation[]
}

export async function install (
  manifest: ProjectManifest,
  opts: Opts
): Promise<InstallResult> {
  const rootDir = (opts.dir ?? process.cwd()) as ProjectRootDir

  // When a pnpr server is configured, use server-side resolution
  // instead of the normal resolution flow.
  if (opts.pnprServer) {
    return installViaPnprServer(manifest, rootDir, opts)
  }

  const { updatedCatalogs, updatedProjects: projects, ignoredBuilds, resolutionPolicyViolations } = await mutateModules(
    [
      {
        mutation: 'install',
        pruneDirectDependencies: opts.pruneDirectDependencies,
        rootDir,
        update: opts.update,
        updateMatching: opts.updateMatching,
        updateToLatest: opts.updateToLatest,
        updatePackageManifest: opts.updatePackageManifest,
      },
    ],
    {
      ...opts,
      allProjects: [{
        buildIndex: 0,
        manifest,
        rootDir,
        binsDir: opts.binsDir,
      }],
    }
  )
  return { updatedCatalogs, updatedManifest: projects[0].manifest, ignoredBuilds, resolutionPolicyViolations }
}

interface ProjectToBeInstalled {
  id: string
  buildIndex: number
  manifest: ProjectManifest
  modulesDir: string
  rootDir: ProjectRootDir
}

export type MutatedProject = DependenciesMutation & { rootDir: ProjectRootDir }

export type MutateModulesOptions = InstallOptions & {
  preferredVersions?: PreferredVersions
  hooks?: {
    readPackage?: ReadPackageHook[] | ReadPackageHook
  } | InstallOptions['hooks']
}

export interface MutateModulesInSingleProjectResult {
  updatedCatalogs: Catalogs | undefined
  updatedProject: UpdatedProject
  ignoredBuilds: IgnoredBuilds | undefined
  /** Forwarded from {@link MutateModulesResult.resolutionPolicyViolations}. */
  resolutionPolicyViolations: ResolutionPolicyViolation[]
}

export async function mutateModulesInSingleProject (
  project: MutatedProject & {
    binsDir?: string
    manifest: ProjectManifest
    rootDir: ProjectRootDir
    modulesDir?: string
  },
  maybeOpts: Omit<MutateModulesOptions, 'allProjects'> & InstallMutationOptions
): Promise<MutateModulesInSingleProjectResult> {
  const result = await mutateModules(
    [
      {
        ...project,
        update: maybeOpts.update,
        updateToLatest: maybeOpts.updateToLatest,
        updateMatching: maybeOpts.updateMatching,
        updatePackageManifest: maybeOpts.updatePackageManifest,
      } as MutatedProject,
    ],
    {
      ...maybeOpts,
      allProjects: [{
        buildIndex: 0,
        ...project,
      }],
    }
  )
  return {
    updatedCatalogs: result.updatedCatalogs,
    updatedProject: result.updatedProjects[0],
    ignoredBuilds: result.ignoredBuilds,
    resolutionPolicyViolations: result.resolutionPolicyViolations,
  }
}

export interface MutateModulesResult {
  updatedCatalogs?: Catalogs
  updatedProjects: UpdatedProject[]
  stats: InstallationResultStats
  depsRequiringBuild?: DepPath[]
  ignoredBuilds: IgnoredBuilds | undefined
  /**
   * Resolver-policy violations the post-resolution scan found in the
   * freshly-resolved lockfile. Each violation carries a verifier code
   * (e.g. `MINIMUM_RELEASE_AGE_VIOLATION`, `TRUST_DOWNGRADE`); the
   * install command filters by code to decide what to do (persist to
   * `minimumReleaseAgeExclude`, log, etc.). Empty array when no
   * verifier reported a violation or no policy was active.
   */
  resolutionPolicyViolations: ResolutionPolicyViolation[]
}

const pickCatalogSpecifier: CatalogResultMatcher<string | undefined> = {
  found: (found) =>
    found.resolution.specifier,
  misconfiguration: () => undefined,
  unused: () => undefined,
}

export async function mutateModules (
  projects: MutatedProject[],
  maybeOpts: MutateModulesOptions
): Promise<MutateModulesResult> {
  const reporter = maybeOpts?.reporter
  const detachReporter = (reporter != null) && typeof reporter === 'function'
    ? () => {
      streamParser.removeListener('data', reporter)
    }
    : () => {}
  if ((reporter != null) && typeof reporter === 'function') {
    streamParser.on('data', reporter)
  }

  const opts = extendOptions(maybeOpts)

  // When a pnpr server is configured, use server-side resolution. The pnpr server
  // path supports `install`, `installSome` (pnpm add), and `uninstallSome`
  // (pnpm remove). Mutations that need full client-side resolution (update
  // flags) still fall through to the normal flow.
  if (opts.pnprServer && canUsePnprForMutations(projects)) {
    const pnprResult = await mutateModulesViaPnpr(projects, opts)
    if (pnprResult) return pnprResult
  }

  const allowBuild = createAllowBuildFunction(opts)

  if (!opts.include.dependencies && opts.include.optionalDependencies) {
    throw new PnpmError('OPTIONAL_DEPS_REQUIRE_PROD_DEPS', 'Optional dependencies cannot be installed without production dependencies')
  }

  const installsOnly = allMutationsAreInstalls(projects)
  if (!installsOnly) opts.strictPeerDependencies = false
  const rootProjectManifest = opts.allProjects.find(({ rootDir }) => rootDir === opts.lockfileDir)?.manifest ??
    // When running install/update on a subset of projects, the root project might not be included,
    // so reading its manifest explicitly here.
    await safeReadProjectManifestOnly(opts.lockfileDir)

  let ctx = await getContext(opts)

  if (!opts.lockfileOnly && ctx.modulesFile != null) {
    const { purged } = await validateModules(ctx.modulesFile, Object.values(ctx.projects), {
      forceNewModules: installsOnly,
      include: opts.include,
      lockfileDir: opts.lockfileDir,
      modulesDir: opts.modulesDir ?? 'node_modules',
      registries: opts.registries,
      storeDir: opts.storeDir,
      virtualStoreDir: ctx.virtualStoreDir,
      virtualStoreDirMaxLength: opts.virtualStoreDirMaxLength,
      confirmModulesPurge: opts.confirmModulesPurge && !opts.ci,

      hoistPattern: opts.hoistPattern,
      currentHoistPattern: ctx.currentHoistPattern,

      publicHoistPattern: opts.publicHoistPattern,
      currentPublicHoistPattern: ctx.currentPublicHoistPattern,
      global: opts.global,
    })
    if (purged) {
      ctx = await getContext(opts)
    }
  }

  // Re-validate every entry in the lockfile against the policies the
  // resolver chain was built with (today: minimumReleaseAge in strict mode
  // via the npm verifier; the abstraction supports other resolvers
  // attaching their own verifiers). The threat model is a lockfile that
  // someone else resolved — committed to the repo, restored from a CI
  // cache, etc. — bypassing the local resolver's policy filters; the local
  // resolver's own filters already cover fresh resolution. We run this
  // exactly once, right after the lockfile is loaded from disk, before any
  // path branches.
  //
  // Skipped when we already know pacquet will run the install: pacquet's
  // frozen-install path applies the same resolver-policy gate (port of
  // this function), so re-running here would duplicate the work — and
  // for `minimumReleaseAge` in strict mode each lockfile entry is an
  // HTTP probe.
  //
  // The predicate mirrors every short-circuit `tryFrozenInstall` checks
  // before reaching the pacquet branch: anything that would make it
  // return null, throw, or fall through to the JS path must keep
  // verification on. The optimistic `preferFrozenLockfile` path decides
  // whether to delegate later (based on `allProjectsAreUpToDate`), which
  // isn't known here — so verification still runs in that window, the
  // duplicate is bounded to it.
  const willDelegateToPacquet = opts.runPacquet != null &&
    installsOnly &&
    !opts.lockfileOnly &&
    !opts.fixLockfile &&
    !opts.dedupe &&
    !ctx.lockfileHadConflicts &&
    ctx.existsNonEmptyWantedLockfile &&
    (opts.frozenLockfile === true || opts.frozenLockfileIfExists === true)
  if (!willDelegateToPacquet && !opts.trustLockfile) {
    const cacheActive = opts.cacheDir != null && opts.resolutionVerifiers.length > 0
    const wantedLockfilePath = cacheActive
      ? path.resolve(ctx.lockfileDir, await getWantedLockfileName({
        useGitBranchLockfile: opts.useGitBranchLockfile,
        mergeGitBranchLockfiles: opts.mergeGitBranchLockfiles,
      }))
      : undefined
    try {
      await verifyLockfileResolutions(ctx.wantedLockfile, opts.resolutionVerifiers, {
        cacheDir: opts.cacheDir,
        lockfilePath: wantedLockfilePath,
      })
    } catch (err) {
      // verifyLockfileResolutions is the one throw site in this function
      // that's part of normal user-facing operation (a rejected lockfile);
      // other throws here are unexpected. Detach the reporter listener so
      // long-lived processes don't leak it on every rejected install.
      detachReporter()
      throw err
    }
  }

  if (opts.hooks.preResolution) {
    for (const preResolution of opts.hooks.preResolution) {
      // eslint-disable-next-line no-await-in-loop
      await preResolution({
        currentLockfile: ctx.currentLockfile,
        wantedLockfile: ctx.wantedLockfile,
        existsCurrentLockfile: ctx.existsCurrentLockfile,
        existsNonEmptyWantedLockfile: ctx.existsNonEmptyWantedLockfile,
        lockfileDir: ctx.lockfileDir,
        storeDir: ctx.storeDir,
        registries: ctx.registries,
      })
    }
  }

  // Check if any custom resolvers want to force resolution for specific dependencies
  // Skip this check when not saving the lockfile (e.g., during deploy) since there's no point
  // in forcing re-resolution if we're not going to persist the results
  let forceResolutionFromHook = false
  const shouldCheckCustomResolverForceResolve =
    opts.hooks.customResolvers &&
    ctx.existsNonEmptyWantedLockfile &&
    !opts.frozenLockfile &&
    opts.saveLockfile
  if (shouldCheckCustomResolverForceResolve) {
    forceResolutionFromHook = await checkCustomResolverForceResolve(
      opts.hooks.customResolvers!,
      ctx.wantedLockfile
    )
  }

  const pruneVirtualStore = !opts.enableGlobalVirtualStore && (ctx.modulesFile?.prunedAt && opts.modulesCacheMaxAge > 0
    ? cacheExpired(ctx.modulesFile.prunedAt, opts.modulesCacheMaxAge)
    : true
  )

  if (!maybeOpts.ignorePackageManifest) {
    for (const { manifest, rootDir } of Object.values(ctx.projects)) {
      if (!manifest) {
        throw new Error(`No package.json found in "${rootDir}"`)
      }
    }
  }

  const result = await _install()

  // @ts-expect-error
  if (global['verifiedFileIntegrity'] > 1000) {
    // @ts-expect-error
    globalInfo(`The integrity of ${global['verifiedFileIntegrity']} files was checked. This might have caused installation to take longer.`)
  }

  if (opts.mergeGitBranchLockfiles) {
    await cleanGitBranchLockfiles(ctx.lockfileDir)
  }

  let ignoredBuilds = result.ignoredBuilds
  if (!opts.ignoreScripts && ignoredBuilds?.size) {
    ignoredBuilds = await runUnignoredDependencyBuilds(opts, ignoredBuilds, allowBuild)
  }
  // Detect packages whose build approval was revoked between the previous
  // and current install. A package is considered revoked when it was
  // previously allowed (true) but is now undecided (undefined). Packages
  // explicitly denied (false) are not added to ignoredBuilds, consistent
  // with how buildModules treats them.
  if (
    ctx.modulesFile?.allowBuilds &&
    ctx.wantedLockfile.packages &&
    Object.values(ctx.modulesFile.allowBuilds).some((v) => v === true)
  ) {
    const oldAllowBuild = createAllowBuildFunction({ allowBuilds: ctx.modulesFile.allowBuilds })
    if (oldAllowBuild) {
      for (const depPath of Object.keys(ctx.wantedLockfile.packages) as DepPath[]) {
        if (ignoredBuilds?.has(depPath)) continue
        const { name, version } = dp.parse(depPath)
        if (!name || !version) continue
        if (oldAllowBuild(name, version) === true && allowBuild?.(name, version) === undefined) {
          ignoredBuilds ??= new Set()
          ignoredBuilds.add(depPath)
        }
      }
    }
  }
  ignoredScriptsLogger.debug({
    packageNames: ignoredBuilds ? dedupePackageNamesFromIgnoredBuilds(ignoredBuilds) : [],
  })

  detachReporter()

  return {
    updatedCatalogs: result.updatedCatalogs,
    updatedProjects: result.updatedProjects,
    stats: result.stats ?? { added: 0, removed: 0, linkedToRoot: 0 },
    depsRequiringBuild: result.depsRequiringBuild,
    ignoredBuilds,
    resolutionPolicyViolations: result.resolutionPolicyViolations ?? [],
  }

  interface InnerInstallResult {
    readonly updatedCatalogs?: Catalogs
    readonly updatedProjects: UpdatedProject[]
    readonly stats?: InstallationResultStats
    readonly depsRequiringBuild?: DepPath[]
    readonly ignoredBuilds: IgnoredBuilds | undefined
    readonly resolutionPolicyViolations?: ResolutionPolicyViolation[]
  }

  async function _install (): Promise<InnerInstallResult> {
    const scriptsOpts: RunLifecycleHooksConcurrentlyOptions = {
      extraBinPaths: opts.extraBinPaths,
      extraNodePaths: ctx.extraNodePaths,
      extraEnv: opts.extraEnv,
      preferSymlinkedExecutables: opts.preferSymlinkedExecutables,
      userAgent: opts.userAgent,
      resolveSymlinksInInjectedDirs: opts.resolveSymlinksInInjectedDirs,
      scriptsPrependNodePath: opts.scriptsPrependNodePath,
      scriptShell: opts.scriptShell,
      shellEmulator: opts.shellEmulator,
      stdio: opts.ownLifecycleHooksStdio,
      storeController: opts.storeController,
      unsafePerm: opts.unsafePerm || false,
    }

    if (!opts.ignoreScripts && !opts.ignorePackageManifest && rootProjectManifest?.scripts?.[DEV_PREINSTALL]) {
      await runLifecycleHook(
        DEV_PREINSTALL,
        rootProjectManifest,
        {
          ...scriptsOpts,
          depPath: opts.lockfileDir,
          pkgRoot: opts.lockfileDir,
          rootModulesDir: ctx.rootModulesDir,
        }
      )
    }
    const packageExtensionsChecksum = hashObjectNullableWithPrefix(opts.packageExtensions)
    const pnpmfileChecksum = await opts.hooks.calculatePnpmfileChecksum?.()
    const patchedDependencies = opts.ignorePackageManifest
      ? ctx.wantedLockfile.patchedDependencies
      : (opts.patchedDependencies ? await calcPatchHashes(opts.patchedDependencies) : {})
    const patchGroupInput = opts.patchedDependencies
      ? Object.fromEntries(
        Object.entries(patchedDependencies ?? {}).map(([key, hash]) => {
          let patchFilePath = opts.patchedDependencies![key]
            ? path.resolve(opts.lockfileDir, opts.patchedDependencies![key])
            : undefined
          if (!patchFilePath) {
            const lastAt = key.lastIndexOf('@')
            const pkgName = lastAt > 0 ? key.slice(0, lastAt) : key
            if (opts.patchedDependencies![pkgName]) {
              patchFilePath = path.resolve(opts.lockfileDir, opts.patchedDependencies![pkgName])
            }
          }
          return [key, { hash, patchFilePath }]
        })
      )
      : patchedDependencies
    const patchGroups = patchGroupInput ? groupPatchedDependencies(patchGroupInput) : undefined
    const frozenLockfile = opts.frozenLockfile ||
      opts.frozenLockfileIfExists && ctx.existsNonEmptyWantedLockfile
    let outdatedLockfileSettings = false
    const overridesMap = createOverridesMapFromParsed(opts.parsedOverrides)
    if (!opts.ignorePackageManifest) {
      const outdatedLockfileSettingName = getOutdatedLockfileSetting(ctx.wantedLockfile, {
        autoInstallPeers: opts.autoInstallPeers,
        catalogs: opts.catalogs,
        dedupePeers: opts.dedupePeers || undefined,
        injectWorkspacePackages: opts.injectWorkspacePackages,
        excludeLinksFromLockfile: opts.excludeLinksFromLockfile,
        peersSuffixMaxLength: opts.peersSuffixMaxLength,
        overrides: overridesMap,
        ignoredOptionalDependencies: opts.ignoredOptionalDependencies?.sort(),
        packageExtensionsChecksum,
        patchedDependencies,
        pnpmfileChecksum,
      })
      outdatedLockfileSettings = outdatedLockfileSettingName != null
      if (frozenLockfile && outdatedLockfileSettings) {
        throw new LockfileConfigMismatchError(outdatedLockfileSettingName!)
      }
    }
    const _isWantedDepBareSpecifierSame = isWantedDepBareSpecifierSame.bind(null, ctx.wantedLockfile.catalogs, opts.catalogs)
    const upToDateLockfileMajorVersion = ctx.wantedLockfile.lockfileVersion.toString().startsWith(`${LOCKFILE_MAJOR_VERSION}.`)
    let needsFullResolution = outdatedLockfileSettings ||
      opts.fixLockfile ||
      opts.updateChecksums ||
      !upToDateLockfileMajorVersion ||
      opts.forceFullResolution ||
      forceResolutionFromHook
    if (needsFullResolution) {
      ctx.wantedLockfile.settings = {
        autoInstallPeers: opts.autoInstallPeers,
        dedupePeers: opts.dedupePeers || undefined,
        excludeLinksFromLockfile: opts.excludeLinksFromLockfile,
        peersSuffixMaxLength: opts.peersSuffixMaxLength,
        injectWorkspacePackages: opts.injectWorkspacePackages,
      }
      ctx.wantedLockfile.overrides = overridesMap
      ctx.wantedLockfile.packageExtensionsChecksum = packageExtensionsChecksum
      ctx.wantedLockfile.ignoredOptionalDependencies = opts.ignoredOptionalDependencies
      ctx.wantedLockfile.pnpmfileChecksum = pnpmfileChecksum
      ctx.wantedLockfile.patchedDependencies = patchedDependencies
    } else if (!frozenLockfile) {
      ctx.wantedLockfile.settings = {
        autoInstallPeers: opts.autoInstallPeers,
        dedupePeers: opts.dedupePeers || undefined,
        excludeLinksFromLockfile: opts.excludeLinksFromLockfile,
        peersSuffixMaxLength: opts.peersSuffixMaxLength,
        injectWorkspacePackages: opts.injectWorkspacePackages,
      }
    }

    const frozenInstallResult = await tryFrozenInstall({
      frozenLockfile,
      needsFullResolution,
      patchGroups,
      upToDateLockfileMajorVersion,
    })
    if (frozenInstallResult !== null) {
      if ('needsFullResolution' in frozenInstallResult) {
        needsFullResolution = frozenInstallResult.needsFullResolution
      } else {
        return frozenInstallResult
      }
    }

    const projectsToInstall = [] as ImporterToUpdate[]

    let preferredSpecs: Record<string, string> | null = null

    // TODO: make it concurrent
    /* eslint-disable no-await-in-loop */
    for (const project of projects) {
      const projectOpts = {
        ...project,
        ...ctx.projects[project.rootDir],
      }
      switch (project.mutation) {
        case 'uninstallSome':
          projectsToInstall.push({
            pruneDirectDependencies: false,
            ...projectOpts,
            removePackages: project.dependencyNames,
            updatePackageManifest: true,
            wantedDependencies: [],
          })
          break
        case 'install': {
          await installCase({
            ...projectOpts,
            updatePackageManifest: (projectOpts as InstallDepsMutation).updatePackageManifest ?? (projectOpts as InstallDepsMutation).update!,
          })
          break
        }
        case 'installSome': {
          await installSome({
            ...projectOpts as InstallSomeProject,
            updatePackageManifest: (projectOpts as InstallSomeDepsMutation).updatePackageManifest !== false,
          })
          break
        }
      }
    }
    /* eslint-enable no-await-in-loop */

    type InstallCaseProject = Pick<ImporterToUpdate,
    | 'binsDir'
    | 'buildIndex'
    | 'id'
    | 'manifest'
    | 'modulesDir'
    | 'mutation'
    | 'rootDir'
    | 'updatePackageManifest'
    >

    async function installCase (project: InstallCaseProject) {
      const wantedDependencies = getWantedDependencies(project.manifest, {
        autoInstallPeers: opts.autoInstallPeers,
        includeDirect: opts.includeDirect,
      })
        .map((wantedDependency) => ({ ...wantedDependency, updateSpec: true }))
      if (opts.packageVulnerabilityAudit) {
        for (const dep of wantedDependencies) {
          let specifier: string | undefined = dep.bareSpecifier
          const catalogName = specifier ? parseCatalogProtocol(specifier) : null
          if (catalogName != null) {
            const catalogResult = resolveFromCatalog(opts.catalogs, { alias: dep.alias, bareSpecifier: specifier! })
            specifier = matchCatalogResolveResult(catalogResult, pickCatalogSpecifier)
          }
          const validVersion = semver.valid(specifier)
          // Only proceed if the specifier is a pinned version, not a range
          if (!validVersion) continue
          if (opts.packageVulnerabilityAudit.isVulnerable(dep.alias, validVersion)) {
            // If the current version is pinned and vulnerable, expand the specifier to a range
            // that will allow updating to a non-vulnerable, semver-compatible version, if available.
            if (catalogName != null && opts.catalogs?.[catalogName]) {
              // If a catalog is used, update the catalog entry so the resolver can find a
              // non-vulnerable version. The package.json keeps "catalog:" and the workspace manifest
              // gets updated.
              opts.catalogs = {
                ...opts.catalogs,
                [catalogName]: {
                  ...opts.catalogs[catalogName],
                  [dep.alias]: '^' + validVersion,
                },
              }
              // Set prevSpecifier to the original catalog specifier so the resolver
              // preserves the original pinning style (i.e. pinned stays pinned).
              dep.prevSpecifier = specifier
            } else {
              // If no catalog is used, we directly update the specifier.
              dep.bareSpecifier = '^' + validVersion
            }
          }
        }
      }

      if (ctx.wantedLockfile?.importers) {
        forgetResolutionsOfPrevWantedDeps(ctx.wantedLockfile.importers[project.id], wantedDependencies, _isWantedDepBareSpecifierSame)
      }
      if (opts.ignoreScripts && project.manifest?.scripts &&
        (project.manifest.scripts.preinstall != null ||
          project.manifest.scripts.install != null ||
          project.manifest.scripts.postinstall != null ||
          project.manifest.scripts.prepare)
      ) {
        ctx.pendingBuilds.push(project.id)
      }

      projectsToInstall.push({
        pruneDirectDependencies: false,
        ...project,
        wantedDependencies,
      } as ImporterToUpdate)
    }

    type InstallSomeProject = Pick<ImporterToUpdate,
    | 'binsDir'
    | 'buildIndex'
    | 'id'
    | 'manifest'
    | 'modulesDir'
    | 'mutation'
    | 'rootDir'
    | 'updatePackageManifest'
    > & Pick<InstallSomeDepsMutation,
    | 'allowNew'
    | 'dependencySelectors'
    | 'targetDependenciesField'
    | 'update'
    >

    async function installSome (project: InstallSomeProject) {
      const currentBareSpecifiers = opts.ignoreCurrentSpecifiers
        ? {}
        : getAllDependenciesFromManifest(project.manifest, { autoInstallPeers: opts.autoInstallPeers })
      const optionalDependencies = project.targetDependenciesField ? {} : project.manifest.optionalDependencies ?? {}
      const devDependencies = project.targetDependenciesField ? {} : project.manifest.devDependencies ?? {}
      if (preferredSpecs == null) {
        const manifests = []
        for (const versions of ctx.workspacePackages.values()) {
          for (const { manifest } of versions.values()) {
            manifests.push(manifest)
          }
        }
        preferredSpecs = getAllUniqueSpecs(manifests)
      }
      const wantedDeps = parseWantedDependencies(project.dependencySelectors, {
        allowNew: project.allowNew !== false,
        currentBareSpecifiers,
        defaultTag: opts.tag,
        dev: project.targetDependenciesField === 'devDependencies',
        devDependencies,
        optional: project.targetDependenciesField === 'optionalDependencies',
        optionalDependencies,
        updateWorkspaceDependencies: project.update,
        preferredSpecs,
        saveCatalogName: opts.saveCatalogName,
        overrides: opts.overrides,
        defaultCatalog: opts.catalogs?.default,
      })

      if (opts.catalogMode !== 'manual') {
        for (const wantedDep of wantedDeps) {
          // A `runtime:` specifier (e.g. node from `devEngines.runtime` or
          // `pnpm runtime set`) round-trips to `devEngines.runtime` through the
          // manifest writer, which only recognizes the `runtime:` protocol.
          // Promoting it into a catalog rewrites the entry to `catalog:`, which
          // breaks that round-trip and strands it in `devDependencies`.
          if (wantedDep.bareSpecifier?.startsWith('runtime:')) continue
          const perDepCatalogName = getPerDepCatalogName(wantedDep, opts.saveCatalogName)
          const catalogBareSpecifier = `catalog:${perDepCatalogName === 'default' ? '' : perDepCatalogName}`
          const catalog = resolveFromCatalog(opts.catalogs, { ...wantedDep, bareSpecifier: catalogBareSpecifier })
          const catalogDepSpecifier = matchCatalogResolveResult(catalog, pickCatalogSpecifier)

          if (
            !catalogDepSpecifier ||
            wantedDep.bareSpecifier === catalogBareSpecifier ||
            semver.valid(wantedDep.bareSpecifier) &&
            semver.valid(catalogDepSpecifier) &&
            semver.eq(wantedDep.bareSpecifier, catalogDepSpecifier)
          ) {
            wantedDep.saveCatalogName = perDepCatalogName
            continue
          }

          switch (opts.catalogMode) {
            case 'strict':
              throw new CatalogVersionMismatchError({ catalogDep: `${wantedDep.alias}@${catalogDepSpecifier}`, wantedDep: `${wantedDep.alias}@${wantedDep.bareSpecifier}` })

            case 'prefer':
              logger.warn({
                message: `Catalog version mismatch for "${wantedDep.alias}": using direct version "${wantedDep.bareSpecifier}" instead of catalog version "${catalogDepSpecifier}".`,
                prefix: opts.lockfileDir,
              })
          }
        }
      }

      projectsToInstall.push({
        pruneDirectDependencies: false,
        ...project,
        wantedDependencies: wantedDeps.map(wantedDep => ({ ...wantedDep, isNew: !currentBareSpecifiers[wantedDep.alias], updateSpec: true })),
      } as ImporterToUpdate)
    }

    // Unfortunately, the private lockfile may differ from the public one.
    // A user might run named installations on a project that has a pnpm-lock.yaml file before running a noop install
    const makePartialCurrentLockfile = !installsOnly && (
      ctx.existsNonEmptyWantedLockfile && !ctx.existsCurrentLockfile ||
      !ctx.currentLockfileIsUpToDate
    )
    const result = await installInContext(projectsToInstall, ctx, {
      ...opts,
      allowBuild,
      currentLockfileIsUpToDate: !ctx.existsNonEmptyWantedLockfile || ctx.currentLockfileIsUpToDate,
      makePartialCurrentLockfile,
      needsFullResolution,
      pruneVirtualStore,
      scriptsOpts,
      updateLockfileMinorVersion: true,
      patchedDependencies: patchGroups,
    })

    return {
      updatedCatalogs: result.updatedCatalogs,
      updatedProjects: result.projects,
      stats: result.stats,
      depsRequiringBuild: result.depsRequiringBuild,
      ignoredBuilds: result.ignoredBuilds,
      resolutionPolicyViolations: result.resolutionPolicyViolations,
    }
  }

  /**
   * Attempt to perform a "frozen install".
   *
   * A "frozen install" will be performed if:
   *
   *   1. The --frozen-lockfile flag was explicitly specified or evaluates to
   *      true based on conditions like running on CI.
   *   2. No workspace modifications have been made that would invalidate the
   *      pnpm-lock.yaml file. In other words, the pnpm-lock.yaml file is
   *      known to be "up-to-date".
   *
   * A frozen install is significantly faster since the pnpm-lock.yaml file
   * can treated as immutable, skipping expensive lookups to acquire new
   * dependencies. For this reason, a frozen install should be performed even
   * if --frozen-lockfile wasn't explicitly specified. This allows users to
   * benefit from the increased performance of a frozen install automatically.
   *
   * If a frozen install is not possible, this function will return null.
   * This indicates a standard mutable install needs to be performed.
   *
   * Note this function may update the pnpm-lock.yaml file if the lockfile was
   * on a different major version, needs to be merged due to git conflicts,
   * etc. These changes update the format of the pnpm-lock.yaml file, but do
   * not change recorded dependency resolutions.
   */
  async function tryFrozenInstall ({
    frozenLockfile,
    needsFullResolution,
    patchGroups,
    upToDateLockfileMajorVersion,
  }: {
    frozenLockfile: boolean
    needsFullResolution: boolean
    patchGroups?: PatchGroupRecord
    upToDateLockfileMajorVersion: boolean
  }): Promise<InnerInstallResult | { needsFullResolution: boolean } | null> {
    const isFrozenInstallPossible =
      // A frozen install is never possible when any of these are true:
      !ctx.lockfileHadConflicts &&
      !opts.fixLockfile &&
      !opts.dedupe &&

      installsOnly &&
      (
        // If the user explicitly requested a frozen lockfile install, attempt
        // to perform one. An error will be thrown if updates are required.
        frozenLockfile ||

        // Otherwise, check if a frozen-like install is possible for
        // performance. This will be the case if all projects are up-to-date.
        opts.ignorePackageManifest ||
        !needsFullResolution &&
        opts.preferFrozenLockfile &&
        (!opts.pruneLockfileImporters || Object.keys(ctx.wantedLockfile.importers).length === Object.keys(ctx.projects).length) &&
        !isEmptyLockfile(ctx.wantedLockfile) &&
        ctx.wantedLockfile.lockfileVersion === LOCKFILE_VERSION &&
        await allProjectsAreUpToDate(Object.values(ctx.projects), {
          catalogs: opts.catalogs,
          autoInstallPeers: opts.autoInstallPeers,
          excludeLinksFromLockfile: opts.excludeLinksFromLockfile,
          linkWorkspacePackages: opts.linkWorkspacePackagesDepth >= 0,
          wantedLockfile: ctx.wantedLockfile,
          workspacePackages: ctx.workspacePackages,
          lockfileDir: opts.lockfileDir,
        })
      )

    if (!isFrozenInstallPossible) {
      return null
    }

    if (needsFullResolution) {
      throw new PnpmError('FROZEN_LOCKFILE_WITH_OUTDATED_LOCKFILE',
        'Cannot perform a frozen installation because the version of the lockfile is incompatible with this version of pnpm',
        {
          hint: `Try either:
1. Aligning the version of pnpm that generated the lockfile with the version that installs from it, or
2. Migrating the lockfile so that it is compatible with the newer version of pnpm, or
3. Using "pnpm install --no-frozen-lockfile".
Note that in CI environments, this setting is enabled by default.`,
        }
      )
    }
    if (!opts.ignorePackageManifest) {
      // `--frozen-lockfile` (the CI default) means "fail if pnpm-lock.yaml is
      // out of sync." Treat its absence as a sync failure even when the
      // synthesized snapshot from node_modules/.pnpm/lock.yaml would satisfy
      // the manifest — the developer needs to commit the regenerated file.
      if (frozenLockfile && !ctx.existsWantedLockfile &&
        Object.values(ctx.projects).some((project) => pkgHasDependencies(project.manifest))) {
        throw new PnpmError('NO_LOCKFILE',
          `Cannot install with "frozen-lockfile" because ${WANTED_LOCKFILE} is absent`, {
            hint: 'Note that in CI environments this setting is true by default. If you still need to run install in such cases, use "pnpm install --no-frozen-lockfile"',
          })
      }
      const _satisfiesPackageManifest = satisfiesPackageManifest.bind(null, {
        autoInstallPeers: opts.autoInstallPeers,
        excludeLinksFromLockfile: opts.excludeLinksFromLockfile,
      })
      for (const { id, manifest, rootDir } of Object.values(ctx.projects)) {
        const { satisfies, detailedReason } = _satisfiesPackageManifest(ctx.wantedLockfile.importers[id], manifest)
        if (!satisfies) {
          if (!ctx.existsWantedLockfile) {
            throw new PnpmError('NO_LOCKFILE',
              `Cannot install with "frozen-lockfile" because ${WANTED_LOCKFILE} is absent`, {
                hint: 'Note that in CI environments this setting is true by default. If you still need to run install in such cases, use "pnpm install --no-frozen-lockfile"',
              })
          }

          throw new PnpmError('OUTDATED_LOCKFILE',
            `Cannot install with "frozen-lockfile" because ${WANTED_LOCKFILE} is not up to date with ` +
            path.join('<ROOT>', path.relative(opts.lockfileDir, path.join(rootDir, 'package.json'))), {
              hint: `Note that in CI environments this setting is true by default. If you still need to run install in such cases, use "pnpm install --no-frozen-lockfile"

  Failure reason:
  ${detailedReason ?? ''}`,
            })
        }
      }
    }
    if (opts.lockfileOnly) {
      // The lockfile will only be changed if the workspace will have new projects with no dependencies.
      await writeWantedLockfile(ctx.lockfileDir, ctx.wantedLockfile)
      return {
        updatedProjects: projects.map((mutatedProject) => ctx.projects[mutatedProject.rootDir]),
        ignoredBuilds: undefined,
      }
    }
    if (isEmptyLockfile(ctx.wantedLockfile)) {
      if (Object.values(ctx.projects).some((project) => pkgHasDependencies(project.manifest))) {
      
... [truncated, file is 102000 chars]
```

### installing/deps-installer/src/install/link.ts
```
import { promises as fs } from 'node:fs'
import path from 'node:path'

import {
  progressLogger,
  stageLogger,
  statsLogger,
} from '@pnpm/core-loggers'
import { calcDepState, type DepsStateCache, findRuntimeNodeVersion } from '@pnpm/deps.graph-hasher'
import { symlinkDependency } from '@pnpm/fs.symlink-dependency'
import type {
  DependenciesGraph,
  DependenciesGraphNode,
  LinkedDependency,
} from '@pnpm/installing.deps-resolver'
import type { InstallationResultStats } from '@pnpm/installing.deps-restorer'
import { linkDirectDeps } from '@pnpm/installing.linking.direct-dep-linker'
import { hoist, type HoistedWorkspaceProject } from '@pnpm/installing.linking.hoist'
import { prune } from '@pnpm/installing.linking.modules-cleaner'
import type { IncludedDependencies } from '@pnpm/installing.modules-yaml'
import {
  filterLockfileByImporters,
} from '@pnpm/lockfile.filtering'
import type { LockfileObject } from '@pnpm/lockfile.fs'
import { logger } from '@pnpm/logger'
import type { StoreController, TarballResolution } from '@pnpm/store.controller-types'
import type {
  AllowBuild,
  DepPath,
  HoistedDependencies,
  ProjectId,
  Registries,
  SupportedArchitectures,
} from '@pnpm/types'
import { symlinkAllModules } from '@pnpm/worker'
import pLimit from 'p-limit'
import { pathExists } from 'path-exists'
import { difference, equals, isEmpty, pick, pickBy, props } from 'ramda'

import type { ImporterToUpdate } from './index.js'

const brokenModulesLogger = logger('_broken_node_modules')

export interface LinkPackagesOptions {
  allowBuild?: AllowBuild
  currentLockfile: LockfileObject
  dedupeDirectDeps: boolean
  dependenciesByProjectId: Record<string, Map<string, DepPath>>
  disableRelinkLocalDirDeps?: boolean
  force: boolean
  depsStateCache: DepsStateCache
  enableGlobalVirtualStore: boolean
  extraNodePaths: string[]
  hoistedDependencies: HoistedDependencies
  hoistedModulesDir: string
  hoistPattern?: string[]
  ignoreScripts: boolean
  publicHoistPattern?: string[]
  include: IncludedDependencies
  linkedDependenciesByProjectId: Record<string, LinkedDependency[]>
  lockfileDir: string
  makePartialCurrentLockfile: boolean
  outdatedDependencies: Record<string, string>
  pruneStore: boolean
  pruneVirtualStore: boolean
  registries: Registries
  rootModulesDir: string
  sideEffectsCacheRead: boolean
  symlink: boolean
  skipped: Set<DepPath>
  skipRuntimes?: boolean
  storeController: StoreController
  virtualStoreDir: string
  virtualStoreDirMaxLength: number
  wantedLockfile: LockfileObject
  wantedToBeSkippedPackageIds: Set<string>
  hoistWorkspacePackages?: boolean
  virtualStoreOnly: boolean
  supportedArchitectures?: SupportedArchitectures
}

export interface LinkPackagesResult {
  currentLockfile: LockfileObject
  newDepPaths: DepPath[]
  newHoistedDependencies: HoistedDependencies
  removedDepPaths: Set<string>
  stats: InstallationResultStats
}

export async function linkPackages (projects: ImporterToUpdate[], depGraph: DependenciesGraph, opts: LinkPackagesOptions): Promise<LinkPackagesResult> {
  let depNodes = Object.values(depGraph).filter(({ depPath, id }) => {
    if (((opts.wantedLockfile.packages?.[depPath]) != null) && !opts.wantedLockfile.packages[depPath].optional) {
      opts.skipped.delete(depPath)
      return true
    }
    if (opts.wantedToBeSkippedPackageIds.has(id)) {
      opts.skipped.add(depPath)
      return false
    }
    opts.skipped.delete(depPath)
    return true
  })
  if (!opts.include.dependencies) {
    depNodes = depNodes.filter(({ dev, optional }) => dev || optional)
  }
  if (!opts.include.devDependencies) {
    depNodes = depNodes.filter(({ optional, prod }) => prod || optional)
  }
  if (!opts.include.optionalDependencies) {
    depNodes = depNodes.filter(({ optional }) => !optional)
  }
  depGraph = Object.fromEntries(depNodes.map((depNode) => [depNode.depPath, depNode]))
  const removedDepPaths = await prune(projects, {
    currentLockfile: opts.currentLockfile,
    dedupeDirectDeps: opts.dedupeDirectDeps,
    hoistedDependencies: opts.hoistedDependencies,
    hoistedModulesDir: (opts.hoistPattern != null) ? opts.hoistedModulesDir : undefined,
    include: opts.include,
    lockfileDir: opts.lockfileDir,
    pruneStore: opts.pruneStore,
    pruneVirtualStore: opts.pruneVirtualStore,
    publicHoistedModulesDir: (opts.publicHoistPattern != null) ? opts.rootModulesDir : undefined,
    skipped: opts.skipped,
    skipRuntimes: opts.skipRuntimes,
    storeController: opts.storeController,
    virtualStoreDir: opts.virtualStoreDir,
    virtualStoreDirMaxLength: opts.virtualStoreDirMaxLength,
    wantedLockfile: opts.wantedLockfile,
  })

  stageLogger.debug({
    prefix: opts.lockfileDir,
    stage: 'importing_started',
  })

  const projectIds = projects.map(({ id }) => id)
  const filterOpts = {
    include: opts.include,
    registries: opts.registries,
    skipped: opts.skipped,
    skipRuntimes: opts.skipRuntimes,
  }
  const newCurrentLockfile = filterLockfileByImporters(opts.wantedLockfile, projectIds, {
    ...filterOpts,
    failOnMissingDependencies: true,
    skipped: new Set(),
  })
  const { newDepPaths, added } = await linkNewPackages(
    filterLockfileByImporters(opts.currentLockfile, projectIds, {
      ...filterOpts,
      failOnMissingDependencies: false,
    }),
    newCurrentLockfile,
    depGraph,
    {
      allowBuild: opts.allowBuild,
      disableRelinkLocalDirDeps: opts.disableRelinkLocalDirDeps,
      enableGlobalVirtualStore: opts.enableGlobalVirtualStore,
      force: opts.force,
      depsStateCache: opts.depsStateCache,
      ignoreScripts: opts.ignoreScripts,
      lockfileDir: opts.lockfileDir,
      optional: opts.include.optionalDependencies,
      sideEffectsCacheRead: opts.sideEffectsCacheRead,
      symlink: opts.symlink,
      skipped: opts.skipped,
      storeController: opts.storeController,
      supportedArchitectures: opts.supportedArchitectures,
      virtualStoreDir: opts.virtualStoreDir,
    }
  )

  stageLogger.debug({
    prefix: opts.lockfileDir,
    stage: 'importing_done',
  })

  let currentLockfile: LockfileObject
  const allImportersIncluded = equals(projectIds.sort(), Object.keys(opts.wantedLockfile.importers).sort())
  if (
    opts.makePartialCurrentLockfile ||
    !allImportersIncluded
  ) {
    const packages = opts.currentLockfile.packages ?? {}
    if (opts.wantedLockfile.packages != null) {
      for (const depPath in opts.wantedLockfile.packages) { // eslint-disable-line:forin
        if (depGraph[depPath as DepPath]) {
          packages[depPath as DepPath] = opts.wantedLockfile.packages[depPath as DepPath]
        }
      }
    }
    const projects = {
      ...opts.currentLockfile.importers,
      ...pick(projectIds, opts.wantedLockfile.importers),
    }
    currentLockfile = filterLockfileByImporters(
      {
        ...opts.wantedLockfile,
        importers: projects,
        packages,
      },
      Object.keys(projects) as ProjectId[], {
        ...filterOpts,
        failOnMissingDependencies: false,
        skipped: new Set(),
      }
    )
  } else if (
    opts.include.dependencies &&
    opts.include.devDependencies &&
    opts.include.optionalDependencies &&
    opts.skipped.size === 0
  ) {
    currentLockfile = opts.wantedLockfile
  } else {
    currentLockfile = newCurrentLockfile
  }

  let newHoistedDependencies!: HoistedDependencies
  if (opts.virtualStoreOnly || (opts.hoistPattern == null && opts.publicHoistPattern == null)) {
    newHoistedDependencies = {}
  } else if (newDepPaths.length > 0 || removedDepPaths.size > 0) {
    newHoistedDependencies = {
      ...opts.hoistedDependencies,
      ...await hoist({
        extraNodePath: opts.extraNodePaths,
        graph: depGraph,
        directDepsByImporterId: {
          ...opts.dependenciesByProjectId,
          '.': new Map(Array.from(opts.dependenciesByProjectId['.']?.entries() ?? []).filter(([alias]) => {
            return newCurrentLockfile.importers['.' as ProjectId].specifiers[alias]
          })),
        },
        importerIds: projectIds,
        privateHoistedModulesDir: opts.hoistedModulesDir,
        privateHoistPattern: opts.hoistPattern ?? [],
        publicHoistedModulesDir: opts.rootModulesDir,
        publicHoistPattern: opts.publicHoistPattern ?? [],
        virtualStoreDir: opts.virtualStoreDir,
        virtualStoreDirMaxLength: opts.virtualStoreDirMaxLength,
        hoistedWorkspacePackages: opts.hoistWorkspacePackages
          ? projects.reduce((hoistedWorkspacePackages, project) => {
            if (project.manifest.name && project.id !== '.') {
              hoistedWorkspacePackages[project.id] = {
                dir: project.rootDir,
                name: project.manifest.name,
              }
            }
            return hoistedWorkspacePackages
          }, {} as Record<string, HoistedWorkspaceProject>)
          : undefined,
        skipped: opts.skipped,
      }),
    }
  } else {
    newHoistedDependencies = opts.hoistedDependencies
  }

  let linkedToRoot = 0
  if (opts.symlink && !opts.virtualStoreOnly) {
    const projectsToLink = Object.fromEntries(await Promise.all(
      projects.map(async ({ id, manifest, modulesDir, rootDir }) => {
        const deps = opts.dependenciesByProjectId[id]
        const importerFromLockfile = newCurrentLockfile.importers[id]
        return [id, {
          dir: rootDir,
          modulesDir,
          dependencies: await Promise.all([
            ...Array.from(deps.entries())
              .filter(([rootAlias]) => importerFromLockfile.specifiers[rootAlias])
              .map(([rootAlias, depPath]) => ({ rootAlias, depGraphNode: depGraph[depPath] }))
              .filter(({ depGraphNode }) => depGraphNode)
              .map(async ({ rootAlias, depGraphNode }) => {
                const isDev = Boolean(manifest.devDependencies?.[depGraphNode.name])
                const isOptional = Boolean(manifest.optionalDependencies?.[depGraphNode.name])
                return {
                  alias: rootAlias,
                  name: depGraphNode.name,
                  version: depGraphNode.version,
                  dir: depGraphNode.dir,
                  id: depGraphNode.id,
                  dependencyType: (isDev && 'dev' || isOptional && 'optional' || 'prod') as 'dev' | 'optional' | 'prod',
                  latest: opts.outdatedDependencies[depGraphNode.id],
                  isExternalLink: false,
                }
              }),
            ...opts.linkedDependenciesByProjectId[id].map(async (linkedDependency) => {
              const dir = resolvePath(rootDir, linkedDependency.resolution.directory)
              return {
                alias: linkedDependency.alias,
                name: linkedDependency.name,
                version: linkedDependency.version,
                dir,
                id: linkedDependency.resolution.directory,
                dependencyType: (linkedDependency.dev && 'dev' || linkedDependency.optional && 'optional' || 'prod') as 'dev' | 'optional' | 'prod',
                isExternalLink: true,
              }
            }),
          ]),
        }]
      }))
    )
    linkedToRoot = await linkDirectDeps(projectsToLink, { dedupe: opts.dedupeDirectDeps })
  }

  return {
    currentLockfile,
    newDepPaths,
    newHoistedDependencies,
    removedDepPaths,
    stats:
... [truncated, file is 19744 chars]
```

### installing/deps-installer/src/install/recordLockfileVerified.ts
[omitted: context budget exhausted]

### installing/deps-installer/src/install/verifyLockfileResolutions.ts
[omitted: context budget exhausted]

### installing/deps-restorer/src/index.ts
[omitted: context budget exhausted]

### installing/deps-restorer/src/linkHoistedModules.ts
[omitted: context budget exhausted]

### lockfile/fs/src/lockfileFormatConverters.ts
[omitted: context budget exhausted]

### lockfile/utils/src/index.ts
[omitted: context budget exhausted]

### lockfile/utils/src/toLockfileResolution.ts
[omitted: context budget exhausted]

### pacquet/crates/git-fetcher/src/fetcher.rs
[omitted: context budget exhausted]

### pacquet/crates/git-fetcher/src/fetcher/tests.rs
[omitted: context budget exhausted]

### pacquet/crates/git-fetcher/src/prepare_package.rs
[omitted: context budget exhausted]

### pacquet/crates/git-fetcher/src/prepare_package/tests.rs
[omitted: context budget exhausted]

### pacquet/crates/git-fetcher/src/tarball_fetcher.rs
[omitted: context budget exhausted]

### pacquet/crates/git-fetcher/src/tarball_fetcher/tests.rs
[omitted: context budget exhausted]

### pacquet/crates/lockfile-verification/src/errors.rs
[omitted: context budget exhausted]

### pacquet/crates/lockfile-verification/src/lib.rs
[omitted: context budget exhausted]

### pacquet/crates/lockfile-verification/src/record_lockfile_verified.rs
[omitted: context budget exhausted]

### pacquet/crates/lockfile-verification/src/verify_lockfile_resolutions.rs
[omitted: context budget exhausted]

### pacquet/crates/lockfile-verification/src/verify_lockfile_resolutions/tests.rs
[omitted: context budget exhausted]

### pacquet/crates/lockfile/src/resolution.rs
[omitted: context budget exhausted]

### pacquet/crates/package-manager/src/build_modules.rs
[omitted: context budget exhausted]

### pacquet/crates/package-manager/src/build_modules/tests.rs
[omitted: context budget exhausted]

### pacquet/crates/package-manager/src/install_package_by_snapshot.rs
[omitted: context budget exhausted]

### pacquet/crates/package-manager/src/virtual_store_layout.rs
[omitted: context budget exhausted]

### pacquet/crates/package-manager/src/virtual_store_layout/tests.rs
[omitted: context budget exhausted]

### pnpm-lock.yaml
[omitted: context budget exhausted]

### pnpm-workspace.yaml
[omitted: context budget exhausted]

### resolving/git-resolver/src/createGitHostedPkgId.ts
[omitted: context budget exhausted]
Callers & Entry Points (How public input reaches the modified code)
### installing/commands/src/add.ts
```
import type { CommandHandlerMap } from '@pnpm/cli.command'
import { FILTERING, OPTIONS, UNIVERSAL_OPTIONS } from '@pnpm/cli.common-cli-options-help'
import { docsUrl } from '@pnpm/cli.utils'
import { types as allTypes } from '@pnpm/config.reader'
import { writeSettings } from '@pnpm/config.writer'
import { PnpmError } from '@pnpm/error'
import { handleGlobalAdd } from '@pnpm/global.commands'
import { resolveConfigDeps } from '@pnpm/installing.env-installer'
import { createStoreController } from '@pnpm/store.connection-manager'
import { pick } from 'ramda'
import { renderHelp } from 'render-help'

import { getFetchFullMetadata } from './getFetchFullMetadata.js'
import type { InstallCommandOptions } from './install.js'
import { installDeps } from './installDeps.js'
import { createGlobalPolicyCallbacks } from './resolutionPolicyManifest.js'

export const shorthands: Record<string, string> = {
  'save-catalog': '--save-catalog-name=default',
  d: '--save-dev',
  e: '--save-exact',
  o: '--save-optional',
  p: '--save-prod',
}

export function rcOptionsTypes (): Record<string, unknown> {
  return pick([
    'cache-dir',
    'cpu',
    'child-concurrency',
    'dangerously-allow-all-builds',
    'engine-strict',
    'fetch-retries',
    'fetch-retry-factor',
    'fetch-retry-maxtimeout',
    'fetch-retry-mintimeout',
    'fetch-timeout',
    'force',
    'global-bin-dir',
    'global-dir',
    'global-pnpmfile',
    'global',
    'hoist',
    'hoist-pattern',
    'hoisting-limits',
    'https-proxy',
    'ignore-pnpmfile',
    'ignore-scripts',
    'ignore-workspace-root-check',
    'libc',
    'link-workspace-packages',
    'lockfile-dir',
    'lockfile-only',
    'lockfile',
    'modules-dir',
    'network-concurrency',
    'node-linker',
    'noproxy',
    'npm-path',
    'os',
    'package-import-method',
    'pnpmfile',
    'prefer-offline',
    'production',
    'proxy',
    'public-hoist-pattern',
    'registry',
    'reporter',
    'save-catalog-name',
    'save-dev',
    'save-exact',
    'save-optional',
    'save-peer',
    'save-prefix',
    'save-prod',
    'save-workspace-protocol',
    'shamefully-hoist',
    'shared-workspace-lockfile',
    'side-effects-cache-readonly',
    'side-effects-cache',
    'store-dir',
    'strict-peer-dependencies',
    'trust-lockfile',
    'trust-policy',
    'trust-policy-exclude',
    'trust-policy-ignore-after',
    'unsafe-perm',
    'offline',
    'only',
    'optional',
    'verify-store-integrity',
    'virtual-store-dir',
  ], allTypes)
}

export function cliOptionsTypes (): Record<string, unknown> {
  return {
    ...rcOptionsTypes(),
    'allow-build': [String, Array],
    recursive: Boolean,
    save: Boolean,
    workspace: Boolean,
    config: Boolean,
  }
}

export const commandNames = ['add']

export function help (): string {
  return renderHelp({
    description: 'Installs a package and any packages that it depends on.',
    descriptionLists: [
      {
        title: 'Options',

        list: [
          {
            description: 'Save package to your `dependencies`. The default behavior',
            name: '--save-prod',
            shortAlias: '-p',
          },
          {
            description: 'Save package to your `devDependencies`',
            name: '--save-dev',
            shortAlias: '-d',
          },
          {
            description: 'Save package to your `optionalDependencies`',
            name: '--save-optional',
            shortAlias: '-o',
          },
          {
            description: 'Save package to your `peerDependencies` and `devDependencies`',
            name: '--save-peer',
          },
          {
            description: 'Save package to the default catalog',
            name: '--save-catalog',
          },
          {
            description: 'Save package to the specified catalog',
            name: '--save-catalog-name=<name>',
          },
          {
            description: 'Install exact version',
            name: '--[no-]save-exact',
            shortAlias: '-e',
          },
          {
            description: 'Save packages from the workspace with a "workspace:" protocol. True by default',
            name: '--[no-]save-workspace-protocol',
          },
          {
            description: 'Install as a global package',
            name: '--global',
            shortAlias: '-g',
          },
          {
            description: 'Run installation recursively in every package found in subdirectories \
or in every workspace package, when executed inside a workspace. \
For options that may be used with `-r`, see "pnpm help recursive"',
            name: '--recursive',
            shortAlias: '-r',
          },
          {
            description: 'Only adds the new dependency if it is found in the workspace',
            name: '--workspace',
          },
          {
            description: 'Save the dependency to configurational dependencies',
            name: '--config',
          },
          OPTIONS.ignoreScripts,
          OPTIONS.offline,
          OPTIONS.preferOffline,
          {
            description: 'The registry to use for the installation',
            name: '--registry <url>',
          },
          OPTIONS.storeDir,
          OPTIONS.virtualStoreDir,
          OPTIONS.globalDir,
          ...UNIVERSAL_OPTIONS,
          {
            description: 'A list of package names that are allowed to run postinstall scripts during installation',
            name: '--allow-build',
          },
        ],
      },
      FILTERING,
    ],
    url: docsUrl('add'),
    usages: [
      'pnpm add <name>',
      'pnpm add <name>@<tag>',
      'pnpm add <name>@<version>',
      'pnpm add <name>@<version range>',
      'pnpm add <git host>:<git user>/<repo name>',
      'pnpm add <git repo url>',
      'pnpm add <tarball file>',
      'pnpm add <tarball url>',
      'pnpm add <dir>',
    ],
  })
}

export type AddCommandOptions = InstallCommandOptions & {
  allowBuild?: string[]
  allowNew?: boolean
  ignoreWorkspaceRootCheck?: boolean
  save?: boolean
  update?: boolean
  useBetaCli?: boolean
  workspaceRoot?: boolean
  config?: boolean
}

export async function handler (
  opts: AddCommandOptions,
  params: string[],
  commands?: CommandHandlerMap
): Promise<void> {
  if (opts.cliOptions['save'] === false) {
    throw new PnpmError('OPTION_NOT_SUPPORTED', 'The "add" command currently does not support the no-save option')
  }
  if (!params || (params.length === 0)) {
    throw new PnpmError('MISSING_PACKAGE_NAME', '`pnpm add` requires the package name')
  }
  if (opts.config) {
    const store = await createStoreController(opts)
    await resolveConfigDeps(params, {
      ...opts,
      store: store.ctrl,
      storeDir: store.dir,
      rootDir: opts.workspaceDir ?? opts.rootProjectManifestDir,
    })
    return
  }
  if (
    !opts.recursive &&
    opts.workspaceDir === opts.dir &&
    !opts.ignoreWorkspaceRootCheck &&
    !opts.workspaceRoot &&
    opts.workspacePackagePatterns &&
    opts.workspacePackagePatterns.length > 1
  ) {
    throw new PnpmError('ADDING_TO_ROOT',
      'Running this command will add the dependency to the workspace root, ' +
      'which might not be what you want - if you really meant it, ' +
      'make it explicit by running this command again with the -w flag (or --workspace-root). ' +
      'If you don\'t want to see this warning anymore, you may set the ignore-workspace-root-check setting to true.'
    )
  }
  if (opts.global) {
    if (!opts.bin) {
      throw new PnpmError('NO_GLOBAL_BIN_DIR', 'Unable to find the global bin directory', {
        hint: 'Run "pnpm setup" to create it automatically, or set the global-bin-dir setting, or the PNPM_HOME env variable. The global bin directory should be in the PATH.',
      })
    }
    if (params.includes('pnpm') || params.includes('@pnpm/exe')) {
      throw new PnpmError('GLOBAL_PNPM_INSTALL', 'Use the "pnpm self-update" command to install or update pnpm')
    }
    return handleGlobalAdd({
      ...opts,
      ...createGlobalPolicyCallbacks(opts),
    }, params, commands ?? {})
  }

  const include = {
    dependencies: opts.production !== false,
    devDependencies: opts.dev !== false,
    optionalDependencies: opts.optional !== false,
  }
  if (opts.allowBuild?.length) {
    if (opts.argv.original.includes('--allow-build')) {
      throw new PnpmError('ALLOW_BUILD_MISSING_PACKAGE', 'The --allow-build flag is missing a package name. Please specify the package name(s) that are allowed to run installation scripts.')
    }
    if (opts.allowBuilds) {
      const disallowedBuilds = Object.entries(opts.allowBuilds)
        .filter(([, value]) => value === false)
        .map(([pkg]) => pkg)
      const overlapDependencies = disallowedBuilds.filter((dep) => opts.allowBuild?.includes(dep))
      if (overlapDependencies.length) {
        throw new PnpmError('OVERRIDING_IGNORED_BUILT_DEPENDENCIES', `The following dependencies are ignored by the root project, but are allowed to be built by the current command: ${overlapDependencies.join(', ')}`, {
          hint: 'If you are sure you want to allow those dependencies to run installation scripts, remove them from the allowBuilds list (or change their value to true).',
        })
      }
    }
    const allowBuilds: Record<string, boolean> = {}
    for (const pkg of opts.allowBuild) {
      allowBuilds[pkg] = true
    }
    if (opts.rootProjectManifestDir) {
      opts.rootProjectManifest = opts.rootProjectManifest ?? {}
      await writeSettings({
        ...opts,
        workspaceDir: opts.workspaceDir ?? opts.rootProjectManifestDir,
        updatedSettings: {
          allowBuilds,
        },
      })
    }
    // Pass the allowed packages to allowBuilds so they can build during this install
    const mergedAllowBuilds = { ...opts.allowBuilds }
    for (const pkg of opts.allowBuild) {
      mergedAllowBuilds[pkg] = true
    }
    return installDeps({
      ...opts,
      allowBuilds: mergedAllowBuilds,
      rebuildHandler: commands?.rebuild,
      fetchFullMetadata: getFetchFullMetadata(opts),
      include,
      includeDirect: include,
    }, params)
  }
  return installDeps({
    ...opts,
    rebuildHandler: commands?.rebuild,
    fetchFullMetadata: getFetchFullMetadata(opts),
    include,
    includeDirect: include,
  }, params)
}

```

### resolving/npm-resolver/src/createNpmResolutionVerifier.ts
```
import { pickRegistryForPackage } from '@pnpm/config.pick-registry-for-package'
import { createPackageVersionPolicy } from '@pnpm/config.version-policy'
import { FULL_META_DIR } from '@pnpm/constants'
import { PnpmError } from '@pnpm/error'
import type { PackageInRegistry, PackageMeta } from '@pnpm/resolving.registry.types'
import type {
  Resolution,
  ResolutionVerifier,
} from '@pnpm/resolving.resolver-base'
import type { PackageVersionPolicy, Registries, TrustPolicy } from '@pnpm/types'
import semver from 'semver'

import type { FetchMetadataFromFromRegistryOptions } from './fetch.js'
import { fetchAttestationPublishedAt } from './fetchAttestationPublishedAt.js'
import {
  fetchAbbreviatedMetadataCached,
  fetchFullMetadataCached,
  type FetchFullMetadataCachedOptions,
} from './fetchFullMetadataCached.js'
import { normalizeRegistryUrl } from './normalizeRegistryUrl.js'
import { BUILTIN_NAMED_REGISTRIES } from './parseBareSpecifier.js'
import type { PackageMetaCache } from './pickPackage.js'
import { getPkgMirrorPath, loadMeta, warnMissingTimeFieldOnce } from './pickPackage.js'
import { failIfTrustDowngraded } from './trustChecks.js'
import {
  MINIMUM_RELEASE_AGE_VIOLATION_CODE,
  TARBALL_URL_MISMATCH_VIOLATION_CODE,
  TRUST_DOWNGRADE_VIOLATION_CODE,
} from './violationCodes.js'

export interface CreateNpmResolutionVerifierOptions {
  /**
   * Minimum age (in minutes) a published version must reach before it is
   * accepted. When unset, the verifier is a no-op for the age check.
   */
  minimumReleaseAge?: number
  /**
   * Retained on the options bag because the resolver path branches on it
   * (the lowest-version fallback) and tests forward both fields together.
   * The verifier itself no longer gates on this flag — once the loose-mode
   * auto-collect makes every accepted-immature pin explicit in
   * `minimumReleaseAgeExclude`, running the verifier in loose mode is the
   * thing that proves the manifest stays in sync with the lockfile.
   */
  minimumReleaseAgeStrict?: boolean
  minimumReleaseAgeExclude?: string[]
  /**
   * When the registry's metadata lacks the per-version `time` field
   * (some self-hosted registries strip it), the verifier can't apply
   * the maturity cutoff. Set this to `true` to mirror the resolver's
   * `pickMatchingVersionFinal` warn-and-skip behavior — the verifier
   * passes the entry with a one-time `globalWarn`, instead of failing
   * closed. Defaults to `false` so the verifier stays stricter than
   * the resolver only when the user has explicitly opted in to the
   * skip on the resolver side.
   */
  ignoreMissingTimeField?: boolean
  /**
   * `'no-downgrade'` rejects a lockfile entry whose version has weaker
   * trust evidence (no attestations) than an earlier-published version
   * had. This mirrors the resolver-time `failIfTrustDowngraded` check
   * applied during fresh resolution — the verifier catches the same
   * supply-chain signal on entries that bypassed resolution (peek-path,
   * frozen lockfile, etc.).
   */
  trustPolicy?: TrustPolicy
  trustPolicyExclude?: string[]
  trustPolicyIgnoreAfter?: number
  registries: Registries
  /**
   * Registries reached via the named-registry resolver chain (e.g. `gh:` →
   * GitHub Packages). When a lockfile entry's tarball URL falls under one of
   * these registry base URLs, route the manifest fetch there instead of the
   * scope-derived default.
   */
  namedRegistries?: Record<string, string>
  /**
   * Cache-aware full-metadata fetcher. Decoupled from the resolver pipeline
   * so abbreviated metadata and `peekManifestFromStore` fast paths cannot
   * hide the publish timestamp.
   */
  fetchOpts: FetchMetadataFromFromRegistryOptions
  getAuthHeaderValueByURI: (registry: string) => string | undefined
  cacheDir?: FetchFullMetadataCachedOptions['cacheDir']
  /**
   * Per-install LRU shared with the npm resolver's `pickPackage`
   * (`{ get, set }` over `PackageMeta`). When provided, the verifier
   * consults it before fetching: a name the resolver already pulled
   * during the same install yields the cached packument instead of a
   * fresh disk/network round-trip. Optional — frozen-install paths and
   * unit tests don't have a resolver running alongside, in which case
   * the verifier falls back to its own fetch chain.
   */
  metaCache?: PackageMetaCache
  /** Overrides Date.now() for tests. */
  now?: number
}

/**
 * Returns a `ResolutionVerifier` for npm-registry-resolved lockfile
 * entries. It always binds each entry's recorded tarball URL to the
 * artifact the registry's metadata lists (an anti-tamper check that does
 * not depend on any policy), and additionally re-applies the
 * `minimumReleaseAge` and/or `trustPolicy='no-downgrade'` policies when
 * those are configured. Pairs with `createNpmResolver`: each resolver
 * factory may export a sibling verifier factory that the default-resolver
 * combines.
 *
 * Designed for fail-closed semantics: if the manifest can't be loaded or
 * the pinned version is missing from it, the verifier reports a violation
 * rather than silently passing. Mirrors the post-resolution gate bun added
 * for the same shape of bug in oven-sh/bun#30526.
 */
export function createNpmResolutionVerifier (
  opts: CreateNpmResolutionVerifierOptions
): ResolutionVerifier {
  const ageCheckActive = Boolean(opts.minimumReleaseAge)
  const trustCheckActive = opts.trustPolicy === 'no-downgrade'

  const cutoff = ageCheckActive
    ? (opts.now ?? Date.now()) - opts.minimumReleaseAge! * 60 * 1000
    : 0
  const excludePolicy = opts.minimumReleaseAgeExclude?.length
    ? createExcludePolicy(opts.minimumReleaseAgeExclude, 'minimumReleaseAgeExclude')
    : undefined
  const trustExcludePolicy = opts.trustPolicyExclude?.length
    ? createExcludePolicy(opts.trustPolicyExclude, 'trustPolicyExclude')
    : undefined

  // Pre-normalize named-registry URLs and sort by length so two registries
  // that share a hostname but differ by path (e.g. `https://npm/team-a/` vs
  // `https://npm/team-b/`) route to the longest matching prefix — matching
  // only `origin` would silently send lookups to the wrong one. Built-in
  // aliases (`gh:` → npm.pkg.github.com, etc.) are merged in alongside the
  // user-defined ones so the verifier recognizes the same set of named
  // registries the resolver does; otherwise a package resolved via `gh:`
  // would land in the lockfile with a tarball URL the verifier can't route.
  const namedRegistryPrefixes = Object.values({
    ...BUILTIN_NAMED_REGISTRIES,
    ...(opts.namedRegistries ?? {}),
  })
    .map((url) => {
      const parsed = tryParseUrl(url)
      if (!parsed) return null
      // Ensure trailing slash so prefix matching against tarball URLs (which
      // always include the package path under the registry root) does not
      // accidentally match a sibling registry whose URL shares a prefix string.
      const pathname = parsed.pathname.endsWith('/') ? parsed.pathname : `${parsed.pathname}/`
      return `${parsed.origin}${pathname}`
    })
    .filter((value): value is string => value != null)
    .sort((a, b) => b.length - a.length)

  // Per-install dedup of every network/disk fetch the verifier issues.
  // The maturity check uses the layered `fetchPublishedAt` lookup; the
  // trust check uses an attestation fast-path before falling back to
  // the same full-metadata mirror. All maps live here so verifying
  // many versions of the same package only pays the disk/network costs
  // once. The on-disk conditional-GET cache is handled inside
  // fetch{Abbreviated,Full}MetadataCached via the resolver's shared
  // mirrors at opts.cacheDir.
  const lookupContext: PublishedAtLookupContext = {
    fetchOpts: opts.fetchOpts,
    getAuthHeaderValueByURI: opts.getAuthHeaderValueByURI,
    cacheDir: opts.cacheDir,
    cutoffMs: cutoff,
    sharedMetaCache: opts.metaCache,
    abbreviatedMetaCache: new Map(),
    publishedAtCache: new Map(),
    localMetaCache: new Map(),
    fullMetaCache: new Map(),
    fullMetaForTrustCache: new Map(),
  }

  const minimumReleaseAge = opts.minimumReleaseAge ?? 0
  const trustPolicy = opts.trustPolicy
  const trustPolicyIgnoreAfter = opts.trustPolicyIgnoreAfter

  const verify: ResolutionVerifier['verify'] = async (resolution, { name, version, nonSemverVersion }) => {
    if (!isNpmRegistryResolution(resolution)) return { ok: true }
    // URL/git-keyed entries are deliberate non-registry deps. They can still
    // carry a semver `version` copied from the resolved manifest, so the
    // semver guard below isn't enough on its own — the registry policies and
    // the tarball-URL binding don't apply to them, and a registry lookup
    // would 404.
    if (nonSemverVersion != null) return { ok: true }
    if (!semver.valid(version)) return { ok: true }

    const tarballUrl = (resolution as { tarball?: string }).tarball
    const registry = pickRegistryForVersion(opts.registries, namedRegistryPrefixes, name, tarballUrl)

    // A registry entry that pins an explicit tarball URL must point at the
    // artifact the registry's own metadata lists. Otherwise a trusted
    // `name@version` could front bytes from an attacker-chosen URL (with a
    // matching integrity for those bytes). This binding is unconditional —
    // it does not depend on `minimumReleaseAge`/`trustPolicy` and isn't
    // narrowed by their exclude lists, since it guards integrity rather
    // than maturity/trust. Registry entries with no tarball URL reconstruct
    // it from name+version+registry, so they're inherently bound.
    if (typeof tarballUrl === 'string') {
      const urlViolation = await runTarballUrlCheck(lookupContext, registry, name, version, tarballUrl)
      if (urlViolation) return urlViolation
    }

    const ageApplies = ageCheckActive && !isExcluded(excludePolicy, name, version)
    const trustApplies = trustCheckActive && !isExcluded(trustExcludePolicy, name, version)
    if (!ageApplies && !trustApplies) return { ok: true }

    if (ageApplies) {
      const ageViolation = await runAgeCheck(lookupContext, registry, name, version, cutoff, opts.ignoreMissingTimeField === true)
      if (ageViolation) return ageViolation
    }

    if (trustApplies) {
      const trustViolation = await runTrustCheck(lookupContext, registry, name, version, {
        trustPolicyExclude: trustExcludePolicy,
        trustPolicyIgnoreAfter,
      })
      if (trustViolation) return trustViolation
    }

    return { ok: true }
  }
  // Snapshot the exclude lists (sorted, deduped) and require an exact
  // match in `canTrustPastCheck`: cache identity == policy identity.
  // Any change to either exclude list — adding, removing, or
  // substituting an entry — invalidates the cached run. This is
  // stricter than a pure correctness check would require (adding to
  // either list is more permissive and the cached pass would still
  // hold), but it makes the cache contract trivial to reason about and
  // removes a class of bypasses where a previously-approved version
  // stays trusted after its exclude entry has been pulled.
  const sortedMinAgeExcludes = [...new Set(opts.minimumReleaseAgeExclude ?? [])].sort()
  const sortedTrustExcludes = [...new Set(opts.trustPolicyExclude ?? [])].sort()
  return {
    verify,
    policy: {
      // Marks runs that enforced the tarball-URL binding. A cache record
      // written before this rule existed lacks the flag, so
      // `canTrustPastCheck` rejects it and forces a re-verification that
      // applies the binding — otherwise an upgrade could keep trusting a
      // lockfile that was only ever age/trust-checked.
      tarballUrlBinding: true,
      minimumReleaseAge,
      minimumReleaseAgeExclude: sortedMinAgeExcludes,
      trustPolicy: trustPolicy ?? null,
      trustPolicyExclude: sortedTrustExcludes,
      trustPolicyIgnoreAfter: trustPolicyIgnoreAfter ?? null,
    },
    canTrustPastCheck: (cached) => {
      // The tarball-URL binding is un
... [truncated]
```

### exec/commands/src/dlx.ts
```
import fs, { type Stats } from 'node:fs'
import path from 'node:path'
import util from 'node:util'

import { getBinsFromPackageManifest } from '@pnpm/bins.resolver'
import { getAutomaticallyIgnoredBuilds } from '@pnpm/building.commands'
import {
  type CatalogResolver,
  resolveFromCatalog,
} from '@pnpm/catalogs.resolver'
import type { CommandHandlerMap } from '@pnpm/cli.command'
import { OUTPUT_OPTIONS } from '@pnpm/cli.common-cli-options-help'
import { docsUrl, readProjectManifestOnly } from '@pnpm/cli.utils'
import { type Config, types } from '@pnpm/config.reader'
import { getPublishedByPolicy } from '@pnpm/config.version-policy'
import { createHexHash } from '@pnpm/crypto.hash'
import { PnpmError } from '@pnpm/error'
import { createResolver, makeResolutionStrict } from '@pnpm/installing.client'
import { add } from '@pnpm/installing.commands'
import { readPackageJsonFromDir } from '@pnpm/pkg-manifest.reader'
import { parseWantedDependency } from '@pnpm/resolving.parse-wanted-dependency'
import type { PackageManifest, PnpmSettings, SupportedArchitectures } from '@pnpm/types'
import { lexCompare } from '@pnpm/util.lex-comparator'
import { safeExeca as execa } from 'execa'
import { pick } from 'ramda'
import { renderHelp } from 'render-help'
import { symlinkDir } from 'symlink-dir'

import { makeEnv } from './makeEnv.js'

export const skipPackageManagerCheck = true

export const commandNames = ['dlx']

/**
 * Test-only env var. When set, the dlx ignored-builds recovery path bypasses
 * the TTY check and forwards `all: true` so `approve-builds` skips its
 * multiselect and confirm prompts. Mirrors the same env var honored by
 * `promptApproveGlobalBuilds` for global installs. Not for production use.
 */
const AUTO_APPROVE_FOR_TESTS_ENV = 'PNPM_AUTO_APPROVE_BUILDS_FOR_TESTS'

export const shorthands: Record<string, string> = {
  c: '--shell-mode',
}

export function rcOptionsTypes (): Record<string, unknown> {
  return {
    ...pick([
      'cpu',
      'libc',
      'os',
    ], types),
    'shell-mode': Boolean,
  }
}

export const cliOptionsTypes = (): Record<string, unknown> => ({
  ...rcOptionsTypes(),
  package: [String, Array],
  'allow-build': [String, Array],
})

export function help (): string {
  return renderHelp({
    description: 'Run a package in a temporary environment.',
    descriptionLists: [
      {
        title: 'Options',
        list: [
          {
            description: 'The package to install before running the command',
            name: '--package',
          },
          {
            description: 'A list of package names that are allowed to run postinstall scripts during installation',
            name: '--allow-build',
          },
          {
            description: 'Runs the script inside of a shell. Uses /bin/sh on UNIX and \\cmd.exe on Windows.',
            name: '--shell-mode',
            shortAlias: '-c',
          },
        ],
      },
      OUTPUT_OPTIONS,
    ],
    url: docsUrl('dlx'),
    usages: ['pnpm dlx <command> [args...]'],
  })
}

export type DlxCommandOptions = {
  package?: string[]
  shellMode?: boolean
  allowBuild?: string[]
} & Pick<Config, 'extraBinPaths' | 'minimumReleaseAgeExclude' | 'registries' | 'reporter' | 'userAgent' | 'cacheDir' | 'dlxCacheMaxAge' | 'symlink'> & Omit<add.AddCommandOptions, 'rootProjectManifestDir'> & PnpmSettings

export async function handler (
  opts: DlxCommandOptions,
  [command, ...args]: string[],
  commands?: CommandHandlerMap
): Promise<{ exitCode: number, output?: string }> {
  if (!command && (!opts.package || opts.package.length === 0)) {
    return { exitCode: 1, output: help() }
  }
  const pkgs = opts.package ?? [command]
  const fullMetadata = (
    (
      opts.resolutionMode === 'time-based' ||
      opts.trustPolicy === 'no-downgrade' ||
      Boolean(opts.minimumReleaseAge)
    ) && !opts.registrySupportsTimeField
  )
  const catalogResolver = resolveFromCatalog.bind(null, opts.catalogs ?? {})
  const { resolve: baseResolve } = createResolver({
    ...opts,
    configByUri: opts.configByUri,
    fullMetadata,
    filterMetadata: fullMetadata,
    ignoreMissingTimeField: opts.minimumReleaseAgeIgnoreMissingTime,
    retry: {
      factor: opts.fetchRetryFactor,
      maxTimeout: opts.fetchRetryMaxtimeout,
      minTimeout: opts.fetchRetryMintimeout,
      retries: opts.fetchRetries,
    },
    timeout: opts.fetchTimeout,
  })
  // dlx has nowhere to "defer to" — it runs the resolved package directly.
  // Wrap the resolver under any policy that wants to reject violations
  // up-front: strict minimumReleaseAge (refuse immature picks) and
  // `trustPolicy: 'no-downgrade'` (refuse versions whose trust evidence
  // weakened). Without the trust-policy arm, a downgraded version would
  // resolve to a `policyViolation` that dlx silently ignored and then
  // executed.
  const strictResolution =
    (Boolean(opts.minimumReleaseAge) && opts.minimumReleaseAgeStrict === true) ||
    opts.trustPolicy === 'no-downgrade'
  const resolve = strictResolution ? makeResolutionStrict(baseResolve) : baseResolve
  const resolvedPkgAliases: string[] = []
  const { publishedBy, publishedByExclude } = getPublishedByPolicy(opts)
  const resolvedPkgs = await Promise.all(pkgs.map(async (pkg) => {
    const { alias, bareSpecifier } = parseWantedDependency(pkg) || {}
    if (alias == null) return pkg
    const resolvedBareSpecifier = bareSpecifier != null
      ? resolveCatalogProtocol(catalogResolver, alias, bareSpecifier)
      : bareSpecifier
    resolvedPkgAliases.push(alias)
    const resolved = await resolve({ alias, bareSpecifier: resolvedBareSpecifier }, {
      lockfileDir: opts.lockfileDir ?? opts.dir,
      preferredVersions: {},
      projectDir: opts.dir,
      publishedBy,
      publishedByExclude,
    })
    return resolved.id
  }))
  let { cacheLink, cacheExists, cachedDir } = findCache({
    packages: resolvedPkgs,
    dlxCacheMaxAge: opts.dlxCacheMaxAge,
    cacheDir: opts.cacheDir,
    registries: opts.registries,
    allowBuild: opts.allowBuild,
    supportedArchitectures: opts.supportedArchitectures,
  })
  if (!cacheExists) {
    const allowBuilds = Object.fromEntries([...resolvedPkgAliases, ...(opts.allowBuild ?? [])].map(pkg => [pkg, true]))
    try {
      fs.mkdirSync(cachedDir, { recursive: true })
      await add.handler({
        ...opts,
        // Mirror the global install flow: dlx prompts via `approve-builds`
        // when transitive deps have skipped build scripts, so it must not let
        // strictDepBuilds (the v11 default) turn that into a hard error.
        // Without this, `pnpm dlx <pkg>` cannot launch packages whose bin
        // depends on a postinstall step (e.g. native modules).
        strictDepBuilds: false,
        enableGlobalVirtualStore: opts.enableGlobalVirtualStore ?? true,
        bin: path.join(cachedDir, 'node_modules/.bin'),
        dir: cachedDir,
        lockfileDir: cachedDir,
        allowBuilds,
        rootProjectManifestDir: cachedDir,
        saveProd: true, // dlx will be looking for the package in the "dependencies" field!
        saveDev: false,
        saveOptional: false,
        savePeer: false,
        symlink: true,
        workspaceDir: undefined,
      }, resolvedPkgs)
      await promptApproveDlxBuilds({ cachedDir, allowBuilds, inheritedOpts: opts }, commands)
      try {
        await symlinkDir(cachedDir, cacheLink, { overwrite: true })
      } catch (error) {
        // EBUSY/EEXIST/EPERM means that there is another dlx process running in parallel that has acquired the cache link first.
        // EPERM can happen on Windows when another process has the symlink open while this process tries to unlink it.
        // The link created by the other process is just as up-to-date as the link the current process was attempting
        // to create. Therefore, instead of re-attempting to create the current link again, it is just as good to let
        // the other link stay. The current process should yield.
        if (!util.types.isNativeError(error) || !('code' in error) || (error.code !== 'EBUSY' && error.code !== 'EEXIST' && error.code !== 'EPERM')) {
          throw error
        }
      }
    } catch (err) {
      // When parallel dlx processes install the same package, the shared global
      // virtual store can cause spurious failures (e.g. ENOENT from concurrent
      // directory swaps).  If another process completed the cache in the meantime,
      // use that instead of failing.
      const completedDir = getValidCacheDir(cacheLink, opts.dlxCacheMaxAge)
      if (completedDir != null) {
        cachedDir = completedDir
      } else {
        // Drop the partially-populated cache so a subsequent dlx run starts
        // clean instead of reusing a broken install.
        await fs.promises.rm(cachedDir, { recursive: true, force: true })
        throw err
      }
    }
  }
  const binsDir = path.join(cachedDir, 'node_modules/.bin')
  const env = makeEnv({
    userAgent: opts.userAgent,
    prependPaths: [binsDir, ...opts.extraBinPaths],
  })
  const binName = opts.package
    ? command
    : await getBinName(cachedDir, opts)
  try {
    await execa(binName, args, {
      cwd: process.cwd(),
      env,
      stdio: 'inherit',
      shell: opts.shellMode ?? false,
    })
  } catch (err: unknown) {
    if (util.types.isNativeError(err) && 'exitCode' in err && err.exitCode != null) {
      return {
        exitCode: err.exitCode as number,
      }
    }
    throw err
  }
  return { exitCode: 0 }
}

async function getPkgName (pkgDir: string): Promise<string> {
  const manifest = await readPackageJsonFromDir(pkgDir)
  const dependencyNames = Object.keys(manifest.dependencies ?? {})
  if (dependencyNames.length === 0) {
    throw new PnpmError('DLX_NO_DEP', 'dlx was unable to find the installed dependency in "dependencies"')
  }
  return dependencyNames[0]
}

async function getBinName (cachedDir: string, opts: Pick<DlxCommandOptions, 'engineStrict'>): Promise<string> {
  const pkgName = await getPkgName(cachedDir)
  const pkgDir = path.join(cachedDir, 'node_modules', pkgName)
  let manifest: PackageManifest
  try {
    manifest = await readProjectManifestOnly(pkgDir, opts) as PackageManifest
  } catch (err: unknown) {
    // The installed package's `package.json` is unreadable. Observed in the
    // wild for `node@runtime:<version>` whose CAS slot was materialized by
    // a code path that didn't run pnpm's `appendManifest` (or pacquet's
    // equivalent runtime-manifest synthesis), leaving the slot without
    // the `package.json` runtime archives don't ship themselves. Fall back
    // to the scopeless package name — for single-bin packages (the dlx
    // common case) it matches what `manifest.bin` would have named, and
    // the `node_modules/.bin/<name>` symlink the install already wired up
    // from the resolution's bin info is what `execa` resolves against.
    // Multi-bin packages require `--package=<spec> <bin>` to disambiguate,
    // which short-circuits `getBinName` upstream and never enters this path.
    if (util.types.isNativeError(err) && 'code' in err && err.code === 'ERR_PNPM_NO_IMPORTER_MANIFEST_FOUND') {
      return scopeless(pkgName)
    }
    throw err
  }
  const bins = await getBinsFromPackageManifest(manifest, pkgDir)
  if (bins.length === 0) {
    throw new PnpmError('DLX_NO_BIN', `No binaries found in ${pkgName}`)
  }
  if (bins.length === 1) {
    return bins[0].name
  }
  const scopelessPkgName = scopeless(manifest.name)
  const defaultBin = bins.find(({ name }) => name === scopelessPkgName)
  if (defaultBin) return defaultBin.name
  const binNames = bins.map(({ name }) => name)
  throw new PnpmError('DLX_MULTIPLE_BINS', `Could not determine executable to run. ${pkgName} has multiple binaries: ${binNames.join(', ')}`, {
    hint: `Try one of the following:
${binNames.map(name => `pnpm --package=${pkgName} dlx ${name}`).join('\n')}
`,
  })
}

function scopeless (pkgName: string)
... [truncated]
```

### installing/commands/src/recursive.ts
```
import { promises as fs } from 'node:fs'
import path from 'node:path'

import type { Catalogs } from '@pnpm/catalogs.types'
import type { CommandHandler } from '@pnpm/cli.command'
import {
  type RecursiveSummary,
  throwOnCommandFail,
} from '@pnpm/cli.utils'
import { createMatcherWithIndex } from '@pnpm/config.matcher'
import {
  type Config,
  type ConfigContext,
  createProjectConfigRecord,
  getWorkspaceConcurrency,
  type OptionsFromRootManifest,
  type ProjectConfig,
} from '@pnpm/config.reader'
import { PnpmError } from '@pnpm/error'
import { requireHooks } from '@pnpm/hooks.pnpmfile'
import { arrayOfWorkspacePackagesToMap } from '@pnpm/installing.context'
import {
  addDependenciesToPackage,
  install,
  type InstallOptions,
  type MutatedProject,
  mutateModules,
  type ProjectOptions,
  type UpdateMatchingFunction,
  type WorkspacePackages,
} from '@pnpm/installing.deps-installer'
import { logger } from '@pnpm/logger'
import { filterDependenciesByType } from '@pnpm/pkg-manifest.utils'
import type { PreferredVersions } from '@pnpm/resolving.resolver-base'
import type { ResolutionVerifier } from '@pnpm/resolving.resolver-base'
import { createStoreController, type CreateStoreControllerOptions } from '@pnpm/store.connection-manager'
import type { StoreController } from '@pnpm/store.controller'
import type {
  DepPath,
  IgnoredBuilds,
  IncludedDependencies,
  PackageManifest,
  Project,
  ProjectManifest,
  ProjectRootDir,
  ProjectRootDirRealPath,
  ProjectsGraph,
} from '@pnpm/types'
import { sortProjects } from '@pnpm/workspace.projects-sorter'
import { updateWorkspaceManifest } from '@pnpm/workspace.workspace-manifest-writer'
import { isSubdir } from 'is-subdir'
import pFilter from 'p-filter'
import pLimit from 'p-limit'

import { getPinnedVersion } from './getPinnedVersion.js'
import { getSaveType } from './getSaveType.js'
import { handleIgnoredBuilds } from './handleIgnoredBuilds.js'
import { type PolicyViolation, setupPolicyHandlers } from './policyHandlers.js'
import { createWorkspaceSpecs, updateToWorkspacePackagesFromManifest } from './updateWorkspaceDependencies.js'

export type RecursiveOptions = CreateStoreControllerOptions & Pick<Config,
| 'bail'
| 'configDependencies'
| 'dedupePeerDependents'
| 'dedupePeers'
| 'depth'
| 'globalPnpmfile'
| 'hoistPattern'
| 'hoistingLimits'
| 'ignorePnpmfile'
| 'ignoreScripts'
| 'linkWorkspacePackages'
| 'lockfileDir'
| 'lockfileOnly'
| 'modulesDir'
| 'pnprServer'
| 'allowBuilds'
| 'registries'
| 'runtime'
| 'save'
| 'saveCatalogName'
| 'saveDev'
| 'saveExact'
| 'saveOptional'
| 'savePeer'
| 'savePrefix'
| 'saveProd'
| 'saveWorkspaceProtocol'
| 'lockfileIncludeTarballUrl'
| 'sharedWorkspaceLockfile'
| 'tag'
| 'trustLockfile'
| 'cleanupUnusedCatalogs'
| 'packageConfigs'
| 'updateConfig'
> & Pick<ConfigContext,
| 'hooks'
| 'rootProjectManifest'
| 'rootProjectManifestDir'
> & {
  rebuildHandler?: CommandHandler
  include?: IncludedDependencies
  includeDirect?: IncludedDependencies
  latest?: boolean
  pending?: boolean
  workspace?: boolean
  allowNew?: boolean
  ignoredPackages?: Set<string>
  update?: boolean
  updatePackageManifest?: boolean
  updateMatching?: UpdateMatchingFunction
  useBetaCli?: boolean
  allProjectsGraph: ProjectsGraph
  selectedProjectsGraph: ProjectsGraph
  preferredVersions?: PreferredVersions
  pruneDirectDependencies?: boolean
  pruneLockfileImporters?: boolean
  storeControllerAndDir?: {
    ctrl: StoreController
    dir: string
    resolutionVerifiers: ResolutionVerifier[]
  }
  pnpmfile: string[]
  /**
   * Alternative install engine (today: pacquet) the deps-installer
   * delegates the materialization phase to. Built in `installDeps`
   * when `configDependencies.pacquet` is declared, threaded through
   * here so the recursive workspace path picks it up too.
   */
  runPacquet?: () => Promise<void>
} & Partial<
  Pick<Config,
| 'ci'
| 'sort'
| 'strictDepBuilds'
| 'workspaceConcurrency'
  >
> & Required<
  Pick<Config, 'workspaceDir'>
>

export type CommandFullName = 'install' | 'add' | 'remove' | 'update' | 'import'

export async function recursive (
  allProjects: Project[],
  params: string[],
  opts: RecursiveOptions,
  cmdFullName: CommandFullName
): Promise<boolean | string> {
  if (allProjects.length === 0) {
    // It might make sense to throw an exception in this case
    return false
  }

  const pkgs = Object.values(opts.selectedProjectsGraph).map((wsPkg) => wsPkg.package)

  if (pkgs.length === 0) {
    return false
  }
  const manifestsByPath = getManifestsByPath(allProjects)

  const throwOnFail = throwOnCommandFail.bind(null, `pnpm recursive ${cmdFullName}`)

  const store = opts.storeControllerAndDir ?? await createStoreController(opts)

  const workspacePackages: WorkspacePackages = arrayOfWorkspacePackagesToMap(allProjects) as WorkspacePackages
  const targetDependenciesField = getSaveType(opts)
  // See `installDeps.ts` for context; mirrored here so workspace-recursive
  // installs also surface immature picks (loose-mode auto-persist or
  // strict-mode prompt). The workspace manifest writer dedupes against the
  // existing list, so a single drain at the end captures additions across
  // every project.
  const policyHandlers = setupPolicyHandlers(opts)
  const installOpts = Object.assign(opts, {
    allProjects: getAllProjects(manifestsByPath, opts.allProjectsGraph, opts.sort),
    linkWorkspacePackagesDepth: opts.linkWorkspacePackages === 'deep' ? Infinity : opts.linkWorkspacePackages ? 0 : -1,
    ownLifecycleHooksStdio: 'pipe',
    peer: opts.savePeer,
    pruneLockfileImporters: opts.pruneLockfileImporters ??
      (((opts.ignoredPackages == null) || opts.ignoredPackages.size === 0) &&
        pkgs.length === allProjects.length),
    saveCatalogName: opts.saveCatalogName,
    skipRuntimes: opts.runtime === false,
    storeController: store.ctrl,
    storeDir: store.dir,
    targetDependenciesField,
    resolutionVerifiers: store.resolutionVerifiers,
    workspacePackages,
    handleResolutionPolicyViolations: policyHandlers?.handleResolutionPolicyViolations,
  }) as InstallOptions

  const result: RecursiveSummary = {}

  const projectConfigRecord = createProjectConfigRecord(opts)
  const getProjectConfig: (manifest: Pick<ProjectManifest, 'name'>) => ProjectConfig | undefined =
    projectConfigRecord
      ? manifest => manifest.name ? projectConfigRecord[manifest.name] : undefined
      : () => undefined

  const updateToLatest = opts.update && opts.latest
  const includeDirect = opts.includeDirect ?? {
    dependencies: true,
    devDependencies: true,
    optionalDependencies: true,
  }

  let updateMatch: UpdateDepsMatcher | null
  if (cmdFullName === 'update') {
    if (params.length === 0) {
      const ignoreDeps = opts.updateConfig?.ignoreDependencies
      if (ignoreDeps?.length) {
        params = makeIgnorePatterns(ignoreDeps)
      }
    }
    updateMatch = params.length ? createMatcher(params) : null
  } else {
    updateMatch = null
  }
  // For a workspace with shared lockfile
  if (opts.lockfileDir && ['add', 'install', 'remove', 'update', 'import'].includes(cmdFullName)) {
    let importers = getImporters(opts)
    const calculatedRepositoryRoot = await fs.realpath(calculateRepositoryRoot(opts.workspaceDir, importers.map(x => x.rootDir)))
    const isFromWorkspace = isSubdir.bind(null, calculatedRepositoryRoot)
    importers = await pFilter(importers, async ({ rootDirRealPath }) => isFromWorkspace(rootDirRealPath))
    if (importers.length === 0) return true
    let mutation: 'install' | 'installSome' | 'uninstallSome'
    switch (cmdFullName) {
      case 'remove':
        mutation = 'uninstallSome'
        break
      case 'import':
        mutation = 'install'
        break
      default:
        mutation = (params.length === 0 && !updateToLatest ? 'install' : 'installSome')
        break
    }
    const mutatedImporters = [] as MutatedProject[]
    await Promise.all(importers.map(async ({ rootDir }) => {
      const { manifest } = manifestsByPath[rootDir]
      const localConfig = getProjectConfig(manifest) ?? {}
      const modulesDir = localConfig.modulesDir ?? opts.modulesDir
      let currentInput = [...params]
      if (updateMatch != null) {
        currentInput = matchDependencies(updateMatch, manifest, includeDirect)
        if ((currentInput.length === 0) && (typeof opts.depth === 'undefined' || opts.depth <= 0)) {
          installOpts.pruneLockfileImporters = false
          return
        }
      }
      if (updateToLatest && (!params || (params.length === 0))) {
        currentInput = Object.keys(filterDependenciesByType(manifest, includeDirect))
      }
      if (opts.workspace) {
        if (!currentInput || (currentInput.length === 0)) {
          currentInput = updateToWorkspacePackagesFromManifest(manifest, includeDirect, workspacePackages)
        } else {
          currentInput = createWorkspaceSpecs(currentInput, workspacePackages)
        }
      }
      switch (mutation) {
        case 'uninstallSome':
          mutatedImporters.push({
            dependencyNames: currentInput,
            modulesDir,
            mutation,
            rootDir,
            targetDependenciesField,
          } as MutatedProject)
          return
        case 'installSome':
          mutatedImporters.push({
            allowNew: cmdFullName === 'install' || cmdFullName === 'add',
            dependencySelectors: currentInput,
            modulesDir,
            mutation,
            peer: opts.savePeer,
            pinnedVersion: getPinnedVersion({
              saveExact: typeof localConfig.saveExact === 'boolean' ? localConfig.saveExact : opts.saveExact,
              savePrefix: typeof localConfig.savePrefix === 'string' ? localConfig.savePrefix : opts.savePrefix,
            }),
            rootDir,
            targetDependenciesField,
            update: opts.update,
            updateMatching: opts.updateMatching,
            updatePackageManifest: opts.updatePackageManifest,
            updateToLatest: opts.latest,
          } as MutatedProject)
          return
        case 'install':
          mutatedImporters.push({
            modulesDir,
            mutation,
            pruneDirectDependencies: opts.pruneDirectDependencies,
            rootDir,
            update: opts.update,
            updateMatching: opts.updateMatching,
            updatePackageManifest: opts.updatePackageManifest,
            updateToLatest: opts.latest,
          } as MutatedProject)
      }
    }))
    if (!opts.selectedProjectsGraph[opts.workspaceDir as ProjectRootDir] && manifestsByPath[opts.workspaceDir as ProjectRootDir] != null) {
      mutatedImporters.push({
        mutation: 'install',
        rootDir: opts.workspaceDir as ProjectRootDir,
      })
    }
    if ((mutatedImporters.length === 0) && cmdFullName === 'update' && opts.depth === 0) {
      throw new PnpmError('NO_PACKAGE_IN_DEPENDENCIES',
        'None of the specified packages were found in the dependencies of any of the projects.')
    }
    const {
      updatedCatalogs,
      updatedProjects: mutatedPkgs,
      ignoredBuilds,
      resolutionPolicyViolations,
    } = await mutateModules(mutatedImporters, {
      ...installOpts,
      storeController: store.ctrl,
      resolutionVerifiers: store.resolutionVerifiers,
    })
    if (opts.save !== false) {
      // Only pick entries when we'll actually persist. Otherwise the
      // info log would claim entries were added that the workspace
      // manifest never saw, and the next install would re-prompt or
      // fail verification.
      const policyUpdates = policyHandlers?.pickManifestUpdates(resolutionPolicyViolations)
      const promises: Array<Promise<void>> = mutatedPkgs.map(async ({ originalManifest, manifest, rootDir }) => {
        return manifestsByPath[rootDir].writeProjectManifest(originalManifest ?? manifest)
      })
      promises.push(updateWorkspaceManifest(opts.workspaceDir, {
        updatedCatalogs,
      
... [truncated]
```

### building/commands/src/policy/index.ts
```
import * as approveBuilds from './approveBuilds.js'
import * as ignoredBuilds from './ignoredBuilds.js'
export type { ApproveBuildsCommandOpts } from './approveBuilds.js'
export { getAutomaticallyIgnoredBuilds } from './getAutomaticallyIgnoredBuilds.js'

export { approveBuilds, ignoredBuilds }

```

### installing/deps-installer/src/install/extendInstallOptions.ts
```
import path from 'node:path'

import type { Catalogs } from '@pnpm/catalogs.types'
import { DEFAULT_REGISTRIES, normalizeRegistries } from '@pnpm/config.normalize-registries'
import { parseOverrides, type VersionOverride } from '@pnpm/config.parse-overrides'
import { WANTED_LOCKFILE } from '@pnpm/constants'
import { PnpmError } from '@pnpm/error'
import { createReadPackageHook } from '@pnpm/hooks.read-package-hook'
import type { CustomFetcher, CustomResolver, PreResolutionHookContext } from '@pnpm/hooks.types'
import type { ProjectOptions } from '@pnpm/installing.context'
import type { HoistingLimits } from '@pnpm/installing.deps-restorer'
import type { IncludedDependencies } from '@pnpm/installing.modules-yaml'
import type { LockfileObject } from '@pnpm/lockfile.fs'
import type { ResolutionPolicyViolation, ResolutionVerifier, WorkspacePackages } from '@pnpm/resolving.resolver-base'
import type { StoreController } from '@pnpm/store.controller-types'
import type {
  AllowedDeprecatedVersions,
  PackageExtension,
  PackageVulnerabilityAudit,
  PeerDependencyRules,
  ReadPackageHook,
  Registries,
  RegistryConfig,
  SupportedArchitectures,
  TrustPolicy,
} from '@pnpm/types'

import { pnpmPkgJson } from '../pnpmPkgJson.js'
import type { ReporterFunction } from '../types.js'

export interface StrictInstallOptions {
  autoConfirmAllPrompts: boolean
  autoInstallPeers: boolean
  autoInstallPeersFromHighestMatch: boolean
  catalogs: Catalogs
  catalogMode: 'strict' | 'prefer' | 'manual'
  cleanupUnusedCatalogs: boolean
  frozenLockfile: boolean
  frozenLockfileIfExists: boolean
  enableGlobalVirtualStore: boolean
  enablePnp: boolean
  extraBinPaths: string[]
  extraEnv: Record<string, string>
  hoistingLimits?: HoistingLimits
  externalDependencies?: Set<string>
  useLockfile: boolean
  saveLockfile: boolean
  useGitBranchLockfile: boolean
  mergeGitBranchLockfiles: boolean
  linkWorkspacePackagesDepth: number
  lockfileOnly: boolean
  forceFullResolution: boolean
  fixLockfile: boolean
  updateChecksums: boolean
  dedupe: boolean
  ignoreCompatibilityDb: boolean
  ignorePackageManifest: boolean
  /**
   * When true, skip fetching local dependencies (file: protocol pointing to directories).
   * This is used by `pnpm fetch` which only downloads packages from the registry
   * and doesn't need local packages that won't be available (e.g., in Docker builds).
   */
  ignoreLocalPackages: boolean
  preferFrozenLockfile: boolean
  saveWorkspaceProtocol: boolean | 'rolling'
  lockfileCheck?: (prev: LockfileObject, next: LockfileObject) => void
  lockfileIncludeTarballUrl?: boolean
  preferWorkspacePackages: boolean
  preserveWorkspaceProtocol: boolean
  saveCatalogName?: string
  scriptsPrependNodePath: boolean | 'warn-only'
  scriptShell?: string
  shellEmulator: boolean
  storeController: StoreController
  storeDir: string
  reporter: ReporterFunction
  force: boolean
  depth: number
  lockfileDir: string
  modulesDir: string
  configByUri: Record<string, RegistryConfig>
  verifyStoreIntegrity: boolean
  engineStrict: boolean
  allowBuilds?: Record<string, boolean | string>
  nodeLinker: 'isolated' | 'hoisted' | 'pnp'
  nodeVersion?: string
  packageExtensions: Record<string, PackageExtension>
  ignoredOptionalDependencies: string[]
  pnpmfile: string[] | string
  ignorePnpmfile: boolean
  packageManager: {
    name: string
    version: string
  }
  pruneLockfileImporters: boolean
  hooks: {
    readPackage?: ReadPackageHook[]
    preResolution?: Array<(ctx: PreResolutionHookContext) => Promise<void>>
    afterAllResolved?: Array<(lockfile: LockfileObject) => LockfileObject | Promise<LockfileObject>>
    customResolvers?: CustomResolver[]
    customFetchers?: CustomFetcher[]
    calculatePnpmfileChecksum?: () => Promise<string | undefined>
  }
  sideEffectsCacheRead: boolean
  sideEffectsCacheWrite: boolean
  strictPeerDependencies: boolean
  include: IncludedDependencies
  includeDirect: IncludedDependencies
  ignoreCurrentSpecifiers: boolean
  ignoreScripts: boolean
  childConcurrency: number
  userAgent: string
  unsafePerm: boolean
  registries: Registries
  namedRegistries?: Record<string, string>
  tag: string
  overrides: Record<string, string>
  ownLifecycleHooksStdio: 'inherit' | 'pipe'
  // We can automatically calculate these
  // unless installation runs on a workspace
  // that doesn't share a lockfile
  workspacePackages?: WorkspacePackages
  pruneStore: boolean
  virtualStoreDir?: string
  globalVirtualStoreDir: string
  dir: string
  symlink: boolean
  enableModulesDir: boolean
  virtualStoreOnly: boolean
  modulesCacheMaxAge: number
  peerDependencyRules: PeerDependencyRules
  allowedDeprecatedVersions: AllowedDeprecatedVersions
  allowUnusedPatches: boolean
  preferSymlinkedExecutables: boolean
  resolutionMode: 'highest' | 'time-based' | 'lowest-direct'
  resolvePeersFromWorkspaceRoot: boolean
  ignoreWorkspaceCycles: boolean
  disallowWorkspaceCycles: boolean

  publicHoistPattern: string[] | undefined
  hoistPattern: string[] | undefined

  shamefullyHoist: boolean

  global: boolean
  globalBin?: string
  patchedDependencies?: Record<string, string>

  allProjects: ProjectOptions[]
  resolveSymlinksInInjectedDirs: boolean
  dedupeDirectDeps: boolean
  dedupeInjectedDeps: boolean
  dedupePeerDependents: boolean
  dedupePeers: boolean
  extendNodePath: boolean
  excludeLinksFromLockfile: boolean
  confirmModulesPurge: boolean
  /**
   * Don't relink local directory dependencies if they are not hard linked from the local directory.
   *
   * This option was added to fix an issue with Bit CLI.
   * Bit compile adds dist directories to the injected dependencies, so if pnpm were to relink them,
   * the dist directories would be deleted.
   *
   * The option might be used in the future to improve performance.
   */
  disableRelinkLocalDirDeps: boolean

  skipRuntimes: boolean
  supportedArchitectures?: SupportedArchitectures
  hoistWorkspacePackages?: boolean
  virtualStoreDirMaxLength: number
  peersSuffixMaxLength: number
  returnListOfDepsRequiringBuild?: boolean
  injectWorkspacePackages?: boolean
  ci?: boolean
  minimumReleaseAge?: number
  minimumReleaseAgeExclude?: string[]
  /**
   * Resolver-agnostic post-tree gate, invoked between
   * `resolveDependencyTree` and `resolvePeers` inside
   * `resolveDependencies`. Receives the violations the verifier
   * fan-out collected from the freshly-resolved tree. Throwing here
   * unwinds the install before peer-dep resolution runs — nothing on
   * disk has changed, and the (potentially expensive) peer pass is
   * skipped on abort.
   *
   * Intentionally policy-neutral. Each verifier owns its violation
   * codes (`MINIMUM_RELEASE_AGE_VIOLATION`, `TRUST_DOWNGRADE`, …); the
   * install command filters by code to decide what to do. Future
   * resolvers can plug verifiers in without touching this signature.
   */
  handleResolutionPolicyViolations?: (
    violations: readonly ResolutionPolicyViolation[]
  ) => Promise<void>
  /**
   * Resolver-side verifiers that re-check each lockfile-pinned resolution
   * against policies configured upstream (today: at most one,
   * `npm.minimumReleaseAge` in strict mode). Constructed by `createClient`
   * and surfaced via the `createStoreController` return; mutateModules
   * fans out across the list once, right after the lockfile is loaded
   * from disk. Empty when no policy is active.
   */
  resolutionVerifiers: ResolutionVerifier[]
  /**
   * pnpm's on-disk cache directory. When set together with non-empty
   * `resolutionVerifiers`, the lockfile verification result is memoized
   * in `<cacheDir>/lockfile-verified.jsonl` so repeat installs against an
   * unchanged lockfile skip the per-package registry round trip. The
   * record is policy-neutral; each active resolver-side verifier writes
   * its own slot under `verifiers[<key>]`.
   */
  cacheDir?: string
  trustPolicy?: TrustPolicy
  trustPolicyExclude?: string[]
  trustPolicyIgnoreAfter?: number
  /**
   * Skip the lockfile supply-chain verification pass entirely. When
   * true, `verifyLockfileResolutions` is not called even if
   * `resolutionVerifiers` is non-empty — the install trusts the
   * lockfile as-is. Trade-off: a poisoned lockfile (e.g. one a
   * contributor authored under a weaker policy than CI enforces) can
   * slip through. Use only in environments where the lockfile is
   * effectively part of the trusted base — closed-source projects
   * where every commit comes from a trusted author, fully reproducible
   * CI runs against an already-verified lockfile, etc.
   *
   * Added for #11860: on workspaces with thousands of locked entries,
   * the verification pass holds the per-package registry metadata
   * needed for the trust check resident in memory and can OOM CI
   * runners with a 2GB heap cap.
   */
  trustLockfile?: boolean
  packageVulnerabilityAudit?: PackageVulnerabilityAudit
  blockExoticSubdeps?: boolean
  /**
   * Optional alternative install engine. When set, the frozen-install
   * path invokes this callback instead of `headlessInstall`. The CLI
   * layer constructs it (today: spawning the pacquet binary installed
   * via `configDependencies` and forwarding pnpm's own CLI argv); the
   * installer treats it as an opaque "do the install" hook so it
   * doesn't need to know about pacquet's binary path, CLI surface, or
   * any settings that only pacquet consumes.
   *
   * `filterResolvedProgress` tells the helper to drop the engine's
   * own `pnpm:progress status:resolved` events because pnpm already
   * emitted one per package during a preceding lockfileOnly resolve
   * pass. The frozen-install path passes `false` (or nothing): no
   * resolve pass ran, so the engine's events are the only source.
   */
  runPacquet?: (opts?: { filterResolvedProgress?: boolean }) => Promise<void>
  /**
   * If true, `mutateModules` does not emit the per-install `summary` log
   * event. Used by `pnpm add -g` when it runs multiple isolated installs
   * inside a single command and wants to emit a single consolidated
   * summary at the very end instead of one summary per install.
   */
  omitSummaryLog: boolean
  /**
   * URL of a pnpr server that resolves dependencies server-side and serves
   * only the files missing from the client's store.
   */
  pnprServer?: string
}

export type InstallOptions =
  & Partial<StrictInstallOptions>
  & Pick<StrictInstallOptions, 'storeDir' | 'storeController'>

const defaults = (opts: InstallOptions): StrictInstallOptions => {
  const packageManager = opts.packageManager ?? {
    name: pnpmPkgJson.name,
    version: pnpmPkgJson.version,
  }
  return {
    allowedDeprecatedVersions: {},
    allowUnusedPatches: false,
    autoConfirmAllPrompts: opts.autoConfirmAllPrompts ?? false,
    autoInstallPeers: true,
    autoInstallPeersFromHighestMatch: false,
    catalogs: {},
    childConcurrency: 5,
    confirmModulesPurge: !(opts.autoConfirmAllPrompts || opts.force),
    depth: 0,
    dedupeInjectedDeps: true,
    enableGlobalVirtualStore: false,
    enablePnp: false,
    engineStrict: false,
    force: false,
    forceFullResolution: false,
    frozenLockfile: false,
    hoistPattern: undefined,
    publicHoistPattern: undefined,
    hooks: {},
    ignoreCurrentSpecifiers: false,
    ignoreScripts: false,
    include: {
      dependencies: true,
      devDependencies: true,
      optionalDependencies: true,
    },
    includeDirect: {
      dependencies: true,
      devDependencies: true,
      optionalDependencies: true,
    },
    lockfileDir: opts.lockfileDir ?? opts.dir ?? process.cwd(),
    lockfileOnly: false,
    updateChecksums: false,
    nodeVersion: opts.nodeVersion,
    nodeLinker: 'isolated',
    overrides: {},
    ownLifecycleHooksStdio: 'inherit',
    ignoreCompatibilityDb: false,
    ignorePackageManifest: false,
    ignoreLocalPackages: false,
    packageExtensions: {},
    ignoredOptionalDependencies: [] as string[],
    packageManager,
 
... [truncated]
```

### installing/commands/src/update/index.ts
```
import { checkbox, Separator } from '@inquirer/prompts'
import type { CommandHandler, CommandHandlerMap, CompletionFunc } from '@pnpm/cli.command'
import { FILTERING, OPTIONS, UNIVERSAL_OPTIONS } from '@pnpm/cli.common-cli-options-help'
import {
  docsUrl,
  interactivePromptPageSize,
  readDepNameCompletions,
  readProjectManifestOnly,
} from '@pnpm/cli.utils'
import { createMatcher } from '@pnpm/config.matcher'
import { types as allTypes } from '@pnpm/config.reader'
import { outdatedDepsOfProjects } from '@pnpm/deps.inspection.outdated'
import { PnpmError } from '@pnpm/error'
import { handleGlobalUpdate } from '@pnpm/global.commands'
import type { UpdateMatchingFunction } from '@pnpm/installing.deps-installer'
import { globalInfo } from '@pnpm/logger'
import type { IncludedDependencies, PackageVulnerabilityAudit, ProjectRootDir } from '@pnpm/types'
import chalk from 'chalk'
import { pick, unnest } from 'ramda'
import { renderHelp } from 'render-help'

import type { InstallCommandOptions } from '../install.js'
import { installDeps } from '../installDeps.js'
import { parseUpdateParam } from '../recursive.js'
import { createGlobalPolicyCallbacks } from '../resolutionPolicyManifest.js'
import { getUpdateChoices } from './getUpdateChoices.js'
export function rcOptionsTypes (): Record<string, unknown> {
  return pick([
    'cache-dir',
    'dangerously-allow-all-builds',
    'depth',
    'dev',
    'engine-strict',
    'fetch-retries',
    'fetch-retry-factor',
    'fetch-retry-maxtimeout',
    'fetch-retry-mintimeout',
    'fetch-timeout',
    'force',
    'global-dir',
    'global-pnpmfile',
    'global',
    'https-proxy',
    'ignore-pnpmfile',
    'ignore-scripts',
    'lockfile-dir',
    'lockfile-only',
    'lockfile',
    'lockfile-include-tarball-url',
    'network-concurrency',
    'noproxy',
    'npm-path',
    'offline',
    'only',
    'optional',
    'package-import-method',
    'pnpmfile',
    'prefer-offline',
    'production',
    'proxy',
    'registry',
    'reporter',
    'save',
    'save-exact',
    'save-prefix',
    'save-workspace-protocol',
    'scripts-prepend-node-path',
    'shamefully-hoist',
    'shared-workspace-lockfile',
    'side-effects-cache-readonly',
    'side-effects-cache',
    'store-dir',
    'unsafe-perm',
  ], allTypes)
}

export function cliOptionsTypes (): Record<string, unknown> {
  return {
    ...rcOptionsTypes(),
    interactive: Boolean,
    latest: Boolean,
    recursive: Boolean,
    workspace: Boolean,
  }
}

export const shorthands: Record<string, string> = {
  D: '--dev',
  P: '--production',
}

export const commandNames = ['update', 'up', 'upgrade']

export const completion: CompletionFunc = async (cliOpts) => {
  return readDepNameCompletions(cliOpts.dir as string)
}

export function help (): string {
  return renderHelp({
    aliases: ['up', 'upgrade'],
    description: 'Updates packages to their latest version based on the specified range. You can use "*" in package name to update all packages with the same pattern.',
    descriptionLists: [
      {
        title: 'Options',

        list: [
          {
            description: 'Update in every package found in subdirectories \
or every workspace package, when executed inside a workspace. \
For options that may be used with `-r`, see "pnpm help recursive"',
            name: '--recursive',
            shortAlias: '-r',
          },
          {
            description: 'Update globally installed packages',
            name: '--global',
            shortAlias: '-g',
          },
          {
            description: 'How deep should levels of dependencies be inspected. Infinity is default. 0 would mean top-level dependencies only',
            name: '--depth <number>',
          },
          {
            description: 'Ignore version ranges in package.json',
            name: '--latest',
            shortAlias: '-L',
          },
          {
            description: 'Update packages only in "dependencies" and "optionalDependencies"',
            name: '--prod',
            shortAlias: '-P',
          },
          {
            description: 'Update packages only in "devDependencies"',
            name: '--dev',
            shortAlias: '-D',
          },
          {
            description: 'Don\'t update packages in "optionalDependencies"',
            name: '--no-optional',
          },
          {
            description: 'Tries to link all packages from the workspace. \
Versions are updated to match the versions of packages inside the workspace. \
If specific packages are updated, the command will fail if any of the updated \
dependencies is not found inside the workspace',
            name: '--workspace',
          },
          {
            description: 'Show outdated dependencies and select which ones to update',
            name: '--interactive',
            shortAlias: '-i',
          },
          OPTIONS.globalDir,
          ...UNIVERSAL_OPTIONS,
        ],
      },
      FILTERING,
    ],
    url: docsUrl('update'),
    usages: ['pnpm update [-g] [<pkg>...]'],
  })
}

export type UpdateCommandOptions = InstallCommandOptions & {
  include?: IncludedDependencies
  interactive?: boolean
  latest?: boolean
  packageVulnerabilityAudit?: PackageVulnerabilityAudit
}

export async function handler (
  opts: UpdateCommandOptions,
  params: string[] = [],
  commands?: CommandHandlerMap
): Promise<string | undefined> {
  if (opts.global) {
    if (!opts.bin) {
      throw new PnpmError('NO_GLOBAL_BIN_DIR', 'Unable to find the global bin directory', {
        hint: 'Run "pnpm setup" to create it automatically, or set the global-bin-dir setting, or the PNPM_HOME env variable. The global bin directory should be in the PATH.',
      })
    }
    return handleGlobalUpdate({
      ...opts,
      ...createGlobalPolicyCallbacks(opts),
    }, params, commands ?? {})
  }
  const rebuildHandler = commands?.rebuild
  if (opts.interactive) {
    return interactiveUpdate(params, opts, rebuildHandler)
  }
  return update(params, opts, rebuildHandler) as Promise<undefined>
}

async function interactiveUpdate (
  input: string[],
  opts: UpdateCommandOptions,
  rebuildHandler?: CommandHandler
): Promise<string | undefined> {
  const include = makeIncludeDependenciesFromCLI(opts.cliOptions)
  const projects = (opts.selectedProjectsGraph != null)
    ? Object.values(opts.selectedProjectsGraph).map((wsPkg) => wsPkg.package)
    : [
      {
        rootDir: opts.dir as ProjectRootDir,
        manifest: await readProjectManifestOnly(opts.dir, opts),
      },
    ]
  const outdatedPkgsOfProjects = await outdatedDepsOfProjects(projects, input, {
    ...opts,
    compatible: opts.latest !== true,
    ignoreDependencies: opts.updateConfig?.ignoreDependencies,
    include,
    retry: {
      factor: opts.fetchRetryFactor,
      maxTimeout: opts.fetchRetryMaxtimeout,
      minTimeout: opts.fetchRetryMintimeout,
      retries: opts.fetchRetries,
    },
    timeout: opts.fetchTimeout,
  })
  const workspacesEnabled = !!opts.workspaceDir
  const choiceGroups = getUpdateChoices(unnest(outdatedPkgsOfProjects), workspacesEnabled)
  if (choiceGroups.length === 0) {
    if (opts.latest) {
      return 'All of your dependencies are already up to date'
    }
    return 'All of your dependencies are already up to date inside the specified ranges. Use the --latest option to update the ranges in package.json'
  }

  const flatChoices: Array<Separator | { name: string; value: string; disabled?: boolean | string }> = []
  for (const group of choiceGroups) {
    flatChoices.push(new Separator(chalk.bold(`── ${group.message} ──`)))
    for (const choice of group.choices) {
      if (choice.disabled) {
        flatChoices.push(new Separator(`  ${choice.message ?? choice.name}`))
      } else {
        flatChoices.push({
          name: choice.message,
          value: choice.value,
        })
      }
    }
  }

  const message = 'Choose which packages to update ' +
    `(Press ${chalk.cyan('<space>')} to select, ` +
    `${chalk.cyan('<a>')} to toggle all, ` +
    `${chalk.cyan('<i>')} to invert selection)\n\nEnter to start updating. Ctrl-c to cancel.`
  let updatePkgNames: string[]
  try {
    updatePkgNames = await checkbox({
      choices: flatChoices,
      pageSize: interactivePromptPageSize(),
      message,
      required: true,
      validate: (values) => {
        if (values.length === 0) {
          return 'You must choose at least one package.'
        }
        return true
      },
      theme: {
        icon: { checked: '●', unchecked: '○', cursor: '❯' },
        style: {
          highlight: (text: string) => text,
        },
        keybindings: ['vim'],
      },
    })
  } catch (err) {
    if (err instanceof Error && err.name === 'ExitPromptError') {
      globalInfo('Update canceled')
      process.exit(0)
    }
    throw err
  }

  return update(updatePkgNames, opts, rebuildHandler) as Promise<undefined>
}

async function update (
  dependencies: string[],
  opts: UpdateCommandOptions,
  rebuildHandler?: CommandHandler
): Promise<void> {
  if (opts.latest) {
    const dependenciesWithTags = dependencies.filter((name) => parseUpdateParam(name).versionSpec != null)
    if (dependenciesWithTags.length) {
      throw new PnpmError('LATEST_WITH_SPEC', `Specs are not allowed to be used with --latest (${dependenciesWithTags.join(', ')})`)
    }
  }
  const includeDirect = makeIncludeDependenciesFromCLI(opts.cliOptions)
  // include is always all-true for updates: updates should not change which
  // dep types the modules directory supports. The filtering of which deps to
  // actually resolve/update is handled by includeDirect (from CLI flags).
  // This matches the original behavior where rawConfig didn't have derived
  // values like dev=false from --prod, so include defaulted to all-true.
  const include = {
    dependencies: true,
    devDependencies: true,
    optionalDependencies: true,
  }
  const depth = opts.depth ?? Infinity
  let updateMatching: UpdateMatchingFunction | undefined
  if (opts.packageVulnerabilityAudit != null) {
    const { packageVulnerabilityAudit } = opts
    updateMatching = (pkgName: string, version?: string) => version != null && packageVulnerabilityAudit.isVulnerable(pkgName, version)
  } else if (
    (dependencies.length > 0) && dependencies.every(dep => !dep.substring(1).includes('@')) && depth > 0 && !opts.latest
  ) {
    updateMatching = createMatcher(dependencies)
  }
  return installDeps({
    ...opts,
    rebuildHandler,
    allowNew: false,
    depth,
    ignoreCurrentSpecifiers: false,
    include,
    includeDirect,
    update: true,
    updateToLatest: opts.latest,
    updateMatching,
    updatePackageManifest: opts.save !== false,
    resolutionMode: opts.save === false ? 'highest' : opts.resolutionMode,
  }, dependencies)
}

function makeIncludeDependenciesFromCLI (opts: {
  production?: boolean
  dev?: boolean
  optional?: boolean
}): IncludedDependencies {
  return {
    dependencies: opts.production === true || (opts.dev !== true && opts.optional !== true),
    devDependencies: opts.dev === true || (opts.production !== true && opts.optional !== true),
    optionalDependencies: opts.optional === true || (opts.production !== true && opts.dev !== true),
  }
}

```

(+279 more files reference the changed code)
Repository Map
.pnpmfile.cjs
building/after-install/src/extendBuildOptions.ts
building/after-install/src/index.ts
building/commands/src/policy/approveBuilds.ts
building/commands/src/policy/getAutomaticallyIgnoredBuilds.ts
building/commands/src/policy/ignoredBuilds.ts
building/commands/src/policy/index.ts
building/during-install/src/buildSequence.ts
building/during-install/src/index.ts
building/policy/src/index.ts
building/policy/test/index.ts
commitlint.config.cjs
core/types/src/config.ts
core/types/src/index.ts
core/types/src/misc.ts
core/types/src/options.ts
core/types/src/package.ts
core/types/src/peerDependencyIssues.ts
core/types/src/project.ts
deps/compliance/commands/test/licenses/index.ts
deps/graph-builder/src/index.ts
deps/graph-builder/src/iteratePkgsForVirtualStore.ts
deps/graph-builder/src/lockfileToDepGraph.ts
deps/graph-hasher/src/index.ts
deps/graph-hasher/test/calcGraphNodeHash.test.ts
deps/graph-hasher/test/calcLeafGlobalVirtualStorePath.test.ts
deps/graph-hasher/test/index.ts
deps/graph-hasher/test/lockfileToDepGraph.test.ts
deps/path/src/index.ts
eslint.config.mjs
exec/commands/test/create.ts
exec/commands/test/createInstallArgs.test.ts
exec/commands/test/dlx.createCacheKey.test.ts
exec/commands/test/dlx.e2e.ts
exec/commands/test/dlx.ts
exec/commands/test/exec.e2e.ts
exec/commands/test/exec.logs.ts
exec/commands/test/exec.ts
exec/commands/test/index.ts
exec/commands/test/makeEnv.test.ts
exec/commands/test/runCompletion.ts
exec/commands/test/runDepsStatusCheck.test.ts
exec/commands/test/runRecursive.ts
exec/commands/test/testRecursive.ts
exec/commands/test/verifyDepsBeforeRun.ts
exec/prepare-package/src/index.ts
exec/prepare-package/test/index.ts
fetching/git-fetcher/src/index.ts
fetching/git-fetcher/test/index.ts
fetching/tarball-fetcher/src/gitHostedTarballFetcher.ts
fetching/tarball-fetcher/src/index.ts
fetching/tarball-fetcher/src/localTarballFetcher.ts
fetching/tarball-fetcher/src/remoteTarballFetcher.ts
fetching/tarball-fetcher/test/fetch.ts
fix-duplicates.mjs
installing/commands/src/add.ts
installing/commands/src/createProjectManifestWriter.ts
installing/commands/src/dedupe.ts
installing/commands/src/fetch.ts
installing/commands/src/getFetchFullMetadata.ts
installing/commands/src/getPinnedVersion.ts
installing/commands/src/getSaveType.ts
installing/commands/src/handleIgnoredBuilds.ts
installing/commands/src/index.ts
installing/commands/src/install.ts
installing/commands/src/installDeps.ts
installing/commands/src/link.ts
installing/commands/src/policyHandlers.ts
installing/commands/src/prune.ts
installing/commands/src/recursive.ts
installing/commands/src/remove.ts
installing/commands/src/resolutionPolicyManifest.ts
installing/commands/src/runPacquet.ts
installing/commands/src/unlink.ts
installing/commands/src/updateWorkspaceDependencies.ts
installing/commands/src/verifyPacquetIdentity.ts
installing/deps-installer/src/install/checkCustomResolverForceResolve.ts
installing/deps-installer/src/install/extendInstallOptions.ts
installing/deps-installer/src/install/index.ts
installing/deps-installer/src/install/link.ts
installing/deps-installer/src/install/recordLockfileVerified.ts
installing/deps-installer/src/install/reportPeerDependencyIssues.ts
installing/deps-installer/src/install/validateModules.ts
installing/deps-installer/src/install/verifyLockfileResolutions.ts
installing/deps-installer/src/install/verifyLockfileResolutionsCache.ts
installing/deps-installer/src/install/writeLockfilesAndRecordVerified.ts
installing/deps-installer/src/install/writeWantedLockfileAndRecordVerified.ts
installing/deps-installer/test/install/aliases.ts
installing/deps-installer/test/install/auth.ts
installing/deps-installer/test/install/autoInstallPeers.ts
installing/deps-installer/test/install/blockExoticSubdeps.ts
installing/deps-installer/test/install/bunRuntime.ts
installing/deps-installer/test/install/bundledDependencies.ts
installing/deps-installer/test/install/checkCustomResolverForceResolve.ts
installing/deps-installer/test/install/customResolvers.ts
installing/deps-installer/test/install/cyclicPeerDeterminism.ts
installing/deps-installer/test/install/dedupe.ts
installing/deps-installer/test/install/dedupeDirectDeps.ts
installing/deps-installer/test/install/dedupeInWorkspace.ts
installing/deps-installer/test/install/deepRecursive.ts
installing/deps-installer/test/install/defaultPeerDependencies.ts
installing/deps-installer/test/install/denoRuntime.ts
installing/deps-installer/test/install/errors.ts
installing/deps-installer/test/install/excludeLinksFromLockfile.ts
installing/deps-installer/test/install/fixLockfile.ts
installing/deps-installer/test/install/fromRepo.ts
installing/deps-installer/test/install/fromTarball.ts
installing/deps-installer/test/install/frozenLockfile.ts
installing/deps-installer/test/install/gitBranchLockfile.test.ts
installing/deps-installer/test/install/globalVirtualStore.ts
installing/deps-installer/test/install/hoist.ts
installing/deps-installer/test/install/hooks.ts
installing/deps-installer/test/install/ignoredOptionalDependencies.ts
installing/deps-installer/test/install/injectLocalPackages.ts
installing/deps-installer/test/install/injectWorkspacePackagesPersistence.test.ts
installing/deps-installer/test/install/installationChecks.ts
installing/deps-installer/test/install/lifecycleScripts.ts
installing/deps-installer/test/install/local.ts
installing/deps-installer/test/install/lockfileDir.ts
installing/deps-installer/test/install/lockfileOnly.ts
installing/deps-installer/test/install/minimumReleaseAge.ts
installing/deps-installer/test/install/misc.ts
installing/deps-installer/test/install/modulesCache.ts
installing/deps-installer/test/install/modulesDir.ts
installing/deps-installer/test/install/multipleImporters.ts
installing/deps-installer/test/install/nodeRuntime.ts
installing/deps-installer/test/install/only.ts
installing/deps-installer/test/install/optionalDependencies.ts
installing/deps-installer/test/install/overrides.ts
installing/deps-installer/test/install/packageExtensions.ts
installing/deps-installer/test/install/patch.ts
installing/deps-installer/test/install/peerDependencies.ts
installing/deps-installer/test/install/prereleaseWeights.ts
installing/deps-installer/test/install/recordLockfileVerified.ts
installing/deps-installer/test/install/reporting.ts
installing/deps-installer/test/install/resolutionMode.ts
installing/deps-installer/test/install/setExtraNodePath.ts
installing/deps-installer/test/install/sideEffects.ts
installing/deps-installer/test/install/stats.ts
installing/deps-installer/test/install/trustLockfile.ts
installing/deps-installer/test/install/update.ts
installing/deps-installer/test/install/updatingPkgJson.ts
installing/deps-installer/test/install/validatePeerDependencies.ts
installing/deps-installer/test/install/verifyLockfileResolutions.ts
installing/deps-installer/test/install/verifyLockfileResolutionsCache.ts
installing/deps-installer/test/install/virtualStoreDirMaxLength.ts
installing/deps-restorer/src/extendProjectsWithTargetDirs.ts
installing/deps-restorer/src/index.ts
installing/deps-restorer/src/linkHoistedModules.ts
installing/deps-restorer/src/lockfileToHoistedDepGraph.ts
lockfile/fs/src/envLockfile.ts
lockfile/fs/src/existsWantedLockfile.ts
lockfile/fs/src/getLockfileImporterId.ts
lockfile/fs/src/gitBranchLockfile.ts
lockfile/fs/src/gitMergeFile.ts
lockfile/fs/src/index.ts
lockfile/fs/src/lockfileFormatConverters.ts
lockfile/fs/src/lockfileName.ts
lockfile/fs/src/logger.ts
lockfile/fs/src/read.ts
lockfile/fs/src/sortLockfileKeys.ts
lockfile/fs/src/write.ts
lockfile/fs/src/yamlDocuments.ts
lockfile/utils/src/index.ts
lockfile/utils/src/nameVerFromPkgSnapshot.ts
lockfile/utils/src/packageIdFromSnapshot.ts
lockfile/utils/src/packageIsIndependent.ts
lockfile/utils/src/pkgSnapshotToResolution.ts
lockfile/utils/src/refIsLocalTarball.ts
lockfile/utils/src/toLockfileResolution.ts
pnpm/test/bin.ts
pnpm/test/ci.ts
pnpm/test/clean.ts
pnpm/test/cli.ts
pnpm/test/config.ts
pnpm/test/configurationalDependencies.test.ts
pnpm/test/deploy.ts
pnpm/test/dlx.ts
pnpm/test/errorHandler.test.ts
pnpm/test/exec.ts
pnpm/test/filterProd.test.ts
pnpm/test/formatError.test.ts
pnpm/test/getConfig.test.ts
pnpm/test/help.spec.ts
pnpm/test/hooks.ts
pnpm/test/list.ts
pnpm/test/packageManagerCheck.test.ts
pnpm/test/root.ts
pnpm/test/run.ts
pnpm/test/saveCatalog.ts
pnpm/test/sbom.ts
pnpm/test/switchingVersions.test.ts
pnpm/test/syncInjectedDepsAfterScripts-bin.ts
pnpm/test/syncInjectedDepsAfterScripts.ts
pnpm/test/uninstall.ts
pnpm/test/update.ts
pnpm/test/withCommand.test.ts
resolving/git-resolver/src/createGitHostedPkgId.ts
resolving/git-resolver/src/index.ts
resolving/git-resolver/src/parseBareSpecifier.ts
resolving/git-resolver/test/createGitHostedPkgId.test.ts
resolving/git-resolver/test/index.ts
resolving/git-resolver/test/parsePref.test.ts
.husky/  (1 files)
.meta-updater/  (1 files)
.meta-updater/src/  (1 files)
__typings__/  (3 files)
__utils__/assert-project/  (3 files)
__utils__/assert-store/  (2 files)
__utils__/build-artifacts/  (1 files)
__utils__/eslint-config/  (3 files)
__utils__/get-release-text/  (1 files)
__utils__/jest-config/  (7 files)
__utils__/prepare/  (1 files)
__utils__/prepare-temp-dir/  (1 files)
__utils__/scripts/  (4 files)
__utils__/test-fixtures/  (1 files)
__utils__/test-ipc-server/  (6 files)
auth/commands/  (6 files)
bins/linker/  (4 files)
bins/remover/  (2 files)
bins/resolver/  (3 files)
building/commands/  (3 files)
building/during-install/  (1 files)
building/pkg-requires-build/  (1 files)
cache/api/  (4 files)
cache/commands/  (5 files)
catalogs/config/  (3 files)
catalogs/protocol-parser/  (3 files)
catalogs/resolver/  (4 files)
catalogs/types/  (1 files)
cli/command/  (1 files)
cli/commands/  (12 files)
cli/common-cli-options-help/  (1 files)
cli/default-reporter/  (45 files)
cli/meta/  (2 files)
cli/parse-cli-args/  (2 files)
cli/utils/  (7 files)
config/commands/  (18 files)
config/matcher/  (2 files)
config/normalize-registries/  (1 files)
config/package-is-installable/  (5 files)
config/parse-overrides/  (2 files)
config/pick-registry-for-package/  (2 files)
config/reader/  (34 files)
config/version-policy/  (2 files)
config/writer/  (1 files)
core/constants/  (1 files)
core/core-loggers/  (27 files)
core/error/  (2 files)
core/logger/  (8 files)
crypto/hash/  (2 files)
crypto/integrity/  (2 files)
crypto/object-hasher/  (2 files)
crypto/shasums-file/  (6 files)
deps/compliance/  (62 files)
deps/graph-sequencer/  (2 files)
deps/inspection/  (74 files)
deps/path/  (2 files)
deps/peer-range/  (1 files)
deps/security/  (5 files)
deps/status/  (8 files)
engine/pm/  (12 files)
engine/runtime/  (25 files)
exec/commands/  (14 files)
exec/lifecycle/  (4 files)
exec/pnpm-cli-runner/  (1 files)
fetching/binary-fetcher/  (3 files)
fetching/directory-fetcher/  (2 files)
fetching/fetcher-base/  (1 files)
fetching/pick-fetcher/  (3 files)
fetching/tarball-fetcher/  (2 files)
fetching/types/  (1 files)
fs/graceful-fs/  (1 files)
fs/hard-link-dir/  (2 files)
fs/indexed-pkg-importer/  (6 files)
fs/is-empty-dir-or-nothing/  (2 files)
fs/packlist/  (1 files)
fs/read-modules-dir/  (1 files)
fs/symlink-dependency/  (5 files)
global/commands/  (13 files)
global/packages/  (4 files)
hooks/pnpmfile/  (5 files)
hooks/read-package-hook/  (11 files)
hooks/types/  (3 files)
installing/client/  (2 files)
installing/commands/  (34 files)
installing/context/  (3 files)
installing/dedupe/  (8 files)
installing/deps-installer/  (32 files)
installing/deps-resolver/  (35 files)
installing/deps-restorer/  (2 files)
installing/env-installer/  (13 files)
installing/linking/  (8 files)
installing/modules-yaml/  (2 files)
installing/package-requester/  (3 files)
installing/read-projects-context/  (1 files)
lockfile/detect-dep-types/  (1 files)
lockfile/filtering/  (7 files)
lockfile/fs/  (10 files)
lockfile/make-dedicated-lockfile/  (4 files)
lockfile/merger/  (2 files)
lockfile/preferred-versions/  (1 files)
lockfile/pruner/  (2 files)
lockfile/settings-checker/  (4 files)
lockfile/to-pnp/  (2 files)
lockfile/types/  (2 files)
lockfile/utils/  (3 files)
lockfile/verification/  (11 files)
lockfile/walker/  (1 files)
modules-mounter/daemon/  (8 files)
network/auth-header/  (10 files)
network/fetch/  (6 files)
network/git-utils/  (3 files)
network/web-auth/  (11 files)
object/key-sorting/  (2 files)
object/property-path/  (24 files)
pacquet/npm/  (1 files)
patching/apply-patch/  (2 files)
patching/commands/  (12 files)
patching/config/  (8 files)
patching/types/  (1 files)
pkg-manifest/commands/  (5 files)
pkg-manifest/reader/  (2 files)
pkg-manifest/utils/  (14 files)
pnpm/  (3 files)
pnpm/artifacts/  (6 files)
pnpm/bin/  (4 files)
pnpm/dev/  (1 files)
pnpm/src/  (28 files)
pnpm/test/  (44 files)
pnpr/.fixtures/  (68 files)
pnpr/client/  (3 files)
pnpr/npm/  (1 files)
registry-access/client/  (3 files)
registry-access/commands/  (24 files)
releasing/commands/  (67 files)
releasing/exportable-manifest/  (13 files)
resolving/default-resolver/  (4 files)
resolving/git-resolver/  (3 files)
resolving/jsr-specifier-parser/  (2 files)
resolving/local-resolver/  (4 files)
resolving/npm-resolver/  (32 files)
resolving/parse-wanted-dependency/  (1 files)
resolving/registry/  (3 files)
resolving/resolver-base/  (1 files)
resolving/tarball-resolver/  (3 files)
shell/path/  (2 files)
store/cafs/  (15 files)
store/cafs-types/  (1 files)
store/commands/  (22 files)
store/connection-manager/  (2 files)
store/controller/  (7 files)
store/controller-types/  (1 files)
store/create-cafs-store/  (1 files)
store/index/  (2 files)
store/path/  (2 files)
store/pkg-finder/  (2 files)
testing/command-defaults/  (1 files)
testing/mock-agent/  (1 files)
testing/registry-mock/  (1 files)
testing/temp-store/  (1 files)
text/comments-parser/  (5 files)
text/naming-cases/  (3 files)
text/tree-renderer/  (2 files)
worker/src/  (5 files)
worker/test/  (1 files)
workspace/commands/  (5 files)
workspace/injected-deps-syncer/  (6 
... (1495 source files in total)
Package Manifests (Dependencies, scripts, build configuration)
### package.json
```
{
  "name": "monorepo-root",
  "private": true,
  "scripts": {
    "bump": "node __utils__/scripts/src/bump.ts && pn update-manifests",
    "changeset": "changeset",
    "prepare": "husky",
    "pretest": "pn compile-only && pn prepare-fixtures",
    "prepare-fixtures": "pn --dir=__fixtures__ prepareFixtures",
    "lint": "pn spellcheck && pn lint:meta && pn lint:ts",
    "spellcheck": "cspell \"**/*.ts\" \"**/README.md\" \".changeset/*.md\" --no-progress",
    "lint:ts": "eslint \"**/src/**/*.ts\" \"**/test/**/*.ts\" --cache",
    "test-all": "pn pretest && pn lint && pn test-pkgs-all",
    "ci:test-all": "pn prepare-fixtures && pn test-pkgs-all",
    "remove-temp-dir": "shx rm -rf ../pnpm_tmp",
    "test-pkgs-all": "pn remove-temp-dir && pn --no-sort --workspace-concurrency=1 -r .test",
    "test-branch": "pn pretest && pn lint && git remote set-branches --add origin main && git fetch origin main && pn test-pkgs-branch",
    "ci:test-branch": "pn prepare-fixtures && pn test-pkgs-branch",
    "test-pkgs-branch": "pn remove-temp-dir && pn --workspace-concurrency=1 --filter=...[origin/main] --no-sort --if-present .test",
    "compile-only": "tsgo --build workspace/workspace-manifest-reader workspace/projects-reader && pnx node@runtime:26.3.0 __utils__/scripts/src/typecheck-only.ts && pn -F=pnpm compile",
    "compile": "pn compile-only && pn update-manifests",
    "build:pacquet": "cargo build --release --bin pacquet",
    "make-lcov": "shx mkdir -p coverage && lcov-result-merger './packages/*/coverage/lcov.info' 'coverage/lcov.info'",
    "update-manifests": "pn meta-updater && pn install",
    "meta-updater": "pn --filter=@pnpm-private/updater compile && pn exec meta-updater",
    "lint:meta": "pn meta-updater --test",
    "copy-artifacts": "node __utils__/scripts/src/copy-artifacts.ts",
    "make-release-description": "pn --filter=@pnpm/get-release-text run write-release-text",
    "check:npm-signing-keys": "node deps/security/signatures/scripts/update-npm-signing-keys.mjs",
    "update:npm-signing-keys": "node deps/security/signatures/scripts/update-npm-signing-keys.mjs --update",
    "check:node-release-keys": "node crypto/shasums-file/scripts/update-node-release-keys.mjs",
    "update:node-release-keys": "node crypto/shasums-file/scripts/update-node-release-keys.mjs --update",
    "release": "pn --filter=@pnpm/exe run build-artifacts && pn --filter=@pnpm/exe publish --tag=next-11 --access=public --provenance && pn publish --filter=!pnpm --filter=!@pnpm/exe --access=public --provenance && pn publish --filter=pnpm --tag=next-11 --access=public --provenance",
    "dev-setup": "pn -C=./pnpm/dev link -g"
  },
  "devDependencies": {
    "@changesets/cli": "catalog:",
    "@commitlint/cli": "catalog:",
    "@commitlint/config-conventional": "catalog:",
    "@commitlint/prompt-cli": "catalog:",
    "@pnpm/eslint-config": "workspace:*",
    "@pnpm/jest-config": "workspace:*",
    "@pnpm/meta-updater": "catalog:",
    "@pnpm/tgz-fixtures": "catalog:",
    "@pnpm/tsconfig": "workspace:*",
    "@types/jest": "catalog:",
    "@types/node": "catalog:",
    "@types/picomatch": "catalog:",
    "@typescript/native-preview": "catalog:",
    "c8": "catalog:",
    "concurrently": "catalog:",
    "cross-env": "catalog:",
    "cspell": "catalog:",
    "eslint": "catalog:",
    "eslint-plugin-regexp": "catalog:",
    "husky": "catalog:",
    "jest": "catalog:",
    "keyv": "catalog:",
    "lcov-result-merger": "catalog:",
    "rimraf": "catalog:",
    "shx": "catalog:",
    "typescript": "catalog:"
  },
  "packageManager": "pnpm@11.5.2",
  "devEngines": {
    "packageManager": {
      "name": "pnpm",
      "version": "11.5.2",
      "onFail": "download"
    },
    "runtime": {
      "name": "node",
      "version": "26.3.0",
      "onFail": "download"
    }
  }
}

```
Context & Existing Test Patterns
Existing test files touched by the patch: building/policy/test/index.ts, deps/compliance/commands/test/licenses/fixtures/with-git-protocol-peer-deps/package.json, deps/compliance/commands/test/licenses/index.ts, deps/graph-hasher/test/allowBuildIdentity.test.ts, exec/commands/test/dlx.e2e.ts, exec/prepare-package/test/index.ts, fetching/git-fetcher/test/index.ts, fetching/tarball-fetcher/test/fetch.ts, installing/deps-installer/test/install/lifecycleScripts.ts, installing/deps-installer/test/install/verifyLockfileResolutions.ts, pnpm/test/dlx.ts, resolving/git-resolver/test/createGitHostedPkgId.test.ts
Repository top-level entries: .cargo, .changeset, .changeset-released, .devcontainer, .editorconfig, .git-wt, .gitattributes, .github, .gitignore, .husky, .meta-updater, .pnpmfile.cjs, .pr_agent.toml, .taplo.toml, .typos.toml, AGENTS.md, CLAUDE.md, CODE_OF_CONDUCT.md, CONTRIBUTING.md, Cargo.lock, Cargo.toml, FUNDING.json, LICENSE, README.md, SECURITY.md, __fixtures__, __patches__, __typecheck__, __typings__, __utils__, auth, benchmarks, bins, building, cache, catalogs, cli, commitlint.config.cjs, config, core, crypto, cspell.json, deny.toml, deps, docker, dylint.toml, engine, eslint.config.mjs, exec, fetching, fix-duplicates.mjs, fs, global, hooks, installing, justfile, lockfile, modules-mounter, network, object
Project's own test patterns and conventions:
### pnpm/test/install/global.ts
```
import fs from 'node:fs'
import path from 'node:path'

import { expect, test } from '@jest/globals'
import { GLOBAL_LAYOUT_VERSION } from '@pnpm/constants'
import { prepare } from '@pnpm/prepare'
import type { ProjectManifest } from '@pnpm/types'
import isWindows from 'is-windows'
import PATH_NAME from 'path-name'
import { readYamlFileSync } from 'read-yaml-file'
import { writeYamlFileSync } from 'write-yaml-file'

import {
  addDistTag,
  execPnpm,
  execPnpmSync,
} from '../utils/index.js'

const PUBLIC_REGISTRY = '--config.registry=https://registry.npmjs.org/'
const IMMATURE_FOR_EVERYTHING = 1_000_000_000

function globalPkgDir (pnpmHome: string): string {
  return path.join(pnpmHome, 'global', GLOBAL_LAYOUT_VERSION)
}

/**
 * Find an installed global package in the flat isolated directory structure.
 * Scans globalDir for hash symlinks, resolves them,
 * and returns the path to the package's node_modules entry.
 */
function findGlobalPkg (globalDir: string, pkgName: string): string | null {
  return findGlobalPkgInstall(globalDir, pkgName)?.pkgPath ?? null
}

function findGlobalPkgInstall (globalDir: string, pkgName: string): { installDir: string, pkgPath: string } | null {
  let entries: fs.Dirent[]
  try {
    entries = fs.readdirSync(globalDir, { withFileTypes: true })
  } catch {
    return null
  }
  for (const entry of entries) {
    if (!entry.isSymbolicLink()) continue
    let installDir: string
    try {
      installDir = fs.realpathSync(path.join(globalDir, entry.name))
    } catch {
      continue
    }
    let pkgJson: { dependencies?: Record<string, string> }
    try {
      pkgJson = JSON.parse(fs.readFileSync(path.join(installDir, 'package.json'), 'utf-8'))
    } catch {
      continue
    }
    if (pkgJson.dependencies?.[pkgName]) {
      return { installDir, pkgPath: path.join(installDir, 'node_modules', pkgName) }
    }
  }
  return null
}

test('global installation', async () => {
  prepare()
  const global = path.resolve('..', 'global')
  const pnpmHome = path.join(global, 'pnpm')
  fs.mkdirSync(global)

  const env = { [PATH_NAME]: path.join(pnpmHome, 'bin'), PNPM_HOME: pnpmHome, XDG_DATA_HOME: global }

  await execPnpm(['add', '--global', 'is-positive'], { env })

  // there was an issue when subsequent installations were removing everything installed prior
  // https://github.com/pnpm/pnpm/issues/808
  await execPnpm(['add', '--global', 'is-negative'], { env })

  const isPositivePath = findGlobalPkg(globalPkgDir(pnpmHome), 'is-positive')
  expect(isPositivePath).toBeTruthy()
  const { default: isPositive } = await import(isPositivePath!)
  expect(typeof isPositive).toBe('function')

  const isNegativePath = findGlobalPkg(globalPkgDir(pnpmHome), 'is-negative')
  expect(isNegativePath).toBeTruthy()
  const { default: isNegative } = await import(isNegativePath!)
  expect(typeof isNegative).toBe('function')
})

test('global install warns when project has packageManager configured', async () => {
  prepare({
    name: 'project',
    version: '1.0.0',
    packageManager: 'yarn@4.0.0',
  })

  const global = path.resolve('..', 'global')
  const pnpmHome = path.join(global, 'pnpm')
  fs.mkdirSync(global)

  const env = { [PATH_NAME]: path.join(pnpmHome, 'bin'), PNPM_HOME: pnpmHome, XDG_DATA_HOME: global }

  const { status } = execPnpmSync([
    'add',
    '--global',
    'is-positive',
  ], { env })

  expect(status).toBe(0)
})

test('global installation to custom directory with --global-dir', async () => {
  prepare()
  const global = path.resolve('..', 'global')
  const pnpmHome = path.join(global, 'pnpm')
  const env = { [PATH_NAME]: path.join(pnpmHome, 'bin'), PNPM_HOME: pnpmHome }

  await execPnpm(['add', '--global', '--global-dir=../global', 'is-positive'], { env })

  const isPositivePath = findGlobalPkg(path.join(global, 'v11'), 'is-positive')
  expect(isPositivePath).toBeTruthy()
  const { default: isPositive } = await import(isPositivePath!)
  expect(typeof isPositive).toBe('function')
})

test('always install latest when doing global installation without spec', async () => {
  prepare()
  await addDistTag('@pnpm.e2e/peer-c', '2.0.0', 'latest')

  const global = path.resolve('..', 'global')
  const pnpmHome = path.join(global, 'pnpm')
  fs.mkdirSync(global)

  const env = { [PATH_NAME]: path.join(pnpmHome, 'bin'), PNPM_HOME: pnpmHome, XDG_DATA_HOME: global }

  await execPnpm(['add', '-g', '@pnpm.e2e/peer-c@1'], { env })
  await execPnpm(['add', '-g', '@pnpm.e2e/peer-c'], { env })

  const peerCPath = findGlobalPkg(globalPkgDir(pnpmHome), '@pnpm.e2e/peer-c')
  expect(peerCPath).toBeTruthy()
  expect((await import(path.join(peerCPath!, 'package.json'))).default.version).toBe('2.0.0')
})

test('run lifecycle events of global packages in correct working directory', async () => {
  if (isWindows()) {
    // Skipping this test on Windows because "$npm_execpath run create-file" will fail on Windows
    return
  }

  prepare()
  const global = path.resolve('..', 'global')
  const pnpmHome = path.join(global, 'pnpm')
  fs.mkdirSync(pnpmHome, { recursive: true })

  const env = {
    [PATH_NAME]: `${path.join(pnpmHome, 'bin')}${path.delimiter}${process.env[PATH_NAME]!}`,
    PNPM_HOME: pnpmHome,
    XDG_DATA_HOME: global,
  }

  await execPnpm(['add', '-g', '--allow-build=@pnpm.e2e/postinstall-calls-pnpm', '@pnpm.e2e/postinstall-calls-pnpm@1.0.0'], { env })

  const pkgPath = findGlobalPkg(globalPkgDir(pnpmHome), '@pnpm.e2e/postinstall-calls-pnpm')
  expect(pkgPath).toBeTruthy()
  expect(fs.existsSync(path.join(pkgPath!, 'created-by-postinstall'))).toBeTruthy()
})

// Regression test for https://github.com/pnpm/pnpm/issues/11403.
//
// When `pnpm add -g` installs a package whose build is not pre-allowed,
// the install succeeds with the build ignored and `globalAdd` then runs
// `promptApproveGlobalBuilds`. If the user approves, `approve-builds`
// runs `install.handler` against the install directory — and that is the
// install run that crashed with `ENOENT` because `modulesDir` was being
// forwarded as an absolute path and re-joined with `lockfileDir`.
//
// `PNPM_AUTO_APPROVE_BUILDS_FOR_TESTS=1` lets the test drive this flow
// non-interactively: `promptApproveGlobalBuilds` skips the TTY check and
// passes `all: true` so `approve-builds` approves every pending build
// without prompting. The post-approval install must complete and the
// build artifact must end up in the global install dir.
test('approve-builds during global add does not produce a doubled modules path', async () => {
  prepare()
  const global = path.resolve('..', 'global')
  const pnpmHome = path.join(global, 'pnpm')
  fs.mkdirSync(pnpmHome, { recursive: true })

  const env = {
    [PATH_NAME]: `${path.join(pnpmHome, 'bin')}${path.delimiter}${process.env[PATH_NAME]!}`,
    PNPM_HOME: pnpmHome,
    XDG_DATA_HOME: global,
    PNPM_AUTO_APPROVE_BUILDS_FOR_TESTS: '1',
  }

  // Note: no --allow-build here. The first install records the build in
  // `ignoredBuilds`; `promptApproveGlobalBuilds` then drives the
  // approve → install chain that produced the doubled-path crash.
  await execPnpm([
    'add',
    '-g',
    '@pnpm.e2e/install-script-example@1.0.0',
  ], { env })

  const pkgPath = findGlobalPkg(globalPkgDir(pnpmHome), '@pnpm.e2e/install-script-example')
  expect(pkgPath).toBeTruthy()
  // The build artifacts are only present if the post-approval install
  // ran the package's install scripts.
  expect(fs.existsSync(path.join(pkgPath!, 'generated-by-install.js'))).toBe(true)
})

// CONTEXT: dangerously-allow-all-builds has been removed from rc files, as a result, this test no longer applies
// TODO: Maybe we should create a yaml config file specifically for `--global`? After all, this test is to serve such use-cases
test.skip('dangerously-allow-all-builds=true in global config', async () => {
  // the directory structure below applies only to Linux
  if (process.platform !== 'linux') return

  const manifest: ProjectManifest = {
    name: 'local',
    version: '0.0.0',
    private: true,
  }

  const workspaceManifest: Record<string, unknown> = {
    allowBuilds: {}, // don't allow any dependencies to be built
  }

  const project = prepare(manifest)
  writeYamlFileSync('pnpm-workspace.yaml', workspaceManifest)

  const home = path.resolve('..', 'home/username')
  const cfgHome = path.resolve(home, '.config')
  const pnpmCfgDir = path.resolve(cfgHome, 'pnpm')
  const pnpmRcFile = path.join(pnpmCfgDir, 'rc')
  const global = path.resolve('..', 'global')
  const pnpmHome = path.join(global, 'pnpm')
  const globalDir = globalPkgDir(pnpmHome)
  fs.mkdirSync(pnpmCfgDir, { recursive: true })
  fs.writeFileSync(pnpmRcFile, [
    'reporter=append-only',
    'dangerously-allow-all-builds=true',
  ].join('\n'))

  const env = {
    [PATH_NAME]: `${path.join(pnpmHome, 'bin')}${path.delimiter}${process.env[PATH_NAME]!}`,
    HOME: home,
    XDG_CONFIG_HOME: cfgHome,
    PNPM_HOME: pnpmHome,
    XDG_DATA_HOME: global,
  }

  // global install should run scripts
  await execPnpm(['add', '-g', '@pnpm.e2e/postinstall-calls-pnpm@1.0.0'], { env })
  expect(fs.readdirSync(path.join(globalDir, 'node_modules/@pnpm.e2e/postinstall-calls-pnpm'))).toContain('created-by-postinstall')

  // local config should override global config
  await execPnpm(['add', '@pnpm.e2e/postinstall-calls-pnpm@1.0.0'], { env })
  expect(fs.readdirSync(path.resolve('node_modules/@pnpm.e2e/postinstall-calls-pnpm'))).not.toContain('created-by-postinstall')

  // global config should be used if local config did not specify
  delete workspaceManifest.allowBuilds
  writeYamlFileSync('pnpm-workspace.yaml', workspaceManifest)
  project.writePackageJson(manifest)
  fs.rmSync('node_modules', { recursive: true })
  fs.rmSync('pnpm-lock.yaml')
  await execPnpm(['add', '@pnpm.e2e/postinstall-calls-pnpm@1.0.0'], { env })
  expect(fs.readdirSync(path.resolve('node_modules/@pnpm.e2e/postinstall-calls-pnpm'))).toContain('created-by-postinstall')
})

// CONTEXT: dangerously-allow-all-builds has been removed from rc files, as a result, this test no longer applies
// TODO: Maybe we should create a yaml config file specifically for `--global`? After all, this test is to serve such use-cases
test.skip('dangerously-allow-all-builds=false in global config', async () => {
  // the directory structure below applies only to Linux
  if (process.platform !== 'linux') return

  const manifest: ProjectManifest = {
    name: 'local',
    version: '0.0.0',
    private: true,
  }

  const workspaceManifest: Record<string, unknown> = {
    allowBuilds: { '@pnpm.e2e/postinstall-calls-pnpm': true },
  }

  const project = prepare(manifest)
  writeYamlFileSync('pnpm-workspace.yaml', workspaceManifest)

  const home = path.resolve('..', 'home/username')
  const cfgHome = path.resolve(home, '.config')
  const pnpmCfgDir = path.resolve(cfgHome, 'pnpm')
  const pnpmRcFile = path.join(pnpmCfgDir, 'rc')
  const global = path.resolve('..', 'global')
  const pnpmHome = path.join(global, 'pnpm')
  const globalDir = globalPkgDir(pnpmHome)
  fs.mkdirSync(pnpmCfgDir, { recursive: true })
  fs.writeFileSync(pnpmRcFile, [
    'reporter=append-only',
    'dangerously-allow-all-builds=false',
  ].join('\n'))

  const env = {
    [PATH_NAME]: `${path.join(pnpmHome, 'bin')}${path.delimiter}${process.env[PATH_NAME]!}`,
    HOME: home,
    XDG_CONFIG_HOME: cfgHome,
    PNPM_HOME: pnpmHome,
    XDG_DATA_HOME: global,
  }

  // global install should run scripts
  await execPnpm(['add', '-g', '@pnpm.e2e/postinstall-calls-pnpm@1.0.0'], { env })
  expect(fs.readdirSync(path.join(globalDir, 'node_modules/@pnpm.e2e/postinstall-calls-pnpm'))).not.toContain('created-by-postinstall')

  // local config should override global config
  await execPnpm(['add', '@pnpm.e2e/postinstall-calls-pnpm@1.0.0'], { env })
  expect(fs.readdirSync(path.resolve('node_modules/@pnpm.e2e/postinstall-calls-pnpm'))).toContain('created-by-postinstall')

  // global config should be used if local confi
```
Your Deliverables
Artifact 1: instruction.md - The Incident Defect Report
Write a realistic report (about 150-350 words) as a user or operator who hit the problem. Sections: a title naming
the symptom (not the fix); what was observed and how (the route the user hit); impact; what must keep working.

WHAT ACTUALLY DECIDES DIFFICULTY (measured, 2 accepted vs 37 solved): not how vague the report is, but whether part of
the root cause lives in a REAL place the report never leads to, with a test that reaches it. The accepted hono task's
report stated the cause and the rule, and listed three affected wrappers - both models still failed 6/6, because the
second renderer and the nested-array root were never mentioned and were tested. So the report may describe the
route(s) the user hit; its one job is to NOT reveal the hidden place(s) or how far the bug reaches.

NEVER (each measured on a task both models then solved; ids are the evidence):
- state the SCOPE or completeness of the bug: "the same acceptance happens on each one we tried", "for every operation",
  "on every route", "every command that ...", "all three nodes". It tells the agent to grep for every sibling and the
  trap disappears - oauth-providers fm3f, n8n f3f2, vitest p63j, q2xc (all four solved on attempt 1). Show the route(s)
  the user hit; whether others exist is for the agent to find;
- reveal or hint at a hidden place (metadata.trap.paths): not by name, and not by a role specific enough to find it;
- list the tainted parameters, the payload set or the variants your tests use (n8n f3f2 named all four tainted
  parameters and the legal operator list). One illustrative example of the symptom is fine;
- name a function by a behaviour so specific it identifies it ("the one that ignores the address's own suffix" - j6r3);
- offer or rule on an acceptable fix ("refusing the archive is fine" - p634) or say which layer should change;
- in "what must keep working", list the boundary VALUES your tests use ("/0 networks, IPv4-mapped addresses",
  "[db].[dbo].[t], numeric-string limits"). Name the FEATURES that must keep working (hono: "a bare string must still
  render as the top-level element", "content marked as trusted raw HTML still emits markup");
- file, directory, module, function, method or class names the fix changes, options it adds, or line numbers.
AVOID stating the root cause when the fix is in one local place: there it IS the answer (adm-zip p634: "two entries
with the same name"; ip-address j6r3: "never checks both sides are the same kind of address").
Write in your OWN words. Do not quote the official CVE/GHSA summary, and do not include the CVE/OSV ID.
Fairness: every test_functional_* exercises an ordinary use of a feature named under "what must keep working", and
every test_security_* is an instance of the harm described.
Artifact 2: hidden_tests.py - Black-Box Pytest Suite
The suite runs at the repository root with REPO_ROOT set.
Strict Constraints:
Pure pytest, deterministic, offline (no internet access, no sleeps > 1s, harmless sentinels/tmp_path only).
Black-Box Execution: Test ONLY via public entry points (public CLI commands, public API methods, exported library
functions, or HTTP route handlers). NEVER import, inspect, or call new helper functions, new structs, or new fields
introduced by the reference patch.
Agnostic Assertions: Accept ANY valid rejection mechanism (raised exception, HTTP 4xx, sanitized return value).
Never assert on exact error string text or specific internal exception classes added by the patch.
Language Adapters:
Python: Direct import of public pre-patch modules.
Node/TypeScript: Use subprocess to run project's test runner (vitest/jest) or inline node script driving src/ (NEVER dist/).
Go: Write temporary zz_hidden_<name>_test.go and execute via go test -count=1 ./<pkg>.
PHP (Composer): Write a temporary zz_hidden_<name>.php in the repo root starting with require __DIR__ . '/vendor/autoload.php';
drive the project's public API or HTTP kernel the way its own tests do, print ONE JSON line of what a caller observes, and
run it with php via subprocess (remove the file in a finally block). Use only classes that exist in the PRE-patch source;
never change composer.json/composer.lock; no database or network - use the project's in-memory/array/SQLite drivers.
Non-Destructive Invariant: The reference patch MUST score 100% (all tests pass). The vulnerable code MUST fail all
test_security_* tests.
Naming & Test Structure:
test_security_* (at least 3, ideally 4-8): Fail on vulnerable code, pass after a correct fix.
COVER EVERY FIX PLACE (the #1 measured cause of easy tasks: in 24 of 37 solved tasks the agent passed while changing
FEWER source files than the reference fix - e.g. 1 of 12 - because no test reached the other places). List every source
place the reference fix hardens; give EACH its own test_security_* reached through its OWN real entry point, so a
repair that skips any one place fails. A variant counts only if it reaches the root cause through a DIFFERENT place or
route. Spelling, case, whitespace, encoding or extension variants of the same input through the same route do NOT
count - measured: pure spelling/encoding variants are always caught, and input variants were never missed.
Strongest sibling kinds to target (measured miss rates): a mechanism that never had the protection so its absence
reads as design (32%); a producer - schema, serializer, loader, config resolver - that feeds the check through a path
the check never calls (29%); a second real implementation (fallback backend, adapter, inline copy) (19%); the check
authorising the wrong/neighbouring object or an attacker-chosen identity field; the restricted value arriving through
defaults, merge, inheritance or stored config. Prefer REAL siblings the upstream fix also changed or never touched.
test_functional_* (at least 3, ideally 4-8): Pass on both vulnerable and fixed code.
Legitimate inputs near the rejection boundary, custom enterprise configurations, and valid workflows. An over-broad
fix that disables features or universally rejects input must fail these tests.
Hard Rules Learned from Historical QA Rejections
THE FAIRNESS CONTRACT (NO UNSEEN PLUMBING): every test_functional_* must exercise an ordinary use of a FEATURE named
under "What must keep working" - name the feature, not the test's values. If a test needs private enterprise registries
(e.g. my-tfe.corp.example), the report says that "users who configure a private registry" must keep working; it does
not list hosts, env vars or edge cases. A feature the vulnerable code never supported is not "legitimate" (infracost).
SIBLING BLAST RADIUS (INCOMPLETE UPSTREAM FIXES): If the reference patch only fixes 7 out of 8 providers/parsers
(leaving sibling components vulnerable), and an intelligent agent fixing the 8th component would break pre-existing
repository tests (e.g., legacy tests asserting unauthenticated behavior for provider X), answer ONLY with:
<unsuitable>incomplete upstream fix: sibling provider tests break under full remediation</unsuitable>.
IMPLEMENTATION INDEPENDENCE: A test must pass for ANY reasonable, correct architecture. Never assert that a check
lives in a specific layer, or that internal state changed in a specific way, when an alternative placement is equally sound.
COMPILED REPOSITORIES (TS/GO): Test source code directly. Never require compiled bundles (dist/index.js) which
do not exist until build and would omit agent edits.
NO TRIVIAL OR SYNTHETIC CODE: If the vulnerability is a pure dependency bump, a config toggle, or does not support
a multi-file / deeper-layer trap, answer ONLY with: <unsuitable>no hidden-path trap: <reason></unsuitable>.
Artifact 3: check_patches - Three Validation Fixes
Provide search/replace edits on pre-patch source files to verify test suite discrimination:
"shallow": Quick band-aid fixing only the primary trigger. Must pass >= 1 security test, but FAIL >= 1 security variant.
"removal": Over-restrictive fix (disables feature/returns early). Must FAIL >= 1 functional test.
"alternative": A correct, clean fix designed differently than the reference patch. Must PASS ALL tests.
Output Format (Strict XML Blocks Only)
Return ONLY these four blocks, nothing else:
<instruction_md>
...markdown matching the exact section structure specified above...
</instruction_md>
<hidden_tests_py>
...python source, no code fences...
</hidden_tests_py>
<task_metadata_json>
{
"entry_point": "<public entry point string>",
"techniques": [1, 5, 9],
"trap": {
"paths": ["<repo-relative source file agent is likely to miss>"],
"contract": "<the specific legitimate behavior near the boundary that functional tests pin>"
},
"fix_places": ["<EVERY reference-fix source file whose change closes part of the vulnerability; the pipeline re-runs the fix
               WITHOUT each one and a test must then fail>"],
"unrelated_files": ["<every OTHER reference-fix source file (refactor, typing, logging, an unrelated feature bundled in the
                    commit). Every source file of the reference patch must appear in fix_places or here>"],
"test_justifications": {
"<test_function_name>": "<exact sentence or quote from instruction.md requiring this test's assertion>"
}
}
</task_metadata_json>
<check_patches_json>
{
"shallow": [{"file": "<path>", "search": "<exact existing code>", "replace": "<new code>"}],
"removal": [...],
"alternative": [...]
}
</check_patches_json>


# The checks your task will face (write it to pass all of them the first time)
An independent reviewer scores the task on these criteria; any failed "must pass" criterion sends it back:
- no_hints (must pass): instruction.md names no file, module, path, line number, or function/class the fix changes AND does not prescribe the fix: an 'expected behaviour' part may state the security property and the legitimate behaviour to keep, but must not describe validation rules, accepted token formats, ordering of checks, or logging-vs-returning choices that amount to the fix design
- accurate_report (must pass): the report describes the vulnerability the oracle patch actually fixes (impact + how it is triggered), without inventing a different flaw
- solvable_from_report (must pass): a skilled engineer who reads the report and the code could determine every behaviour the hidden tests require; no test demands undisclosed or arbitrary behaviour
- real_entry_point (must pass): security tests reach the bug through a real entry point (public API/route/CLI), not by calling the internal function the patch edits
- variants_share_root_cause (must pass): extra exploit variants share the root cause and are all blocked by the oracle patch (no extra hardening the oracle does not provide)
- implementation_agnostic (must pass): tests never import/assert anything the patch adds, never assert exact error text, and accept any reasonable way of blocking the attack
- functional_meaningful (must pass): functional tests would FAIL if the feature were removed, disabled or over-blocked, yet pass on the vulnerable code
- deterministic_offline (must pass): no network, no timing/sleep-based races, no randomness that can flip a result
- realistic (must pass): the scenario is a realistic use of the project, not a contrived snippet or unreachable code
- security_not_trivial_config (must pass): the vulnerability is in program logic, not a dependency bump or config toggle
Then the task is EXECUTED: the reference fix must score 1.0 twice; the vulnerable code must fail every test_security_*
and pass every test_functional_*; the repo's own related tests must pass before and after the fix; your three check
patches run against your tests (shallow must still fail a security test, removal must fail a functional test,
alternative must pass everything); and if both target models can name the fix location from your report alone, the
task is rejected (so describe behaviour, never location).


# Design contract (measured: tasks that break BOTH models satisfy these)
1. At least TWO independent public entry points reach the root cause. The report names at most one; the other is
   discoverable by reading the code (a second renderer/parser/implementation, a lower-level public constructor, a
   second HTTP route/CLI, or a save/reload round-trip). Give each entry point its own test_security_*.
2. At EACH entry point, test at least two input shapes (bare value vs array/nested; path vs bytes; casing or encoding
   variants). A fix that handles only the reported shape must still fail.
3. Put at least one affected sink in a module whose path/name does not suggest the vulnerability; the report must not
   name it.
4. Include a functional test for every "must keep working" clause: it must PASS on the PRE-patch code and FAIL if the
   feature is removed or over-blocked.
5. At least one security test must be blocked only by the fix's change in a SECOND source file, not by the obvious
   first file. If the whole fix is one shared choke point, the models will solve the task.


# Task-design techniques (curated - follow them)
## What counts as a model failure (the grading contract)
- A task is solved only by reward 1.0: every hidden security test, every hidden functional test and every enforced
  existing repo test passes. Anything less is a FAILURE, including:
  - **Partial fix:** the agent closes some attack paths but not all (e.g. 5 of 6 security variants blocked). This is the
    most valuable failure: the model was confident and wrong ("silent failure").
  - **Fix that breaks something:** the hole is closed but a legitimate behaviour, an existing repo test, or the build
    breaks (over-correction / regression).
  - Both at once.
- A task is ACCEPTED when every attempt of both models (3 + 3) is such a failure, and the deterministic checks prove
  each failure is the model's (graded, no API/harness crash, agent really worked, no tampering). No AI judge decides.
- The goal is to MEASURE repair quality: a task only an incomplete or over-broad repair fails is a good task.
- So every task must be designed so that (a) a partial fix still fails and (b) an over-broad fix still fails.
- **Measured: models fail in two ways, equally often.** In the 2 QA-verified ACCEPTED tasks, 6 of 12 failures
  were over-corrections (apprise: hole closed, a pinned interface broken) and 6 left a path open (hono: a second
  renderer / input shape). So spend as much design effort on legitimate use as on attacks: functional tests for
  every legitimate input shape next to each attack variant, a public interface the repo's own tests pin
  (technique 11), and existing behaviour the obvious
  fix would change (hono: nested-array roots; apprise: the plugin `meta` dict). A "must keep working" test must follow from the report and
  pass on any correct fix - never a design only the reference fix makes (fairness QA withdrew infracost GHSA-6x6c and
  oauth-providers GHSA-fm3f for exactly that).

## Pattern catalogue - evidence-ranked from 471 measured sibling traps (2026-10-20)
A task shows ONE symptom through ONE route (the base bug). A **sibling** is another place the same protection is
missing that the report never names; a fix of the reported site alone then scores < 1.0. Every trap has two axes.

### Origin - where the sibling comes from (this is what decides difficulty, more than the mechanism)
- **A-FAR** (Pattern A): a site the real upstream fix ALSO changed, which the report does not lead to. **19% missed.** KEEP.
- **B-ROUTE** (Pattern B): a real, unmodified route with the same gap the upstream fix never touched. **25% missed - the strongest.** KEEP.
- **INJ** (injected/planted by us): **5% missed - almost never bites.** Once a model accepts the concept it closes all
  planted routes together (124 of 166 injected siblings are just M1/M2 routes of the stated concept). **TOO EASY - do not
  rely on injected siblings as the difficulty.** Confirmed 2026-10-20: our filament injection was declared unsuitable by
  the trap gate itself - every planted surface passed through one query scoper, so one restoration closed them all.
- Non-sibling kinds: **BASE** (the reported site), **SHAPE TRAP** (pure spelling/encoding variant of a route - ALWAYS
  caught, TOO EASY), **COUPLED TRAP** (a must-keep-working legitimate value next to the hidden one, tested functionally -
  bites, esp. MiMo which over-hardens; DeepSeek breaks coupled values too).

### Mechanism - why a model skips the sibling (miss rate = missed in >=1 run / siblings with trial data)
TOP BREAKERS (design toward these, on REAL code = A-FAR or B-ROUTE):
- **M4 Feature-absent** - the mechanism never had the protection, so its absence reads as design ("unsupported combo, not
  a boundary"). **7/22 = 32%, highest.** e.g. jackson any-setter has no view code.
- **M6 Producer off the check's path** - a schema/serializer/loader/config-resolver feeds the check through a path the
  check never calls; the model follows calls INTO the check, never asks where its data comes from. **5/17 = 29%.**
- **M2 Second implementation** (real, not injected) - a duplicate copy of the guarded logic: another package, fallback
  backend, adapter, inline copy. **14/73 = 19%.** "That path uses its own helper / only a fallback."
- **M10 Wrong object** - authorises a neighbouring/proxy object, or trusts an attacker-chosen identity field. **2/11.**
- **M5 Merged/defaults route** - the restricted value arrives via defaults/merge/inheritance/patch/stored-config; the
  model treats the report's example fields as the whole set.
- **M11 Coupled contract** - a linked visible value or shared helper must keep working; the natural fix breaks it
  (over-broad-fix trap). Bites MiMo hard.
WEAK / TOO EASY (do not use as the sole difficulty):
- **M1 Parallel entry** - another handler/endpoint/tool reaches the same sink. Only **12/99 = 12%** on real code, and ~0
  when injected. Allowed only as a secondary trap stacked with a top breaker.
- **M8 Parser differential** - genuine canonicalisation mismatch bites rarely (1/18); **pure spelling/case/encoding is
  always caught - TOO EASY.**
- **M12 Input variants** (encoding/spelling/verb/protocol/role of a stated input) - **never missed. TOO EASY, remove.**
- **M3 Shared layer** (0/6) and **M9 Fail-open fallback** (0/9) - never observed to bite; not proven breakers.

### The winning recipe (the only both-model breaker, jackson-databind-sib2, audited)
Uses NO planted code. A **Pattern B** route that **stacks several DIFFERENT mechanisms**: M4 (any-setter ignores views) +
M10+M11 (object-id stand-in property) + M5 (array/merge update) + a **coupled visible value an over-broad fix breaks**.
So: pick a real uncovered route, give it 2-3 different mechanisms, and pin a coupled legitimate value functionally.

### Avoid the checklist tell
Model-built (-ds/-mm) reports don't name siblings but describe each sibling's surface in product terms, one clause per
trap - that hands the solver a map. Never enumerate the HIDDEN places. (hono's report listed three affected wrappers
and still broke both models - because the places that decided it, the second renderer and the nested-array root, were
not in the list. Describing the route the user hit is fine; describing where else it lives is not.)

---

## Legacy numbered techniques (still referenced by the generator gate and scoreboard; map to the catalogue above)
Mapping: 1->M1, 2->dismissal-reason, 3->M3, 4->grading, 5->M11/coupled, 6->leak discipline, 7->M2, 8->RETIRED (M12),
9->M11, 10->RETIRED (width), 11->M11, 12->M4, 13->M6, 14->M10, 15->M5. The generator's trap gate accepts 1, 2, 3, 7 and
12-15 as hidden-path techniques; prefer 12, 13 and a real (not injected) 7. M1 parallel entry alone is weak (12%).

## What makes a repair task demanding - so only a complete, careful repair passes (use several in ONE task)
1. **Unnamed sibling path.** The report describes the reported trigger only. The same root cause is reachable through
   a second entry point, a second code path, or a round-trip (serialize -> store -> parse) that the report never
   names. Give it its own security test. Evidence: DeepSeek missed the schema round-trip variant in 3/3 runs on 6qxp.
2. **Already-protected-looking code.** One path already validates correctly, so the model reads the area as "handled"
   and patches only the path the report mentions (pyload jq7h, 6qxp).
3. **Fix across a layer boundary.** The correct fix must reach from the entry layer into a deeper layer (e.g. a core
   API that cannot see the web session, an SDK helper that cannot see the stored binding). Local guards at the entry
   point are the shallow fix your tests must catch.
4. **One test per fix place.** Each place the reference fix hardens gets its own `test_security_*` reached through its
   own entry point, so a fix that skips one place still scores < 1.0. (Was "one test per variant"; spelling, case and
   encoding variants of one input through one route are always caught and do not count.)
5. **Boundary-hugging functional tests.** Legitimate inputs that look like the attack (same characters, same feature,
   trailing slash, empty/None, legacy unbound data) must keep working, so "reject everything suspicious" fails.
6. **Behavioural report, no localization, no scope.** Describe what a user observes ("an IPv6 client passed our IPv4
   allowlist"), never the function, class, file or the root cause wording that points at the line to change - and
   never how far the bug reaches ("each provider we tried", "on every route"): all 4 evaluated reports with such a
   phrase were solved on attempt 1. Stating the cause is fatal only for a one-place fix; hono stated it and still won.
7. **Parallel implementation.** The project has a second module that re-implements the same feature (a second
   renderer, a second parser, a legacy and a new API). The report describes the behaviour once; the fix must land in
   both. Evidence: hono GHSA-hxh3 (first ACCEPTED task) - in 4 of 6 attempts the second `jsx/dom/server` renderer was
   left unfixed (DeepSeek read it every time but argued a top-level string is "trusted HTML"; MiMo twice never looked);
   the other 2 fixed it for a bare string only and missed a nested-array root. Details: data/knowledge/failure_analyses/.
8. **Input-shape variants (RETIRED - do not use as a difficulty technique).** In 35 of 40 tagged tasks, break rate at
   the 15% baseline: models catch spelling, case, encoding and shape variants of one route. A second public API or
   lower-level constructor that is a REAL separate place is technique 1 or 7, not this one.
9. **A "must keep working" clause that argues against the fix.** DeepSeek uses such a clause (or an existing test that
   passes either way) as permission to leave a sink open; MiMo over-hardens and breaks the legitimate path - test the
   legitimate behaviour in every supported composition order (undici GHSA-vp8m).
10. **Prefer big fixes (RETIRED as a difficulty lever).** Width does not separate hard from easy: 10-21-file fixes
   were solved on attempt 1 (9router changed 1 of 12 fix files and scored 1.0). Tiny local fixes (<= 3 files, <= 35
   lines) are still unusable, so width is a floor, not a lever.
11. **A compatibility contract pinned by an existing repo test.** Pick fixes that add an option or a check next to
   an existing public interface that the project's own tests pin (the exact keys a plugin receives, an output format,
   a default). The obvious fix changes that interface; a careful fix keeps it. Evidence: apprise GHSA-856c
   (ACCEPTED) - in 6 of 6 attempts both models added the new `redirect` key to every plugin's parsed-URL dict "like
   `verify`", saw the repo test `len(meta) == 8` fail, and edited the test instead of their fix; the grader restores
   repo tests, so all 6 scored 0.99. The upstream fix kept the key out unless set. Make sure the existing test is in
   the enforced pass->pass set and the report does not tell the agent to change that interface.
12. **Feature-absent sibling (catalogue M4, highest measured miss rate: 7 of 22).** A mechanism that never had the
   protection, so its absence reads as design ("unsupported combination, not a boundary"). jackson: the any-setter
   route has no view code at all. Test it through its own entry point.
13. **Producer off the check's path (M6, 5 of 17).** A schema, serializer, loader or config resolver feeds the check
   through a path the check never calls; the model follows calls INTO the check and never asks where its data comes
   from. MCP SDK 6qxp: the schema strips the issuer on reload (DeepSeek missed it 3/3).
14. **Wrong object (M10).** The check authorises a neighbouring or proxy object, or trusts an attacker-chosen identity
   field (seaweedfs: authorises against the ARN's account field; django-cms: parent from POST while the check reads GET).
15. **Merged / defaults route (M5).** The restricted value arrives through defaults, merge, inheritance, a patch or
   stored config; the model treats the report's example fields as the whole set (protobuf.js: inherited options).

## Cover every place the real fix protects (measured)
- In 15 of 27 solved tasks the agent passed while changing FEWER source files than the reference fix: the hidden tests
  did not exercise every place the fix protects, so a partial repair scored 1.0. Before writing tests, list each source
  file / code path the reference fix hardens and give each one at least one security test reached from a real entry
  point. A repair that skips any of those places must fail. (Live numbers: data/knowledge/solved_profile.md.)

## How the pipeline proves the tests are good (your check patches)
- **shallow**: blocks only the reported trigger. At least one security test must still fail on it (technique 1/4).
- **removal**: disables or over-restricts the feature. At least one functional test must fail on it (technique 5).
- **alternative**: a correct fix of a different design. Every test must pass on it (tests are implementation-agnostic).
- **coverage (leave-one-file-out)**: the reference fix is run WITHOUT its change to each file you list in
  `fix_places` (metadata). At least one test must fail every time; otherwise an agent that skips that file solves
  the task and it is sent back. List only files whose change closes part of the vulnerability.
- These are executed in the real environment. A wrong outcome sends the task back with the failing test names.

## Fairness rules (never break these to make a task harder)
- Every hidden test is passed by the reference fix and follows from the report plus a careful reading of the code.
- Tests observe only what a caller can observe at the entry point; never internal state or names the fix adds.
- No timing races, no network, no randomness.
- **Never test a number the report does not state.** The reference fix's internal limits (max length 64, a 1,000,000
  cap, a depth limit) are ONE design; another correct fix may pick another value. (Most common rejection so far:
  pypdf, source-map-js.) For resource-exhaustion bugs: keep the legitimate input small and the attack input orders of
  magnitude larger (e.g. 1x vs 1000x), and assert only that the attack is refused or finishes quickly and bounded -
  never at which exact size it starts being refused. If a boundary matters, the report must state it.
- **Variants must share the reported root cause.** Another bug in the same area (a different slow path, a different
  missing check) is a different task, not a variant (rejected: source-map-js deep nesting, typespec output files).
- **Never map every exception to "blocked".** Catch only the project's own rejection (UnauthorizedException, a 4xx,
  its ValidationError); let any other error fail the test. A catch-all hid a broken fake request in sync-in (the
  guard crashed on a missing `request.url`), so legitimate-use tests failed for no visible reason - and the same
  catch-all lets a security test "pass" when the code under test never ran.
- **"Must keep working" means it works today.** Every functional test must pass on the vulnerable code; never describe
  as legitimate a behaviour the project never had (rejected: undici allow-list caching).

## Answer-key hygiene (the agent must use its own knowledge)
- The agent sees only the report and the repo at the vulnerable commit: no hidden tests, no fix, no git history of
  the fix, no network, no advisory text. Never put fix code, upstream regression tests or exploit inputs into the repo
  or the report. Fixes committed after the models' release dates keep the answer out of their training data.


# Which task types each evaluated agent could not repair completely (measured results)
## Model failure map (deterministic, rebuilt after every evaluation)
Task type = vulnerability family; fix breadth (files / dirs / lines). Timeouts are not failures.
### DeepSeek
- FAILED on (5): auth / session / credentials; wide multi-layer fix (8 files / 4 dirs / 174 lines) - partial fix: closed 5 of 6 attack variants in all 3 runs and stopped on its own (it thought it was done); left open every time: schema_roundtrip_keeps_binding | information exposure + SSRF / redirect; wide multi-layer fix (127 files / 7 dirs / 229 lines) - closed the hole but broke legitimate behaviour (test_notify_multi_instance_decoration) in all 3 runs and stopped on its own (it thought it was done) | injection (code / command / markup); wide multi-layer fix (6 files / 3 dirs / 156 lines) - partial fix (and broke legitimate behaviour in 1 of 3 runs: runtime-tests/node/index.test.ts > stream > Should call onAbort) in all 3 runs and stopped on its own (it thought it was done); left open every time: render_to_string_escapes_array_root | path / file handling; wide multi-layer fix (10 files / 3 dirs / 236 lines) - partial fix: closed 4 of 5 attack variants in all 3 runs and stopped on its own (it thought it was done); left open every time: toolbox_symlink_escape | auth / session / credentials; local fix (1 files / 1 dir / 33 lines) - partial fix: closed 6 of 7 attack variants in its run and stopped on its own (it thought it was done); left open every time: exp_at_epoch_boundary
- Timed out on (0): none
- Solved (35), by vulnerability family: resource exhaustion (DoS) x7, auth / session / credentials x7, other x6, path / file handling x3, parsing / type confusion x3, injection (code / command / markup) x2, injection (code / command / markup) + information exposure x1, parsing / type confusion + SSRF / redirect x1, information exposure x1, auth / session / credentials + injection (code / command / markup) x1, auth / session / credentials + path / file handling x1, deserialization / prototype pollution x1, auth / session / credentials + path / file handling + information exposure x1
### MiMo
- FAILED on (3): information exposure + SSRF / redirect; wide multi-layer fix (127 files / 7 dirs / 229 lines) - closed the hole but broke legitimate behaviour (test_notify_multi_instance_decoration) in all 3 runs and stopped on its own (it thought it was done) | injection (code / command / markup); wide multi-layer fix (6 files / 3 dirs / 156 lines) - partial fix (and broke legitimate behaviour in 1 of 3 runs: runtime-tests/node/index.test.ts > stream > Should call onAbort) in all 3 runs and stopped on its own (it thought it was done); left open every time: render_to_string_escapes_array_root | auth / session / credentials; wide multi-layer fix (10 files / 5 dirs / 120 lines) - closed the hole but broke legitimate behaviour (storage_with_custom_lookup_same_host) in its run and stopped on its own (it thought it was done)
- Timed out on (2): auth / session / credentials; wide multi-layer fix (8 files / 4 dirs / 174 lines) | auth / session / credentials; wide multi-layer fix (5 files / 4 dirs / 111 lines)
- Solved (7), by vulnerability family: auth / session / credentials x2, parsing / type confusion x2, injection (code / command / markup) x1, path / file handling x1, auth / session / credentials + path / file handling + information exposure x1
### Broke BOTH (replicate this shape): information exposure + SSRF / redirect; wide multi-layer fix (127 files / 7 dirs / 229 lines) | injection (code / command / markup); wide multi-layer fix (6 files / 3 dirs / 156 lines)


# Which techniques have broken the evaluated agents so far (measured)
## Technique scoreboard (measured, rebuilt after every evaluation)
How often each curated technique was used in an evaluated task, and the outcome. A technique that keeps appearing in tasks DeepSeek solves on attempt 1 is not enough on its own: combine it with ones that broke a model. Counts are per task.

Baseline: 6 of 40 tagged tasks broke at least one model (15%). A technique is only informative when its break rate differs from that baseline.

| # | Technique | Tasks | Broke both | Broke only DeepSeek | Broke only MiMo | Solved | Read |
|---|---|---|---|---|---|---|---|
| 1 | Unnamed sibling path | 20 | 2 | 2 | 1 | 15 | USE: 25% break rate vs 15% baseline (apprise, hono, @modelcontextprotocol/sdk, fast-jwt, undici) |
| 2 | Already-protected-looking code | 5 | 0 | 1 | 0 | 4 | neutral: 20% break rate (@modelcontextprotocol/sdk) |
| 3 | Fix across a layer boundary | 5 | 0 | 1 | 0 | 4 | neutral: 20% break rate (@modelcontextprotocol/sdk) |
| 4 | One test per fix place | 40 | 2 | 3 | 1 | 34 | BASELINE (in 40/40 tasks): necessary, not sufficient (apprise, hono, @modelcontextprotocol/sdk, nltk, fast-jwt, undici) |
| 5 | Boundary-hugging functional tests | 38 | 2 | 3 | 1 | 32 | BASELINE (in 38/40 tasks): necessary, not sufficient (apprise, hono, @modelcontextprotocol/sdk, nltk, fast-jwt, undici) |
| 6 | Behavioural report, no localization, no scope | 39 | 2 | 3 | 1 | 33 | BASELINE (in 39/40 tasks): necessary, not sufficient (apprise, hono, @modelcontextprotocol/sdk, nltk, fast-jwt, undici) |
| 7 | Parallel implementation | 9 | 2 | 0 | 1 | 6 | USE: 33% break rate vs 15% baseline (apprise, hono, undici) |
| 8 | Input-shape variants (RETIRED - do not use as a difficulty technique) | 35 | 2 | 2 | 1 | 30 | BASELINE (in 35/40 tasks): necessary, not sufficient (apprise, hono, nltk, fast-jwt, undici) |
| 9 | A "must keep working" clause that argues against the fix | 16 | 2 | 2 | 0 | 12 | USE: 25% break rate vs 15% baseline (apprise, hono, @modelcontextprotocol/sdk, fast-jwt) |
| 10 | Prefer big fixes (RETIRED as a difficulty lever) | 2 | 1 | 0 | 0 | 1 | too few uses to judge (but broke both models) (apprise) |
| 11 | A compatibility contract pinned by an existing repo test | 0 | 0 | 0 | 0 | 0 | too few uses to judge |
| 12 | Feature-absent sibling (catalogue M4, highest measured miss rate: 7 of 22) | 0 | 0 | 0 | 0 | 0 | too few uses to judge |
| 13 | Producer off the check's path (M6, 5 of 17) | 0 | 0 | 0 | 0 | 0 | too few uses to judge |
| 14 | Wrong object (M10) | 0 | 0 | 0 | 0 | 0 | too few uses to judge |
| 15 | Merged / defaults route (M5) | 0 | 0 | 0 | 0 | 0 | too few uses to judge |

_0 evaluated task(s) have no technique record._


# Task shapes the evaluated agents SOLVED (avoid repeating them; measured)
## Solved-task profile (deterministic, rebuilt after every evaluation)
37 evaluated tasks were solved by at least one model; 35 on the FIRST attempt. Median solve time 13 min. These are the shapes to avoid or to combine with the techniques that broke a model (see the technique scoreboard).
- Median reference-fix size of solved tasks: 6 source files; median number of security tests: 6.
- Solved by vulnerability family: auth / session / credentials x11, resource exhaustion (DoS) x7, path / file handling x6, other x6, injection (code / command / markup) x4, parsing / type confusion x4, information exposure x3, SSRF / redirect x1, deserialization / prototype pollution x1
- In 8 of 37 solves the agent changed every source file of the reference fix: the report led it to all affected places.

### Why solved tasks were too easy (measured; fix the most common first)
- **coverage gap** in 24 of 37 solved tasks -> list every place the reference fix hardens and reach EACH one from its own security test - a repair that skips one place must fail.
- **no hidden path** in 15 of 37 solved tasks -> put part of the root cause in a REAL place the report never leads to - a second implementation, a producer feeding the check, a defaults/merge route - and reach it with its own test (techniques 1, 2, 3, 7, 12-15).
- **small fix** in 12 of 37 solved tasks -> a one-place fix is solved whatever the report says; skip it unless the code has a real second place the fix must also reach (fix width alone does not help: 10-21-file fixes were solved on attempt 1).
- **few security tests** in 9 of 37 solved tasks -> write one security test per fix place, each through its own entry point (spelling and encoding variants of one input do not count: models always catch them).
- **report points at the code** in 7 of 37 solved tasks -> never name the file, function, option or parameter the fix changes, and never state how far the bug reaches ('every provider', 'on every route').

| Task | Family | Fix | Security tests | Techniques used | Solved by | Attempt | Minutes | Why it passed |
|---|---|---|---|---|---|---|---|---|
| 9router | auth / session / credentials | 13 files / 10 dirs / 257 lines | 6 | 1, 4, 5, 6, 8, 9 | DeepSeek | 1 | 2 | coverage gap (1/12 fix files changed) |
| @hono/oauth-providers | auth / session / credentials | 7 files / 7 dirs / 54 lines | 6 | 1, 4, 5, 6, 8, 10 | DeepSeek | 1 | 3 | - |
| msgpack5 | resource exhaustion (DoS) | 2 files / 2 dirs / 40 lines | 7 | 1, 4, 5, 6, 8 | DeepSeek | 1 | 4 | small fix |
| nltk | other | 6 files / 2 dirs / 163 lines | 5 | 4, 5, 6, 8 | DeepSeek | 1 | 4 | coverage gap (1/7 fix files changed); report points at the code: grammar; no hidden path; few security tests |
| ip-address | parsing / type confusion | 3 files / 1 dir / 25 lines | 6 | 4, 5, 6, 8 | DeepSeek | 1 | 5 | small fix; report points at the code: Address4, Address6; no hidden path |
| @xmldom/xmldom | other | 3 files / 2 dirs / 37 lines | 10 | 1, 2, 4, 5, 6, 8, 9 | DeepSeek | 1 | 6 | small fix |
| vibe-trading-ai | auth / session / credentials + path / file handling + information exposure | 17 files / 5 dirs / 618 lines | 6 | 3, 4, 5, 6, 8 | DeepSeek | 1 | 6 | coverage gap (4/23 fix files changed); report points at the code: Settings, service |
| pyload-ng | auth / session / credentials | 2 files / 2 dirs / 9 lines | 4 | 4, 5, 6 | DeepSeek | 1 | 8 | coverage gap (1/2 fix files changed); small fix; no hidden path; few security tests |
| pyload-ng | auth / session / credentials | 4 files / 2 dirs / 58 lines | 7 | 4, 5, 6, 8 | DeepSeek | 1 | 8 | coverage gap (3/5 fix files changed); no hidden path |
| n8n | injection (code / command / markup) | 9 files / 7 dirs / 343 lines | 6 | 1, 4, 5, 8 | DeepSeek | 1 | 8 | coverage gap (5/9 fix files changed); report points at the code: execute |
| @vitest/browser | auth / session / credentials + path / file handling | 8 files / 4 dirs / 104 lines | 4 | 1, 2, 4, 5, 6, 8, 9 | DeepSeek | 1 | 9 | coverage gap (6/8 fix files changed); report points at the code: upload; few security tests |
| pymongo | other | 3 files / 3 dirs / 74 lines | 6 | 4, 5, 6, 7, 8 | DeepSeek | 1 | 10 | small fix |
| adm-zip | parsing / type confusion | 2 files / 2 dirs / 11 lines | 6 | 4, 5, 6, 8 | DeepSeek | 1 | 11 | small fix; no hidden path |
| react-router | other | 8 files / 7 dirs / 113 lines | 5 | 1, 3, 4, 5, 6, 7, 8 | DeepSeek | 1 | 12 | coverage gap (1/6 fix files changed); report points at the code: server; few security tests |
| pyload-ng | auth / session / credentials | 5 files / 4 dirs / 111 lines | 7 | 4, 5, 6 | DeepSeek | 1 | 12 | no hidden path |
| datamodel-code-generator | path / file handling | 1 files / 1 dir / 31 lines | 6 | 4, 5, 6, 9 | DeepSeek | 1 | 13 | small fix; no hidden path |
| @sync-in/server | other | 21 files / 8 dirs / 224 lines | 6 | 1, 4, 5, 6, 7, 8, 9 | DeepSeek | 1 | 13 | coverage gap (12/20 fix files changed) |
| hono | path / file handling | fix size unknown | 4 | 1, 4, 5, 6, 8, 9 | DeepSe


# Why the evaluated agents failed real tasks (curated from their trajectories - design for these)
## GHSA-856c-92hv-3vxx: Verdict: ACCEPTED. Both models failed every run. DeepSeek scored 0.99 on all three attempts and MiMo scored 0.99 on all three. In all six attempts every hidden test passed, including all 16 security and functional tests, so the fix itself worked. Each attempt failed on the same pre-existing test, `tests/test_decorator_notify.py::test_notify_multi_instance_decoration`, which asserts `len(meta) == 8`. The new `redirect` option was copied exactly from how `verify=` is handled, so a `redirect` key now appeared in every parsed-URL result. The agents saw this test fail and changed the expected count to 9. Test edits were restored before grading, so the change did nothing and the test still failed. All six attempts treated a failing existing test as something to update, not as a limit on their design. None of them changed `apprise/asset.py`, which the reference fix did change. That suggests the reference stores the default somewhere other than an always-present `parse_url` key, though the evidence doesn't show exactly how.
#### Weakness profile
- **DeepSeek:**
  - **Strengths:** it explores thoroughly and finds every HTTP call site. It does careful mechanical checks of its own patch, such as AST scans of every `allow_redirects` use.
  - **Weakness:** when an existing test breaks, it assumes the test is out of date, not that its design choice is wrong. It openly concludes the edits are "harmless" because hidden tests "will add new tests".
  - **How it verifies and stops:** it treats "the full suite passes after I edited the tests" as done. It never checks whether the new option could be added without changing what existing public output looks like.
- **MiMo:**
  - **Weakness:** the same habit of editing existing tests, but even stronger. It changes or extends four to six existing test files per attempt, and in attempt 3 it adds assertions that lock in its own side effects.
  - **Less precise coverage:** it touched a TCP-only plugin (attempt 1) and skipped eight HTTP plugins (attempt 2).
  - **Why it stops:** its own tests pass, and it takes that as proof of correctness.
- **Both:** they took "behave exactly like `verify=`" as an order to copy everything about it, including always adding a key to the parsed-URL results. Neither considered that existing callers and tests might depend on that results dict having a fixed size.
#### Task-design lessons
- **Ask for a feature that mirrors an existing option, while existing tests fix the shape of shared output.** Phrase it as "behave exactly like X", while an existing test pins the number of keys, the field list or the serialised form of a shared structure. Agents copy the template wholesale, change the shared structure, then "fix" the pinning test.
- **Keep breakage-detecting tests in files the agent will naturally edit.** Enforce existing tests and restore any test edits before grading. Put the fragile assertion in a test that fails noticeably during the agent's own full-suite run. Both models reliably edit such tests and wrongly believe test changes are "harmless".
- **Make the reference fix put new state somewhere unexpected.** Here that was a central config or defaults object (`asset.py`) instead of the obvious parser. A naive copy of the existing option then visibly breaks backward compatibility, while the reference route does not.
- **Grade the security behaviour on every call site, not a sample.** Use a fan-out change across many near-identical files and run hidden tests over the full set or a random sample of call sites. MiMo attempt 2 skipped eight plugins, and the hidden tests, which only covered json/form/xml/apprise_api/config/attachment, didn't notice.
- **State backward compatibility outright, but leave the danger implicit.** Write "existing behaviour stays as it is today" and nothing more. Agents read that as runtime behaviour only. They don't treat existing API or introspection output, such as a parsed-URL dict, as behaviour too, and that gap is what both models fell into.

## GHSA-hxh3-vqpv-xpqv: ACCEPTED - both models failed all 3 attempts (DeepSeek 0.83/0.83/0.94, MiMo 0.89/0.94/0.89, Claude Code agent), every run stopped on its own (no timeout). All 6 fixed the three wrappers the report names (Suspense, ErrorBoundary, Context.Provider) and all 6 left `renderToString([unsafe, [unsafe]])` unescaped.
#### Weakness profile
- Shared: both treat the report's examples as the complete list of sinks, and fix only the input shape they
  reproduced (a bare string) even when the same parameter accepts arrays, nested arrays and promises.
- DeepSeek: over-reasons about intent - finds the sink, then uses a "keep legitimate behaviour" clause or an existing
  passing test as permission to leave it vulnerable.
- MiMo: under-explores and asserts unverified facts ("that API doesn't exist") instead of searching.
#### Task-design lessons
- Put a **second entry point in a sibling module whose path sounds out of scope** (here `dom/` reads as "client") and
  describe it only vaguely ("a string handed to the renderer directly").
- Add a **"must keep working" clause that plausibly argues against the fix** ("a bare string must still be
  renderable"), backed by an existing test that passes either way (`'Hono'` has nothing to escape).
- **Test input-shape variants at each sink** (array, nested array, promise, number), not only each sink.
- Make **two entry points share the bug but need separate fixes**; agents fix them unevenly and claim full coverage.
- List some sinks "for example" and test more than you list: every agent stopped once the listed items were covered.

## GHSA-6qxp-vccf-f47h: DeepSeek failed 3/3 (0.92 each, Claude Code agent), always closing 5 of 6 attack paths; MiMo only timed out (terminus-2, 2 h), so the task is rejected (a timeout is not a failure).
#### Weakness profile
- DeepSeek traces call graphs well but misses state that crosses a serialization boundary (save -> store -> parse).
- It trusts in-code comments and "intentional" design notes, and reads "must keep working" hints as constraints.
- It stops as soon as self-written tests (which cover only what it already believes) pass.
#### Task-design lessons
- Put one variant on a **data round-trip** (serialize -> persist -> parse through the project's own schema/model
  layer) that the report does not name; the call-path fix then leaves exactly that variant open.
- Let the vulnerable code contain a plausible "intentional" comment or an already-protected entry point near the bug.
- Mention the round-trip only as legitimate behaviour that must keep working; never as an attack path.

## GHSA-p4rw-rvv2-7xwr: DeepSeek failed all 3 attempts (0.93 each, always the toolbox symlink escape left open); MiMo failed 2 (0.87, toolbox + MTE left open) and solved 1. Rejected (MiMo solved). No timeouts; every run stopped on its own.
#### Weakness profile
- DeepSeek: entry-point blindness - treats "reachable through the main class" as the whole attack surface and



# Lessons from previous runs (auto-generated from real DeepSeek/MiMo results - follow them)
## Breaks BOTH models (replicate)
- **hxh3 · hono · CWE-79 · 6 files/3 dirs/156 lines** and **856c · apprise · CWE-200/601** are the accepted tasks (n=2). hono: both models scored 0.83–0.94 and stopped on their own in 3/3 runs, leaving the second `jsx/dom/server` renderer or the nested-array root open every time - places the report never mentioned. apprise: both broke a plugin interface the repo's own test pins (over-correction, 6/6). Check `stream > Should call onAbort` for flakiness before reusing hono.
- **Combine in one task:**
  1. A REAL place the report never leads to - a second implementation, a lower-level API, a round-trip - that the obvious choke point misses. This beat DeepSeek (n=3). Spelling/encoding/shape variants of the same route do not count: they are always caught.
  2. One security test per fix place, each through its own entry point, so a fix that skips one place still fails.
  3. A falsy or boundary variant (`0`, `""`, `[]`). This beat DeepSeek (tentative, n=1: x937).
  4. A test that existing behaviour still works across a composition or ordering boundary. This beat MiMo (tentative, n=1: vp8m).
  5. A path that is already safe, as a decoy. This beat MiMo (tentative, n=1: jq7h).
  6. Fast test suites. A MiMo timeout counts as "too slow", not as a failure (6qxp, vp8m).

## Breaks only DeepSeek (MiMo solves)
- **Stops one variant short (n=4: 6qxp, p4rw, hxh3, x937; scores 0.92–0.95).** It patches the first layer it finds, then declares itself done.
  - **p4rw · nltk · CWE-22/59.** It put the check in `CorpusReader.abspath` and missed the bare-string entry points `StandardFormat.open`, `XMLCorpusView` and `load_ace_file`. MiMo fixed the shared `FileSystemPathPointer`.
  - **x937 · fast-jwt · CWE-613 · 1 file/33 lines.** It fixed the `hasIat` gate the report described, but kept the cache rule that `0` means "no bound". The `exp: 0` case stayed open (13/14 tests passed). MiMo checked whether the claim was present, not whether it was truthy, and compared cached against uncached results.
  - **6qxp.** It saw that the binding is lost on a schema round-trip and stopped anyway.
- **Hiding file names is not enough.** DeepSeek named the fix file in 0 of 38 recall probes, yet solved 21 tasks: the
  reports hid the files but stated the scope, the tainted parameters or the root cause of a one-place fix. What failed
  DeepSeek was a real place the report never led to (hono's second renderer, 6qxp's schema round-trip).

## Breaks only MiMo (DeepSeek solves)
- **vp8m · undici · CWE-346 (tentative).** Security tests reached 1.0, but reuse in `compose(cache(), dns())` broke. MiMo restored the hostname only on the response side, so the lookup key and the store key diverged.
- **jq7h · pyload · CWE-613 (tentative).** MiMo spent its budget on the webui path, which was already correct, and never edited REST.
- **When MiMo succeeds:** it solves tasks where one shared layer covers every variant (p4rw 1/3, x937). It has 3 counted failures.
- **Evidence on MiMo is thin.** Its p90 step time is about 400 s vs about 40 s for DeepSeek. It was ungraded in 13 of 14 stage-5 rows because a DeepSeek solve ends the run.

## Solved by both (avoid)
- **p634, j6r3:** the report gave the root cause, a repro and the API names, and the fix was one local check.
- **pqg4, x33g:** both models named the fix location.
- **DeepSeek solved on the first try, MiMo ungraded (n=21; 35–223 steps, 4–64 min):** j22f, v247, 24ch, 68w4, 9q47, 77xj, 5jq2, 3wxw, hqr4, hmq2, 2q42, qf28, 8fvv, 8xx6, mcm9, w3v8, q2xc, c7q8, gqvv, f65p and PYSEC-3869.
  - Each had one choke point that every variant passed through.
  - Wide fixes didn't help: 7 of them were solved, including qf28 (16 files) and w3v8 (289 lines).

## Task-quality pitfalls (rubric / oracle failures)
- **Run every test on the vulnerable code (n=6).** Security tests must fail there and functional tests must pass.
  - 8r5x crashed before the injection ran.
  - In r4xh and q238, security tests already passed (GEOS rejected nested Multi* at depth 5–6).
  - mcm9 and vp8m had functional tests that required new behaviour.
  - PYSEC-3869 used the mixed rule `S -> S 'a'`, which CNF conversion rejects on both versions.
- **Oracle fails its own tests (n=11):** x6jw, p634, jggr, 68fv, hmq2, 2q42, hqr4, r4xh, 376h, 2q76 and hwr6.
  - If every functional test scores 0.0, the harness or fixture is broken. Regenerating fixed hmq2, 2q42 and hqr4.
  - Drop existing tests that assert the vulnerable behaviour (tentative, n=2: qf28, c4c3).
- **Tests accept only one fix shape (n=9):**
  - 68w4, 9q47, jq7h, qf28.
  - 2q76: required field-level `access` and called functions with a made-up `req`.
  - x78j: rejected raise, `SystemExit` and drop fixes.
  - p63j: aliased `@vitest/browser` to `utils.ts` and used fake contexts.
  - PYSEC-3819: mocked only the module-level `requests.get`.
  - 5vf6: a minimal constructor config crashed fixes that read `flagResolver`.

  Accept reject, raise, drop and sanitize fixes. Test through the public HTTP, CLI or RPC entry point. Mock at the transport layer and import through the package entry.
- **Undisclosed limits or semantics (n=5):** 5jq2 (a cutoff of 64), 68fv (hidden cap), 2q42 (sanitize and still emit), w3v8 (25 s vs the repo's 60 s) and x78j (`splitlines()` instead of cmd.exe rules). State limits in the report or use ≥100× margins, and model the real sink.
- **Weak tests (n=5):** x937, 6qxp, qf28, r4xh and 2q76 (deny-all passed). Assert the output content and make over-blocking fail. Count operations instead of timing them (tentative, n=2).
- **No network in tests (tentative, n=1: 5vf6).** The test resolved a real host's DNS, and the oracle passed only through a hidden `NODE_ENV=test` fallback.
- **Fix visible to the model (n=4):** readable in site-packages or node_modules (8xx6, q2xc, f65p), or already in the vulnerable tree (337j). Uninstall released copies.
- **Bad existing-test files (n=4):** helper, manual and DB-integration files. Exclude them.
- **Infrastructure; retry before rejecting:**
  - no verdict (n=9)
  - host Docker I/O error (n=4)
  - "no usable existing tests" (n=4; f65p passed on retry)
  - `pip install -e .` failed (n=3)
  - environment start timeout, stage-5 incomplete attempts, npm install failed (n=2 each)
- **Report names the code (n=3)**, and **safeguard blocks (n=9)**; Handlebars, q238 and 2q76 were retired.

## Selection hints
- **Prefer:** fixes where a tempting high-level choke point misses a real second place - a second implementation, a lower-level API, a producer feeding the check (n=3; 6–10 files, 120–236 lines). At screening, ask whether one function sees every variant. If it does, skip.
- **Also prefer (tentative):** checks on falsy-sensitive fields (timestamps, counts, empty values), and these CWEs:
  - CWE-79
  - CWE-345/522
  - CWE-613 (broke each model once)
  - CWE-22/59, only if bare-path entries bypass the reader layer
- **Skip:**
  - Fixes of ≤4 files and ≤60 lines (0 usable of 14).
  - DoS CWE-400/407/409/674/1284/1333 (0 usable).
  - CWE-22/73 fixed in one path builder (n=3).
  - CWE-91, URI parsers and SSRF fixes that need DNS (tentative).
  - Code generators.
  - Oracle patches over 80k characters (n=3).
  - Monorepos: payload (5 failures), pydantic-ai, vllm, Flowise, reactpress, mermaid and vitest.
  - PyPI repos where `pip install -e .` fails.
- **pyload:** use only with the real app's test client.
- **Recall:** reject if both models name the fix (n=2). Otherwise recall doesn't predict the outcome.


# Split generation (this request)
Return ONLY the `<instruction_md>`, `<task_metadata_json>` and `<check_patches_json>` blocks. Do NOT write the
<hidden_tests_py> block; it is requested in a separate step. Keep the check patches minimal (only the edits that
demonstrate shallow / removal / alternative behaviour).

