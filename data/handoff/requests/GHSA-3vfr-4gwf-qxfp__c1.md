<!-- label=GHSA-3vfr-4gwf-qxfp call=1 hash=65a3b3dbf7 -->
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
- OSV ID: GHSA-3vfr-4gwf-qxfp
- CVE: CVE-2026-55629
- CWE: CWE-22
- Ecosystem / Package: npm / whistle
- Repository: https://github.com/avwo/whistle
- Official Summary: Whistle vulnerable to path traversal

# Reference Patch (Historical human fix; hidden from evaluated agents)
```diff
diff --git a/lib/config.js b/lib/config.js
index cbf21d3a7c36055f71370326e44487cdfefc13e6..2a9fb0100dc8fef89df3726af17ccfe8a0ba2262 100644
--- a/lib/config.js
+++ b/lib/config.js
@@ -148,7 +148,6 @@ function getDataDir(dirname) {
 }
 
 config.baseDir = getDataDir();
-config.TEMP_FILES_PATH = path.join(getWhistlePath(), 'temp_files');
 config.CUSTOM_PLUGIN_PATH = path.join(getWhistlePath(), 'custom_plugins');
 config.CUSTOM_CERTS_DIR = path.resolve(getWhistlePath(), 'custom_certs');
 config.SAVED_SESSIONS_PATH = path.resolve(getWhistlePath(), 'saved_sessions');
@@ -158,8 +157,8 @@ config.valuesDir = path.join(config.baseDir, 'values');
 config.propertiesDir = path.join(config.baseDir, 'properties');
 
 try {
-  fse.ensureDirSync(config.TEMP_FILES_PATH);
-  var blankFile = path.join(config.TEMP_FILES_PATH, 'blank');
+  fse.ensureDirSync(common.TEMP_FILES_PATH);
+  var blankFile = path.join(common.TEMP_FILES_PATH, 'blank');
   if (!fs.existsSync(blankFile)) {
     fs.writeFileSync(blankFile, '');
   }
@@ -796,7 +795,7 @@ exports.extend = function (newConf) {
         setDefaultResultOrder(m.toLowerCase());
       } else if (m === 'proxyOnly') {
         config.pureProxy = true;
-      } else if (m === 'useMultipleRules' || m === 'enableMultipleRules') {
+      } else if (m === 'useMultipleRules' || m === 'enableMultipleRules' || m === 'allowMultipleChoice') {
         config.allowMultipleChoice = true;
       } else if (m === 'disableMultipleRules') {
         config.allowMultipleChoice = false;
diff --git a/lib/handlers/file-proxy.js b/lib/handlers/file-proxy.js
index 95bc0724f226b4fa40ad6ab1543ce3247166e2b7..039db9b3461e24e417c3bac57cdde33bd15419cb 100644
--- a/lib/handlers/file-proxy.js
+++ b/lib/handlers/file-proxy.js
@@ -66,7 +66,7 @@ function parseRes(str, rawHeaderNames, fromValue) {
     };
   }
   var headers = str.split(CRLF_RE);
-  var statusLine = headers.shift().trim().split(/\s+/g);
+  var statusLine = headers.shift().trim().split(/\s+/);
   headers = util.parseHeaders(headers, rawHeaderNames);
   if (fromValue) {
     delete headers['content-encoding'];
diff --git a/lib/https/ca.js b/lib/https/ca.js
index a6658df3b74f419207c75df137b957b5cded22a5..b05abae8862e7cafb79e7d15c84044c0a67452c4 100644
--- a/lib/https/ca.js
+++ b/lib/https/ca.js
@@ -177,6 +177,19 @@ exports.hasCustomCerts = function () {
   return customCertCount;
 };
 
+var rootSkiBytes;
+
+function getRootSKI() {
+  if (!rootSkiBytes) {
+    try {
+      rootSkiBytes = ROOT_CRT.generateSubjectKeyIdentifier().getBytes();
+    } catch (e) {
+      rootSkiBytes = null;
+    }
+  }
+  return rootSkiBytes;
+}
+
 function getCacheCert(hostname) {
   return (
     customPairs[hostname] ||
@@ -205,13 +218,6 @@ function createSelfCert(hostname) {
     }
   ]);
   cert.setIssuer(ROOT_CRT.subject.attributes);
-  // Get SKI from ROOT_CRT for authorityKeyIdentifier extension
-  var rootSkiBytes;
-  try {
-    rootSkiBytes = ROOT_CRT.generateSubjectKeyIdentifier().getBytes();
-  } catch(ex) {
-    rootSkiBytes = null;
-  }
   cert.setExtensions([
     {
       name: 'basicConstraints',
@@ -243,7 +249,7 @@ function createSelfCert(hostname) {
     },
     {
       name: 'authorityKeyIdentifier',
-      keyIdentifier: rootSkiBytes
+      keyIdentifier: getRootSKI() // Get SKI from ROOT_CRT for authorityKeyIdentifier extension
     }
   ]);
   cert.sign(ROOT_KEY, forge.md.sha256.create());
diff --git a/lib/https/index.js b/lib/https/index.js
index a49b709b70cfadcabc62760d1e9214657f98cd86..8a125fcbb0c34c35232b6025f148a567f987be75 100644
--- a/lib/https/index.js
+++ b/lib/https/index.js
@@ -718,9 +718,10 @@ function resolveWebsocket(socket, wss) {
           extend(headers, reqHeaders);
           headers.host = headers.host || host;
         }
-        auth = util.getAuthBasic(auth || authObj);
+        authObj = auth || authObj;
+        auth = util.getAuthBasic(authObj);
         if (auth) {
-          headers['authorization'] = auth;
+          headers[(authObj.proxy ? 'proxy-' : '') + 'authorization'] = auth;
         }
         var reqRuleData = { headers: headers };
         util.setReqCors(reqRuleData, reqCors);
diff --git a/lib/index.js b/lib/index.js
index b6d65049f25309e13eca089dbb091bf51c6a69b0..400a5394d0ef934a335cbe2477acb5b92552f7b0 100644
--- a/lib/index.js
+++ b/lib/index.js
@@ -13,7 +13,6 @@ var rulesUtil = require('./rules/util');
 var initDataServer = require('./util/data-server');
 var pluginMgr = require('./plugins');
 var config = require('./config');
-var loadService = require('./service');
 var initSocketMgr = require('./socket-mgr');
 var tunnelProxy = require('./tunnel');
 var upgradeProxy = require('./upgrade');
@@ -222,7 +221,6 @@ function exportInterfaces(obj) {
   obj.httpsUtil = httpsUtil;
   obj.pluginMgr = pluginMgr;
   obj.logger = logger;
-  obj.loadService = loadService;
   obj.setAuth = config.setAuth;
   obj.setUIHost = config.setUIHost;
   obj.setPluginUIHost = config.setPluginUIHost;
diff --git a/lib/inspectors/data.js b/lib/inspectors/data.js
index 80dc4b8e30d663d6782ff3f07f41ecffd60ce713..bd09391eacba5bcfe8b2087742e416cc867060e0 100644
--- a/lib/inspectors/data.js
+++ b/lib/inspectors/data.js
@@ -10,7 +10,9 @@ var MAX_REQ_BODY_SIZE = (config.strict ? 256 : 2048) * 1024;
 var MAX_RES_BODY_SIZE = (config.strict ? 256 : 2048) * 1024;
 var BIG_DATA_SIZE = 1024 * 1024 * 16;
 var LOCALHOST = '127.0.0.1';
-var SSE_RE = /^\s*text\/event-stream/i;
+var MAX_PAYLOAD = util.MAX_FRAME_PAYLOAD;
+var SSE_SEP = Buffer.from('\n\n');
+var FRAME_SEP_KEY = 'x-whistle-custom-frame-separator';
 
 function getZipType(options) {
   return options.headers && options.headers['content-encoding'];
@@ -57,6 +59,80 @@ function emitDataEvents(req, res, proxy) {
   if (!util.showPluginReq(req) || util.isHide(req)) {
     return;
   }
+
+  var reqSepInfo = parseFrameSep(req.headers);
+  var cseSep = reqSepInfo && reqSepInfo.sep;
+  var resSepInfo;
+
+  function emitFrame(chunk, fromServer) {
+    proxy.emit('frame', {
+      reqId: req.reqId,
+      frameId: util.getFrameId(),
+      isClient: !fromServer,
+      length: chunk.length,
+      bin: chunk
+    });
+  }
+
+  function parseFrameSep(headers) {
+    var sep = headers[FRAME_SEP_KEY];
+    if (!util.isString(sep)) {
+      return;
+    }
+    var result = {};
+    delete headers[FRAME_SEP_KEY];
+    try {
+      sep = decodeURIComponent(sep);
+    } catch (e) {}
+    if (sep[0] === '/') {
+      result.keepSep = true;
+      sep = sep.slice(1);
+    }
+    if (sep) {
+      result.sep = Buffer.from(sep);
+      result.sepLen = sep.length;
+    }
+    return result;
+  }
+
+  function parseFrame(buf, isRes, end) {
+    var len = buf && buf.length;
+    if (!len) {
+      return null;
+    }
+    var sep, sepLen, keepSep;
+    var info = isRes ? resSepInfo : reqSepInfo;
+    if (info) {
+      sep = info.sep;
+      sepLen = info.sepLen;
+      keepSep = info.keepSep;
+    } else {
+      sep = SSE_SEP;
+      sepLen = 2;
+    }
+    var index = buf.indexOf(sep);
+    while (index !== -1) {
+      if (keepSep) {
+        index += sepLen;
+      }
+      index && emitFrame(buf.slice(0, index), isRes);
+      buf = buf.slice(keepSep ? index : index + sepLen);
+      index = buf.indexOf(sep);
+    }
+    len = buf.length;
+    if (!len) {
+      return null;
+    }
+    if (end) {
+      emitFrame(buf, isRes);
+      return null;
+    }
+    if (len > MAX_PAYLOAD) {
+      emitFrame(buf.slice(0, -1), isRes);
+      buf = buf.slice(-1);
+    }
+    return buf;
+  }
   var getTTFB = function () {
     if (req._ttfb >= now) {
       return req._ttfb - now;
@@ -167,12 +243,20 @@ function emitDataEvents(req, res, proxy) {
   var captureReqStream;
   var maxReqSize;
   var reqInfo;
+  var setReqBody = function (body, end) {
+    if (captureReqStream && cseSep) {
+      reqBody = parseFrame(reqBody, false, end);
+    } else {
+      reqData.body = reqBody;
+    }
+  };
   var updateReqInfo = function() {
     if (reqInfo && !captureReqStream) {
       captureReqStream = !disable.captureStream && (resDone || enable.captureStream) && !getZipType(reqInfo);
       maxReqSize = useBigData ? BIG_DATA_SIZE : (captureReqStream ? MAX_REQ_BODY_SIZE : MAX_SIZE);
-      if (captureReqStream && reqBody && !reqData.body) {
-        reqData.body = reqBody;
+      if (captureReqStream) {
+        data.isCse = !!cseSep;
+        reqBody && !reqData.body && setReqBody(reqBody);
       }
     }
   };
@@ -198,7 +282,7 @@ function emitDataEvents(req, res, proxy) {
           } else {
             reqBody = reqBody ? Buffer.concat([reqBody, chunk]) : chunk;
             if (captureReqStream) {
-              reqData.body = reqBody;
+              setReqBody(reqBody);
             }
             if (reqBody.length > maxReqSize) {
               reqBody = false;
@@ -225,8 +309,8 @@ function emitDataEvents(req, res, proxy) {
           data.endTime = endTime;
         }
         reqBody = err ? util.getErrorStack(err) : body;
-        reqData.body = reqBody;
-        setUnzipSize(body, reqData);
+        setReqBody(reqBody, true);
+        !data.isCse && setUnzipSize(body, reqData);
         checkBodySize(reqData, useBigData);
       });
       updateEvent && proxy.emit(updateEvent, req.fullUrl, false, true);
@@ -239,9 +323,22 @@ function emitDataEvents(req, res, proxy) {
     }
     resDone = true;
     info = info || (res._needGunzip ? { statusCode: res.statusCode, headers: '' } : res);
-    var captureStream = !disable.captureStream && (requestTime == null || enable.captureStream ||
-      (info.headers && SSE_RE.test(info.headers['content-type']))) && !getZipType(info);
+    var isSse;
+    var captureStream;
+    if (!disable.captureStream && !getZipType(info)) {
+      var headers = info.headers;
+      captureStream = requestTime == null || enable.captureStream;
+      if (headers) {
+        isSse = headers['content-type'] === 'text/event-stream';
+        captureStream = captureStream || isSse;
+        resSepInfo = parseFrameSep(headers);
+        if (resSepInfo && resSepInfo.sep) {
+          isSse = captureStream;
+        }
+      }
+    }
     var maxResSize = useBigData ? BIG_DATA_SIZE : (captureStream ? MAX_RES_BODY_SIZE : MAX_SIZE);
+    data.isSse = isSse;
     captureStream && updateReqInfo();
     if (!cleared && util.hasBody(info, req) && checkType(info)) {
       if (info.headers['content-length'] > maxResSize && !captureStream) {
@@ -261,9 +358,13 @@ function emitDataEvents(req, res, proxy) {
           } else {
             resBody = resBody ? Buffer.concat([resBody, chunk]) : chunk;
             if (captureStream) {
-              resData.body = resBody;
+              if (isSse) {
+                resBody = parseFrame(resBody, true);
+              } else {
+                resData.body = resBody;
+              }
             }
-            if (resBody.length > maxResSize) {
+            if (resBody && resBody.length > maxResSize) {
               resBody = false;
             }
           }
@@ -286,9 +387,13 @@ function emitDataEvents(req, res, proxy) {
       resData.hasGzipError = unzipBody(info, resBody, function (err, body) {
         if (!data.resError) {
           resBody = err ? util.getErrorStack(err) : body;
-          resData.body = resBody;
+          if (isSse) {
+            resBody = parseFrame(resBody, true, true);
+          } else {
+            resData.body = resBody;
+          }
         }
-        setUnzipSize(body, resData);
+        !isSse && setUnzipSize(body, resData);
         checkBodySize(resData, useBigData);
         setEndTime();
         reqEmitter.emit('end', data);
@@ -341,7 +446,8 @@ function emitDataEvents(req, res, proxy) {
     }
     !endTime && setEndTime();
     delete data.abort;
-    if (err && err.message !== 'Aborted') {
+    var msg = err && err.message;
+    if (msg !== 'Aborted') {
       data.resError = true;
       if (resData.body) {
         data.errMsg = util.getErrorStack(err);
diff --git a/lib/inspectors/req.js b/lib/inspectors/req.js
index 2b3103ac82a9732002cf76fda3d26bc13a4c0ae3..360cc695d542ef6e6956af7f2ecf5db338b8f50a 100644
--- a/lib/inspectors/req.js
+++ b/lib/inspectors/req.js
@@ -147,9 +147,11 @@ function handleReq(req, data, reqRules, delType) {
   }
 }
 
-function handleAuth(data, auth) {
-  auth = util.getAuthBasic(auth);
-  auth && util.setHeader(data, 'authorization', auth);
+function handleAuth(data, authObj) {
+  var auth = util.getAuthBasic(authObj);
+  if (auth) {
+    util.setHeader(data, (authObj.proxy ? 'proxy-' : '') + 'authorization', auth);
+  }
 }
 
 function handleParams(req, params, urlParams, enableBigData) {
diff --git a/lib/plugins/get-plugins-sync.js b/lib/plugins/get-plugins-sync.js
index e5e2db2bf8ab3efba936471651da428113d36f4e..b4dabac7b97e36b28da80ebbc0c5a72b03c77f67 100644
--- a/lib/plugins/get-plugins-sync.js
+++ b/lib/plugins/get-plugins-sync.js
@@ -12,6 +12,7 @@ var notUninstallPluginPaths = config.notUninstallPluginPaths || [];
 var projectPluginPaths = config.projectPluginPaths || [];
 var accountPluginsPath = config.accountPluginsPath || [];
 var paths = mp.getPaths();
+var PLUGIN_DIR = pluginUtil.PLUGIN_DIR;
 
 function getMTimeSync(filePath) {
   var stats = common.getStatSync(filePath);
@@ -41,8 +42,9 @@ function readPluginModulesSync(dir, plugins) {
               var mtime = getMTimeSync(path.join(root, 'package.json'));
               if (mtime != null) {
                 var old = plugins[name];
-                if (!old || (mtime > old.mtime && root === old.root)) {
+                if (pluginUtil.compparePlugin(dir, mtime, old)) {
                   plugins[name] = {
+                    [PLUGIN_DIR]: dir,
                     mtime: mtime,
                     root: root,
                     account: account,
@@ -65,8 +67,9 @@ function readPluginModulesSync(dir, plugins) {
       var mtime = getMTimeSync(path.join(root, 'package.json'));
       if (mtime != null) {
         var old = plugins[name];
-        if (!old || (mtime > old.mtime && root === old.root)) {
+        if (pluginUtil.compparePlugin(dir, mtime, old)) {
           plugins[name] = {
+            [PLUGIN_DIR]: dir,
             root: root,
             mtime: mtime,
             account: account,
@@ -95,15 +98,15 @@ module.exports = function () {
     if (pluginUtil.excludePlugin(simpleName)) {
       return;
     }
-    var dir = plugins[name];
-    var account = dir.account;
-    var isSys = dir.isSys;
-    var isProj = dir.isProj;
-    var notUn = dir.notUn;
-    var isDev = dir.isDev;
-    var dirName = dir.dir;
-    var mtime = dir.mtime;
-    dir = dir.root;
+    var obj = plugins[name];
+    var account = obj.account;
+    var isSys = obj.isSys;
+    var isProj = obj.isProj;
+    var notUn = obj.notUn;
+    var isDev = obj.isDev;
+    var dirName = obj.dir;
+    var mtime = obj.mtime;
+    var dir = obj.root;
     var pkgPath = path.join(dir, 'package.json');
     var pkg = common.readJsonSync(pkgPath);
     if (!pkg) {
@@ -120,6 +123,7 @@ module.exports = function () {
       var tabs = util.getInspectorTabs(conf);
       var hintList = util.getHintList(conf);
       var plugin = {
+        [PLUGIN_DIR]: obj[PLUGIN_DIR],
         account: account,
         dir: dirName,
         isSys: isSys,
diff --git a/lib/plugins/get-plugins.js b/lib/plugins/get-plugins.js
index 2be82d3817f99bd2172c7931812d6bcf9333fb01..94f79013a59b798e6e7bbd2d706bfae3691ed4e8 100644
--- a/lib/plugins/get-plugins.js
+++ b/lib/plugins/get-plugins.js
@@ -9,6 +9,7 @@ var customPluginPaths = config.customPluginPaths || [];
 var notUninstallPluginPaths = config.notUninstallPluginPaths || [];
 var projectPluginPaths = config.projectPluginPaths || [];
 var accountPluginsPath = config.accountPluginsPath || [];
+var PLUGIN_DIR = pluginUtil.PLUGIN_DIR;
 
 function readPluginRootList(dir, callback) {
   var roots = [];
@@ -31,7 +32,7 @@ function readPluginRootList(dir, callback) {
       if (pluginUtil.isWhistleModule(name)) {
         roots[i] = {
           name: name,
-          dir: dir
+          [PLUGIN_DIR]: dir
         };
       } else if (pluginUtil.isOrgModule(name)) {
         ++count;
@@ -44,7 +45,7 @@ function readPluginRootList(dir, callback) {
                 orgList.push({
                   org: name,
                   name: pluginName,
-                  dir: dir
+                  [PLUGIN_DIR]: dir
                 });
               }
             });
@@ -74,7 +75,7 @@ function readPluginModules(dir, callback, plugins, isSys) {
       return callback(plugins);
     }
     list.forEach(function (obj) {
-      var dir = obj.dir;
+      var dir = obj[PLUGIN_DIR];
       var dirName = obj.org ? obj.org + '/' + obj.name : obj.name;
       pluginUtil.getSysPath(dir, dirName, isSys, function(root) {
         common.getStat(path.join(root, 'package.json'), function (_, stats) {
@@ -83,13 +84,10 @@ function readPluginModules(dir, callback, plugins, isSys) {
             obj.mtime = stats.mtime.getTime();
           }
           if (--len === 0) {
-            list.forEach(function (obj) {
-              var name = pluginUtil.getPluginName(obj.name);
-              if (obj.root) {
-                var old = plugins[name];
-                if (!old || (obj.mtime > old.mtime && obj.root === old.root)) {
-                  plugins[name] = obj;
-                }
+            list.forEach(function (item) {
+              var name = pluginUtil.getPluginName(item.name);
+              if (item.root && pluginUtil.compparePlugin(dir, item.mtime, plugins[name])) {
+                plugins[name] = item;
               }
             });
             callback(plugins);
@@ -121,10 +119,11 @@ module.exports = function (callback) {
           if (pluginUtil.excludePlugin(name)) {
             return;
           }
-          var old = result[name + ':'];
           var obj = plugins[name];
-          if (!old || (obj.mtime > old.mtime && obj.root === old.path)) {
+          var dir = obj[PLUGIN_DIR];
+          if (pluginUtil.compparePlugin(dir, obj.mtime, result[name + ':'])) {
             result[name + ':'] = {
+              [PLUGIN_DIR]: dir,
               account: account,
               dir: config.whistleName,
               isSys: isSys,
diff --git a/lib/plugins/load-plugin.js b/lib/plugins/load-plugin.js
index 95d2f6145f56684059858be27e648d3263e2fc2b..4bd0fe672c74966bd36dbf8db87ac853d2fe48ba 100644
--- a/lib/plugins/load-plugin.js
+++ b/lib/plugins/load-plugin.js
@@ -1202,7 +1202,7 @@ module.exports = async function (options, callback) {
   PROXY_ID_HEADER = config.PROXY_ID_HEADER;
   options.getTempFilePath = function(filePath) {
     if (common.TEMP_PATH_RE.test(filePath)) {
-      return path.join(config.TEMP_FILES_PATH, RegExp.$1);
+      return path.join(common.TEMP_FILES_PATH, RegExp.$1);
     }
   };
 
diff --git a/lib/plugins/module-paths.js b/lib/plugins/module-paths.js
index c03171a8d694c8cec454561e20d5ebdb21d59fcc..ecaa47717c5c60e9eb7ce2840303b2ce455a7be4 100644
--- a/lib/plugins/module-paths.js
+++ b/lib/plugins/module-paths.js
@@ -36,6 +36,7 @@ var pluginPaths = config.pluginPaths;
 if (pluginPaths) {
   pluginPaths = pluginPaths.concat(pluginPaths.map(formatPath).concat(addon));
   pluginPaths = prePlugins.concat(pluginPaths);
+  config.PLUGIN_INSTALL_ROOT = pluginPaths[0];
   addDebugPaths(pluginPaths);
   pluginPaths = uniqueArr(pluginPaths);
   exports.getPaths = function () {
@@ -80,6 +81,9 @@ if (pluginsPath && paths.indexOf(pluginsPath) == -1) {
 }
 if (!config.customPluginPaths || !config.customPluginPaths.length) {
   paths.unshift(config.CUSTOM_PLUGIN_PATH);
+  config.PLUGIN_INSTALL_ROOT = config.CUSTOM_PLUGIN_PATH;
+} else {
+  config.PLUGIN_INSTALL_ROOT = config.customPluginPaths[0];
 }
 paths = addon.concat(paths);
 addDebugPaths(paths);
diff --git a/lib/plugins/util.js b/lib/plugins/util.js
index 1544dcf2554cef7e5a5dde98f76b5c9e1276d627..3191c8e47d4443b17eb29a3dfc3f165098df1957 100644
--- a/lib/plugins/util.js
+++ b/lib/plugins/util.js
@@ -13,11 +13,14 @@ var MAX_EXPIRE = 36000;
 var UTF8_OPTIONS = { encoding: 'utf8' };
 var workerScript = util.readFileSync(path.join(__dirname, '../../assets/js/worker.js'), false);
 var workers = {};
+var PLUGIN_DIR = Symbol('dir');
 
 function replaceScript(ctn, name) {
   return workerScript.replace('$PLUGIN_NAME', name).replace('/*sourcecode*/', ctn);
 }
 
+exports.PLUGIN_DIR = PLUGIN_DIR;
+
 exports.readWorkerSync = function(root, conf, name) {
   var file = util.getWebWorker(conf);
   file = file && util.readFileSync(path.join(root, file));
@@ -140,6 +143,7 @@ function setPlugin(plugins, pkg, root, mtime, sync) {
   if (PLUGIN_NAME_RE.test(pkg.name)) {
     var name = sync ? RegExp.$1 : getPluginName(RegExp.$1);
     plugins[name] = {
+      [PLUGIN_DIR]: DEV_PLUGINS_PATH,
       root: root,
       mtime: mtime,
       notUn: true,
@@ -256,3 +260,7 @@ exports.getSysPath = function(dir, name, isSys, cb) {
     cb(exists ? sysRoot : root);
   });
 };
+
+exports.compparePlugin = function (dir, mtime, old) {
+  return !old || (mtime > old.mtime && dir === old[PLUGIN_DIR]);
+};
diff --git a/lib/rules/dns.js b/lib/rules/dns.js
index 47c9d0ce2deb9d6c310eda998ca82bd81557717a..f50b370a1f1d1d4652097ba1905fa911b364a0d0 100644
--- a/lib/rules/dns.js
+++ b/lib/rules/dns.js
@@ -177,3 +177,7 @@ module.exports = function lookup(hostname, callback, allowDnsCache) {
     err ? lookupDNS(hostname, callback) : callback(err, ip);
   });
 };
+
+module.exports.clearCache = function() {
+  dnsCache = {};
+};
diff --git a/lib/rules/rules.js b/lib/rules/rules.js
index e39ae8cff0132e15599e5f110bd0a4636547d6bf..7dca81b9c3ce2980834c4a45372ccc8c23475cd0 100644
--- a/lib/rules/rules.js
+++ b/lib/rules/rules.js
@@ -14,7 +14,6 @@ var env = process.env || {};
 var allowDnsCache = true;
 var SUB_MATCH_RE = /\$[&\d]/;
 var BODY_MATCH_RE = /\$b[&\d]/;
-var SPACE_RE = /\s+/g;
 var EXACT_RE = /^\$/;
 var NON_RE = /^!/;
 var HAS_SPACE_RE = /\s/;
@@ -371,7 +370,7 @@ function joinUrl(a, b) {
 }
 
 function toLine(_, line) {
-  return line.replace(SPACE_RE, ' ');
+  return line.replace(/\s+/g, ' ');
 }
 
 function mergeLines(text) {
@@ -1866,7 +1865,7 @@ function matchFilter(url, filter, req) {
     if (keyLen > 0 && key[keyLen] === '%') {
       key = key.substring(0, keyLen) / 100;
     }
-    return getFilterResult(Math.random() < chance.key, filter);
+    return getFilterResult(Math.random() < key, filter);
   }
   if (filterProp(req.method, filter.method, filter.mPattern)) {
     return getFilterResult(result, filter);
diff --git a/lib/service/composer.js b/lib/service/composer.js
index 5851012ddda3eba9d39dc181a2cefdad02c3953a..e57bf334f3e195dce78aa0ddede59b2d89611329 100644
--- a/lib/service/composer.js
+++ b/lib/service/composer.js
@@ -38,7 +38,12 @@ function saveComposerHistory() {
   } catch (e) {}
 }
 
-function handleComposerHistory(data) {
+function getUrl(url, isConn) {
+  url = isConn ? url.replace(/[?#].*$/, '') : url;
+  return url.length > MAX_URL_LEN ? url.substring(0, MAX_URL_LEN) : url;
+}
+
+function handleComposerHistory(data, isConn) {
   var url = data.url;
   var method = data.method;
   var headers = data.headers;
@@ -50,7 +55,7 @@ function handleComposerHistory(data) {
   var result = {
     date: Date.now(),
     useH2: data.useH2,
-    url: url.length > MAX_URL_LEN ? url.substring(0, MAX_URL_LEN) : url,
+    url: getUrl(url, isConn),
     method:
         method.length > MAX_METHOD_LEN
           ? method.substring(0, MAX_METHOD_LEN)
@@ -335,13 +340,13 @@ function getCharset(headers) {
 exports.handleRequest = function(req, res) {
   var fullUrl = req.body.url;
   if (!fullUrl || typeof fullUrl !== 'string') {
-    return res.json({ec: 0});
+    return res.json({ec: 2, em: 'Invalid URL'});
   }
 
   fullUrl = common.encodeNonLatin1Char(fullUrl.replace(/#.*$/, ''));
   var options = common.parseUrl(common.setProtocol(fullUrl));
   if (!options.host) {
-    return res.json({ec: 0});
+    return res.json({ec: 2, em: 'Invalid URL'});
   }
   var protocol = options.protocol;
   if (protocol) {
@@ -386,7 +391,7 @@ exports.handleRequest = function(req, res) {
     }
   }
   if (!req.body.noStore && req.body.needResponse && common.checkHistory(req.body)) {
-    handleComposerHistory(req.body);
+    handleComposerHistory(req.body, isConn);
     dataCenter.saveData({
       type: 'composer',
       history: composerHistory
diff --git a/lib/service/service.js b/lib/service/service.js
index 5504786afb0dd7ea48f0a3dce1df3632520785ce..edaf796585893959275170aabe698a4c6635a7c2 100644
--- a/lib/service/service.js
+++ b/lib/service/service.js
@@ -32,7 +32,7 @@ var TEMP_PLUGINS_PATH = path.join(common.getWhistlePath(), '.temp_plugins');
 var SESSIONS_FILE_RE = /\.(txt|json|saz)$/i;
 var limiter = new Limiter({ concurrency: 10 });
 var MAX_PLUGINS = 10;
-var TEMP_FILES_PATH;
+var TEMP_FILES_PATH = common.TEMP_FILES_PATH;
 var SAVED_SESSIONS_PATH;
 var LIMIT_SIZE = 1024 * 1024 * 128;
 var MAX_TEMP_SIZE = 1024 * 1024 * 12;
@@ -47,7 +47,6 @@ var hasWhistleToken;
 var whistleIdFile;
 var storage = multer.memoryStorage();
 var INVALID_NAME_RE = /[\u001e\u001f\u200e\u200f\u200d\u200c\u202a\u202d\u202e\u202c\u206e\u206f\u206b\u206a\u206d\u206c'<>:"\\/|?*]+/g;
-var SPACE_RE = /\s+/g;
 var upload = multer({
   storage: storage,
   fieldSize: LIMIT_SIZE
@@ -91,7 +90,7 @@ process.on('data', function(data) {
 });
 
 function getFilename(filename, time, count) {
-  filename = common.isString(filename) ? filename.replace(INVALID_NAME_RE, '').replace(SPACE_RE, ' ').substring(0, 64).trim() : '';
+  filename = common.isString(filename) ? filename.replace(INVALID_NAME_RE, '').replace(/\s+/g, ' ').substring(0, 64).trim() : '';
   time = time || Date.now();
   return common.getMonth(time) + '/' + filename + '_' + count + '_' + time;
 }
@@ -108,7 +107,7 @@ function saveSessions(data, cb) {
         return cb(err);
       }
       var filename = getFilename(data.filename, 0, count);
-      util.writeFile(path.join(SAVED_SESSIONS_PATH, filename), buf, function(e) {
+      common.writeFile(path.join(SAVED_SESSIONS_PATH, filename), buf, function(e) {
         !e && saveData({ type: 'savedData', filename: filename, buffer: buf } );
         cb(e);
       });
@@ -167,7 +166,8 @@ function getTempFiles(list, cb) {
     }
   };
   list = list.forEach(function(filename) {
-    if (!common.isTempFile(filename)) {
+    filename = common.getTempFile(filename);
+    if (!filename) {
       return execCb();
     }
     filename = path.join(TEMP_FILES_PATH, filename);
@@ -194,7 +194,7 @@ function writeTempPlugin(plugin, data, cb) {
   plugin = plugin.split('/').pop();
   var tempPath = path.join(TEMP_PLUGINS_PATH, plugin);
   ensureTempPluginsDir();
-  util.writeFile(tempPath, data, function(e) {
+  common.writeFile(tempPath, data, function(e) {
     cb(e, e ? null : tempPath);
   });
 }
@@ -308,6 +308,10 @@ function sessionsHandler() {
     function abort() {
       res.destroy();
     }
+    if (req.headers[common.WHISTLE_UID_HEADER] !== config.uid) {
+      return res.status(403).end('Forbidden');
+    }
+    delete req.headers[common.WHISTLE_UID_HEADER];
     next();
   });
   app.get('/service/*', forwardRequest);
@@ -456,8 +460,9 @@ function sessionsHandler() {
       });
     }
     var filename = req.query.filename;
-    if (common.isTempFile(filename)) {
-      filename = path.join(TEMP_FILES_PATH, filename);
+    var tempFile = common.getTempFile(filename);
+    if (tempFile) {
+      filename = path.join(TEMP_FILES_PATH, tempFile);
     }
     getFile(filename, function(em, data) {
       if (em) {
@@ -470,7 +475,7 @@ function sessionsHandler() {
   app.use('/cgi-bin/temp/create',
     jsonParser,
     function(req, res) {
-      util.writeTempFile(TEMP_FILES_PATH, getContent(req.body), function(e, filename) {
+      common.writeTempFile(getContent(req.body), function(e, filename) {
         if (e) {
           return res.json({ ec: 2, em: e.message });
         }
@@ -609,7 +614,6 @@ function checkWhistleId(cb) {
 module.exports = function (options, callback) {
   config = options;
   whistleIdFile = path.join(options.baseDir, options.storage || '', '.whistle_id');
-  TEMP_FILES_PATH = options.TEMP_FILES_PATH;
   SAVED_SESSIONS_PATH = options.SAVED_SESSIONS_PATH;
   dataCenter.setup(options);
   composer.setup(options);
diff --git a/lib/service/util.js b/lib/service/util.js
index 6ffcc73a02092c7c6825c81fd67b625e98103805..1385462a633215a3e4468bd9743df3201ccb3d98 100644
--- a/lib/service/util.js
+++ b/lib/service/util.js
@@ -1,7 +1,5 @@
-var crypto = require('crypto');
 var path = require('path');
 var fs = require('fs');
-var fse = require('fs-extra2');
 var zlib = require('../util/zlib');
 var common = require('../util/common');
 
@@ -426,16 +424,6 @@ function parseFrames(res, content, callback) {
 
 exports.parseFrames = parseFrames;
 
-function getHexHash(ctn, key) {
-  return crypto
-    .createHmac('sha256', key || 'whistle_temp_files')
-    .update(ctn || '').digest('hex').toLowerCase();
-}
-
-function descSorter(a, b) {
-  return a > b ? -1 : 1;
-}
-
 var MAX_SESSIONS_FILES = 2000;
 var SAVED_SESSIONS_FILE_RE = /_([1-9]\d*)_(\d+)$/;
 var DIR_RE = /^\d{6}$/;
@@ -492,7 +480,9 @@ exports.getSavedList = function(savedDir, cb) {
         list.push(dir);
       }
     });
-    list = list.sort(descSorter).slice(0, 12).map(function(dir) {
+    list = list.sort(function (a, b) {
+      return a > b ? -1 : 1;
+    }).slice(0, 12).map(function(dir) {
       return path.join(savedDir, dir);
     });
     readSessionsFiles(list, cb);
@@ -504,32 +494,3 @@ var SHARE_TYPE_RE = /Share$/;
 exports.isShareType = function(type) {
   return SHARE_TYPE_RE.test(type);
 };
-
-function writeRetry(filepath, data, callback, retry) {
-  fse.outputFile(filepath, data, function(e) {
-    if (!e || retry) {
-      return callback(e);
-    }
-    writeRetry(filepath, data, callback, true);
-  });
-}
-
-function writeFile(filepath, data, callback) {
-  common.getStat(filepath, function(_, stat) {
-    if (!stat || !stat.isFile()) {
-      return writeRetry(filepath, data, callback);
-    }
-    callback();
-  });
-}
-
-exports.writeFile = writeFile;
-
-function writeTempFile(dir, value, callback) {
-  var filename = getHexHash(value);
-  writeFile(path.join(dir, filename), value, function(err) {
-    callback(err, filename);
-  });
-}
-
-exports.writeTempFile = writeTempFile;
diff --git a/lib/socket-mgr.js b/lib/socket-mgr.js
index 7cb9e2eaf02f325a12912d27d552abed3ec15fc7..c09dcf917563cf1d1042490925900896a790ad65 100644
--- a/lib/socket-mgr.js
+++ b/lib/socket-mgr.js
@@ -7,28 +7,14 @@ var extend = require('extend');
 var pendingReqList = [];
 var INTERVAL = 22 * 1000;
 var proxy;
-var index = 0;
-var MAX_PAYLOAD = 1024 * 1024;
 var conns = {};
 var PING = Buffer.from('iQA=', 'base64');
 var PONG = Buffer.from('ioAn6ubf', 'base64');
 var PAUSE_STATUS = 1;
 var IGNORE_STATUS = 2;
 var MAX_COMPOSE_FRAME_COUNT = 5;
-
-function getFrameId() {
-  ++index;
-  if (index > 999) {
-    index = 0;
-  }
-  if (index > 99) {
-    return Date.now() + '-' + index;
-  }
-  if (index > 9) {
-    return Date.now() + '-0' + index;
-  }
-  return Date.now() + '-00' + index;
-}
+var getFrameId = util.getFrameId;
+var MAX_PAYLOAD = util.MAX_FRAME_PAYLOAD;
 
 exports = module.exports = function (p) {
   proxy = p;
diff --git a/lib/util/common.js b/lib/util/common.js
index 0fe7788eebb6715948cf9f5cca4ae62f3035c2aa..c45effb34554f52b3cfa76e73eb6b5a127b47504 100644
--- a/lib/util/common.js
+++ b/lib/util/common.js
@@ -70,10 +70,16 @@ var ALLOW_ACK = 'x-whistle-allow-tunnel-ack';
 var PLUS_RE = /\+/g;
 var TOKEN = '\r\u0000\n\u0003\r';
 var PROP_SEP_RE = /(\\*)([|&]|\\[stnrfv])/g;
-var TEMP_FILE_RE = /^[\da-f]{64}$/;
+var TEMP_FILE_RE = /^(?:\/?temp\/)?([\da-f]{64})(?:\.[\w.-]+)?$/;
+var TEMP_FILES_PATH = path.join(getWhistlePath(), 'temp_files');
+
+
+exports.WHISTLE_UID_HEADER = '_x-whistle-uid_';
+
+exports.getTempFile = function(str) {
+  var match = TEMP_FILE_RE.exec(str);
+  return match && match[1];
 
-exports.isTempFile = function(str) {
-  return TEMP_FILE_RE.test(str);
 };
 
 var PROPS_CHAR = {
@@ -135,6 +141,7 @@ exports.parseQuery = function (str, sep, eq, escape) {
   return '';
 };
 
+exports.TEMP_FILES_PATH = TEMP_FILES_PATH;
 exports.ALLOW_ACK = ALLOW_ACK;
 exports.CONN_TIMEOUT = CONN_TIMEOUT;
 exports.TGZ_FILE_NAME_RE = /^(?:[\w.~-]+-)?whistle\.[a-z\d_-]+-\d+\.\d+\.\d+[\w.-]*\.(?:tgz|tar(?:\.gz)?)$/;
@@ -481,14 +488,8 @@ exports.isConnect = function(options) {
   );
 };
 
-var NO_PROTO_RE = /[^a-zA-Z0-9.-]/;
-
 function hasProtocol(url) {
-  var index = isString(url) ? url.indexOf('://') : -1;
-  if (index <= 0) {
-    return false;
-  }
-  return !NO_PROTO_RE.test(url.substring(0, index));
+  return /^[a-zA-Z0-9.-]+:\/\//.test(url);
 }
 
 function setProtocol(url, isHttps) {
@@ -2001,3 +2002,36 @@ exports.getSessionInfo = function(headers) {
   result._ = rawResult;
   return result;
 };
+
+function writeRetry(filepath, data, callback, retry) {
+  fse.outputFile(filepath, data, function(e) {
+    if (!e || retry) {
+      return callback(e);
+    }
+    writeRetry(filepath, data, callback, true);
+  });
+}
+
+function writeFile(filepath, data, callback) {
+  getStat(filepath, function(_, stat) {
+    if (!stat || !stat.isFile()) {
+      return writeRetry(filepath, data, callback);
+    }
+    callback();
+  });
+}
+
+exports.writeFile = writeFile;
+
+function getHexHash(ctn, key) {
+  return crypto
+    .createHmac('sha256', key || 'whistle_temp_files')
+    .update(ctn || '').digest('hex').toLowerCase();
+}
+
+exports.writeTempFile = function (value, callback) {
+  var filename = getHexHash(value);
+  writeFile(path.join(TEMP_FILES_PATH, filename), value, function(err) {
+    callback(err, filename);
+  });
+};
\ No newline at end of file
diff --git a/lib/util/index.js b/lib/util/index.js
index d13f0078968714fd6d836bef6c7b3a6e8db8fbbb..cea4af96d30e59349e49e3ed41fad51bdc72d3bc 100644
--- a/lib/util/index.js
+++ b/lib/util/index.js
@@ -1164,7 +1164,7 @@ function getTempFilePath(filePath, rule) {
   var root = rule.root;
   if (!root && common.TEMP_PATH_RE.test(filePath)) {
     rule._suffix = RegExp.$2;
-    return path.join(config.TEMP_FILES_PATH, RegExp.$1);
+    return path.join(common.TEMP_FILES_PATH, RegExp.$1);
   }
   return joinPath(root, decodePath(filePath));
 }
@@ -3102,10 +3102,10 @@ function getCookieItem(name, cookie) {
   if (!cookie || typeof cookie != 'object') {
     return name + '=' + (cookie == null ? '' : cookie);
   }
-  var attrs = [name + '=' + escapeValue(cookie.value)];
+  var attrs = [name + '=' + escapeValue(cookie.value || cookie.Value)];
   var maxAge = cookie.maxAge ||  cookie.maxage ||
       cookie.MaxAge || cookie['Max-Age'] || cookie['max-age'];
-  maxAge = parseInt(cookie.maxAge, 10);
+  maxAge = parseInt(maxAge, 10);
   if (!Number.isNaN(maxAge)) {
     attrs.push('Expires=' + new Date(Date.now() + maxAge * 1000).toGMTString());
     attrs.push('Max-Age=' + (maxAge === EXPIRED_SEC ? 0 : maxAge));
@@ -3638,7 +3638,8 @@ function formatAuth(obj) {
   var password = obj.password;
   return {
     username: username == null ? null : String(username),
-    password: password == null ? null : String(password)
+    password: password == null ? null : String(password),
+    proxy: !!obj.proxy
   };
 }
 
@@ -3997,3 +3998,22 @@ exports.isHide = function(req) {
   var d = req.disable || '';
   return req.fromComposer ? checkHideProp(e, d, 'Composer') : checkHideProp(e, d, '', req._filters && req._filters.hide);
 };
+
+
+var frameIndex = 0;
+
+exports.MAX_FRAME_PAYLOAD = 1024 * 1024;
+
+exports.getFrameId = function() {
+  ++frameIndex;
+  if (frameIndex > 999) {
+    frameIndex = 0;
+  }
+  if (frameIndex > 99) {
+    return Date.now() + '-' + frameIndex;
+  }
+  if (frameIndex > 9) {
+    return Date.now() + '-0' + frameIndex;
+  }
+  return Date.now() + '-00' + frameIndex;
+};

Pre-Patch Source Files (Vulnerable state of files modified by patch)
### lib/config.js
```
var path = require('path');
var http = require('http');
var fs = require('fs');
var net = require('net');
var dns = require('dns');
var qs = require('querystring');
var LRU = require('lru-cache');
var httpAgent = http.Agent;
var httpsAgent = require('https').Agent;
var parseUrl = require('./util/parse-url-safe');
var fse = require('fs-extra2');
var extend = require('extend');
var tunnel = require('hagent').agent;
var socks = require('sockx');
var json5 = require('json5');
var pkgConf = require('../package.json');
var config = extend(exports, pkgConf);
var common = require('./util/common');

var customUIHost;
var customHostPluginMap = {};
var customPluginNameHost = {};
var WHISTLE_PLUGIN_RE = /^(?:whistle\.)?([a-z\d_\-]+)$/;
var CMD_RE = /^[\w]{1,12}(?:\s+-g)?$/;
var httpsAgents = new LRU({ max: 360 });
var socksAgents = new LRU({ max: 100 });
var version = process.version.substring(1).split('.');
var disableAgent = version[0] > 10;
var useVerbatim = version[0] >= 17;
var hasIPv6First = version[0] >= 22 && version[1] >= 1;
var hasDnsOrder = typeof dns.setDefaultResultOrder === 'function';
var uid = Date.now().toString(16) + (process.pid * 10000 + Math.floor(Math.random() * 10000)).toString(16);
var IPV4_RE = /^([\d.]+)(:\d{1,5})?$/;
var IPV6_RE = /^\[([\w:]+)\](:\d{1,5})?$/;
var noop = function () {};
var DATA_KEY_RE = /^(clientip|clientid|tunneldata)([=.])([\w.-]+)$/i;
var DNS_ORDERS = ['ipv4First', 'ipv4first', 'ipv6first', 'ipv6First', 'verbatim'];
var LOCAL_UI_HOST_LIST = [
  'local.whistlejs.com',
  'local.wproxy.org',
  'rootca.pro'
];
var variableProperties = [
  'encrypted',
  'sockets',
  'dataDirname',
  'storage',
  'baseDir',
  'noGlobalPlugins',
  'pluginsDataMap',
  'globalData',
  'username',
  'password',
  'debugMode',
  'localUIHost',
  'extra',
  'rules',
  'values',
  'dnsCache',
  'allowDisableShadowRules',
  'disableInstaller'
];
if (hasDnsOrder) {
  if (hasIPv6First) {
    config.verbatim = 2;
  } else {
    config.verbatim = 1;
  }
}

config.appName = common.upperFirst(config.name);
config.defaultDnsOrder = useVerbatim ? 1 : 2;
config.uid = uid;
config.rejectUnauthorized = false;
config.enableH2 = version[0] > 12; // 支持 HTTP2 要求的最低 Node 版本
config.ASSESTS_PATH = path.join(__dirname, '../assets');
config.WHISTLE_POLICY_HEADER = 'x-whistle-policy';
config.CLIENT_IP_HEADER = common.CLIENT_IP_HEADER;
config.HTTPS_FIELD = common.HTTPS_FIELD;
config.CLIENT_INFO_HEADER = 'x-whistle-client-info-' + uid;
config.SHOW_LOGIN_BOX = 'x-whistle-show-login-box-' + uid;
config.WEBUI_PATH = '/.whistle-path.5b6af7b9884e1165/';
config.PREVIEW_PATH_RE = /\?\?\?WHISTLE_PREVIEW_CHARSET=([A-Z\d_-]+)\?\?\?$/;
config.PLUGIN_HOOK_NAME_HEADER = 'x-whistle-plugin-hook-name_';
config.CLIENT_ID_HEADER = common.CLIENT_ID_HEADER;
config.CLIENT_PORT_HEADER = common.CLIENT_PORT_HEADER;
config.ALPN_PROTOCOL_HEADER = common.ALPN_PROTOCOL_HEADER;
config.DISABLE_RULES_HEADER = 'x-whistle-proxy-rules-' + uid;
config.PROXY_ID_HEADER = 'x-whistle-proxy-id-' + uid;
config.WEBUI_HEAD = 'x-forwarded-from-whistle-' + uid;
config.RES_RULES_HEAD = 'x-whistle-res-rules-' + uid;
config.COMPOSER_CLIENT_ID_HEADER = 'x-whistle-client-id-' + uid;
config.FROM_COM_HEADER = 'x-whistle-composer-' + uid;
config.PLUGIN_HOOKS = {
  SNI: 'sni-' + uid,
  AUTH: 'auth-' + uid,
  HTTP: 'http-' + uid,
  UI: 'ui-' + uid,
  TUNNEL: 'tunnel-' + uid,
  TUNNEL_RULES: 'tunnel-rules-' + uid,
  REQ_STATS: 'req-stats-' + uid,
  RES_STATS: 'res-stats-' + uid,
  REQ_RULES: 'req-rules-' + uid,
  RES_RULES: 'res-rules-' + uid,
  REQ_READ: 'req-read-' + uid,
  REQ_WRITE: 'req-write-' + uid,
  RES_READ: 'res-read-' + uid,
  RES_WRITE: 'res-write-' + uid,
  WS_REQ_READ: 'ws-req-read-' + uid,
  WS_REQ_WRITE: 'ws-req-write-' + uid,
  WS_RES_READ: 'ws-res-read-' + uid,
  WS_RES_WRITE: 'ws-res-write-' + uid,
  TUNNEL_REQ_READ: 'tunnel-req-read-' + uid,
  TUNNEL_REQ_WRITE: 'tunnel-req-write-' + uid,
  TUNNEL_RES_READ: 'tunnel-res-read-' + uid,
  TUNNEL_RES_WRITE: 'tunnel-res-write-' + uid
};

var KEEP_ALIVE_MSECS = 10000;
var CONN_TIMEOUT = common.CONN_TIMEOUT;
var DNS_ORDERS_OPTS = ['', 'verbatim', 'ipv4first', hasIPv6First ? 'ipv6first' : ''];
var DOMAIN_STAR_RE = /([*~]+)(\\.)?/g;

config.CONN_TIMEOUT = CONN_TIMEOUT;

var getWhistlePath = common.getWhistlePath;
var getHostPort = common.getHostPort;

var ALL_WHISTLES_PATH = path.join(getWhistlePath(), 'all_whistles');


function domainToRegExp(_, star, dot) {
  var len = star.length;
  var result = len > 1 ? '([^/?]*)' : '([^/?.]*)';
  if (dot) {
    result += '\\.';
    if (len > 2) {
      result = '(?:' + result + ')?';
    }
  }
  return result;
}

function getDataDir(dirname) {
  var dir = path.join(getWhistlePath(), dirname || '.' + config.name);
  fse.ensureDirSync(dir);
  return dir;
}

config.baseDir = getDataDir();
config.TEMP_FILES_PATH = path.join(getWhistlePath(), 'temp_files');
config.CUSTOM_PLUGIN_PATH = path.join(getWhistlePath(), 'custom_plugins');
config.CUSTOM_CERTS_DIR = path.resolve(getWhistlePath(), 'custom_certs');
config.SAVED_SESSIONS_PATH = path.resolve(getWhistlePath(), 'saved_sessions');
config.DEV_PLUGINS_PATH = path.resolve(getWhistlePath(), 'dev_plugins');
config.rulesDir = path.join(config.baseDir, 'rules');
config.valuesDir = path.join(config.baseDir, 'values');
config.propertiesDir = path.join(config.baseDir, 'properties');

try {
  fse.ensureDirSync(config.TEMP_FILES_PATH);
  var blankFile = path.join(config.TEMP_FILES_PATH, 'blank');
  if (!fs.existsSync(blankFile)) {
    fs.writeFileSync(blankFile, '');
  }
} catch (e) {}
try {
  fse.ensureDirSync(config.CUSTOM_CERTS_DIR);
} catch (e) {}
try {
  fse.ensureDirSync(config.SAVED_SESSIONS_PATH);
} catch (e) {}

exports.getWhistlePath = getWhistlePath;
exports.getDataDir = getDataDir;
var async_id_symbol;
if (version[0] < 16) {
  try {
    async_id_symbol = process.binding('async_wrap').async_id_symbol;
  } catch (e) {}
}
var emptyHandle = {
  asyncReset: noop,
  getAsyncId: noop
};

function createAgent(agentConfig, https) {
  var agent = new (https ? httpsAgent : httpAgent)(agentConfig);
  if (async_id_symbol) {
    var addRequest = agent.addRequest;
    agent.addRequest = function (req, options) {
      // fix: https://github.com/nodejs/node/issues/13539
      var freeSockets = this.freeSockets[this.getName(options)];
      if (freeSockets && freeSockets.length) {
        var socket = freeSockets[0];
        var handle = socket._handle;
        if (!handle) {
          socket._handle = emptyHandle;
        } else if (typeof handle.asyncReset !== 'function') {
          handle.asyncReset = noop;
        }
        var originalRef = socket.ref;
        socket.ref = function () {
          socket.ref = originalRef;
          if (socket._handle === emptyHandle) {
            delete socket._handle;
          } else if (socket._handle.asyncReset === noop) {
            delete socket._handle.asyncReset;
          }
          socket.ref();
        };
      }
      var onSocket = req.onSocket;
      req.onSocket = function (socket) {
        try {
          socket[async_id_symbol] = socket._handle.getAsyncId();
        } catch (e) {}
        onSocket.apply(this, arguments);
      };
      addRequest.apply(this, arguments);
    };
  }
  return agent;
}

function capitalize(str) {
  return (str && str[0].toUpperCase()) + str.substring(1);
}

function getHttpsAgent(options, reqOpts) {
  var key = getCacheKey(options);
  var agent = httpsAgents.get(key);
  if (reqOpts) {
    var headers = options.headers || {};
    var proxyHeaders = {};
    Object.keys(headers).forEach(function (key) {
      var rawKey = key.split('-').map(capitalize).join('-');
      proxyHeaders[rawKey] = headers[key];
    });
    reqOpts._tunnelProxyHeaders = proxyHeaders;
  }
  if (!agent) {
    options.proxyAuth = options.auth;
    options.rejectUnauthorized = config.rejectUnauthorized;
    options.proxy = {
      host: options.proxyHost,
      port: options.proxyPort,
      enableIntercept: options.enableIntercept,
      keepStreamResume: options.keepStreamResume,
      proxyTunnelPath: options.proxyTunnelPath
    };
    var agentName = options.isHttps ? 'httpsOverHttp' : 'httpOverHttp';
    if (options.proxyServername) {
      options.proxy.servername = options.proxyServername;
      agentName += 's';
    }
    agent = new tunnel[agentName](options);
    httpsAgents.set(key, agent);
    agent.on('free', preventThrowOutError);
  }
  return agent;
}

exports.getHttpsAgent = getHttpsAgent;

function getCacheKey(options, isSocks) {
  var auth = options.auth || options.proxyAuth;
  if (!auth) {
    var headers = options.headers || '';
    auth = headers['proxy-authorization'] || '';
  }
  var ip = (!isSocks && options.clientIp) || '';
  return [
    options.proxyServername ? 'https-proxy' : '',
    options.isHttps ? 'https' : 'http',
    options.proxyHost,
    options.proxyPort,
    auth,
    ip,
    options.proxyTunnelPath || '',
    (options.isHttps && options.cacheKey) || ''
  ].join(':');
}

function getAuths(_url) {
  var options = typeof _url == 'string' ? parseUrl(_url) : _url;
  if (!options || !options.auth) {
    return [socks.auth.None()];
  }

  var auths = [];
  options.auth.split('|').forEach(function (auth) {
    auth = auth.trim();
    if (auth) {
      var index = auth.indexOf(':');
      auths.push({
        username: index == -1 ? auth : auth.substring(0, index),
        password: index == -1 ? '' : auth.substring(index + 1)
      });
    }
  });

  return auths.length
    ? auths.map(function (auth) {
      return socks.auth.UserPassword(auth.username, auth.password);
    })
    : [socks.auth.None()];
}

exports.getAuths = getAuths;

function setDefaultResultOrder(order) {
  if (!hasDnsOrder) {
    return;
  }
  order = DNS_ORDERS_OPTS.indexOf(order) === -1 ? DNS_ORDERS_OPTS[order] : order;
  if (!order) {
    return;
  }
  config.ipv4First = false;
  config.ipv6First = false;
  if (order[3] === '6') {
    config.ipv6First = true;
  } else if (order[3] === '4') {
    config.ipv4First = true;
  }
  try {
    if (dns.getDefaultResultOrder() !== order) {
      dns.setDefaultResultOrder(order);
    }
    config.dnsOrder = DNS_ORDERS_OPTS.indexOf(order);
    return true;
  } catch (e) {}
}

exports.setDefaultResultOrder = setDefaultResultOrder;

exports.setAuth = function (auth) {
  if (auth) {
    config.username = getString(auth.username);
    var password = (config.password = getString(auth.password));
    config.passwordHash = password && common.createHash(password);
    setGuestAuth(auth);
  }
  return config;
};

exports.getPluginData = function (name) {
  var pluginsDataMap = name && config.pluginsDataMap;
  if (!pluginsDataMap) {
    return;
  }
  name = name.substring(name.lastIndexOf('.') + 1);
  return pluginsDataMap[name];
};

exports.setGuestAuth = function (auth) {
  auth && setGuestAuth(auth);
};

function parseHost(host) {
  if (Array.isArray(host)) {
    return host.filter(function (h) {
      return h && typeof h === 'string';
    });
  }
  host = typeof host === 'string' ? host.trim() : '';
  return host && host.split('|').map(getHostname);
}

exports.setUIHost = function (host) {
  customUIHost = parseHost(host);
};

exports.setPluginUIHost = function (pluginName, host) {
  if (!pluginName || !WHISTLE_PLUGIN_RE.test(pluginName)) {
    return;
  }
  pluginName = RegExp.$1;
  host = parseHost(host);
  if (host) {
    customPluginNameHost[pluginName] = host;
    host.forEach(function (h) {
      delete customHostPluginMap[h];
    });
  } else {
    delete customPluginNameHost[pluginName];
  }
  customHostPluginMap = {};
  Object.keys(customPluginNameHost).forEach(function (name) {
    var list = customPluginNameHost[name];
    list &&
      list.forEach(function (h) {
        customHostPluginMap[h] = name;
      });
  });
};

exports.connect = function (options, cb) {
  return common.connectInner(options, cb, config);
};

function preventThrowOutError(socket) {
  if (socket.listeners('error').indexOf(freeSocketErrorListener) === -1) {
    socket.once('error', freeSocketErrorListener);
  }
}

function freeSocketErrorListener() {
  var socket = this;
  socket.destroy();
  socket.emit('agentRemove');
  socket.removeListener('error', freeSocketErrorListener);
}

function resolvePath(file) {
  if (!file || !(file = file.trim())) {
    return file;
  }

  return /^[\w-]+$/.test(file) ? file : path.resolve(file);
}

function getHostname(_url) {
  if (typeof _url != 'string') {
    return '';
  }
  if (_url.indexOf('/') != -1) {
    return parseUrl(_url).hostname;
  }
  var index = _url.indexOf(':');
  return index == -1 ? _url : _url.substring(0, index);
}

function getPaths(paths, isCustom) {
  if (typeof paths === 'string') {
    paths = paths.trim().split(/\s*[|,;]\s*/);
  } else if (!Array.isArray(paths)) {
    return;
  }
  var result = [];
  paths.forEach(function (path) {
    if (isCustom && ['self', 'buildin', 'buildIn', 'build-in'].indexOf(path) !== -1) {
      result.push(config.CUSTOM_PLUGIN_PATH);
    } else if (path && typeof path === 'string') {
      result.push(path);
    }
  });
  return result.length ? result : null;
}

function getSecureFilter(newConf) {
  var secureFilter = newConf.secureFilter;
  if (typeof secureFilter === 'function') {
    return secureFilter;
  }
  if (!secureFilter || typeof secureFilter !== 'string') {
    return;
  }
  try {
    return require(secureFilter);
  } catch (e) {}
}

function getString(str) {
  return str && typeof str === 'string' ? str : '';
}

function readFileText(filepath) {
  var text = common.readFileTextSync(filepath);
  return text && text.trim();
}

function readFileBuffer(filepath, required) {
  return common.readFileBufferSync(filepath, required === false);
}

function isPort(port) {
  return /^\d+$/.test(port) && port <= 65535 && port > 0;
}

function setGuestAuth(auth) {
  if (auth.guestName === '-' && !auth.guestPassword) {
    config.guest = {};
  } else if (auth.guestName && auth.guestPassword) {
    config.guest = {
      username: auth.guestName,
      password: auth.guestPassword
    };
  } else if ('guest' in auth) {
    config.guest = auth.guest;
  }
}

function parseString(str) {
  str = str && typeof str === 'string' && str.trim();
  if (!str) {
    return '';
  }
  str = readFileText(str) || str;
  if (!/\s/.test(str) && str.indexOf('%') !== -1) {
    try {
      str = decodeURIComponent(str);
    } catch (e) {}
  }
  if (/^\{[\s\S]+\}$/.test(str) || /^\[[\s\S]+\]$/.test(str)) {
    try {
      return json5.parse(str);
    } catch (e) {}
  }
  return str;
}

function getPluginList(list) {
  if (typeof list == 'string') {
    list = list.trim().split(/\s*[,|]\s*/);
  }
  var result;
  if (Array.isArray(list)) {
    list.forEach(function (name) {
      if (WHISTLE_PLUGIN_RE.test(name)) {
        result = result || [];
        result.push(RegExp.$1);
      }
    });
  }
  return result;
}

function readUIExt(uiExt) {
  if (!uiExt) {
    return;
  }
  var htmlPrepend = uiExt.htmlPrepend && readFileBuffer(uiExt.htmlPrepend, uiExt.required);
  var htmlAppend = uiExt.htmlAppend && readFileBuffer(uiExt.htmlAppend, uiExt.required);
  var jsPrepend = uiExt.jsPrepend && readFileBuffer(uiExt.jsPrepend, uiExt.required);
  var jsAppend = uiExt.jsAppend && readFileBuffer(uiExt.jsAppend, uiExt.required);
  if (htmlPrepend ||htmlAppend || jsPrepend || jsAppend) {
    if (htmlPrepend) {
      htmlPrepend = Buffer.concat([Buffer.from('<!DOCTYPE html>\n'), htmlPrepend]);
    }
    return {
      htmlPrepend: htmlPrepend,
      htmlAppend: htmlAppend,
      jsPrepend: jsPrepend,
      jsAppend: jsAppend
    };
  }
}

exports.extend = function (newConf) {
  config.pluginHostMap = {};
  config.uiport = config.port;
  config.ipv6Only = false;
  var rcConf = common.readWhistleRc(newConf);
  newConf = extend({}, rcConf, newConf);
  if (rcConf) {
    if (rcConf.clearPreOptions) {
      newConf.clearPreOptions = true;
    }
    if (rcConf.noGlobalPlugins) {
      newConf.noGlobalPlugins = true;
    }
  }
  if (process.env.WHISTLE_MODE) {
    newConf.mode = process.env.WHISTLE_MODE + '|' + (newConf.mode || '');
  }
  var useAgent;
  var newAgentConf;

  if (newConf.specialPath && typeof newConf.specialPath === 'string') {
    config.SPEC_PATH = newConf.specialPath;
  }
  if (newConf.whistleName && common.isWhistleName(newConf.whistleName)) {
    config.whistleName = newConf.whistleName;
  }
  config.uiExt = readUIExt(newConf.uiExt);
  config.specialAuth = newConf.specialAuth;
  config.uiMiddleware = newConf.uiMiddlewares || newConf.uiMiddleware;
  newAgentConf = newConf.agentConfig;
  if (newConf.cmdName && CMD_RE.test(newConf.cmdName)) {
    config.cmdName = newConf.cmdName;
  }
  if (newConf.account && typeof newConf.account === 'string') {
    config.account = newConf.account;
  }
  config.allowPluginList = getPluginList(newConf.allowPluginList);
  config.blockPluginList = getPluginList(newConf.blockPluginList);

  if (newConf.webUIPath && /^[\w.-]+$/.test(newConf.webUIPath)) {
    config.WEBUI_PATH = '/.' + newConf.webUIPath + config.WEBUI_PATH.substring(1);
  }
  if (newConf.cluster) {
    config.headless = true;
    config.workerIndex = process.env.workerIndex;
    if (typeof newConf.mode !== 'string') {
      newConf.mode = '';
    }
  }
  var dnsServer = newConf.dnsServer;
  var resolve6;
  var dnsOptional;
  if (common.isString(dnsServer)) {
    dnsServer = dnsServer.trim();
    if (common.isUrl(dnsServer)) {
      config.dnsOverHttps = dnsServer;
    } else {
      dnsServer = dnsServer.split(/[|,&]/);
    }
  }

  var allowOrigin = newConf.allowOrigin;
  if (common.isString(allowOrigin)) {
    allowOrigin = allowOrigin.trim().toLowerCase().split(/\s*[|,&]\s*/);
    if (allowOrigin.indexOf('*') === -1) {
      allowOrigin = allowOrigin.map(function(h) {
        if (h.indexOf('*') === -1) {
          return h;
        }
        h = common.escapeRegExp(h);
        h = h.replace(DOMAIN_STAR_RE, domainToRegExp);
        try {
          return new RegExp('^' + h + '$');
        } catch (e) {}
      }).filter(function(h) {
        return h;
      });
      if (allowOrigin.length) {
        config.allowOrigin = allowOrigin;
      }
    } else {
      config.allowAllOrigin = true;
    }
  }

  if (dns.getServers && Array.isArray(dnsServer)) {
    var newServers = [];
    dnsServer.forEach(function (ip) {
      ip = typeof ip === 'string' && ip.trim();
      if (/^ipv6$/i.test(ip)) {
        resolve6 = true;
      } else if (ip === 'optional' || ip === 'default' || ip === 'fallback') {
        dnsOptional = true;
      } else if (net.isIP(ip)) {
        newServers.push(ip);
      } else if (IPV4_RE.test(ip) || IPV6_RE.test(ip)) {
        var dnsIp = RegExp.$1;
        var dnsPort = RegExp.$2;
        if (net.isIP(dnsIp) && (!dnsPort || isPort(dnsPort.substring(1)))) {
          newServers.push(ip);
        }
      }
    });
    if (newServers.length) {
      dns.setServers(newServers);
      config.resolve6 = resolve6;
      config.dnsOptional = dnsOptional;
      config.dnsServer = newServers.join();
    }
  }

  if (newConf.inspect || newConf.inspectBrk) {
    config.inspectMode = true;
    process.env.PFORK_MODE = 'inline';
  }
  variableProperties.forEach(function (name) {
    config[name] = newConf[name] || pkgConf[name];
  });
  var shadowRules = parseString(newConf.shadowRules);
  var resolveShadowValues = function (obj) {
    if (
        (!obj.rules || typeof obj.rules === 'string') &&
        obj.values &&
        typeof obj.values !== 'string'
      ) {
      config.shadowRules = obj.rules || obj.rules.trim();
      if (Object.keys(obj.values).length) {
        config.shadowValues = obj.values;
      }
    } else {
      config.rules = extend({}, newConf.rules, obj);
    }
  };
  if (typeof shadowRules === 'string') {
    config.shadowRules = shadowRules.trim();
  } else if (Array.isArray(shadowRules)) {
    if (typeof shadowRules[0] === 'string') {
      config.shadowRules = shadowRules[0].trim();
      if (shadowRules[1]) {
        config.rules = extend({}, newConf.rules, shadowRules[1]);
      }
      if (shadowRules[2]) {
        config.values = extend({}, newConf.values, shadowRules[2]);
      }
    } else if (shadowRules[0]) {
      resolveShadowValues(shadowRules[0]);
      if (shadowRules[1]) {
        config.values = extend({}, newConf.values, shadowRules[1]);
      }
    } else if (shadowRules[1]) {
      config.values = extend({}, newConf.values, shadowRules[1]);
    }
  } else if (shadowRules) {
    resolveShadowValues(shadowRules);
  }
  var extra = newConf.extra;
  if (common.isString(extra)) {
    extra = /^\s*\{[\w\W]*\}\s*$/.test(extra) ? extra : readFileText(extra);
    try {
      extra = extra && JSON.parse(extra);
      if (extra && typeof extra === 'object') {
        config.pluginsDataMap = extend({}, config.pluginsDataMap, extra);
      }
    } catch (e) {}
    extra = null;
  }
  var customHandler = newConf.customHandler || newConf.customHandle;
  if (typeof customHandler === 'function') {
    config.customHandler = customHandler;
  }
  if (isPort(newConf.realPort) && config.realPort != config.port) {
    config.realPort = newConf.realPort;
  }
  var realHost = newConf.realHost;
  if (typeof realHost === 'string' && (!realHost || /^[\w.-]+$/.test(newConf.realHost))) {
    config.realHost = newConf.realHost;
  }

  var socksPort = getHostPort(newConf.socksPort);
  if (socksPort) {
    config.socksPort = socksPort.port;
    config.socksHost = socksPort.host;
  }
  var httpPort = getHostPort(newConf.httpPort);
  if (httpPort) {
    config.httpPort = httpPort.port;
    config.httpHost = httpPort.host;
  }
  var httpsPort = getHostPort(newConf.httpsPort);
  if (httpsPort) {
    config.httpsPort = httpsPort.port;
    config.httpsHost = httpsPort.host;
  }

  if (common.isString(newConf.host)) {
    config.defaultHost = newConf.host;
  }

  if (typeof newConf.authKey === 'string') {
    config.authKey = newConf.authKey;
  }
  if (typeof newConf.guestAuthKey === 'string') {
    config.guestAuthKey = newConf.guestAuthKey;
  }
  if (newConf.reqCacheSize > 0) {
    config.reqCacheSize = newConf.reqCacheSize;
  }
  if (newConf.frameCacheSize > 0) {
    config.frameCacheSize = newConf.frameCacheSize;
  }
  config.allowMultipleChoice = newConf.allowMultipleChoice;
  if (common.isString(newConf.mode)) {
    var mode = newConf.mode.trim().split(/\s*[|,&]\s*/);
    var useResolve;
    var dnsFallback;
    if (mode.indexOf('admin') !== -1) {
      var admin = 'proxyServer|master|x-forwarded-proto';
      admin = config.debugMode ? admin : `${admin}|strict|rules|disableUpdateTips|proxifier|notAllowedDisablePlugins`;
      mode = admin.split('|').concat(mode);
    }
    if (mode.indexOf('multiple') !== -1) {
      mode = 'multiEnv|disableUpdateTips|keepXFF|x-forwarded-proto'.split('|').concat(mode);
    }
    mode.forEach(function (m) {
      m = m.trim();
      if (
          /^(pureProxy|debug|ipv6Only|master|client|diagnose|disableAuthUI|captureData|headless|strict|proxyServer|encrypted|noGzip|disableUpdateTips|proxifier2?)$/.test(m)
        ) {
        config[m] = true;
      } else if(m === 'ipv6only') {
        config.ipv6Only = true;
      } else if (m === 'keepProxyUI') {
        config.keepProxyUI = true;
      } else if (m === 'agent') {
        useAgent = true;
      } else if (m === 'disableUIAuth') {
        config.disableAuthUI = true;
      } else if (m === 'showPluginReq') {
        config.showPluginReq = config.debugMode;
      } else if (m === 'disableCustomCerts') {
        config.disableCustomCerts = true;
      } else if (m === 'nohost' || m === 'multienv' || m === 'multiEnv') {
        config[m] = true;
        config.multiEnv = true;
      } else if (DNS_ORDERS.indexOf(m) !== -1) {
        setDefaultResultOrder(m.toLowerCase());
      } else if (m === 'proxyOnly') {
        config.pureProxy = true;
      } else if (m === 'useMultipleRules' || m === 'enableMultipleRules') {
        config.allowMultipleChoice = true;
      } else if (m === 'disableMultipleRules') {
        config.allowMultipleChoice = false;
      } else if (
        m === 'notAllowDisableRules' ||
        m === 'notAllowedDisableRules'
      ) {
        config.notAllowedDisableRules = true;
      } else if (m === 'disableBackOption' || m === 'disabledBackOption') {
        config.disabledBackOption = true;
      } else if (
        m === 'disableMultipleOption' ||
        m === 'disabledMultipleOption'
      ) {
        config.disabledMultipleOption = true;
      } else if (
        m === 'disableRulesOptions' ||
        m === 'disabledRulesOptions'
      ) {
        config.disabledRulesOptions = true;
        config.disabledBackOption = true;
        config.disabledMultipleOption = true;
        config.notAllowedDisableRules = true;
      } else if (
        m === 'notAllowDisablePlugins' ||
        m === 'notAllowedDisablePlugins'
      ) {
        config.notAllowedDisablePlugins = true;
      } else if (
        m === 'notAllowEnableHTTPS' ||
        m === 'notAllowedEnableHTTPS'
      ) {
        config.notAllowedEnableHTTPS = true;
      } else if (m === 'socks') {
        config.socksMode = true;
      } else if (m === 'network') {
        config.networkMode = true;
        config.captureData = true;
      } else if (m === 'shadowRules') {
        config.shadowRulesMode = true;
      } else if (m === 'shadowRulesOnly') {
        config.shadowRulesMode = true;
        config.disableWebUI = true;
      } else if (m === 'plugins') {
        config.pluginsMode = true;
      } else if (m === 'pluginsOnly') {
        config.pluginsOnlyMode = true;
      } else if (m === 'rules') {
        config.rulesMode = true;
      } else if (m === 'rulesOnly') {
        config.rulesOnlyMode = true;
      } else if (m === 'httpProxy') {
        config.pureProxy = true;
      } else if (
        m === 'keepXFF' ||
        m === common.CLIENT_IP_HEADER ||
        m === 'forwardedFor'
      ) {
        config.keepXFF = true;
      } else if (m === 'x-forwarded-host') {
        config.enableFwdHost = true;
      } else if (m === 'x-forwarded-proto') {
        config.enableFwdProto = true;
      } else if (m === 'INADDR_ANY') {
        config.INADDR_ANY = true;
      } else if (m === 'buildIn' || m === 'build-in') {
        process.env.PFORK_EXEC_PATH = process.execPath;
      } else if (m === 'safe' || m === 'rejectUnauthorized') {
        config.rejectUnauthorized = true;
      } else if (m === 'enableRequestHeaderRules') {
        config.enableRequestHeaderRules = true;
      } else if (m === 'persistentCapture') {
        config.isEnableCapture = true;
        config.persistentCapture = true;
      } else if (['capture', 'intercept', 'enable-capture', 'enableHttps', 'enableHTTPS', 'enableCapture'].indexOf(m) !== -1) {
        config.isEnableCapture = true;
      } else if (['disable-capture', 'disableCapture'].indexOf(m) !== -1) {
        config.isEnableCapture = false;
      } else if (['http2',  'enable-http2', 'enableHttp2', 'enable-h2', 'enableH2'].indexOf(m) !== -1) {
        config.isEnableHttp2 = true;
      } else if (
        ['disable-http2', 'disableHttp2', 'disable-h2', 'disableH2'].indexOf(m) !== -1
      ) {
        config.isEnableHttp2 = false;
      } else if (m === 'hideLeftBar' || m === 'hideLeftMenu') {
        config.hideLeftMenu = true;
      } else if (DATA_KEY_RE.test(m)) {
        var type = RegExp.$1;
        var override = RegExp.$2 === '=';
        var key = RegExp.$3.toLowerCase();
        switch (type) {
        case 'clientip':
          config.overCipKey = override;
          config.cipKey = key;
          break;
        case 'clientid':
          config.overCidKey = override;
          config.cidKey = key;
          break;
        default:
          config.overTdKey = override;
          config.tdKey = key;
          break;
        }
      } else if (['dnsResolve', 'dnsResolve4', 'dnsResolve6'].indexOf(m) !== -1) {
        useResolve = true;
        config[m] = true;
      } else if (m === 'dnsFallback') {
        dnsFallback = true;
      }
    });

    if (useResolve && dnsFallback) {
      config.dnsFallback = true;
    }
    if (config.headless) {
      if (!config.pluginsMode) {
        config.noGlobalPlugins = true;
      }
      config.pluginsOnlyMode = true;
      config.disableWebUI = true;
      delete config.rulesOnlyMode;
    } else if (config.shadowRulesMode) {
      config.networkMode = true;
      delete config.rulesOnlyMode;
      delete config.pluginsOnlyMode;
    }
    if (config.rulesOnlyMode) {
      delete config.pluginsOnlyMode;
      delete config.networkMode;
      delete config.pluginsMode;
      config.rulesMode = true;
    } else if (config.pluginsOnlyMode) {
      delete config.networkMode;
      config.rulesMode = true;
      config.pluginsMode = true;
    } else if (config.networkMode) {
      delete config.rulesMode;
      delete config.pluginsMode;
    } else if (config.rulesMode) {
      delete config.pluginsMode;
      delete config.networkMode;
    }
  }
  if (/^\d+$/.test(newConf.timeout)) {
    config.timeout = +newConf.timeout;
  }

  setGuestAuth(newConf);
  config.disableAllRules = newConf.disableAllRules;
  config.disableAllPlugins = newConf.disableAllPlugins;
  if (newConf.replaceExistRule === false) {
    config.replaceExistRule = false;
  } else {
    config.replaceExistRule = newConf.replaceRules;
  }
  if (newConf.replaceExistValue === false) {
    config.replaceExistValue = false;
  } else {
    config.replaceExistValue = newConf.replaceValues;
  }
  if (common.isString(newConf.certDir)) {
    config.certDir = path.resolve(newConf.certDir);
  }
  var mw = newConf.middlewares || newConf.middleware;
  if (typeof mw == 'string') {
    config.middlewares = mw.trim().split(/\s*,\s*/);
  }
  var secureFilter = getSecureFilter(newConf);
  if (typeof secureFilter === 'function') {
    config.secureFilter = secureFilter;
  }
  if (typeof newConf.installPlugins === 'function') {
    config.installPlugins = newConf.installPlugins;
    config.hasInstaller = true;
  }
  if (typeof newConf.handleWebReq === 'function') {
    config.handleWebReq = newConf.handleWebReq;
  }
  if (typeof newConf.handleUpdate === 'function') {
    config.handleUpdate = newConf.handleUpdate;
    config.hasUpdater = true;
  }
  config.notUninstallPluginPaths = getPaths(newConf.notUninstallPluginPath || newConf.notUninstallPluginPaths);
  config.pluginPaths = getPaths(newConf.pluginPaths || newConf.pluginsPath || newConf.pluginPath);
  config.prePluginsPath = config.projectPluginPaths = getPaths(newConf.projectPluginPaths || newConf.projectPluginsPath || newConf.projectPluginPath);
  config.accountPluginsPath = getPaths(newConf.accountPluginPaths || newConf.accountPluginsPath || newConf.accountPluginPath);
  config.customPluginPaths = getPaths(newConf.customPluginPaths || newConf.customPluginsPath || newConf.customPluginPath, true);
  config.addon = getPaths(newConf.addonsPath || newConf.addonPath || newConf.addon);
  if (config.accountPluginsPath) {
    config.customPluginPaths = config.accountPluginsPath.concat(config.customPluginPaths || []);
  }
  if (config.customPluginPaths) {
    config.prePluginsPath = (config.prePluginsPath || []).concat(config.customPluginPaths);
  }

  var pluginHost = newConf.pluginHost;
  if (typeof pluginHost === 'string' && (pluginHost = pluginHost.trim())) {
    pluginHost = qs.parse(pluginHost);
    Object.keys(pluginHost).forEach(function (name) {
      var host = pluginHost[name];
      if (typeof host === 'string' && (host = host.trim())) {
        host = host.toLowerCase().split(/\s*[|,&]\s*/);
        host.forEach(function (h) {
          config.pluginHostMap[h] = name;
        });
      }
    });
  }

  var port = getHostPort(newConf.port);
  if (port) {
    config.host = port.host;
    config.uiport = config.port = port.port;
  }
  if (config.disableWebUI) {
    config.notAllowedDisablePlugins = true;
  } else {
    var uiPort = getHostPort(newConf.uiport);
    if (uiPort) {
      var curHost = config.host || config.defaultHost;
      if (curHost && uiPort.host && curHost !== uiPort.host) {
        config.customUIPort = true;
      } else {
        config.customUIPort = uiPort.port != config.port;
      }
      config.uiport = uiPort.port;
      config.uihost = uiPort.host;
    }
  }


  if (!config.rulesMode) {
    config.captureData = true;
  }

  if (!config.authKey) {
    config.authKey = 'auto_' + (Date.now() + Math.random().toFixed(6));
  }
  config.middlewares = Array.isArray(config.middlewares)
    ? config.middlewares.map(resolvePath)
    : [];
  var uiHostList = (config.uiHostList = []);
  if (typeof config.localUIHost === 'string') {
    var localHostList = config.localUIHost.toLowerCase().split(/\s*[|,&]\s*/);
    localHostList.forEach(function (hostname) {
      hostname = getHostname(hostname);
      if (hostname && LOCAL_UI_HOST_LIST.indexOf(hostname) == -1) {
        uiHostList.push(hostname);
      }
    });
    LOCAL_UI_HOST_LIST.push.apply(LOCAL_UI_HOST_LIST, uiHostList);
    // 兼容老版本
    config.customLocalUIHost = uiHostList[0];
  }

  config.setLocalUIHost = function (hostname) {
    config.customLocalUIHost = getHostname(hostname);
  };

  config.localUIHost = 'local.whistlejs.com';

  var isWebUIHost = function (host) {
    if (
      host === 'local.wproxy.org' ||
      uiHostList.indexOf(host) !== -1 ||
      (customUIHost && customUIHost.indexOf(host) !== -1)
    ) {
      return true;
    }
    if (config.pureProxy) {
      return false;
    }
    return LOCAL_UI_HOST_LIST.indexOf(host) !== -1;
  };
  var isLocalUIUrl = function (url) {
    var host = getHostname(url);
    return (
      isWebUIHost(host) ||
      !!config.pluginHostMap[host] ||
      !!customHostPluginMap[host]
    );
  };
  config.isLocalUIUrl = isLocalUIUrl;
  exports.isWebUIHost = isWebUIHost;
  exports.getPluginNameByHost = function (host) {
    host = getHostname(host);
    if (isWebUIHost(host)) {
      return;
    }
    return config.pluginHostMap[host] || customHostPluginMap[host];
  };

  config.sockets = Math.max(parseInt(config.sockets, 10) || 0, 1);
  if (config.strict) {
    config.sockets = Math.max(config.sockets, 360);
  }
  var agentConfig = newAgentConf || {
    maxSockets: config.sockets,
    keepAlive: true,
    keepAliveMsecs: KEEP_ALIVE_MSECS,
    maxFreeSockets: 0
  };
  // node 11及以上版本缓存连接有问题，先禁掉
  disableAgent = !newAgentConf && !useAgent && (disableAgent || config.debug);
  config.httpAgent = disableAgent ? false : createAgent(agentConfig);
  config.httpsAgent = disableAgent ? false : createAgent(agentConfig, true);
  config.getSocksAgent = function (options) {
    var key = getCacheKey(options, true);
    var agent = socksAgents.get(key);
    if (agent) {
      return agent;
    }
    extend(options, agentConfig);
    options.proxyPort = parseInt(options.proxyPort, 10) || 1080;
    options.rejectUnauthorized = config.rejectUnauthorized;
    options.localDNS = false;
    options.auths = getAuths(options);
    agent = options.isHttps
      ? new socks.HttpsAgent(options)
      : new socks.HttpAgent(options);
    socksAgents.set(key, agent);
    agent.on('free', preventThrowOutError);
    return agent;
  };
  var baseDir = config.baseDir
    ? path.resolve(common.getHomePath(config.baseDir), config.dataDirname)
    : (config.whistleName ? path.join(ALL_WHISTLES_PATH, config.whistleName) : getDataDir(config.dataDirname));
  var customDirs = path.join(baseDir, 'custom_dirs');
  config.baseDir = baseDir;
  config.storage = config.storage && encodeURIComponent(config.storage);
  if (config.storage) {
    baseDir = path.join(customDirs, config.storage);
  }
  if (config.whistleName) {
    config.CUSTOM_PLUGIN_PATH = path.join(baseDir, 'custom_plugins');
    config.CUSTOM_CERTS_DIR = path.resolve(baseDir, 'custom_certs');
    config.SAVED_SESSIONS_PATH = path.resolve(baseDir, 'saved_sessions');
    fse.ensureDirSync(config.CUSTOM_PLUGIN_PATH);
    fse.ensureDirSync(config.CUSTOM_CERTS_DIR);
    fse.ensureDirSync(config.SAVED_SESSIONS_PATH);
  }
  fse.ensureDirSync(baseDir);
  config.baseDirHash = common.createHash(baseDir);
  if (config.password) {
    config.passwordHash = common.createHash(config.password);
  }
  config.rulesDir = path.join(baseDir, 'rules');
  config.valuesDir = path.join(baseDir, 'values');
  config.propertiesDir = path.join(baseDir, 'properties');
  if (config.storage && newConf.copy) {
    var copyDir =
      typeof newConf.copy == 'string' && encodeURIComponent(newConf.copy);
    if (copyDir !== config.storage) {
      var dataDir = copyDir ? path.join(customDirs, copyDir) : config.baseDir;
      var rulesDir = path.join(dataDir, 'rules');
      var valuesDir = path.join(dataDir, 'values');
      var propsDir = path.join(dataDir, 'properties');
      fse.ensureDirSync(rulesDir);
      fse.ensureDirSync(valuesDir);
      fse.ensureDirSync(propsDir);
      fse.copySync(rulesDir, config.rulesDir);
      fse.copySync(valuesDir, config.valuesDir);
      fse.copySync(propsDir, config.propertiesDir);
    }
  }
  var clientIdFile = path.join(config.baseDir, '.clientid');
  var clientId = readFileText(clientIdFile);
  if (!clientId) {
    clientId = [
      Date.now(),
      Math.random(),
      Math.random(),
      Math.random(),
      Math.random(),
      Math.random()
    ].join();
    fs.writeFileSync(clientIdFile, clientId);
  }
  if (config.whistleName) {
    clientId += '/' + config.whistleName;
  }
  config.clientId = clientId;
  config.clientIdNo = common.getStatSync(clientIdFile).ino + '';
  config.setModified = function (clientId, isRules) {
    if (isRules) {
      config.mrulesClientId = clientId || '';
      config.mrulesTime = Date.now();
    } else {
      config.mvaluesClientId = clientId || '';
      config.mvaluesTime = Date.now();
    }
  };
  return config;
};

```

### lib/handlers/file-proxy.js
```
var fs = require('fs');
var extend = require('extend');
var util = require('../util');
var mime = require('mime');
var qs = require('querystring');
var rulesMgr = require('../rules');
var protoMgr = require('../rules/protocols');
var pluginMgr = require('../plugins');

var CRLF_RE = /\r\n|\r|\n/g;
var RAW_FILE_RE = /rawfile/;
var HEADERS_SEP_RE = /(\r?\n(?:\r\n|\r|\n)|\r\r\n?)/;
var MAX_HEADERS_SIZE = 256 * 1024;
var TPL_RE = /(?:dust|tpl|jsonp):$/;
var VAR_RE = /\{\S+\}/;
var QUERY_VAR_RE = /\$?(?:\{\{([\w$-]+)\}\}|\{([\w$-]+)\})/g;
var UTF8_OPTIONS = { encoding: 'utf8' };
var ENABLE_OPTIONS = { enable: true };
var SLASH_RE = /\\+/g;
var QUOTE_RE = /"/g;
var JS_RE = /^js:/i;
var HTML_RE = /^html:/i;
var REPLACE_RE = /^replace:/i;
var BLANK_RE = /\s/g;
var HASH_RE = /#.*$/;
var CROSS_RE = /^x(s)?/;
var HTTP_RE = /^http:/;
var NOT_A_FILE_ERR = new Error('Not a file');
var INVALID_PATH = '(Path contains parent directory notation \'..\')';

function urlToStr(url) {
  return url.replace(SLASH_RE, '').replace(QUOTE_RE, '\\$&').replace(BLANK_RE, ' ');
}

function isRawFileProtocol(protocol) {
  return RAW_FILE_RE.test(protocol);
}

function readFiles(files, callback) {
  var file = files.shift();
  var execCallback = function (err, stat) {
    if (!err && stat && stat.isFile()) {
      callback(null, file, stat.size);
    } else if (file && file.originalKey) {
      pluginMgr.requestBin(file, function(buffer, err, res) {
        file = file.originalKey;
        callback(err, file, buffer ? buffer.length : 0, buffer, res);
      });
    } else if (files.length) {
      readFiles(files, callback);
    } else {
      callback(err || NOT_A_FILE_ERR, file == null ? INVALID_PATH : file);
    }
  };

  !file || typeof file != 'string'
    ? execCallback()
    : util.getStat(file, execCallback);
}

function parseRes(str, rawHeaderNames, fromValue) {
  if (!str) {
    return {
      statusCode: 200,
      headers: {}
    };
  }
  var headers = str.split(CRLF_RE);
  var statusLine = headers.shift().trim().split(/\s+/g);
  headers = util.parseHeaders(headers, rawHeaderNames);
  if (fromValue) {
    delete headers['content-encoding'];
  }
  return {
    statusCode: statusLine[1] || 200,
    headers: headers
  };
}

function addLength(reader, length) {
  reader.headers['content-length'] = length;
}

function getRawResByValue(body) {
  var headers;
  if (HEADERS_SEP_RE.test(body)) {
    var crlfStr = RegExp.$1;
    var index = body.indexOf(crlfStr);
    headers = body.substring(0, index);
    body = body.substring(index + crlfStr.length);
  }
  var rawHeaderNames = {};
  var reader = parseRes(headers, rawHeaderNames, true);
  reader.rawHeaderNames = rawHeaderNames;
  reader.body = body;
  addLength(reader, body ? Buffer.byteLength(body) : 0);
  return reader;
}

function getRawResByPath(protocol, path, req, size, callback, body) {
  var isRawFile = isRawFileProtocol(protocol);
  var range = isRawFile ? undefined : util.parseRange(req, req.localFileSize);
  var reader;
  if (body == null) {
    reader = fs.createReadStream(path, range);
  } else {
    reader = util.createTransform();
    if (!body || !range) {
      reader.end(body);
    } else {
      reader.end(body.slice(range.start, range.end + 1));
    }
  }
  var rawHeaderNames = (reader.rawHeaderNames = rawHeaderNames);
  if (isRawFile) {
    var buffer;
    var response = function (err, crlf) {
      reader.removeAllListeners();
      reader.on('error', util.noop);
      var stream = reader;
      reader = util.createTransform();
      if (err) {
        var stack = util.getErrorStack(err);
        reader.statusCode = 500;
        reader.push(stack);
        reader.push(null);
        size = Buffer.byteLength(stack);
      } else {
        if (crlf) {
          crlf = util.toBuffer(crlf);
          var index = buffer.indexOf(crlf);
          if (index != -1) {
            extend(
              reader,
              parseRes(buffer.slice(0, index) + '', rawHeaderNames)
            );
            var headerLen = index + crlf.length;
            size -= headerLen;
            buffer = buffer.slice(headerLen);
          }
        }
        buffer && reader.push(buffer);
        stream.on('error', function (err) {
          reader.emit('error', err);
        });
        stream.pipe(reader);
      }
      callback(reader, null, size);
    };

    reader.on('data', function (data) {
      buffer = buffer ? Buffer.concat([buffer, data]) : data;
      if (HEADERS_SEP_RE.test(buffer + '')) {
        response(null, RegExp.$1);
      } else if (buffer.length > MAX_HEADERS_SIZE) {
        response();
      }
    });
    reader.on('error', response);
    reader.on('end', response);
  } else {
    callback(reader, range, size);
  }
}

function addRangeHeaders(res, range, size) {
  if (!range) {
    return;
  }
  var headers = res.headers;
  headers['content-range'] =
    'bytes ' + (range.start + '-' + range.end) + '/' + size;
  headers['accept-ranges'] = 'bytes';
  headers['content-length'] = range.end - range.start + 1;
  res.statusCode = 206;
}

function isAutoCors(req, rule) {
  if (rule.lineProps.disableAutoCors || rule.lineProps.disabledAutoCors) {
    return false;
  }
  return !req.disable.autoCors && req.headers.origin;
}

function sendResponse(rule, res, reader, req) {
  if (isAutoCors(req, rule)) {
    util.setResCors(reader, ENABLE_OPTIONS, req);
  }
  rule.isLoc = 1;
  res.response(reader);
}

function handleLocHref(req, rule, handleRes) {
  var body = util.getMatcherValue(rule) || '';
  var isJs = JS_RE.test(body);
  var isHtml = HTML_RE.test(body);
  var isReplace = REPLACE_RE.test(body);
  if (isJs) {
    body = body.substring(3);
  } else if (isHtml) {
    body = body.substring(5);
  } else if (isReplace) {
    body = body.substring(8);
  } else {
    isJs = req.headers['sec-fetch-dest'] === 'script';
  }
  var type = isJs ? 'application/javascript' : 'text/html';
  if (body) {
    body = urlToStr(body);
    if (util.compareUrl(body.replace(HASH_RE, ''), req.fullUrl)) {
      return false;
    }
    if (isReplace) {
      body = 'window.location.replace("' + body + '");';
    } else {
      body = 'window.location.href = "' + body + '";';
    }
    if (!isJs) {
      body = '<script>' + body + '</script>';
    }
  }

  handleRes({
    statusCode: 200,
    body: body,
    headers: {
      'content-type': type + '; charset=utf-8'
    }
  });
  return true;
}

module.exports = function (req, res, next) {
  var options = req.options;
  var config = this.config;
  var protocol = options && options.protocol;
  if (!protoMgr.isFileProxy(protocol)) {
    return next();
  }
  var rules = req.rules;
  var rule = rules.rule;
  if (protoMgr.isLocHref(protocol)) {
    if (handleLocHref(req, rule, render)) {
      return;
    }
    req.isWebProtocol = true;
    req.options = util.parseUrl(req.fullUrl);
    return next();
  }
  if (isAutoCors(req, rule) && req.method === 'OPTIONS') {
    var optsRes = util.wrapResponse({ statusCode: 200  }, rule.matcher);
    return sendResponse(rule, res, optsRes, req);
  }
  var isTpl = TPL_RE.test(protocol);
  var defaultType = mime.lookup(
    util.getPureUrl(req.fullUrl),
    'text/html'
  );
  delete rules.proxy;
  delete rules.host;
  if (rule.value) {
    var body = util.removeProtocol(rule.value, true);
    var isRawFile = isRawFileProtocol(protocol);
    var reader = isRawFile
      ? getRawResByValue(body)
      : {
        statusCode: 200,
        body: body,
        headers: {
          'content-type':
              (rule.key ? mime.lookup(rule.key, defaultType) : defaultType) +
              '; charset=utf-8'
        }
      };

    if (isTpl) {
      reader.realUrl = rule.matcher;
      render(reader);
    } else {
      if (!isRawFile) {
        var size = Buffer.byteLength(body);
        var range = util.parseRange(req, size);
        if (range) {
          body = Buffer.from(body);
          reader.body = body.slice(range.start, range.end + 1);
          addRangeHeaders(reader, range, size);
        } else {
          addLength(reader, size);
        }
      }
      reader = util.wrapResponse(reader, rule.matcher);
      sendResponse(rule, res, reader, req);
    }
    return;
  }

  readFiles(util.getRuleFiles(rule, req), function (err, path, size, buffer, svrRes) {
    if (err) {
      if (CROSS_RE.test(protocol)) {
        var fullUrl = RegExp.$1 ? req.fullUrl.replace(HTTP_RE, 'https:') : req.fullUrl;
        extend(options, util.parseUrl(fullUrl));
        return next();
      }
      var is502 = err.code > 0 && err.code != 404;
      var notFound = util.wrapResponse({
        statusCode: is502 ? 502 : 404,
        body: is502 ? util.encodeHtml(err.message) : 'Not found ' + (rule.key ? 'key' : 'file') +
          ' <strong>' + util.encodeHtml(rule.key || path) + '</strong>',
        headers: { 'content-type': 'text/html; charset=utf-8' }
      }, rule.matcher);
      return sendResponse(rule, res, notFound, req);
    }
    var type = buffer != null && svrRes && svrRes.headers && svrRes.headers['x-whistle-response-type'];
    type = type || mime.lookup(rule._suffix || path, defaultType);
    var headers = {
      server: config.appName,
      'content-type': type + (util.isText(type) ? '; charset=utf-8' : '')
    };

    if (isTpl) {
      var reader = {
        statusCode: 200,
        realUrl: path,
        headers: headers
      };
      if (buffer != null) {
        reader.body = buffer + '';
        render(reader);
      } else {
        fs.readFile(path, UTF8_OPTIONS, function (err, data) {
          if (err) {
            return util.emitError(req, err);
          }
          reader.body = data;
          render(reader);
        });
      }
    } else {
      req.localFileSize = size;
      getRawResByPath(
        protocol,
        path,
        req,
        size,
        function (reader, range, realSize) {
          reader.realUrl = path;
          reader.statusCode = reader.statusCode || 200;
          reader.headers = reader.headers || headers;
          addRangeHeaders(reader, range, size);
          !range && addLength(reader, realSize);
          sendResponse(rule, res, reader, req);
        },
        buffer
      );
    }
  });

  function render(reader) {
    if (reader.body) {
      if (VAR_RE.test(reader.body)) {
        var data = util.getQueryString(req.fullUrl);
        data = data && qs.parse(data);
        if (data) {
          reader.body = reader.body.replace(QUERY_VAR_RE, function (all, matched1, matched2) {
            if (all[0] === '$') {
              return all;
            }
            var value = data[matched1 || matched2];
            return value === undefined ? all : util.getQueryValue(value);
          }
          );
        }
        reader.body = rulesMgr.resolveTplVar(reader.body, req);
      }
      addLength(reader, Buffer.byteLength(reader.body));
    } else {
      addLength(reader, 0);
    }
    reader = util.wrapResponse(reader, reader.realUrl);
    sendResponse(rule, res, reader, req);
  }
};

```

### lib/https/ca.js
```
var forge = require('node-forge');
var fs = require('fs');
var net = require('net');
var path = require('path');
var crypto = require('crypto');
var LRU = require('lru-cache');
var hagent = require('hagent');
var extend = require('extend');
var h2 = require('./h2');
var createSecureContext =
  require('tls').createSecureContext || crypto.createCredentials;
var util = require('../util');
var config = require('../config');
var common = require('../util/common');
var rulesUtil = require('../rules/util');

var pki = forge.pki;
var HTTPS_DIR = mkdir(path.join(config.getDataDir(), 'certs'));
var ROOT_NEW_KEY_FILE = path.join(HTTPS_DIR, 'root_new.key');
var ROOT_NEW_CRT_FILE = path.join(HTTPS_DIR, 'root_new.crt');
var CUSTOM_CERTS_DIR = config.disableCustomCerts
  ? null
  : config.CUSTOM_CERTS_DIR;
var useNewKey =
  fs.existsSync(ROOT_NEW_KEY_FILE) && fs.existsSync(ROOT_NEW_CRT_FILE);
var ROOT_KEY_FILE = useNewKey
  ? ROOT_NEW_KEY_FILE
  : path.join(HTTPS_DIR, 'root.key');
var ROOT_CRT_FILE = useNewKey
  ? ROOT_NEW_CRT_FILE
  : path.join(HTTPS_DIR, 'root.crt');
var customCertDir = config.certDir;
var customPairs = {};
var customCertsInfo = {};
var customCertsFiles = {};
var allCustomCerts = {};
var customCertCount = 0;
var cachePairs = new LRU({ max: 5120 });
var certsCache = new LRU({ max: 256 });
var remoteCerts = new LRU({ max: 1280 });
var KEY_SIZE = 2048;
var ILEGAL_CHAR_RE = /[^a-z\d-]/i;
// https://cloud.tencent.com/developer/ask/sof/58155
var RANDOM_SERIAL = '/' + Date.now() + '/' + process.pid + '/' + Math.floor(Math.random() * 100);
var ONE_DAY = 1000 * 60 * 60 * 24;
var MIN_DATE = ONE_DAY * 20;
var CLEAR_CERTS_INTERVAL = ONE_DAY * 20;
var MAX_INNTERFAL = 16;
var PORT_RE = /:\d*$/;
var pureCertFiles = {};
var customRoot;
var ROOT_KEY, ROOT_CRT;
var rootKey, rootCrt;
var ILLEGAL_PATH_RE = /[/\\]/;

exports.remoteCerts = remoteCerts;
exports.createSecureContext = createSecureContext;
exports.CUSTOM_CERTS_DIR = CUSTOM_CERTS_DIR;

function notRootCa(name) {
  return name !== 'root';
}

function checkFilename(name) {
  return name && !ILLEGAL_PATH_RE.test(name) && notRootCa(name);
}

function resetAllCerts() {
  cachePairs.reset();
  certsCache.reset();
}

// When delay is larger than 2147483647 or less than 1, the delay will be set to 1. Non-integer delays are truncated to an integer.
var intervalCount = 0;
var timer = setInterval(function () {
  if (++intervalCount >= MAX_INNTERFAL) {
    intervalCount = 0;
    resetAllCerts();
  }
}, CLEAR_CERTS_INTERVAL);

if (timer && typeof timer.unref === 'function') {
  timer.unref();
}

if (!useNewKey && !checkCertificate()) {
  try {
    fs.unlinkSync(ROOT_KEY_FILE);
    fs.unlinkSync(ROOT_CRT_FILE);
  } catch (e) {}
}

function mkdir(path) {
  !fs.existsSync(path) && fs.mkdirSync(path);
  return path;
}

function isExpiredCert(crt) {
  var now = Date.now();
  try {
    var startDate = new Date(crt.notBefore);
    var endDate = new Date(crt.notAfter);
    return startDate.getTime() >= now || endDate.getTime() <= now;
  } catch (e) {}
}

function checkCertificate() {
  try {
    var crt = pki.certificateFromPem(fs.readFileSync(ROOT_CRT_FILE));
    if (crt.publicKey.n.toString(2).length < KEY_SIZE || isExpiredCert(crt.validity)) {
      return false;
    }
    return /^whistle\.\d+$/.test(getCommonName(crt));
  } catch (e) {}
  return true;
}

function getCommonName(crt) {
  var attrs = crt.issuer && crt.issuer.attributes;
  if (Array.isArray(attrs)) {
    for (var i = 0, len = attrs.length; i < len; i++) {
      var attr = attrs[i];
      if (attr && attr.name === 'commonName') {
        return attr.value;
      }
    }
  }
  return '';
}

function getDomain(hostname) {
  if (getCacheCert(hostname) || net.isIP(hostname)) {
    return hostname;
  }
  var list = hostname.split('.');
  var prefix = list[0];
  list[0] = '*';
  var wildDomain = list.join('.');
  if (getCacheCert(wildDomain)) {
    return wildDomain;
  }
  var len = list.length;
  if (len < 3) {
    return hostname;
  }
  if (
    len > 3 ||
    ILEGAL_CHAR_RE.test(prefix) ||
    list[1].length > 3 ||
    list[2] === 'com' ||
    list[2] === 'net' ||
    list[1] === 'url'
  ) {
    // For tencent cdn
    return wildDomain;
  }

  return hostname;
}

exports.getDomain = getDomain;
exports.existsCustomCert = function (hostname) {
  if (!customCertCount) {
    return false;
  }
  hostname = hostname.replace(PORT_RE, '');
  var cert = customPairs[hostname];
  if (cert) {
    return true;
  }
  hostname = hostname.split('.');
  hostname[0] = '*';
  return customPairs[hostname.join('.')];
};

exports.hasCustomCerts = function () {
  return customCertCount;
};

function getCacheCert(hostname) {
  return (
    customPairs[hostname] ||
    cachePairs.get(hostname) ||
    certsCache.get(hostname)
  );
}

function createSelfCert(hostname) {
  // https://blog.csdn.net/OnlyLove_/article/details/125815813
  var serialNumber =
    crypto
      .createHash('sha1')
      .update(hostname + RANDOM_SERIAL, 'binary')
      .digest('hex');
  serialNumber = (parseInt(serialNumber[0], 16) % 8) + serialNumber.substring(1);
  var cert = createCert(
    pki.setRsaPublicKey(ROOT_KEY.n, ROOT_KEY.e),
    serialNumber,
    true
  );
  cert.setSubject([
    {
      name: 'commonName',
      value: hostname
    }
  ]);
  cert.setIssuer(ROOT_CRT.subject.attributes);
  // Get SKI from ROOT_CRT for authorityKeyIdentifier extension
  var rootSkiBytes;
  try {
    rootSkiBytes = ROOT_CRT.generateSubjectKeyIdentifier().getBytes();
  } catch(ex) {
    rootSkiBytes = null;
  }
  cert.setExtensions([
    {
      name: 'basicConstraints',
      cA: false
    },
    {
      name: 'keyUsage',
      digitalSignature: true,
      keyEncipherment: true
    },
    {
      name: 'extKeyUsage',
      serverAuth: true,
      clientAuth: true
    },
    {
      name: 'subjectAltName',
      altNames: [
        net.isIP(hostname)
          ? {
            type: 7,
            ip: hostname
          }
          : {
            type: 2,
            value: hostname
          }
      ]
    },
    {
      name: 'authorityKeyIdentifier',
      keyIdentifier: rootSkiBytes
    }
  ]);
  cert.sign(ROOT_KEY, forge.md.sha256.create());
  return {
    key: pki.privateKeyToPem(ROOT_KEY),
    cert: pki.certificateToPem(cert)
  };
}

exports.createCertificate = function (hostname) {
  hostname = getDomain(hostname);
  var cert = cachePairs.get(hostname); // 确保使用自己生成的证书，防止把用户证书下载出去
  if (!cert) {
    cert = createSelfCert(hostname);
    certsCache.set(hostname, cert);
  }
  return cert;
};

function parseCert(cert) {
  var pem = pki.certificateFromPem(cert.cert);
  var altNames = getAltNames(pem.extensions);
  if (!altNames || !altNames.length) {
    return;
  }
  return { cert: cert, altNames: altNames, validity: pem.validity };
}

function parseAllCustomCerts() {
  var pairs = {};
  var certsInfo = {};
  var certFiles = {};
  var keys = Object.keys(allCustomCerts).sort(function (key1, key2) {
    return util.compare(
      allCustomCerts[key1].cert.mtime,
      allCustomCerts[key2].cert.mtime
    );
  });
  keys.forEach(function (filename) {
    var info = allCustomCerts[filename];
    var cert = info.cert;
    var mtime = cert.mtime;
    var validity = info.validity;
    var altNames = info.altNames;
    var dnsName = [];
    var disabled = (notRootCa(filename) && rulesUtil.isDisabledCertFile(filename)) || undefined;
    altNames.forEach(function (item) {
      if ((item.type === 2 || item.type === 7) && !pairs[item.value]) {
        if (!disabled) {
          var preCert = customPairs[item.value];
          if (preCert && preCert.key === cert.key && preCert.cert === cert.cert) {
            if (preCert.mtime < mtime) {
              preCert.mtime = mtime;
            }
            pairs[item.value] = preCert;
          } else {
            pairs[item.value] = cert;
          }
        }
        dnsName.push(item.value);
        certsInfo[item.value] = extend(
          { filename: filename, type: cert.type, mtime: mtime, domain: item.value, disabled: disabled },
          validity
        );
      }
    });
    if (dnsName.length) {
      certFiles[filename] = extend(
        { mtime: mtime, type: cert.type, dir: cert.dir, dnsName: dnsName.join(', '), disabled: disabled },
        validity
      );
    }
  });
  certFiles.root = certFiles.root || customCertsFiles.root;
  customPairs = pairs;
  customCertsInfo = certsInfo;
  customCertsFiles = certFiles;
  customCertCount = Object.keys(customPairs).length;
  checkExpired();
}

function loadCustomCerts(certDir, isCustom) {
  if (!certDir) {
    return;
  }
  var certs = {};
  pureCertFiles = {};
  try {
    fs.readdirSync(certDir).forEach(function (name) {
      if (!/^(.+)\.(crt|cer|pem|key)$/.test(name)) {
        return;
      }
      var filename = RegExp.$1;
      var type = RegExp.$2;
      var cert = (certs[filename] = certs[filename] || {});
      var isCert = type !== 'key';
      try {
        var filePath = path.join(certDir, name);
        var mtime = common.getStatSync(filePath).mtime.getTime();
        if (isCert && cert.type && (cert.mtime == null || cert.mtime >= mtime)) {
          return;
        }
        cert.dir = certDir;
        if (isCert) {
          cert.mtime = mtime;
          cert.type = type;
          type = 'cert';
        }
        cert[type] = fs.readFileSync(filePath, { encoding: 'utf8' });
      } catch (e) {}
    });
  } catch (e) {}
  var rootCA = certs.root;
  delete certs.root;
  if (rootCA && rootCA.key && rootCA.cert && !customRoot) {
    customRoot = rootCA;
    ROOT_KEY_FILE = path.join(certDir, 'root.key');
    ROOT_CRT_FILE = path.join(certDir, 'root.' + rootCA.type);
  }
  Object.keys(certs).filter(function (key) {
    var cert = certs[key];
    if (cert && cert.mtime != null && cert.key && cert.cert) {
      pureCertFiles[key] = {
        type: cert.type,
        name: key,
        key: cert.key,
        cert: cert.cert
      };
      try {
        cert = parseCert(cert);
        if (cert) {
          allCustomCerts[isCustom ? 'z/' + key : key] = cert;
        }
      } catch (e) {}
    }
  });
}

function getAltNames(exts) {
  for (var i = 0, len = exts.length; i < len; i++) {
    var item = exts[i];
    if (item.name === 'subjectAltName') {
      return Array.isArray(item.altNames) && item.altNames.filter(util.noop);
    }
  }
}

function resetRootCA() {
  var cert = createCACert();
  var key = pki.privateKeyToPem(cert.key).toString();
  var crt = pki.certificateToPem(cert.cert).toString();
  fs.writeFileSync(ROOT_KEY_FILE, key);
  fs.writeFileSync(ROOT_CRT_FILE, crt);
  rootKey = key;
  rootCrt = crt;
  ROOT_KEY = cert.key;
  ROOT_CRT = cert.cert;
}

function createRootCASafe() {
  if (isExpiredCert(ROOT_CRT.validity)) {
    try {
      resetRootCA();
      resetAllCerts();
    } catch (e) {}
  }
}

function createRootCA() {
  allCustomCerts = {};
  loadCustomCerts(customCertDir, true);
  loadCustomCerts(CUSTOM_CERTS_DIR);
  parseAllCustomCerts();
  if (ROOT_KEY && ROOT_CRT) {
    return;
  }
  try {
    ROOT_KEY = fs.readFileSync(ROOT_KEY_FILE);
    ROOT_CRT = fs.readFileSync(ROOT_CRT_FILE);
    rootKey = ROOT_KEY.toString();
    rootCrt = ROOT_CRT.toString();
  } catch (e) {
    ROOT_KEY = ROOT_CRT = null;
  }

  if (ROOT_KEY && ROOT_CRT && ROOT_KEY.length && ROOT_CRT.length) {
    ROOT_KEY = pki.privateKeyFromPem(ROOT_KEY);
    ROOT_CRT = pki.certificateFromPem(ROOT_CRT);
    if (customRoot) {
      customCertsFiles.root = extend(
        {
          mtime: customRoot.mtime,
          dir: customRoot.dir,
          type: customRoot.type,
          dnsName: ''
        },
        ROOT_CRT.validity
      );
    }
    try {
      var altNames = getAltNames(ROOT_CRT.extensions);
      var dnsName = [];
      altNames.forEach(function (item) {
        if (
          (item.type === 2 || item.type === 7) &&
          dnsName.indexOf(item.value) === -1
        ) {
          dnsName.push(item.value);
        }
      });
      customCertsFiles.root.dnsName = dnsName.join(', ');
    } catch (e) {}
  } else {
    resetRootCA();
  }
}

function createCACert(opts) {
  opts = opts || {};
  var keys = pki.rsa.generateKeyPair(KEY_SIZE);
  var cert = createCert(keys.publicKey);
  var now = Date.now() + common.padLeft(Math.floor(Math.random() * 1000), 3);
  var attrs = [
    {
      name: 'commonName',
      value: opts.commonname || opts.commonName || 'whistle.' + now
    },
    {
      name: 'countryName',
      value: opts.countryname || opts.countryName || 'CN'
    },
    {
      shortName: 'ST',
      value: opts.st || opts.ST || 'ZJ'
    },
    {
      name: 'localityName',
      value: opts.localityname || opts.localityName || 'HZ'
    },
    {
      name: 'organizationName',
      value: opts.organizationname || opts.organizationName || now + '.wproxy.org'
    },
    {
      shortName: 'OU',
      value: opts.ou || opts.OU || 'wproxy.org'
    }
  ];

  cert.setSubject(attrs);
  cert.setIssuer(attrs);
  cert.setExtensions([
    {
      name: 'basicConstraints',
      cA: true
    },
    {
      name: 'keyUsage',
      keyCertSign: true,
      digitalSignature: true,
      nonRepudiation: true,
      keyEncipherment: true,
      dataEncipherment: true
    },
    {
      name: 'extKeyUsage',
      serverAuth: true,
      clientAuth: true,
      codeSigning: true,
      emailProtection: true,
      timeStamping: true
    },
    {
      name: 'nsCertType',
      client: true,
      server: true,
      email: true,
      objsign: true,
      sslCA: true,
      emailCA: true,
      objCA: true
    }
  ]);

  cert.sign(keys.privateKey, forge.md.sha256.create());

  return {
    key: keys.privateKey,
    cert: cert
  };
}

exports.createRootCA = function(opts) {
  var cert = createCACert(opts);
  cert.key = pki.privateKeyToPem(cert.key).toString();
  cert.cert = pki.certificateToPem(cert.cert).toString();
  return cert;
};

function createCert(publicKey, serialNumber, isShortPeriod) {
  var cert = pki.createCertificate();
  cert.publicKey = publicKey;
  cert.serialNumber = serialNumber || '01';
  var curDate = new Date();
  var curYear = curDate.getFullYear();
  if (isShortPeriod) {
    cert.validity.notBefore = new Date(curDate.getTime() - MIN_DATE);
  } else {
    cert.validity.notBefore = new Date();
    cert.validity.notBefore.setFullYear(curYear - 1);
  }
  // https://www.ssls.com/blog/apples-new-ssl-lifetime-limitation-and-what-it-means-for-you/
  // https://chromium.googlesource.com/chromium/src/+/refs/heads/master/net/cert/cert_verify_proc.cc#900
  cert.validity.notAfter = new Date();
  cert.validity.notAfter.setFullYear(curYear + (isShortPeriod ? 1 : 10));
  return cert;
}

function getRootCAFile() {
  createRootCASafe();
  return ROOT_CRT_FILE;
}

createRootCA(); // 启动生成ca

function getOrCreateCert(servername) {
  var requestCert = servername[0] === ':';
  if (requestCert) {
    servername = servername.substring(1);
  }
  var cert = remoteCerts.get(servername);
  if (!cert) {
    servername = getDomain(servername);
    cert = getCacheCert(servername);
    if (!cert) {
      cert = createSelfCert(servername);
      cachePairs.set(servername, cert);
    }
  }
  return requestCert
    ? extend(
      {
        requestCert: true,
        rejectUnauthorized: false
      },
        cert
      )
    : cert;
}

hagent.serverAgent.createCertificate = getOrCreateCert;
var getHttp2Server = hagent.create(h2.getHttpServer, 42900);
var getHttpsServer = hagent.create(h2.getServer, 43900);
var cbs = {};
var ports = {};
var TIMEOUT = 6000;

var SNICallback = function (servername, cb) {
  var options = getOrCreateCert(servername);
  if (!options._ctx) {
    try {
      options._ctx = createSecureContext(options);
    } catch (e) {}
  }
  cb(null, options._ctx);
};

exports.getRootCA = function () {
  createRootCASafe();
  return {
    key: rootKey,
    cert: rootCrt
  };
};

exports.getCustomCertsInfo = function () {
  return customCertsInfo;
};
exports.getCustomCertsFiles = function () {
  return customCertsFiles;
};

exports.getRootCAFile = getRootCAFile;
exports.serverAgent = hagent.serverAgent;

exports.SNICallback = SNICallback;

function addCallback(name, callback) {
  var cbList = cbs[name];
  if (!cbList) {
    cbList = [];
    cbs[name] = cbList;
  }
  cbList.push(callback);
  return cbList;
}

function createServer(name, cbList, listener, options) {
  var removeServer = function () {
    ports[name] = null;
    try {
      this.close();
    } catch (e) {} //重复关闭会导致异常
  };
  ports[name] = false; // pending
  var getServer = options ? getHttpsServer : getHttp2Server;
  getServer(options, listener, function (server, port) {
    server.on('error', removeServer);
    var timeout = setTimeout(removeServer, TIMEOUT);
    var clearup = function () {
      clearTimeout(timeout);
    };
    if (options) {
      server.once('tlsClientError', clearup);
      server.once('secureConnection', clearup);
    } else {
      server.once('connection', clearup);
    }
    ports[name] = port;
    cbList.forEach(function (cb) {
      cb(port);
    });
    cbs[name] = [];
  });
}

exports.getHttp2Server = function (listener, callback) {
  var name = 'httpH2';
  var curPort = ports[name];
  if (curPort) {
    return callback(curPort);
  }
  var cbList = addCallback(name, callback);
  if (curPort === false) {
    return;
  }
  createServer(name, cbList, listener);
};

exports.getSNIServer = function (listener, callback, disableH2, requestCert) {
  var enableH2 = config.enableH2 && !disableH2;
  var name = (enableH2 ? 'h2Sni' : 'sni') + (requestCert ? 'WithCert' : '');
  var curPort = ports[name];
  if (curPort) {
    return callback(curPort);
  }
  var cbList = addCallback(name, callback);
  if (curPort === false) {
    return;
  }
  var options = { SNICallback: SNICallback };
  options.allowHTTP1 = enableH2; // 是否启用http2
  if (requestCert) {
    options = extend(
      {
        requestCert: true,
        rejectUnauthorized: false
      },
      options
    );
  }
  createServer(name, cbList, listener, options);
};

var checkTimer;

function checkExpired() {
  clearTimeout(checkTimer);
  var files = Object.keys(customCertsFiles);
  exports.hasInvalidCerts = false;
  for (var i = 0, len = files.length; i < len; i++) {
    var file = customCertsFiles[files[i]];
    if (file && isExpiredCert(file)) {
      exports.hasInvalidCerts = true;
      return;
    }
  }
  checkTimer = setTimeout(checkExpired, 600000);
}

function removeFile(filename) {
  fs.unlink(filename, function (err) {
    err && fs.unlink(filename, util.noop);
  });
}

function writeFile(filename, ctn, callback) {
  fs.writeFile(filename, ctn, function (err) {
    if (!err) {
      return callback();
    }
    fs.writeFile(filename, ctn, callback);
  });
}
// 异步重试，出错重试即可
function removeCertFile(filename, type) {
  removeFile(path.join(CUSTOM_CERTS_DIR, filename + '.key'));
  removeFile(path.join(CUSTOM_CERTS_DIR, filename + type));
  delete pureCertFiles[filename];
}
// 异步写入，出错重试即可
function writeCertFile(filename, type, cert, mtime) {
  var keyFile = path.join(CUSTOM_CERTS_DIR, filename + '.key');
  var certFile = path.join(CUSTOM_CERTS_DIR, filename + '.' + (type || 'crt'));
  writeFile(keyFile, cert.key, function () {
    fs.utimes && fs.utimes(keyFile, mtime, mtime, util.noop);
  });
  writeFile(certFile, cert.cert, function () {
    fs.utimes && fs.utimes(certFile, mtime, mtime, util.noop);
  });
}

function getCertType(type) {
  if (type !== 'cer' && type !== 'pem') {
    return 'crt';
  }
  return type;
}

exports.removeCert = function (opts) {
  if (!CUSTOM_CERTS_DIR) {
    return;
  }
  var filename = opts.filename;
  var type = getCertType(opts.type);
  if (checkFilename(filename) && allCustomCerts[filename]) {
    removeCertFile(filename, type);
    delete allCustomCerts[filename];
    parseAllCustomCerts();
  }
};

exports.setActiveCert = function (opts) {
  if (!CUSTOM_CERTS_DIR) {
    return;
  }
  var filename = opts.filename;
  if (notRootCa(filename) && allCustomCerts[filename]) {
    rulesUtil.setDisabledCertFile(filename, opts.disabled);
    parseAllCustomCerts();
  }
};

exports.uploadCerts = function (certs) {
  if (!CUSTOM_CERTS_DIR) {
    return;
  }
  var now = Date.now();
  var hasChanged;
  var index = 0;
  Object.keys(certs).forEach(function (filename) {
    if (!checkFilename(filename) || filename.length > 128) {
      return;
    }
    var cert = certs[filename];
    if (!cert) {
      return;
    }
    var keyStr, certStr, type;
    if (Array.isArray(cert)) {
      keyStr = cert[0];
      certStr = cert[1];
      type = getCertType(cert[2]);
    } else {
      keyStr = cert.key;
      certStr = cert.cert;
      type = getCertType(cert.type);
    }
    if (util.isString(keyStr) && util.isString(certStr)) {
      var mtime = now + index * 1000;
      ++index;
      try {
        cert = parseCert({
          key: keyStr,
          type: type,
          cert: certStr,
          mtime: mtime
        });
        if (cert) {
          writeCertFile(filename, type, cert.cert, new Date(mtime));
          pureCertFiles[filename] = {
            type: type,
            name: filename,
            key: keyStr,
            cert: certStr
          };
          allCustomCerts[filename] = cert;
          hasChanged = true;
        }
      } catch (e) {}
    }
  });
  hasChanged && parseAllCustomCerts();
};

exports.getPureCertFiles = function () {
  return pureCertFiles;
};

```

### lib/https/index.js
```
var net = require('net');
var tls = require('tls');
var http = require('http');
var parseUrl = require('../util/parse-url-safe');
var socks = require('sockx');
var crypto = require('crypto');
var EventEmitter = require('events').EventEmitter;
var LRU = require('lru-cache');
var checkSNI = require('sni');
var util = require('../util');
var extend = require('extend');
var config = require('../config');
var rules = require('../rules');
var pluginMgr = require('../plugins');
var socketMgr = require('../socket-mgr');
var hparser = require('hparser');
var properties = require('../rules/util').properties;
var ca = require('./ca');
var loadCert = require('./load-cert');
var h2Consts = config.enableH2 ? require('http2').constants : {};

var STATUS_CODES = http.STATUS_CODES || {};
var getRawHeaders = hparser.getRawHeaders;
var getRawHeaderNames = hparser.getRawHeaderNames;
var formatHeaders = hparser.formatHeaders;
var parseReq = hparser.parse;
var getDomain = ca.getDomain;
var serverAgent = ca.serverAgent;
var getSNIServer = ca.getSNIServer;
var getHttp2Server = ca.getHttp2Server;
var LOCALHOST = '127.0.0.1';
var tunnelTmplData = new LRU({ max: 3000, maxAge: 30000 });
var uaCache = new LRU({ max: 1024 });
var TIMEOUT = 12000;
var CONN_TIMEOUT = 60000;
var X_RE = /^x/;
var PROTO_SEP_RE = /,\s*/;
var HTTP_PROTO_RE = /^(ws|http)s?:\/\//;
var clientIpKey = config.CLIENT_IP_HEADER;
var proxy, server;

function handleWebsocket(socket, clientIp, clientPort) {
  var wss = socket.isHttps;
  clientIp = util.removeIPV6Prefix(
    clientIp || socket._remoteAddr || socket.remoteAddress
  );
  socket.clientIp = clientIp;
  socket.method = 'GET';
  socket.reqId = util.getReqId();
  socket.clientPort = clientPort || socket._remotePort || socket.remotePort;
  rules.initHeaderRules(socket);
  pluginMgr.resolvePipePlugin(socket, function () {
    socket.rules = rules.initRules(socket);
    rules.resolveRulesFile(socket, function () {
      resolveWebsocket(socket, wss);
    });
  });
}

function setCaptureUA(ua) {
  if (ua && typeof ua === 'string' && ua.length < 1024) {
    uaCache.set(ua, 1);
  }
}

function isCaptureUA(ua) {
  return ua && uaCache.get(ua);
}

function getTransProto(str) {
  if (!str || typeof str !== 'string') {
    return;
  }
  if (str.indexOf(',') === -1) {
    return str;
  }
  return str.trim().split(PROTO_SEP_RE)[0];
}

function handleFrames(socket, reqSocket, headers) {
  if (socket.enable.websocket || util.isWebSocket(headers)) {
    socketMgr.handleUpgrade(socket, reqSocket);
  } else {
    socketMgr.handleConnect(socket, reqSocket, true);
  }
}

function resolveWebsocket(socket, wss) {
  var headers = socket.headers;
  var reqEmitter = new EventEmitter();
  var fullUrl = socket.fullUrl;
  var _rules = socket.rules;
  var clientIp = socket.clientIp;
  var filter = socket._filters;
  var now = Date.now();
  var reqData = {
    ip: clientIp,
    port: socket.clientPort,
    method: 'GET',
    httpVersion: socket.httpVersion || '1.1',
    headers: headers,
    rawHeaderNames: socket.rawHeaderNames
  };
  var resData = {};
  var data = {
    _clientId: socket._clientId,
    id: socket.reqId,
    fc: socket.fromComposer ? 1 : undefined,
    url: fullUrl,
    startTime: now,
    sniPlugin: socket.sniPlugin,
    fwdHost: socket._fwdHost,
    rules: _rules,
    req: reqData,
    res: resData,
    pipe: socket._pipeRule,
    rulesHeaders: socket.rulesHeaders
  };

  var reqSocket,
    options,
    isXProxy,
    isInternalProxy;
  var origProto, done, proxyUrl, clientKey, clientCert, isPfx, curStatus;
  var timeout = setTimeout(function () {
    destroy(util.TIMEOUT_ERR);
  }, CONN_TIMEOUT);
  var handleResponse = function () {
    var svrRes = util.getStatusCodeFromRule(_rules);
    if (!svrRes) {
      return;
    }
    var statusCode = svrRes.statusCode;
    var status = util.getStatusCode(statusCode);
    var resHeaders = resData.headers = svrRes.headers;
    var body = '';
    var statusMsg;
    util.deleteReqHeaders(socket);
    resData.body = body;
    resData.ip = resData.ip || LOCALHOST;
    data.requestTime = data.dnsTime = Date.now();
    getResRules(socket, resData, function () {
      status = curStatus || status;
      util.addMatchedRules(socket, resData);
      var isSuccess = status == 101;
      if (isSuccess) {
        statusMsg = 'HTTP/1.1 101 Switching Protocols';
        var key = headers['sec-websocket-key'];
        var protocol = getTransProto(headers['sec-websocket-protocol']);
        headers.upgrade = getTransProto(headers.upgrade) || 'websocket';
        if (key) {
          key += '258EAFA5-E914-47DA-95CA-C5AB0DC85B11';
          resHeaders['Sec-WebSocket-Accept'] = crypto.createHash('sha1').update(key, 'binary').digest('base64');
        }
        if (protocol) {
          resHeaders['Sec-WebSocket-Protocol'] = protocol;
        }
        resHeaders.Upgrade = headers.upgrade ;
        resHeaders.Connection = 'Upgrade';
        reqSocket = util.getEmptyRes();
        reqSocket.headers = resHeaders;
        handleFrames(socket, reqSocket, headers);
      } else {
        if (!status) {
          status = 502;
          body = 'Invalid status code: ' + statusCode;
          resHeaders['Content-Type'] = 'text/html; charset=utf8';
          resHeaders['Content-Length'] = Buffer.byteLength(body) + '';
        }
        resHeaders.Connection = 'close';
        statusMsg = 'HTTP/1.1 ' + status;
      }
      resData.statusCode = status;
      var curHeaders = resHeaders;
      if (socket.fromComposer) {
        curHeaders = extend({}, resHeaders);
        curHeaders['x-whistle-req-id'] = socket.reqId;
        util.setFramesMode(curHeaders, isSuccess);
      }
      var rawData =
        statusMsg + '\r\n' + getRawHeaders(curHeaders) + '\r\n\r\n' + body;
      var end = function () {
        if (util.needAbortRes(socket)) {
          socket.__statusCode = status;
          return destroy();
        }
        data.responseTime = data.endTime = Date.now();
        if (isSuccess) {
          socket.write(rawData);
        } else {
          socket.end(rawData);
        }
        execCallback(null, socket);
      };
      var reqDelay = util.getMatcherValue(_rules.reqDelay) || 0;
      var resDelay = util.getMatcherValue(_rules.resDelay) || 0;
      var delay = reqDelay + resDelay;
      if (delay > 0) {
        clearTimeout(timeout);
        setTimeout(end, delay);
      } else {
        end();
      }
    });

    return true;
  };

  var plugin = pluginMgr.resolveWhistlePlugins(socket);
  handleEnd(socket);
  pluginMgr.getRules(socket, function (rulesMgr) {
    if (rulesMgr) {
      socket.pluginRules = rulesMgr;
      socket.curUrl = fullUrl;
      util.mergeRules(socket, rulesMgr.resolveReqRules(socket));
      util.filterWeakRule(socket);
      if (util.isIgnored(filter, 'rule')) {
        plugin = null;
      } else {
        plugin = pluginMgr.getPluginByRuleUrl(util.rule.getUrl(_rules.rule));
      }
    } else {
      util.filterWeakRule(socket);
    }

    var ruleUrlValue = plugin ? null : util.rule.getUrl(_rules.rule);
    if (ruleUrlValue && fullUrl !== ruleUrlValue && HTTP_PROTO_RE.test(ruleUrlValue)) {
      if (RegExp.$1 === 'http') {
        ruleUrlValue = ruleUrlValue.replace('http', 'ws');
      }
      data.realUrl = fullUrl = util.encodeNonLatin1Char(ruleUrlValue);
    }
    if (_rules.referer) {
      var referer = util.getMatcherValue(_rules.referer);
      headers.referer = referer;
    }
    if (_rules.ua) {
      var ua = util.getMatcherValue(_rules.ua);
      headers['user-agent'] = ua;
    }
    if (util.showPluginReq(socket) && !socket.isInternalUrl) {
      if (socket.isLogRequests !== false) {
        ++util.proc.wsRequests;
        ++util.proc.totalWsRequests;
        socket.isLogRequests = true;
      }
      if (!util.isHide(socket)) {
        data.abort = destroy;
        if (socket.isPluginReq) {
          data.isPR = 1;
        }
        proxy.emit('request', reqEmitter, data);
      }
    }
    setupSocket(function () {
      if (util.needAbortReq(socket)) {
        return destroy();
      }
      if (handleResponse()) {
        return;
      }

      pluginMgr.loadPlugin(
        socket.isPluginReq ? null : plugin,
        function (err, ports) {
          if (plugin) {
            data.dnsTime = Date.now();
          }
          if (err) {
            return execCallback(err);
          }
          var port = ports && ports.upgrade && ports.port;
          if (port) {
            options.isPlugin = true;
            options.port = port;
            data.realUrl = util.changePort(fullUrl, options.port);
            socket.customParser = util.getParserStatus(socket);
            pluginMgr.addSessionInfo(socket, _rules);
            socketMgr.setPending(socket);
            options.protocol = 'ws:';
            socket.headers[config.PLUGIN_HOOK_NAME_HEADER] =
              config.PLUGIN_HOOKS.HTTP;
            connectServer();
            return;
          }
          plugin = null;
          rules.getClientCert(socket, function (_key, _cert, _isPfx) {
            clientKey = _key;
            clientCert = _cert;
            isPfx = _isPfx;
            rules.getProxy(fullUrl, socket, function (err, hostIp, hostPort) {
              var proxyRule = _rules.proxy;
              var connectProxy;
              var send = function () {
                data.requestTime = Date.now();
                if (connectProxy) {
                  connectProxy();
                } else {
                  connectServer(hostIp, hostPort);
                }
              };
              var connect = function () {
                var reqDelay = util.getMatcherValue(_rules.reqDelay);
                if (reqDelay > 0) {
                  clearTimeout(timeout);
                  setTimeout(function () {
                    timeout = setTimeout(function () {
                      destroy(util.TIMEOUT_ERR);
                    }, CONN_TIMEOUT);
                    send();
                  }, reqDelay);
                } else {
                  send();
                }
              };
              proxyUrl = proxyRule ? util.rule.getMatcher(proxyRule) : null;
              if (proxyUrl) {
                isXProxy = X_RE.test(proxyUrl);
                var isSocks = proxyRule.isSocks;
                isInternalProxy = proxyRule.isInternal || util.isInternalProxy(socket);
                var isHttpsProxy = proxyRule.isHttps;
                if (!isInternalProxy && !wss && proxyRule.isHttp2https) {
                  wss = true;
                } else {
                  wss = options.protocol === 'wss:';
                }
                proxyUrl = 'http:' + util.removeProtocol(proxyUrl);
                getServerIp(
                  proxyUrl,
                  function (ip) {
                    var proxyOptions = parseUrl(proxyUrl);
                    proxyOptions.auth = proxyOptions.auth || socket._pacAuth;
                    hostPort = proxyOptions.port;
                    hostIp = ip;
                    var proxyPort = (proxyOptions.port =
                      parseInt(hostPort, 10) ||
                      (isSocks ? 1080 : isHttpsProxy ? 443 : 80));
                    var isProxyPort = util.isProxyPort(proxyPort);
                    if (isProxyPort && util.isLocalAddress(ip)) {
                      return execCallback(
                        new Error('Self loop (' + util.joinIpPort(ip, proxyPort) + ')')
                      );
                    }

                    options.proxyHost = ip;
                    resData.port = options.proxyPort = proxyPort;
                    socket.serverPort = resData.port;
                    options.host = options.hostname;
                    if (!options.port) {
                      options.port = wss ? 443 : 80;
                    }
                    var proxyOpts, tlsOpts;
                    var handleProxy = function (proxySocket) {
                      if (wss) {
                        var conf = { socket: proxySocket };
                        if (tlsOpts) {
                          extend(conf, tlsOpts);
                        }
                        var opts = util.setRejectUnauthorized(socket, conf);
                        if (!socket.disable.secureOptions) {
                          util.setSecureOptions(opts);
                        }
                        if (!socket.disable.servername) {
                          opts.servername = options.hostname;
                        }
                        util.setClientCert(opts, clientKey, clientCert, isPfx);
                        var handleProxyError = function (err) {
                          if (
                            connectProxy &&
                            !tlsOpts &&
                            util.isCiphersError(err)
                          ) {
                            tlsOpts = util.getTlsOptions(_rules);
                            connectProxy();
                          } else if (
                            connectProxy &&
                            util.checkTlsError(err) &&
                            util.checkAuto2Http(socket, ip, proxyUrl)
                          ) {
                            wss = false;
                            data.httpsTime = data.httpsTime || Date.now();
                            data.useHttp = true;
                            if (proxyOpts && options.port == 443) {
                              proxyOpts.port = options.port = 80;
                              proxyOpts.headers.host = util.joinIpPort(proxyOpts.host, proxyOpts.port);
                            }
                            connectProxy();
                          } else {
                            execCallback(err);
                          }
                        };
                        try {
                          proxySocket = tls.connect(opts);
                          proxySocket.on('error', handleProxyError);
                          reqSocket = proxySocket;
                          proxySocket.on('secureConnect', function () {
                            handleEnd(reqSocket);
                            pipeData();
                          });
                        } catch (e) {
                          handleProxyError(e);
                        }
                        return;
                      }
                      reqSocket = proxySocket;
                      handleEnd(reqSocket);
                      pipeData();
                    };
                    // 对应 internal-proxy 要用直接请求，方便用来穿透 nginx
                    if (isInternalProxy && !socket._phost) {
                      if (wss) {
                        headers[config.HTTPS_FIELD] = 1;
                        options.protocol = null;
                        origProto = 'wss:';
                        wss = false;
                      }
                    } else {
                      if (isSocks) {
                        options.localDNS = false;
                        options.auths = config.getAuths(proxyOptions);
                      } else {
                        var proxyHeaders = (options.headers = {});
                        pluginMgr.getTunnelKeys().forEach(function (k) {
                          var val = headers[k];
                          if (val) {
                            proxyHeaders[k] = val;
                          }
                        });
                        var auth = headers['proxy-authorization'];
                        if (auth) {
                          proxyHeaders['proxy-authorization'] = auth;
                        }
                        if (socket.disable.proxyUA) {
                          delete proxyHeaders['user-agent'];
                        } else if (headers['user-agent']) {
                          proxyHeaders['user-agent'] = headers['user-agent'];
                        }
                        if (wss && isInternalProxy) {
                          headers[config.HTTPS_FIELD] = 1;
                          options.protocol = null;
                          origProto = 'wss:';
                          wss = false;
                        }
                        if (!util.isLocalAddress(clientIp)) {
                          proxyHeaders[clientIpKey] = clientIp;
                        }
                        if (isProxyPort) {
                          proxyHeaders[config.WEBUI_HEAD] = 1;
                        }
                        if (util.isLocalPHost(socket, wss)) {
                          headers[config.WEBUI_HEAD] = 1;
                        }
                        var clientId = headers[config.CLIENT_ID_HEADER];
                        if (clientId) {
                          proxyHeaders[config.CLIENT_ID_HEADER] = clientId;
                        }
                        util.checkIfAddInterceptPolicy(proxyHeaders, headers);
                        util.setClientId(
                          proxyHeaders,
                          socket.enable,
                          socket.disable,
                          clientIp,
                          isInternalProxy
                        );
                        options.proxyAuth = proxyOptions.auth;
                      }
                      var netMgr = isSocks ? socks : config;
                      proxyOpts = util.setProxyHost(socket, options);
                      if (isHttpsProxy) {
                        proxyOpts.proxyServername = proxyOptions.hostname;
                      }
                      connectProxy = function () {
                        if (destroyed) {
                          return;
                        }
                        if (socket._phost) {
                          resData.phost = socket._phost.host;
                        }
                        proxyOpts.enableIntercept = true;
                        proxyOpts.proxyTunnelPath = util.getProxyTunnelPath(
                          socket,
                          wss
                        );
                        try {
                          var s = netMgr.connect(proxyOpts, handleProxy);
                          s.on(
                            'error',
                            isXProxy
                              ? function () {
                                if (isXProxy) {
                                  isXProxy = false;
                                  resData.phost = undefined;
                                  if (isInternalProxy) {
                                    options.protocol = origProto;
                                  }
                                  connectServer();
                                }
                              }
                              : execCallback
                          );
                        } catch (e) {
                          execCallback(e);
                        }
                      };
                    }
                    connect();
                  },
                  null,
                  null,
                  proxyRule
                );
              } else {
                connect();
              }
            });
          });
        }
      );
    });
  });

  var retryConnect, auto2http, newIp;
  var retryXHost = 0;
  function connectServer(hostIp, hostPort, tlsOpts) {
    getServerIp(
      fullUrl,
      function (ip, port) {
        var isWss = options.protocol === 'wss:';
        var _port = port;
        resData.port = port = port || options.port || (isWss ? 443 : 80);
        socket.serverPort = port;
        if (destroyed) {
          return;
        }
        if (util.isProxyPort(port) && util.isLocalAddress(ip)) {
          return execCallback(new Error('Self loop (' + util.joinIpPort(ip, port) + ')'));
        }
        // checkHandUpError, retry
        try {
          var opts = util.setRejectUnauthorized(socket, {
            host: ip,
            port: port
          });
          if (!socket.disable.servername) {
            opts.servername =
              util.parseHost(headers.host)[0] || options.hostname;
          }
          isWss && util.setClientCert(opts, clientKey, clientCert, isPfx);
          if (tlsOpts) {
            extend(opts, tlsOpts);
          }
          if (!socket.disable.secureOptions) {
            util.setSecureOptions(opts);
          }
          reqSocket = (isWss ? tls : net).connect(opts, pipeData);
        } catch (e) {
          return execCallback(e);
        }
        if (retryConnect) {
          handleEnd(reqSocket);
        } else {
          retryConnect = function (e) {
            if (!newIp && (newIp = util.getLocalhostIP(e, socket, socket._w2hostname, socket.hostIp))) {
              ip = newIp;
            } else if (
              retryXHost < 2 &&
              ((_rules.host && X_RE.test(_rules.host.matcher)) ||
                (isInternalProxy && isXProxy))
            ) {
              ++retryXHost;
              retryConnect = false;
              if (retryXHost > 1) {
                socket.curUrl = fullUrl;
                rules.lookupHost(socket, function (err, _ip) {
                  socket.hostIp = resData.ip = _ip || LOCALHOST;
                  if (err) {
                    return execCallback(err);
                  }
                  connectServer(_ip);
                });
                return;
              }
            } else if (isWss && util.checkAuto2Http(socket, ip, proxyUrl)) {
              if (auto2http || util.checkTlsError(e)) {
                options.protocol = null;
                data.httpsTime = data.httpsTime || Date.now();
                data.useHttp = true;
              } else {
                retryConnect = false;
                auto2http = true;
              }
            }
            connectServer(ip, _port);
          };
          var retried;
          // 不要用once，防止多次触发error导致crash
          reqSocket.on('error', function (err) {
            if (retried) {
              return;
            }
            retried = true;
            this.destroy && this.destroy();
            if (destroyed || !retryConnect) {
              return;
            }
            if (!tlsOpts && isWss && util.isCiphersError(err)) {
              connectServer(hostIp, hostPort, util.getTlsOptions(_rules));
            } else {
              retryConnect(err);
            }
          });
        }
      },
      hostIp,
      hostPort
    );
  }

  function pipeData() {
    var enable = socket.enable;
    var disable = socket.disable;
    if (retryConnect) {
      reqSocket.removeListener('error', retryConnect);
      handleEnd(reqSocket);
      retryConnect = null;
    }
    clearTimeout(timeout);
    var clientId = headers[config.CLIENT_ID_HEADER];
    if (clientId) {
      if (!options.isPlugin && !socket._customClientId && !util.isKeepClientId(socket, proxyUrl)) {
        socket._origClientId = clientId;
        util.removeClientId(headers);
      }
      data.clientId = clientId;
    } else {
      util.setClientId(headers, enable, disable, clientIp, isInternalProxy);
    }
    if (disable.clientIp || disable.clientIP) {
      delete headers[clientIpKey];
    } else {
      var forwardedFor = util.getMatcherValue(_rules.forwardedFor);
      if (net.isIP(forwardedFor)) {
        headers[clientIpKey] = forwardedFor;
      } else if (socket._customXFF) {
        headers[clientIpKey] = socket._customXFF;
      } else if (
        (!isInternalProxy &&
          !plugin &&
          !socket.enableXFF &&
          !enable.clientIp &&
          !enable.clientIP) ||
        util.isLocalAddress(clientIp)
      ) {
        delete headers[clientIpKey];
      } else {
        headers[clientIpKey] = clientIp;
      }
    }
    util.deleteReqHeaders(socket);
    util.addMatchedRules(socket);
    reqSocket.write(socket.getBuffer(headers, options.path));
    reqSocket.resume();
    delete headers['x-whistle-frame-parser'];
    delete headers[config.HTTPS_FIELD];
    _pipeData();
  }

  function setupSocket(cb) {
    var authObj = util.getAuthByRules(_rules);
    var list = [
      _rules.reqHeaders,
      _rules.reqCors,
      _rules.reqCookies,
      _rules.params,
      _rules.urlReplace,
      _rules.urlParams,
      authObj ? null : _rules.auth
    ];
    util.parseRuleJson(
      list,
      function (
        reqHeaders,
        reqCors,
        reqCookies,
        params,
        urlReplace,
        urlParams,
        auth
      ) {
        if (params && urlParams) {
          extend(params, urlParams);
        } else {
          params = params || urlParams;
        }
        var newUrl = params
          ? util.replaceUrlQueryString(fullUrl, params)
          : fullUrl;
        var dProps = util.parseDelQuery(socket);
        newUrl = util.parsePathReplace(newUrl, urlReplace, dProps.paths) || newUrl;
        newUrl = util.deleteQuery(newUrl, dProps.query, socket._delQueryString);
        if (newUrl !== fullUrl) {
          fullUrl = newUrl;
          socket._realUrl = newUrl;
        }
        options = util.parseUrl(fullUrl);
        socket._w2hostname = options.hostname;
        data.realUrl = fullUrl;
        var host = (headers.host = options.host);
        socket._origin = headers.origin;
        if (reqHeaders) {
          reqHeaders = util.lowerCaseify(reqHeaders, socket.rawHeaderNames);
          var xff = reqHeaders[clientIpKey];
          if (net.isIP(xff)) {
            socket._customXFF = xff;
          }
          socket._customClientId = reqHeaders[config.CLIENT_ID_HEADER];
          delete reqHeaders[clientIpKey];
          extend(headers, reqHeaders);
          headers.host = headers.host || host;
        }
        auth = util.getAuthBasic(auth || authObj);
        if (auth) {
          headers['authorization'] = auth;
        }
        var reqRuleData = { headers: headers };
        util.setReqCors(reqRuleData, reqCors);
        util.setReqCookies(reqRuleData, reqCookies, headers.cookie, socket);
        if (_rules.referer) {
          headers.referer = util.getMatcherValue(_rules.referer);
        }

        util.disableReqProps(socket);
        pluginMgr.postStats(socket);
        cb();
      },
      socket
    );
  }

  function getResRules(socket, res, callback) {
    socket.statusCode = res.statusCode || '';
    var curResHeaders = (socket.resHeaders = res.headers);
    pluginMgr.getResRules(socket, res, function () {
      util.parseRuleJson(
        [_rules.resHeaders, _rules.resCors, _rules.resCookies],
        function (resHeaders, cors, cookies) {
          if (resHeaders) {
            resHeaders = util.lowerCaseify(resHeaders, res.rawHeaderNames);
            extend(res.headers, resHeaders);
          }
          var origin = curResHeaders['access-control-allow-origin'];
          if (socket._origin && origin && origin !== '*') {
            curResHeaders['access-control-allow-origin'] = socket._origin;
          }
          util.setResCors(res, cors, socket);
          util.setResCookies(res, cookies, socket);
          util.setResponseFor(_rules, curResHeaders, socket, socket.hostIp, socket._phost);
          util.deleteResHeaders(socket, curResHeaders);
          util.disableResProps(socket, curResHeaders);
          curStatus = util.getMatcherValue(_rules.replaceStatus);
          callback();
        },
        socket
      );
    });
  }

  function _pipeData() {
    parseReq(
      reqSocket,
      function (err, res) {
        if (err) {
          return execCallback(err);
        }
        reqSocket.pause();
        socket.statusCode = res.statusCode || '';
        var curResHeaders = (reqSocket.headers = res.headers);
        socket.resHeaders = curResHeaders;
        getResRules(socket, res, function () {
          util.delay(util.getMatcherValue(_rules.resDelay), function () {
            if (util.needAbortRes(socket)) {
              socket.__statusCode = res.statusCode;
              return destroy();
            }
            reqSocket.reqId = data.id;
            var code = curStatus || res.statusCode;
            var isSuccess = code == 101;
            socket.statusCode = res.statusCode = code;
            util.addMatchedRules(socket, res);
            var curHeaders = curResHeaders;
            if (socket.fromComposer) {
              curHeaders = extend({}, curResHeaders);
              curHeaders['x-whistle-req-id'] = reqSocket.reqId;
              util.setFramesMode(curHeaders, isSuccess);
            }
            if (isSuccess) {
              socket.write(res.getHeaders(curHeaders, curStatus));
              if (res.bodyBuffer.length) {
                reqSocket.unshift(res.bodyBuffer);
              }
              handleFrames(socket, reqSocket, curResHeaders);
              resData.body = '';
            } else {
              socket.write(res.getBuffer(curHeaders, curStatus));
              reqSocket.resume();
              resData.body = res.body;
            }
            resData.headers = curResHeaders;
            resData.rawHeaderNames = res.rawHeaderNames;
            resData.statusCode = code;
            reqEmitter.emit('response', data);
            execCallback(null, reqSocket);
          });
        });
      },
      true
    );
  }

  function getServerIp(url, callback, hostIp, hostPort, proxyRule) {
    if (plugin) {
      return callback(LOCALHOST);
    }
    var hostHandler = function (err, ip, port, hostRule) {
      if (err) {
        return execCallback(err);
      }
      if (hostRule) {
        (proxyRule || _rules).host = hostRule;
      }
      socket.hostIp = resData.ip = util.joinIpPort(ip, port);
      data.requestTime = data.dnsTime = Date.now();
      reqEmitter.emit('send', data);
      callback(ip, port);
    };
    if (hostIp) {
      hostHandler(null, hostIp, hostPort);
    } else {
      socket.curUrl = url;
      rules.resolveHost(
        socket,
        hostHandler,
        socket.pluginRules,
        socket.rulesFileMgr,
        socket.headerRulesMgr
      );
    }
  }

  function handleEnd(socket) {
    return util.onSocketEnd(socket, destroy);
  }
  var destroyed, reqDestroyed, resDestroyed;
  function destroy(err) {
    if (!reqDestroyed) {
      reqDestroyed = true;
      socket.destroy();
    }
    if (reqSocket && !resDestroyed) {
      resDestroyed = true;
      reqSocket.destroy();
    }
    if (destroyed) {
      return;
    }
    destroyed = true;
    execCallback(err);
  }

  function execCallback(err, _socket) {
    if (done) {
      return;
    }
    done = true;
    data.dnsTime = data.dnsTime || Date.now();
    clearTimeout(timeout);
    data.responseTime = data.endTime = Date.now();
    socket.hostIp = resData.ip = resData.ip || LOCALHOST;
    if (!err && !_socket) {
      err = new Error('Aborted');
      data.reqError = true;
      resData.statusCode = 'aborted' + (socket.__statusCode ? ' (' + socket.__statusCode + ')' : '');
      reqData.body = util.getErrorStack(err);
      reqEmitter.emit('abort', data);
    } else if (err) {
      data.resError = true;
      resData.statusCode = resData.statusCode || 502;
      resData.body = util.getErrorStack(err);
      util.emitError(reqEmitter, data);
      destroy(err);
    } else {
      reqEmitter.emit('end', data);
    }
    if (socket.resHeaders) {
      resData.headers = socket.resHeaders;
    } else if (err) {
      resData.headers = { 'x-server': 'whistle' };
    }
    pluginMgr.postStats(socket, _socket || resData);
  }
}

function getTunnelData(socket, clientIp, clientPort, isHttpH2) {
  var enable = socket.enable || '';
  var disable = socket.disable || '';
  var headers = socket.headers;
  var tunnelData = headers[util.TUNNEL_DATA_HEADER];
  var tdKey = config.tdKey;
  if (tdKey && (!tunnelData || config.overTdKey)) {
    tunnelData = headers[tdKey] || tunnelData;
  }
  var tunnelHeaders;
  var tunnelKeys = pluginMgr.getTunnelKeys();
  tunnelKeys.forEach(function (k) {
    var val = headers[k];
    if (val) {
      tunnelHeaders = tunnelHeaders || {};
      tunnelHeaders[k] = val;
    }
  });
  return {
    id: socket.reqId,
    clientIp: clientIp,
    clientPort: clientPort,
    remoteAddr: socket._remoteAddr,
    remotePort: socket._remotePort,
    clientId: headers[config.CLIENT_ID_HEADER],
    proxyAuth: disable.tunnelAuthHeader
                  ? undefined
                  : headers['proxy-authorization'],
    tunnelData: tunnelData,
    headers: tunnelHeaders,
    tunnelFirst:
                  enable.tunnelHeadersFirst && !disable.tunnelHeadersFirst,
    isHttpH2: isHttpH2,
    sniPlugin: socket.sniPlugin
  };
}

function addReqInfo(req) {
  var socket = req.socket;
  var remoteData =
    socket._remoteDataInfo ||
    tunnelTmplData.get(socket.remotePort + ':' + socket.localPort);
  var headers = req.headers;
  if (remoteData) {
    req.isHttpH2 = remoteData.isHttpH2;
    req.reqId = remoteData.id;
    socket._remoteDataInfo = remoteData;
    remoteData._connected = true;
    headers[config.CLIENT_INFO_HEADER] =
      (remoteData.clientIp || LOCALHOST) +
      ',' + remoteData.clientPort +
      ',' + remoteData.remoteAddr +
      ',' + remoteData.remotePort;
    util.setTunnelHeaders(headers, remoteData);
  }
  if (!req.isHttpH2) {
    headers[config.HTTPS_FIELD] = 1;
    setCaptureUA(req.headers['user-agent']);
  }
}

function getStatusMessage(obj) {
  return obj.statusMessage || STATUS_CODES[obj.code] || 'Unknown';
}

function isIllegalcHeader(name, value) {
  switch (name) {
  case h2Consts.HTTP2_HEADER_CONNECTION:
  case h2Consts.HTTP2_HEADER_UPGRADE:
  case h2Consts.HTTP2_HEADER_HOST:
  case h2Consts.HTTP2_HEADER_HTTP2_SETTINGS:
  case h2Consts.HTTP2_HEADER_KEEP_ALIVE:
  case h2Consts.HTTP2_HEADER_PROXY_CONNECTION:
  case h2Consts.HTTP2_HEADER_TRANSFER_ENCODING:
    return true;
  case h2Consts.HTTP2_HEADER_TE:
    return value !== 'trailers';
  default:
    return false;
  }
}

function formatRawHeaders(obj, isH2) {
  var headers = obj.headers;
  if (isH2) {
    var newHeaders = {};
    Object.keys(headers).forEach(function (name) {
      var value = headers[name];
      if (!isIllegalcHeader(name, value)) {
        newHeaders[name] = value;
      }
    });
    return newHeaders;
  }
  var rawNames =
    Array.isArray(obj.rawHeaders) && getRawHeaderNames(obj.rawHeaders);
  return formatHeaders(headers, rawNames);
}

function addStreamEvents(stream, handleAbort) {
  if (stream) {
    stream.on('error', handleAbort);
    stream.on('aborted', handleAbort);
    stream.on('close', handleAbort);
  }
}

function toHttp1(req, res) {
  var isH2 = req.httpVersion == 2;
  var client;
  var handleAbort = function () {
    if (client) {
      client.abort();
      res.destroy();
      client = null;
    }
  };
  addReqInfo(req);
  addStreamEvents(req.stream, handleAbort);
  req.on('error', handleAbort);
  res.on('error', handleAbort);
  res.once('close', handleAbort);
  var host = req.headers[':authority'];
  var headers = req.headers;
  if (host) {
    req.headers.host = host;
    var newHeaders = { host: host };
    Object.keys(headers).forEach(function (name) {
      if (name[0] !== ':') {
        newHeaders[name] = headers[name];
      }
    });
    headers = newHeaders;
  } else {
    headers = formatRawHeaders(req);
  }
  var options = util.parseUrl(util.getFullUrl(req));
  options.protocol = null;
  options.hostname = null;
  options.agent = false;
  options.host = config.host || LOCALHOST;
  options.port = config.port;
  options.headers = headers;
  if (isH2) {
    headers[config.ALPN_PROTOCOL_HEADER] = (req.isHttpH2 ? 'httpH2' : 'h2') + (req.reqId ? '.' + req.reqId : '');
  }
  options.method = req.method;
  client = http.request(options);
  client.on('error', handleAbort);
  client.on('response', function (svrRes) {
    svrRes.on('error', handleAbort);
    svrRes.once('end', function () {
      var trailers = svrRes.trailers;
      if (!util.isEmptyObject(trailers)) {
        var rawHeaderNames = svrRes.rawTrailers
          ? getRawHeaderNames(svrRes.rawTrailers)
          : null;
        try {
          res.addTrailers(formatHeaders(trailers, rawHeaderNames));
        } catch (e) {}
      }
    });
    var addHeaders = svrRes.headers[util.ADDITIONAL_HEAD];
    if (addHeaders) {
      delete svrRes.headers[util.ADDITIONAL_HEAD];
      if (isH2 && res.stream && typeof res.stream.additionalHeaders === 'function'
        && (addHeaders = util.parseRawJson(addHeaders))) {
        try {
          res.stream.additionalHeaders(addHeaders);
        } catch (e) {}
      }
    }
    try {
      var code = svrRes.statusCode;
      res.writeHead(
        code,
        getStatusMessage(svrRes),
        formatRawHeaders(svrRes, isH2)
      );
      var write = res.write;
      res.write = function (chunk) {
        return write.call(res, chunk, function (e) {
          e && handleAbort();
        });
      };
      svrRes.pipe(res);
      res.flushHeaders && res.flushHeaders();
    } catch (e) {
      handleAbort();
    }
  });
  req.pipe(client);
}

var handlers = {
  request: function (req, res) {
    addReqInfo(req);
    server.emit('request', req, res);
  },
  upgrade: function (req, socket) {
    addReqInfo(req);
    server.emit('upgrade', req, socket);
  }
};
var h2Handlers = config.enableH2
  ? {
    request: toHttp1,
    upgrade: handlers.upgrade
  }
  : handlers;

var HTTP_RE = /^(\w+)\s+(\S+)\s+HTTP\/1.\d$/im;
var HTTP2_RE = /^PRI\s\*\s+HTTP\/2.0$/im;
var CONNECT_RE = /^CONNECT$/i;

function addClientInfo(socket, chunk, statusLine, clientIp, clientPort) {
  var len = Buffer.byteLength(statusLine);
  chunk = chunk.slice(len);
  statusLine +=
    '\r\n' +
    config.CLIENT_INFO_HEADER +
    ': ' +
    clientIp +
    ',' +
    clientPort +
    ',' +
    socket._remoteAddr +
    ',' +
    socket._remotePort;
  var tunnelData = getTunnelData(socket, clientIp, clientPort);
  if (tunnelData) {
    statusLine += '\r\n' + util.TEMP_TUNNEL_DATA_HEADER + ': ' + encodeURIComponent(JSON.stringify(tunnelData));
  }
  return Buffer.concat([Buffer.from(statusLine), chunk]);
}

module.exports = function (socket, next, isWebPort) {
  var reqSocket, reqDestroyed, resDestroyed;
  var headersStr;
  var enable = socket.enable || '';
  var disable = socket.disable || '';
  var isCaptureIp = function() {
    if (disable.captureIp || disable.captureIP) {
      return false;
    }
    if (enable.capture || enable.captureIp || enable.captureIP) {
      return true;
    }
    return isCaptureUA(socket.headers['user-agent']);
  };
  var isEnable = function(p1) {
    return enable[p1] && !disable[p1];
  };
  var destroy = function (err) {
    if (reqSocket) {
      if (!resDestroyed) {
        resDestroyed = true;
        reqSocket.destroy(err);
      }
    } else if (!reqDestroyed) {
      reqDestroyed = true;
      socket.destroy(err);
    }
  };

  util.onSocketEnd(socket, destroy);

  var clientIp = socket.clientIp;
  var clientPort = socket.clientPort;
  util.readOneChunk(socket, function (chunk) {
    headersStr = chunk && chunk.toString();
    var isHttp = chunk && HTTP_RE.test(headersStr);
    var statusLine = isHttp && RegExp['$&'];
    if (isHttp && CONNECT_RE.test(RegExp.$1)) {
      chunk = addClientInfo(socket, chunk, statusLine, clientIp, clientPort);
      util.connect(
        {
          port: config.port,
          host: config.host || LOCALHOST
        },
          function (err, s) {
            reqSocket = s;
            if (err || socket._hasError) {
              return destroy(err);
            }
            reqSocket.on('error', destroy);
            reqSocket.write(chunk);
            reqSocket.pipe(socket).pipe(reqSocket);
            socket.resume();
          }
        );
      return;
    }
    if (!chunk) {
        //没有数据
      return isWebPort ? socket.destroy() : next(chunk);
    }
    if (isHttp) {
      if (isEnable('forHttps') || disable.captureHttp) {
        next(chunk);
      } else {
        socket.resume();
       
... [truncated, file is 43910 chars]
```

### lib/index.js
```
var express = require('express');
var http = require('http');
var https = require('https');
var socks = require('sockx');
var extend = require('extend');
var EventEmitter = require('events');
var util = require('./util');
var logger = require('./util/logger');
var rules = require('./rules');
var setupHttps = require('./https').setup;
var httpsUtil = require('./https/ca');
var rulesUtil = require('./rules/util');
var initDataServer = require('./util/data-server');
var pluginMgr = require('./plugins');
var config = require('./config');
var loadService = require('./service');
var initSocketMgr = require('./socket-mgr');
var tunnelProxy = require('./tunnel');
var upgradeProxy = require('./upgrade');
var proc = require('./util/process');
var perf = require('./util/perf');
var loadCert = require('./https/load-cert');
var common = require('./util/common');

function handleClientError(err, socket) {
  if (!socket.writable) {
    return socket.destroy(err);
  }
  var errCode = err && err.code;
  var statusCode = errCode === 'HPE_HEADER_OVERFLOW' ? 431 : 400;
  var stack = util.getErrorStack(
    'clientError: Bad request' + (errCode ? ' (' + errCode + ')' : '')
  );
  socket.end('HTTP/1.1 ' + statusCode + ' Bad Request\r\n\r\n' + stack);
}

function proxy(callback, _server) {
  var app = express();
  var server = _server || http.createServer();
  var proxyEvents = new EventEmitter();
  var middlewares = ['./init', '../biz']
    .concat(require('./inspectors'))
    .concat(config.middlewares)
    .concat(require('./handlers'));
  server.timeout = config.timeout;
  server.requestTimeout = 0;
  proxyEvents.config = config;
  proxyEvents.server = server;
  app.disable('x-powered-by');
  app.logger = logger;
  middlewares.forEach(function (mw) {
    mw && app.use((typeof mw == 'string' ? require(mw) : mw).bind(proxyEvents));
  });
  server.on('clientError', handleClientError);
  pluginMgr.setProxy(proxyEvents);
  perf.setProxy(proxyEvents);
  initSocketMgr(proxyEvents);
  setupHttps(server, proxyEvents);
  exportInterfaces(proxyEvents);
  tunnelProxy(server, proxyEvents);
  upgradeProxy(server);
  initDataServer(proxyEvents);
  rulesUtil.setup(proxyEvents);
  var properties = rulesUtil.properties;
  if (config.disableAllRules) {
    properties.set('disabledAllRules', true);
  } else if (config.disableAllRules === false) {
    properties.set('disabledAllRules', false);
  }
  if (config.disableAllPlugins) {
    properties.set('disabledAllPlugins', true);
  } else if (config.disableAllPlugins === false) {
    properties.set('disabledAllPlugins', false);
  }
  if (config.allowMultipleChoice) {
    properties.set('allowMultipleChoice', true);
  } else if (config.allowMultipleChoice === false) {
    properties.set('allowMultipleChoice', false);
  }
  rulesUtil.addValues(config.values, config.replaceExistValue);
  rulesUtil.addRules(config.rules, config.replaceExistRule);
  config.debug && rules.disableDnsCache();
  var count = _server ? 1 : 2;
  var execCallback = function () {
    if (--count === 0) {
      process.whistleStarted = true;
      process.emit('whistleStarted', proxyEvents);
      typeof callback === 'function' && callback.call(server, proxyEvents);
    }
  };
  !_server && util.getBoundIp(config.host, function (host) {
    util.checkPort(!config.INADDR_ANY && !host && config.port, function () {
      config.host = host;
      server.listen(config.port, host, execCallback);
    });
  });
  var createNormalServer = function (port, httpModule, opts) {
    if (!port) {
      return;
    }
    ++count;
    var optionServer = httpModule.createServer(opts);
    var isHttps = !!opts;
    proxyEvents[isHttps ? 'httpsServer' : 'httpServer'] = optionServer;
    optionServer.timeout = config.timeout;
    optionServer.requestTimeout = 0;
    optionServer.on('request', function (req, res) {
      req.isHttps = isHttps;
      app.handle(req, res);
    });
    optionServer.isHttps = isHttps;
    tunnelProxy(optionServer, proxyEvents, isHttps ? 1 : 2);
    upgradeProxy(optionServer);
    optionServer.on('clientError', handleClientError);
    util.getBoundIp(
      config[isHttps ? 'httpsHost' : 'httpHost'],
      function (host) {
        util.checkPort(!config.INADDR_ANY && !host && port, function () {
          optionServer.listen(port, host, execCallback);
        });
      }
    );
  };
  createNormalServer(config.httpPort, http);
  createNormalServer(
    config.httpsPort,
    https,
    extend(
      {
        SNICallback: function (servername, callback) {
          var curUrl = 'https://' + servername;
          loadCert(
            {
              isHttpsServer: true,
              fullUrl: curUrl,
              curUrl: curUrl,
              useSNI: true,
              headers: {},
              servername: servername,
              serverName: servername,
              commonName: httpsUtil.getDomain(servername)
            },
            function () {
              httpsUtil.SNICallback(servername, callback);
            }
          );
        }
      },
      httpsUtil.createCertificate('*.wproxy.org')
    )
  );
  if (config.socksPort) {
    ++count;
    var boundHost;
    var socksServer = socks.createServer(function (info, accept, deny) {
      var dstPort = info.dstPort;
      var dstAddr = info.dstAddr;
      var connPath = util.joinIpPort(dstAddr, dstPort);
      var headers = { host: connPath };
      var clientIp = util.removeIPV6Prefix(info.srcAddr) || '127.0.0.1';
      var clientPort = info.srcPort;
      headers['x-whistle-server'] = 'socks';
      headers[config.CLIENT_INFO_HEADER] = [clientIp, clientPort, clientIp, clientPort].join();
      if (config.socksMode) {
        headers[config.WHISTLE_POLICY_HEADER] = 'weakTunnel';
      }
      var client = http.request({
        method: 'CONNECT',
        agent: false,
        path: connPath,
        host: boundHost,
        port: config.port,
        headers: headers
      });
      var destroy = function () {
        if (client) {
          client.abort();
          client = null;
          deny();
        }
      };
      client.on('error', destroy);
      client.on('connect', function (res, socket) {
        socket.on('error', destroy);
        if (res.statusCode != 200) {
          return destroy();
        }
        var reqSock = accept(true);
        if (reqSock) {
          reqSock.pipe(socket).pipe(reqSock);
        } else {
          destroy();
        }
      });
      client.end();
    });
    proxyEvents.socksServer = socksServer;
    util.getBoundIp(config.socksHost, function (host) {
      boundHost = host || '127.0.0.1';
      util.checkPort(
        !config.INADDR_ANY && !host && config.socksPort,
        function () {
          socksServer.listen(config.socksPort, host, execCallback);
        }
      );
      socksServer.useAuth(socks.auth.None());
    });
  }
  require('../biz/init')(proxyEvents, function () {
    server.on('request', app);
    execCallback();
  });
  return proxyEvents;
}

function exportInterfaces(obj) {
  obj.getWhistlePath = common.getWhistlePath;
  obj.rules = rules;
  obj.util = util;
  obj.rulesUtil = rulesUtil;
  obj.rulesMgr = rules;
  obj.httpsUtil = httpsUtil;
  obj.pluginMgr = pluginMgr;
  obj.logger = logger;
  obj.loadService = loadService;
  obj.setAuth = config.setAuth;
  obj.setUIHost = config.setUIHost;
  obj.setPluginUIHost = config.setPluginUIHost;
  obj.socketMgr = initSocketMgr;
  obj.getRuntimeInfo = function () {
    return proc;
  };
  obj.getShadowRules = function () {
    return config.shadowRules;
  };
  obj.setShadowRules = function (shadowRules) {
    if (typeof shadowRules === 'string') {
      config.shadowRules = shadowRules;
      rulesUtil.parseRules();
    }
  };
  return obj;
}
var HTTP2_ERR_RE = /^ERR_HTTP2_/;
function handleGlobalException(err) {
  var code = err && err.code;
  if (
    !config.diagnose &&
    (code === 'EPIPE' ||
    HTTP2_ERR_RE.test(code) ||
    code === 'ENETUNREACH' ||
    code === 'ERR_HTTP_TRAILER_INVALID' ||
    code === 'ERR_INTERNAL_ASSERTION' ||
    code === 'ERR_INVALID_ARG_TYPE' ||
    (err && /finishwrite|'_hadError'/i.test(err.message)))
  ) {
    return;
  }
  if (
    !err ||
    (code !== 'ERR_IPC_CHANNEL_CLOSED' && code !== 'ERR_IPC_DISCONNECTED')
  ) {
    var stack = util.getErrorStack(err);
    common.writeLogSync('\r\n' + stack + '\r\n');
    /*eslint no-console: "off"*/
    console.error(stack);
    if (
      typeof process.handleUncauthtWhistleErrorMessage === 'function' &&
      process.handleUncauthtWhistleErrorMessage(stack, err) === false
    ) {
      return;
    }
  }
  setTimeout(function () {
    process.exit(1);
  }, 360);
}

process.on('unhandledRejection', handleGlobalException);
process.on('uncaughtException', handleGlobalException);

rulesUtil.setPluginMgr(pluginMgr);
rulesUtil.parseRules();

module.exports = exportInterfaces(proxy);

```

### lib/inspectors/data.js
```
var EventEmitter = require('events').EventEmitter;
var zlib = require('../util/zlib');
var util = require('../util');
var socketMgr = require('../socket-mgr');
var config = require('../config');

var MAX_BODY_SIZE = 360 * 1024;
var MAX_SIZE = (config.strict ? 256 : 1024) * 1024;
var MAX_REQ_BODY_SIZE = (config.strict ? 256 : 2048) * 1024;
var MAX_RES_BODY_SIZE = (config.strict ? 256 : 2048) * 1024;
var BIG_DATA_SIZE = 1024 * 1024 * 16;
var LOCALHOST = '127.0.0.1';
var SSE_RE = /^\s*text\/event-stream/i;

function getZipType(options) {
  return options.headers && options.headers['content-encoding'];
}

function unzipBody(options, body, callback) {
  return zlib.unzip(getZipType(options), body, callback);
}

function checkType(res) {
  if (!config.strict) {
    return true;
  }
  var type = res.headers['content-type'];
  if (!type) {
    return true;
  }
  type = util.getContentType(type);
  return type && type !== 'CSS' && type !== 'IMG';
}

function checkBodySize(data, useBigData) {
  if (
    config.strict &&
    data.body &&
    data.body.length > (useBigData ? BIG_DATA_SIZE : MAX_BODY_SIZE)
  ) {
    data.body = '';
  }
}

function getEventName(proxy) {
  if (util.listenerCount(proxy, '_request')) {
    return '_request';
  } else if (util.listenerCount(proxy, 'httpRequest')) {
    return 'httpRequest';
  }
}

function emitDataEvents(req, res, proxy) {
  var now = Date.now();
  var eventName = getEventName(proxy);
  eventName && proxy.emit(eventName, req.fullUrl);
  if (!util.showPluginReq(req) || util.isHide(req)) {
    return;
  }
  var getTTFB = function () {
    if (req._ttfb >= now) {
      return req._ttfb - now;
    }
  };
  var _res = {};
  var reqEmitter = new EventEmitter();
  var reqData = {
    method: util.toUpperCase(req.method) || 'GET',
    httpVersion: req.httpVersion || '1.1',
    ip: req.clientIp,
    port: req.clientPort,
    isWhistleHttps: req.isWhistleHttps,
    rawHeaderNames: req.rawHeaderNames,
    headers: req.headers
  };
  var resData = {};
  var reqBody = false;
  var resBody = false;
  var cleared;
  var data = {
    useH2: req.isH2,
    h2Id: req._alpn,
    fc: req.fromComposer ? 1 : undefined,
    isPR: req.isPluginReq ? 1 : undefined,
    _clientId: req._clientId,
    startTime: now,
    ttfb: getTTFB(),
    id: req.reqId,
    sniPlugin: req.sniPlugin,
    url: req.fullUrl,
    req: reqData,
    res: resData,
    rules: req.rules,
    fwdHost: req._fwdHost,
    pipe: req._pipeRule,
    rulesHeaders: req.rulesHeaders,
    abort: function (clear) {
      if (clear === true) {
        data = reqData = resData = reqBody = resBody = false;
        cleared = true;
      } else {
        var err = new Error('Aborted');
        err.code = 'ERR_WHISTLE_ABORTED';
        req.emit('error', err);
      }
    }
  };
  proxy.emit('request', reqEmitter, data);

  var requestTime;
  var endTime;
  var updateEvent;
  var useFrames;
  var enable = req.enable;
  var disable = req.disable;
  var useBigData =
    (enable.bigData || enable.largeData) &&
    !disable.bigData &&
    !disable.largeData;
  var setRequestTime = function (time) {
    data.requestTime = time;
    data.connectTime = req._connectTime;
  };
  var setEndTime = function () {
    if (data.requestTime || !requestTime) {
      data.endTime = endTime || Date.now();
      setRequestTime(data.requestTime || data.endTime);
    } else if (endTime == null) {
      endTime = endTime || Date.now();
    }
  };
  var updateVersion = function () {
    if (req.useH2 != null) {
      data.useH2 = req.useH2;
    }
    data.httpsTime = req.httpsTime;
    data.useHttp = req.useHttp;
    if (data.useH2 && !req.useHttp) {
      reqData.httpVersion = '2.0';
    } else {
      reqData.httpVersion = '1.1';
    }
  };
  var setUnzipSize = function (body, obj) {
    var len = body ? body.length : -1;
    if (len >= 0 && len !== obj.size) {
      obj.unzipSize = len;
    }
  };
  req.setServerPort = function (serverPort) {
    req.serverPort = serverPort;
    setReqStatus(LOCALHOST);
    resData.port = serverPort;
  };
  req.setClientId = function (clientId) {
    data.clientId = clientId;
  };
  req.setTTFB = function() {
    data.ttfb = getTTFB();
  };
  res.setCurTrailers = function (trailers, rawTrailerNames) {
    resData.trailers = trailers;
    resData.rawTrailerNames = rawTrailerNames;
  };
  var reqDone;
  var resDone;
  var captureReqStream;
  var maxReqSize;
  var reqInfo;
  var updateReqInfo = function() {
    if (reqInfo && !captureReqStream) {
      captureReqStream = !disable.captureStream && (resDone || enable.captureStream) && !getZipType(reqInfo);
      maxReqSize = useBigData ? BIG_DATA_SIZE : (captureReqStream ? MAX_REQ_BODY_SIZE : MAX_SIZE);
      if (captureReqStream && reqBody && !reqData.body) {
        reqData.body = reqBody;
      }
    }
  };

  var handleReqBody = function (stream, info) {
    if (reqDone) {
      return;
    }
    reqDone = true;
    reqInfo = info || (req._needGunzip ? { method: req.method, headers: '' } : req);
    if (!cleared && util.hasRequestBody(reqInfo)) {
      reqBody = null;
    }
    reqData.size = 0;
    updateReqInfo();
    var write = stream.write;
    var end = stream.end;
    stream.write = function (chunk) {
      if (chunk) {
        if (reqBody || reqBody === null) {
          if (useFrames) {
            reqBody = '';
          } else {
            reqBody = reqBody ? Buffer.concat([reqBody, chunk]) : chunk;
            if (captureReqStream) {
              reqData.body = reqBody;
            }
            if (reqBody.length > maxReqSize) {
              reqBody = false;
            }
          }
        }
        reqData.size += chunk.length;
      }
      updateEvent && proxy.emit(updateEvent, req.fullUrl, false);
      return write.apply(this, arguments);
    };
    stream.end = function (chunk) {
      if (chunk) {
        reqData.size += chunk.length;
        reqBody = reqBody ? Buffer.concat([reqBody, chunk]) : chunk;
      }
      requestTime = Date.now();
      if (useFrames) {
        reqBody = '';
      }
      unzipBody(reqInfo, reqBody, function (err, body) {
        setRequestTime(requestTime);
        if (endTime) {
          data.endTime = endTime;
        }
        reqBody = err ? util.getErrorStack(err) : body;
        reqData.body = reqBody;
        setUnzipSize(body, reqData);
        checkBodySize(reqData, useBigData);
      });
      updateEvent && proxy.emit(updateEvent, req.fullUrl, false, true);
      return end.apply(this, arguments);
    };
  };
  var handleResBody = function (stream, info) {
    if (resDone) {
      return;
    }
    resDone = true;
    info = info || (res._needGunzip ? { statusCode: res.statusCode, headers: '' } : res);
    var captureStream = !disable.captureStream && (requestTime == null || enable.captureStream ||
      (info.headers && SSE_RE.test(info.headers['content-type']))) && !getZipType(info);
    var maxResSize = useBigData ? BIG_DATA_SIZE : (captureStream ? MAX_RES_BODY_SIZE : MAX_SIZE);
    captureStream && updateReqInfo();
    if (!cleared && util.hasBody(info, req) && checkType(info)) {
      if (info.headers['content-length'] > maxResSize && !captureStream) {
        resBody = false;
      } else {
        resBody = null;
      }
    }
    resData.size = 0;
    var write = stream.write;
    var end = stream.end;
    stream.write = function (chunk) {
      if (chunk) {
        if (resBody || resBody === null) {
          if (useFrames) {
            resBody = '';
          } else {
            resBody = resBody ? Buffer.concat([resBody, chunk]) : chunk;
            if (captureStream) {
              resData.body = resBody;
            }
            if (resBody.length > maxResSize) {
              resBody = false;
            }
          }
        }
        resData.size += chunk.length;
      }
      updateEvent && proxy.emit(updateEvent, req.fullUrl, true);
      return write.apply(this, arguments);
    };
    stream.end = function (chunk) {
      if (chunk) {
        resData.size += chunk.length;
        resBody = resBody ? Buffer.concat([resBody, chunk]) : chunk;
      }
      endTime = Date.now();
      delete data.abort;
      if (useFrames) {
        resBody = '';
      }
      resData.hasGzipError = unzipBody(info, resBody, function (err, body) {
        if (!data.resError) {
          resBody = err ? util.getErrorStack(err) : body;
          resData.body = resBody;
        }
        setUnzipSize(body, resData);
        checkBodySize(resData, useBigData);
        setEndTime();
        reqEmitter.emit('end', data);
      });
      updateEvent && proxy.emit(updateEvent, req.fullUrl, true, true);
      return end.apply(this, arguments);
    };
  };

  var hasReqPipe = req._pipePluginPorts.reqWritePort;
  var hasResPipe = req._pipePluginPorts.resWritePort;

  if (hasReqPipe) {
    req.on('bodyStreamReady', handleReqBody);
  }

  if (hasResPipe) {
    res.on('bodyStreamReady', handleResBody);
  }

  req.once('dest', function (_req) {
    _req.once('finish', function () {
      if (!requestTime) {
        setRequestTime(requestTime);
      }
    });
    setReqStatus();
    reqEmitter.emit('send', data);
    !hasReqPipe && handleReqBody(_req, req);
  });
  res.once('src', function (r) {
    _res = r;
    data.pipe = req._pipeRule;
    resData.rawHeaderNames = res.rawHeaderNames;
    if (!data.endTime) {
      setResStatus();
      reqEmitter.emit('response', data);
    }
    !hasResPipe && handleResBody(res, _res);
  });
  req.once('error', handleError);
  res.once('error', handleError);
  res.once('close', handleError);
  res.once('finish', setEndTime);

  function handleError(err) {
    req._hasError = true;
    if (!data || endTime || data.endTime || (data.responseTime && !err)) {
      return;
    }
    !endTime && setEndTime();
    delete data.abort;
    if (err && err.message !== 'Aborted') {
      data.resError = true;
      if (resData.body) {
        data.errMsg = util.getErrorStack(err);
      } else {
        resData.body = util.getErrorStack(err);
      }
      util.emitError(reqEmitter, data);
      setResStatus(502);
    } else {
      data.reqError = true;
      if (!reqData.body) {
        reqData.body = 'aborted';
      } else if (!resData.body) {
        resData.body = 'aborted';
      } else {
        data.errMsg = 'aborted';
      }
      if (req.__resHeaders) {
        _res.headers = req.__resHeaders;
      }
      reqEmitter.emit('abort', data);
      setResStatus('aborted' + (req.__statusCode ? ' (' + req.__statusCode + ')' : ''));
    }
  }

  function setReqStatus(defaultHost) {
    data.dnsTime = (req.dnsTime || 0) + now;
    data.realUrl = data.url === req.realUrl ? undefined : req.realUrl;
    updateVersion();
    resData.ip = req.hostIp || defaultHost;
    resData.phost = req._phost && req._phost.host;
  }

  req.initCustomParser = function () {
    if (req.customParser) {
      data.useFrames = false;
      socketMgr.setPending(req);
      req.disableCustomParser = function () {
        data.useFrames = null;
        req.customParser = null;
        req.enableCustomParser = null;
        req.disableCustomParser = null;
        socketMgr.removePending(req);
        delete req.headers['x-whistle-frame-parser'];
      };
      req.enableCustomParser = function (svrRes) {
        useFrames = true;
        reqData.body = '';
        resData.body = '';
        reqData.base64 = '';
        resData.base64 = '';
        data.useFrames = true;
        socketMgr.setContext(
          req,
          svrRes,
          eventName,
          { data: [] },
          { data: [] }
        );
        socketMgr.removePending(req);
        delete req.headers['x-whistle-frame-parser'];
      };
    }
  };

  function setResStatus(defaultCode) {
    if (data.responseTime) {
      return;
    }
    setReqStatus(LOCALHOST);
    resData.statusCode = _res.statusCode || defaultCode || 502;
    resData.statusMessage = _res.statusMessage;
    data.responseTime = Date.now();
    if (!requestTime && !data.requestTime) {
      updateEvent = eventName;
    }
    resData.headers = _res.headers;
  }
}

module.exports = function (req, res, next) {
  emitDataEvents(req, res, this);
  util.delay(util.getMatcherValue(req.rules.reqDelay), function () {
    if (util.needAbortReq(req)) {
      return res.destroy();
    }
    next();
  });
};

```

### lib/inspectors/req.js
```
var qs = require('querystring');
var iconv = require('iconv-lite');
var net = require('net');
var util = require('../util');
var extend = require('extend');
var mime = require('mime');
var pluginMgr = require('../plugins');
var config = require('../config');
var handleWeinre = require('./weinre');
var handleLog = require('./log');

var Transform = require('pipestream').Transform;
var WhistleTransform = util.WhistleTransform;
var ReplacePatternTransform = util.ReplacePatternTransform;
var ReplaceStringTransform = util.ReplaceStringTransform;
var FileWriterTransform = util.FileWriterTransform;

var JSON_RE = /{[\w\W]*}|\[[\w\W]*\]/;
var BUOUNDARY_RE = /boundary=(?:"([^"]+)"|([^;]+))/i;
var MAX_REQ_SIZE = 1024 * 1024 * (config.strict ? 1 : 2); // 2MB
var BIG_MAX_REQ_SIZE = 1024 * 1024 * 16;
var MAX_HEADER_SIZE = 1024 * 8;
var CRLF = Buffer.from('\r\n');
var CR = CRLF[0];
var LF = CRLF[1];
var LINE = Buffer.from('-')[0];
var UPLOAD_CTN_SEP = Buffer.from('\r\n\r\n');
var CTN_DIS = 'Content-Disposition: form-data; name="';
var clientIpKey = config.CLIENT_IP_HEADER;

var REQ_TYPE = {
  urlencoded: 'application/x-www-form-urlencoded',
  form: 'application/x-www-form-urlencoded',
  json: 'application/json',
  xml: 'application/xml',
  text: 'text/plain',
  upload: 'multipart/form-data',
  multipart: 'multipart/form-data',
  defaultType: 'application/octet-stream'
};
var NAME_RE = /name=(?:"([^"]+)"|([^;]+))/i;

function getName(firstLine) {
  if (!NAME_RE.test(firstLine)) {
    return null;
  }
  var name = RegExp.$1;
  if (name) {
    return name;
  }
  name = RegExp.$2;
  if (name[0] === '\'') {
    var lastIndex = name.length - 1;
    if (name[lastIndex] === '\'') {
      return name.substring(1, lastIndex);
    }
  }
  return name;
}

function toMultipart(name, value) {
  if (value === undefined) {
    return null;
  }
  if (value == null) {
    value = '';
  }
  if (typeof value == 'object') {
    var filename = value.filename || value.name;
    var base64 = value.base64;
    var type = value.type;
    filename = filename == null ? name : filename + '';
    value = value.content || value.value || '';
    if (value && typeof value === 'object') {
      try {
        value = JSON.stringify(value, null, '  ') || '';
      } catch (e) {}
    } else if (base64) {
      try {
        base64 = Buffer.from(base64, 'base64');
        value = '';
      } catch (e) {
        base64 = '';
      }
    }
    if (!util.isString(type)) {
      type = '';
    } else if (type.indexOf('/') === -1) {
      type = mime.lookup(type, type);
    }
    value = Buffer.from(CTN_DIS + name + '"; filename="' + filename
      + '"\r\nContent-Type: ' + (type || mime.lookup(filename)) + '\r\n\r\n' + value);
    return base64 ? Buffer.concat([value, base64]) : value;
  }
  return Buffer.from(CTN_DIS + name + '"\r\n\r\n' + value);
}

/**
 * 处理请求数据
 *
 * @param req：method、body、headers，top，bottom，speed、delay，charset, timeout
 * @param data
 */
function handleReq(req, data, reqRules, delType) {
  extend(req.headers, data.headers);
  if (reqRules.reqType) {
    var newType = util.getMatcherValue(reqRules.reqType).split(';');
    var type = newType[0];
    newType[0] =
      !type || type.indexOf('/') != -1
        ? type
        : REQ_TYPE[type] || util.lookupType(type);
    req.headers['content-type'] = util.getNewType(newType.join(';'), req.headers);
  }
  util.setCharset(req.headers, data.charset, delType.reqType, delType.reqCharset);
  if (!util.hasRequestBody(req.method)) {
    delete data.top;
    delete data.bottom;
    delete data.body;
    delete req.headers['content-length'];
  } else {
    util.removeReqBody(req, data);
    if (data.top || data.bottom || data.body) {
      delete req.headers['content-length'];
      req._hasInjectBody = true;
    }
  }

  util.isWhistleTransformData(data) &&
    req.addZipTransform(new WhistleTransform(data));
  var opList = util.parseHeaderReplace(req.rules.headerReplace).req;
  if (opList) {
    var host = req.headers.host;
    var xff = req.headers[clientIpKey];
    var clientId = req.headers[config.CLIENT_ID_HEADER];
    util.handleHeaderReplace(req.headers, opList);
    if (req.headers.host !== host) {
      req._customHost = req.headers.host;
    }
    var newXFF = req.headers[clientIpKey];
    if (xff !== newXFF && net.isIP(newXFF)) {
      req._customXFF = newXFF;
    }
    if (clientId !== req.headers[config.CLIENT_ID_HEADER]) {
      req._customClientId = req.headers[config.CLIENT_ID_HEADER];
    }
  }
}

function handleAuth(data, auth) {
  auth = util.getAuthBasic(auth);
  auth && util.setHeader(data, 'authorization', auth);
}

function handleParams(req, params, urlParams, enableBigData) {
  params = util.isEmptyObject(params) ? null : params;
  var delProps = util.parseDelReqBody(req);
  var hasBody;
  var buffer;
  if (params || delProps) {
    var maxReqSize = enableBigData || util.isEnable(req, 'reqMergeBigData') ? BIG_MAX_REQ_SIZE : MAX_REQ_SIZE;
    var transform;
    var headers = req.headers;
    var isJson = util.isJSONContent(req);
    if (isJson || util.isUrlEncoded(req)) {
      delete headers['content-length'];
      transform = new Transform();
      var interrupt;
      transform._transform = function (chunk, _, callback) {
        if (chunk) {
          if (!interrupt) {
            buffer = buffer ? Buffer.concat([buffer, chunk]) : chunk;
            chunk = null;
            if (buffer.length > maxReqSize) {
              interrupt = true;
              chunk = buffer;
              buffer = null;
            }
          }
        } else if (buffer && buffer.length) {
          var body;
          var isGBK = !util.isUtf8(buffer);
          if (isGBK) {
            try {
              body = iconv.decode(buffer, 'GB18030');
            } catch (e) {}
          }
          if (!body) {
            body = buffer + '';
          }
          if (isJson) {
            body = body.replace(JSON_RE, function (json) {
              var obj = util.parseRawJson(json);
              if (obj) {
                if (params) {
                  obj = extend(true, obj, params);
                }
                util.deleteProps(obj, delProps);
                json = JSON.stringify(obj);
              }
              return json;
            });
          } else {
            body = util.replaceQueryString(body, params, delProps);
          }
          if (isGBK) {
            try {
              body = iconv.encode(body, 'GB18030');
            } catch (e) {}
          } else {
            chunk = util.toBuffer(body);
          }
          buffer = null;
        } else if (!interrupt && params) {
          util.deleteProps(params, delProps);
          var data = isJson ? JSON.stringify(params) : qs.stringify(params);
          chunk = util.toBuffer(data);
        }

        callback(null, chunk);
      };
      req.addZipTransform(transform);
      hasBody = true;
    } else if (util.isMultipart(req) && BUOUNDARY_RE.test(headers['content-type'])) {
      delete headers['content-length'];
      var boundaryStr = '--' + (RegExp.$1 || RegExp.$2);
      var startBoundary = Buffer.from(boundaryStr + '\r\n');
      var boundary = Buffer.from('\r\n' + boundaryStr);
      var sepBoundary = Buffer.from('\r\n' + boundaryStr + '\r\n');
      var endBoudary = Buffer.from('\r\n' + boundaryStr + '--');
      var length = startBoundary.length;
      var endLength = sepBoundary.length;
      var minCtnLen = length + endLength;
      var preBuffer;
      var ended;
      var lastChunk;
      var badMultipart;
      var pass;
      var ignore;
      var result;

      transform = new Transform();

      if (delProps) {
        params = params || delProps;
        Object.keys(delProps).forEach(function(key) {
          params[key] = undefined;
        });
      }

      var getRestData = function() {
        var rest;
        Object.keys(params).forEach(function(name) {
          var part = toMultipart(name, params[name]);
          if (part) {
            if (rest) {
              rest.push(sepBoundary);
            } else {
              rest = [];
            }
            rest.push(part);
          }
        });
        if (!rest) {
          return null;
        }
        return rest.length < 2 ? rest[0] : Buffer.concat(rest);
      };

      var pushResult = function(buf, addSep) {
        if (buf && buf.length) {
          result = result || [];
          if (addSep) {
            if (startBoundary) {
              result.unshift(startBoundary);
              startBoundary = null;
            } else {
              result.push(sepBoundary);
            }
          }
          result.push(buf);
        }
      };
      var getResult = function() {
        if (ended) {
          pushResult(getRestData(), true);
        }
        if (!result) {
          return null;
        }
        if (ended && !pass && result.length) {
          result.push(endBoudary);
        }
        if (result.length < 2) {
          return result[0];
        }
        return Buffer.concat(result);
      };

      var getChunk = function() {
        result = null;
        while(!ended && buffer.length >= endLength) {
          var index = buffer.indexOf(boundary);
          var isMatched = index !== -1;
          if (isMatched) {
            var first = buffer[index + length];
            var sec = buffer[index + length + 1];
            ended = first === LINE && sec === LINE;
            isMatched = ended || (first === CR && sec === LF);
          }
          if (ignore || pass) {
            if (!isMatched) {
              index = -endLength + 1;
              if (pass) {
                pushResult(buffer.slice(0, index));
              }
              buffer = buffer.slice(index);
              return getResult();
            }
            if (pass) {
              pushResult(buffer.slice(0, index));
            }
            buffer = buffer.slice(index + endLength);
            ignore = false;
            pass = false;
          } else {
            var part;
            var ctnIndex;
            var name;
            if (isMatched) {
              part = buffer.slice(0, index);
              ctnIndex = part.indexOf(UPLOAD_CTN_SEP);
              if (ctnIndex !== -1) {
                name = getName(buffer.slice(0, ctnIndex) + '');
                if (name != null && (name in params)) {
                  part = toMultipart(name, params[name]);
                  params[name] = undefined;
                }
              }
              pushResult(part, true);
              buffer = buffer.slice(index + endLength);
            } else {
              ctnIndex = buffer.indexOf(UPLOAD_CTN_SEP);
              if (ctnIndex !== -1) {
                name = getName(buffer.slice(0, ctnIndex) + '');
                pass = name == null || !(name in params);
                index = -endLength + 1;
                if (pass) {
                  pushResult(buffer.slice(0, index), true);
                } else {
                  pushResult(toMultipart(name, params[name]), true);
                  params[name] = undefined;
                  ignore = true;
                }
                buffer = buffer.slice(index);
              } else {
                if (buffer.length > MAX_HEADER_SIZE) {
                  badMultipart = true;
                  pass = true;
                  pushResult(buffer, true);
                }
                return getResult();
              }
            }
          }
        }
        if (pass && lastChunk) {
          pushResult(buffer);
        }
        return getResult();
      };

      var getCustomData = function() {
        var chunk = lastChunk ? getRestData() : null;
        return chunk && Buffer.concat([startBoundary, chunk, endBoudary]);
      };

      transform._transform = function (chunk, _, callback) {
        if (ended) {
          return callback();
        }
        if (badMultipart) {
          return callback(null, chunk);
        }

        lastChunk = !chunk;
        if (chunk && preBuffer !== null) {
          preBuffer = preBuffer ? Buffer.concat([preBuffer, chunk]) : chunk;
          if (!preBuffer || preBuffer.length <= length) {
            return callback(null, lastChunk ? preBuffer : null);
          }
          if (!util.startWithList(preBuffer, startBoundary)) {
            lastChunk = true;
            if (chunk = getCustomData()) {
              ended = true;
            } else {
              badMultipart = true;
              chunk = preBuffer;
            }
            return callback(null, chunk);
          }
          chunk = preBuffer.slice(length);
          preBuffer = null;
        }

        buffer = buffer && chunk ? Buffer.concat([buffer, chunk]) : (buffer || chunk);
        if (!buffer || buffer.length < minCtnLen) {
          return callback(null, getCustomData());
        }
        callback(null, getChunk());
      };
      req.addZipTransform(transform);
      hasBody = true;
    }
    var matcher = req.rules.params && req.rules.params.matcher;
    if (matcher && !matcher.indexOf(' params://')) {
      hasBody = true;
    }
  }
  var _params = hasBody ? null : params;
  if (_params || urlParams) {
    req._urlParams =
      urlParams && _params ? extend(_params, urlParams) : _params || urlParams;
  }
}

function handleReplace(req, replacement) {
  if (!util.hasRequestBody(req) || !replacement) {
    return;
  }

  var type = req.headers['content-type'];
  type = util.isUrlEncoded(req) ? 'FORM' : util.getContentType(type);
  if (!type || type == 'IMG') {
    return;
  }

  Object.keys(replacement).forEach(function (pattern) {
    var value = replacement[pattern];
    if (
      util.isOriginalRegExp(pattern) &&
      (pattern = util.toOriginalRegExp(pattern))
    ) {
      req.addTextTransform(new ReplacePatternTransform(pattern, value));
    } else if (pattern) {
      req.addTextTransform(new ReplaceStringTransform(pattern, value));
    }
  });
}

module.exports = function (req, res, next) {
  handleWeinre(req, res);
  handleLog(req, res);
  var reqRules = req.rules;
  var authObj = util.getAuthByRules(reqRules);
  var reqMerge = reqRules.params;

  util.parseRuleJson(
    [
      reqRules.reqHeaders,
      reqRules.reqCookies,
      authObj ? null : reqRules.auth,
      reqMerge,
      reqRules.reqCors,
      reqRules.reqReplace,
      reqRules.urlReplace,
      reqRules.urlParams
    ],
    function (
      headers,
      cookies,
      auth,
      params,
      cors,
      replacement,
      urlReplace,
      urlParams
    ) {
      var data = {};
      if (headers) {
        data.headers = extend(data.headers || {}, headers);
      }
      if (data.body && typeof data.body !== 'string') {
        try {
          data.body = JSON.stringify(data.body);
        } catch (e) {}
      }

      if (data.headers) {
        data.headers = util.lowerCaseify(data.headers, req.rawHeaderNames);
        req._customHost = data.headers.host;
        req._customXFF = data.headers[clientIpKey];
        req._customClientId = data.headers[config.CLIENT_ID_HEADER];
        if (typeof data.headers['content-type'] !== 'string') {
          delete data.headers['content-type'];
        }
      }

      if (reqRules.method) {
        var method = util.getMatcherValue(reqRules.method);
        data.method = method;
      }

      if (reqRules.reqCharset) {
        data.charset = util.getMatcherValue(reqRules.reqCharset);
      }

      if (reqRules.referer) {
        var referer = util.getMatcherValue(reqRules.referer);
        util.setHeader(data, 'referer', referer);
      }

      if (reqRules.ua) {
        var ua = util.getMatcherValue(reqRules.ua);
        util.setHeader(data, 'user-agent', ua);
      }

      var reqSpeed = util.getMatcherValue(reqRules.reqSpeed);
      reqSpeed = reqSpeed && parseFloat(reqSpeed);
      if (reqSpeed > 0) {
        data.speed = reqSpeed;
      }
      var cookie = data.headers && data.headers.cookie;
      if (typeof cookie !== 'string') {
        if (Array.isArray(cookie)) {
          cookie = cookie.join('; ');
        } else {
          cookie = req.headers.cookie;
        }
      }
      util.setReqCookies(data, cookies, cookie, req);
      handleAuth(data, auth || authObj);
      util.setReqCors(data, cors);
      req.method = util.getMethod(data.method || req.method);
      var bodyList = [
        reqRules.reqBody,
        reqRules.reqPrepend,
        reqRules.reqAppend
      ];
      util.getRuleValue(
        bodyList,
        function (reqBody, reqPrepend, reqAppend) {
          if (reqBody != null) {
            data.body = reqBody || util.EMPTY_BUFFER;
          }

          if (reqPrepend) {
            data.top = reqPrepend;
          }

          if (reqAppend) {
            data.bottom = reqAppend;
          }
          var delType = {};
          var dProps = util.parseDelQuery(req, delType);
          var queryProps = dProps.query;
          var pathProps = dProps.paths;
          handleReq(req, data, reqRules, delType);
          handleParams(req, params, urlParams, reqMerge && reqMerge.lineProps.enableBigData);
          if (req._urlParams || urlReplace || pathProps || queryProps || req._delQueryString) {
            var options = req.options;
            var isUrl = util.isUrl(options.href);
            var newUrl = isUrl ? options.href : req.fullUrl;
            if (req._urlParams) {
              newUrl = util.replaceUrlQueryString(newUrl, req._urlParams);
            }
            newUrl = util.parsePathReplace(newUrl, urlReplace, pathProps) || newUrl;
            newUrl = util.deleteQuery(newUrl, queryProps, req._delQueryString);
            if (newUrl !== options.href) {
              if (isUrl) {
                req.options = util.parseUrl(newUrl);
              } else {
                req._realUrl = newUrl;
              }
            }
          }
          util.removeUnsupportsHeaders(req.headers);
          util.disableReqProps(req);
          handleReplace(req, replacement);
          var reqWriter = util.hasRequestBody(req)
            ? util.getWriteFilePath(reqRules.reqWrite)
            : null;
          util.getFileWriters(
            [reqWriter, util.getWriteFilePath(reqRules.reqWriteRaw)],
            function (writer, rawWriter) {
              if (writer) {
                req.addZipTransform(
                  new FileWriterTransform(writer, req, false, false, true)
                );
              }
              if (rawWriter) {
                req.addZipTransform(
                  new FileWriterTransform(rawWriter, req, true, false, true)
                );
              }
              pluginMgr.postStats(req);
              next();
            },
            util.isEnable(req, 'forceReqWrite')
          );
        },
        !util.hasRequestBody(req.method),
        null,
        null,
        req
      );
    },
    req
  );
};

```

### lib/plugins/get-plugins-sync.js
```
var path = require('path');
var fs = require('fs');
var util = require('../util');
var pluginUtil = require('./util');
var mp = require('./module-paths');
var config = require('../config');
var common = require('../util/common');

var CUSTOM_PLUGIN_PATH = config.CUSTOM_PLUGIN_PATH;
var customPluginPaths = config.customPluginPaths || [];
var notUninstallPluginPaths = config.notUninstallPluginPaths || [];
var projectPluginPaths = config.projectPluginPaths || [];
var accountPluginsPath = config.accountPluginsPath || [];
var paths = mp.getPaths();

function getMTimeSync(filePath) {
  var stats = common.getStatSync(filePath);
  return stats &&stats.isFile() ? stats.mtime.getTime() : null;
}

function readPluginModulesSync(dir, plugins) {
  var isAccount = accountPluginsPath.indexOf(dir) !== -1;
  var account = isAccount ? config.account : undefined;
  var isSys = isAccount || CUSTOM_PLUGIN_PATH === dir || customPluginPaths.indexOf(dir) !== -1;
  var isProj = projectPluginPaths.indexOf(dir) !== -1;
  var notUn = notUninstallPluginPaths.indexOf(dir) !== -1;

  try {
    var list = fs.readdirSync(dir).filter(function (name) {
      if (pluginUtil.isWhistleModule(name)) {
        return true;
      }

      if (pluginUtil.isOrgModule(name)) {
        try {
          var _dir = path.join(dir, name);
          var org = name;
          fs.readdirSync(_dir).forEach(function (name) {
            if (pluginUtil.isWhistleModule(name)) {
              var root = isSys ? pluginUtil.getSysPathSync(_dir, name, org) : path.join(_dir, name);
              var mtime = getMTimeSync(path.join(root, 'package.json'));
              if (mtime != null) {
                var old = plugins[name];
                if (!old || (mtime > old.mtime && root === old.root)) {
                  plugins[name] = {
                    mtime: mtime,
                    root: root,
                    account: account,
                    dir: config.whistleName,
                    isSys: isSys,
                    notUn: notUn,
                    isProj: isProj
                  };
                }
              }
            }
          });
        } catch (e) {}
      }
      return false;
    });

    list.forEach(function (name) {
      var root = isSys ? pluginUtil.getSysPathSync(dir, name) : path.join(dir, name);
      var mtime = getMTimeSync(path.join(root, 'package.json'));
      if (mtime != null) {
        var old = plugins[name];
        if (!old || (mtime > old.mtime && root === old.root)) {
          plugins[name] = {
            root: root,
            mtime: mtime,
            account: account,
            dir: config.whistleName,
            isSys: isSys,
            notUn: notUn,
            isProj: isProj
          };
        }
      }
    });
  } catch (e) {}

  return plugins;
}

module.exports = function () {
  var plugins = pluginUtil.readDevPluginsSync();
  paths.forEach(function (dir) {
    readPluginModulesSync(dir, plugins);
  });

  var _plugins = {};
  Object.keys(plugins).forEach(function (name) {
    var simpleName = pluginUtil.getPluginName(name);
    if (pluginUtil.excludePlugin(simpleName)) {
      return;
    }
    var dir = plugins[name];
    var account = dir.account;
    var isSys = dir.isSys;
    var isProj = dir.isProj;
    var notUn = dir.notUn;
    var isDev = dir.isDev;
    var dirName = dir.dir;
    var mtime = dir.mtime;
    dir = dir.root;
    var pkgPath = path.join(dir, 'package.json');
    var pkg = common.readJsonSync(pkgPath);
    if (!pkg) {
      return;
    }
    if (!pkg.version || !pluginUtil.isPluginName(pkg.name)) {
      try {
        fs.renameSync(pkgPath, pkgPath + '.' + Date.now());
      } catch (e) {}
      return;
    }
    try {
      var conf = pkg.whistleConfig || '';
      var tabs = util.getInspectorTabs(conf);
      var hintList = util.getHintList(conf);
      var plugin = {
        account: account,
        dir: dirName,
        isSys: isSys,
        isDev: isDev,
        isProj: isProj,
        noOpt: !!(conf.noOption || conf.notOption || conf.disableOption|| conf.disabledOption),
        notUn: notUn,
        moduleName: pkg.name,
        enableAuthUI: !!conf.enableAuthUI,
        inheritAuth: !!conf.inheritAuth,
        updateUrl: util.getUpdateUrl(conf),
        tunnelKey: util.getTunnelKey(conf),
        staticDir: util.getStaticDir(conf),
        pluginVars: util.getPluginVarsConf(conf),
        networkColumn: util.getNetworkColumn(conf),
        webWorker: pluginUtil.readWorkerSync(dir, conf, simpleName),
        networkMenus: util.getPluginMenu(
            conf.networkMenus || conf.networkMenu,
            simpleName
          ),
        rulesMenus: util.getPluginMenu(
            conf.rulesMenus || conf.rulesMenu,
            simpleName
          ),
        valuesMenus: util.getPluginMenu(
            conf.valuesMenus || conf.valuesMenu,
            simpleName
          ),
        pluginsMenus:  util.getPluginMenu(
            conf.pluginsMenus || conf.pluginsMenu,
            simpleName
          ),
        reqTab: util.getCustomTab(tabs.req, simpleName),
        resTab: util.getCustomTab(tabs.res, simpleName),
        tab: util.getCustomTab(tabs, simpleName),
        toolTab: util.getCustomTab(conf.toolsTab || conf.toolTab, simpleName),
        comTab: util.getCustomTab(conf.composerTab, simpleName),
        pluginHomepage: pluginUtil.getPluginHomepage(pkg) || pluginUtil.getPluginHomepage(conf),
        openInPlugins: conf.openInPlugins ? 1 : undefined,
        openInModal: util.getPluginModal(conf),
        openExternal: conf.openExternal ? 1 : undefined,
        priority: parseInt(conf.priority, 10) || parseInt(pkg.pluginPriority, 10) || 0,
        rulesUrl: util.getCgiUrl(conf.rulesUrl),
        valuesUrl: util.getCgiUrl(conf.valuesUrl),
        installUrl: util.getCgiUrl(conf.installUrl),
        favicon: util.getCgiUrl(conf.favicon),
        installRegistry: util.getInstallRegistry(conf.installRegistry),
        hintUrl: hintList ? undefined : util.getCgiUrl(conf.hintUrl),
        hideShortProtocol: !!conf.hideShortProtocol,
        hideLongProtocol: !!conf.hideLongProtocol,
        hintList: hintList,
        registry: util.getRegistry(pkg),
        path: dir,
        mtime: mtime,
        version: pkg.version,
        description: pkg.description,
        homepage: pluginUtil.getHomePageFromPackage(pkg) || pluginUtil.getHomePageFromPackage(conf),
        rules: util.renderPluginRules(
            util.trim(util.readFileSync(path.join(dir, 'rules.txt'))),
            pkg,
            simpleName
          ),
        _rules: util.renderPluginRules(
            util.trim(util.readFileSync(path.join(dir, '_rules.txt'))) ||
              util.trim(util.readFileSync(path.join(dir, 'reqRules.txt'))),
            pkg,
            simpleName
          ),
        resRules: util.renderPluginRules(
            util.trim(util.readFileSync(path.join(dir, 'resRules.txt'))),
            pkg,
            simpleName
          )
      };

      plugin[util.PLUGIN_VALUES] = pluginUtil.parseValues(
          util.renderPluginRules(
            util.readFileSync(path.join(dir, '_values.txt')),
            pkg,
            simpleName
          ), simpleName);
      plugin[util.PLUGIN_MENU_CONFIG] = util.getPluginMenuConfig(conf);
      plugin[util.PLUGIN_INSPECTOR_CONFIG] =
          util.getPluginInspectorConfig(conf);
      _plugins[simpleName + ':'] = plugin;

    } catch (e) {}
  });

  return _plugins;
};

```

### lib/plugins/get-plugins.js
```
var path = require('path');
var pluginUtil = require('./util');
var mp = require('./module-paths');
var config = require('../config');
var common = require('../util/common');

var CUSTOM_PLUGIN_PATH = config.CUSTOM_PLUGIN_PATH;
var customPluginPaths = config.customPluginPaths || [];
var notUninstallPluginPaths = config.notUninstallPluginPaths || [];
var projectPluginPaths = config.projectPluginPaths || [];
var accountPluginsPath = config.accountPluginsPath || [];

function readPluginRootList(dir, callback) {
  var roots = [];
  pluginUtil.readDir(dir, function (_, list) {
    if (!list || !list.length) {
      return callback(roots);
    }
    var handleCallback = function () {
      var orgRoots = [];
      roots = roots.filter(function (obj) {
        if (!Array.isArray(obj)) {
          return obj;
        }
        orgRoots.push.apply(orgRoots, obj);
      });
      callback(orgRoots.concat(roots));
    };
    var count = 0;
    list.forEach(function (name, i) {
      if (pluginUtil.isWhistleModule(name)) {
        roots[i] = {
          name: name,
          dir: dir
        };
      } else if (pluginUtil.isOrgModule(name)) {
        ++count;
        pluginUtil.readDir(path.join(dir, name), function (_, list2) {
          if (list2 && list2.length) {
            var orgList;
            list2.forEach(function (pluginName) {
              if (pluginUtil.isWhistleModule(pluginName)) {
                orgList = orgList || [];
                orgList.push({
                  org: name,
                  name: pluginName,
                  dir: dir
                });
              }
            });
            roots[i] = orgList;
          }
          if (--count === 0) {
            count = -1;
            handleCallback(roots);
          }
        });
      }
    });
    if (count === 0) {
      count = -1;
      handleCallback(roots);
    }
  });
}

function readPluginModules(dir, callback, plugins, i
... [truncated, file is 4602 chars]
```

### lib/plugins/load-plugin.js
[omitted: context budget exhausted]

### lib/plugins/module-paths.js
[omitted: context budget exhausted]

### lib/plugins/util.js
[omitted: context budget exhausted]

### lib/rules/dns.js
[omitted: context budget exhausted]

### lib/rules/rules.js
[omitted: context budget exhausted]

### lib/service/composer.js
[omitted: context budget exhausted]

### lib/service/service.js
[omitted: context budget exhausted]

### lib/service/util.js
[omitted: context budget exhausted]

### lib/socket-mgr.js
[omitted: context budget exhausted]

### lib/util/common.js
[omitted: context budget exhausted]

### lib/util/index.js
[omitted: context budget exhausted]
Callers & Entry Points (How public input reaches the modified code)
### lib/plugins/index.js
```
var path = require('path');
var p = require('pfork');
var http = require('http');
var LRU = require('lru-cache');
var extend = require('extend');
var EventEmitter = require('events').EventEmitter;
var pluginMgr = new EventEmitter();
var colors = require('colors/safe');
var util = require('../util');
var logger = require('../util/logger');
var pluginUtil = require('./util');
var config = require('../config');
var getPluginsSync = require('./get-plugins-sync');
var getPlugin = require('./get-plugins');
var rulesMgr = require('../rules');
var properties = require('../rules/util').properties;
var httpMgr = require('../util/http-mgr');
var protocols = require('../rules/protocols');
var common = require('../util/common');
var mp = require('./module-paths');
var createSharedStorage = require('../plugins/shared-storage');

var Rules = rulesMgr.Rules;
var getPluginName = pluginUtil.getPluginName;
var encodeURIComponent = util.encodeURIComponent;
var RULES_TPL_RE = /^[^\n\r\S]*(``)[^\n\r\S]*((?:_?var(\.[^\s=]+)?|whistle|rule)\.tpl)[^\n\r\S]*[\r\n]([\s\S]+?)[\r\n][^\n\r\S]*\1\s*$/gm;
var REMOTE_RULES_RE =
  /^\s*@(`?)([\w.-]+(?:[\\/][^\s#]*)?|(?:https?:\/\/|[a-z]:[\\/]|~?\/)[^\s#]+|\$(?:whistle\.)?[a-z\d_-]+[/:][^\s#]+)\s*?\1(?:#.*)?$/gim;
var PLUGIN_MAIN = path.join(__dirname, './load-plugin');
var PIPE_PLUGIN_RE =
  /^pipe:\/\/(?:whistle\.|plugin\.)?([a-z\d_\-]+)(?:\(([\s\S]*)\))?$/;
var JSON_RE = /^\{[\s\S]+\}$/;
var ETAG_HEADER = 'x-whistle-etag';
var MAX_AGE_HEADER = 'x-whistle-max-age';
var STATUS_ERR = new Error('Non 200');
var INTERVAL = 6000;
var CHECK_INTERVAL = 1000 * 60 * 60 * 2;
var MAX_CERT_SIZE = 72 * 1024;
var portsField = Symbol('ports');
var notLoadPlugins = config.networkMode || config.rulesOnlyMode;
var allPlugins = notLoadPlugins ? {} : getPluginsSync();
var authPlugins = [];
var tunnelKeys = [];
var LOCALHOST = '127.0.0.1';
var MAX_RULES_LENGTH = 1024 * 256;
var rulesCache = new LRU({ max: 36 });
var PLUGIN_HOOKS = config.PLUGIN_HOOKS;
var PLUGIN_HOOK_NAME_HEADER = config.PLUGIN_HOOK_NAME_HEADER;
var conf = {};
var EXCLUDE_CONF_KEYS = {
  uid: 1,
  WEBUI_HEAD: 1,
  COMPOSER_CLIENT_ID_HEADER: 1,
  DISABLE_RULES_HEADER: 1,
  WHISTLE_POLICY_HEADER: 1,
  CLIENT_IP_HEADER: 1,
  HTTPS_FIELD: 1,
  CLIENT_PORT_HEADER: 1,
  CLIENT_ID_HEADER: 1,
  FROM_COM_HEADER: 1,
  ALPN_PROTOCOL_HEADER: 1
};
var EXCLUDE_NAMES = {
  password: 1,
  shadowRules: 1,
  rules: 1,
  values: 1
};
var debugMode = config.debugMode;
var proxy;
var REGISTRY_LIST = path.join(common.getDefaultWhistlePath(), '.registry.list');
var MAX_REG_COUNT = 100;
var storage = createSharedStorage(REGISTRY_LIST);
var registryList = filterRegList(common.readJsonSync(REGISTRY_LIST));

function filterRegList(l) {
  if (!Array.isArray(l)) {
    l = [];
  }
  return l.filter(function(url) {
    return common.getRegistry(url);
  }).slice(0, MAX_REG_COUNT);
}

function readRegList() {
  common.readJson(REGISTRY_LIST, function(e, list) {
    if (!e) {
      registryList = filterRegList(list);
    }
  });
}

if (notLoadPlugins) {
  getPlugin = function (cb) {
    cb({});
  };
}

pluginMgr.addRegistry = function(registry) {
  registry = common.getRegistry(registry);
  if (registry && registryList.indexOf(registry) === -1) {
    registryList.push(registry);
    storage.setAll(registryList);
  }
};

/*eslint no-console: "off"*/
Object.keys(config).forEach(function (name) {
  if (EXCLUDE_NAMES[name]) {
    return;
  }
  var value = config[name];
  if (name === 'passwordHash') {
    conf.password = value;
  }
  if (name === 'globalData') {
    conf.globalData = value;
  } else if (!EXCLUDE_CONF_KEYS[name]) {
    var type = typeof value;
    if (type == 'string' || type == 'number' || type === 'boolean') {
      conf[name] = value;
    }
  }
});
conf.client = config.client;
conf.PLUGIN_HOOKS = config.PLUGIN_HOOKS;
conf.uiHostList = config.uiHostList;
var pluginHostMap = config.pluginHostMap;
var pluginHosts = (conf.pluginHosts = {});
if (pluginHostMap) {
  Object.keys(pluginHostMap).forEach(function (host) {
    var name = pluginHostMap[host];
    var list = (pluginHosts[name] = pluginHosts[name] || []);
    list.push(host);
  });
}

pluginMgr.REGISTRY_LIST = REGISTRY_LIST;

pluginMgr.getPluginsPath = mp.getPaths;

pluginMgr.getRegistryList = function() {
  return registryList;
};

pluginMgr.disableAllPlugins = function(disabled) {
  properties.set('disabledAllPlugins', disabled);
  pluginMgr.emit('updateRules', 'disableAllPlugins');
};

pluginMgr.getTunnelKeys = function () {
  return tunnelKeys;
};

var MAX_REMOTE_RULES_COUNT = 3;

pluginMgr.on('updateRules', function (byParse) {
  rulesMgr.clearAppend();
  authPlugins = [];
  tunnelKeys = [];
  var ruleTpls;
  Object.keys(allPlugins)
    .sort(function (a, b) {
      var p1 = allPlugins[a];
      var p2 = allPlugins[b];
      return (
        util.compare(p1.priority, p2.priority) ||
        util.compare(p2.mtime, p1.mtime) ||
        (a > b ? 1 : 0)
      );
    })
    .forEach(function (name) {
      if (pluginIsDisabled(name.slice(0, -1))) {
        return;
      }
      var plugin = allPlugins[name];
      var rules = plugin.rules;
      if (plugin.enableAuthUI) {
        authPlugins.push(plugin);
      }
      if (plugin.tunnelKey) {
        plugin.tunnelKey.forEach(function (key) {
          if (tunnelKeys.indexOf(key) === -1) {
            tunnelKeys.push(key);
          }
        });
      }
      if (rules) {
        var root = plugin.path;
        var index = 0;
        rules = rules.replace(REMOTE_RULES_RE, function (_, apo, rulesUrl) {
          if (index >= MAX_REMOTE_RULES_COUNT) {
            return '';
          }
          ++index;
          return util.getRemoteRules(apo, rulesUrl, root);
        });
        rules = rules.replace(RULES_TPL_RE, function (_, __, key, subVar, value) {
          ruleTpls = ruleTpls || {};
          var simpleName = name.slice(0, -1);
          var isPrivate = key[0] === '_';
          if (isPrivate || key[0] === 'v') {
            key = (isPrivate ? '_' : '') + '%' + simpleName + (subVar || '');
          } else if (key === 'whistle.tpl') {
            key = 'whistle.' + simpleName;
          } else {
            key = simpleName;
          }
          if (!ruleTpls[key]) {
            ruleTpls[key] = value;
          }
          return '';
        });
        rulesMgr.append(rules, plugin.path, true);
      }
    });
  pluginMgr.ruleTpls = ruleTpls;
  if (byParse !== true) {
    httpMgr.triggerChange();
    proxy.emit('pluginsChange');
  }
});

pluginMgr.updateRules = function() {
  pluginMgr.emit('updateRules');
};

pluginMgr.loadCert = function (req, plugin, callback) {
  loadPlugin(plugin, function (err, ports) {
    if (err || !ports || !ports.sniPort) {
      return callback();
    }
    if (!req.useSNI || req.isHttpsServer) {
      req._sniType = req.isHttpsServer ? '1' : '0';
    }
    var options = getOptions(req);
    options.maxLength = MAX_CERT_SIZE;
    options.headers[PLUGIN_HOOK_NAME_HEADER] = PLUGIN_HOOKS.SNI;
    options.port = ports.sniPort;
    addPluginVars(req, options.headers, {
      plugin: plugin,
      value: ''
    });
    requestPlugin(options, function (err, body, res) {
      if (err || res.statusCode !== 200) {
        return callback(err || STATUS_ERR);
      }
      if (!body) {
        return callback();
      }
      if (body === 'false') {
        return callback(false);
      }
      if (body === 'true') {
        return callback(true);
      }
      try {
        body = JSON.parse(body);
        if (
          !body ||
          !body.name ||
          !util.isString(body.key) ||
          !util.isString(body.cert)
        ) {
          return callback();
        }
        callback({
          key: body.key,
          cert: body.cert,
          name: body.name,
          mtime: body.mtime > 0 ? body.mtime : undefined
        });
      } catch (e) {
        callback(e);
      }
    });
  });
};

pluginMgr.on('update', function (result) {
  Object.keys(result).forEach(function (name) {
    pluginMgr.stopPlugin(result[name]);
  });
  readRegList();
});
pluginMgr.on('uninstall', function (result) {
  Object.keys(result).forEach(function (name) {
    pluginMgr.stopPlugin(result[name]);
  });
});

function formatMTime(mtime) {
  return '[' + (new Date(mtime).toLocaleTimeString()) + ']';
}

function showVerbose(oldData, newData) {
  if (!debugMode) {
    return;
  }
  var uninstallData, installData, updateData;
  Object.keys(oldData).forEach(function (name) {
    var oldItem = oldData[name];
    var newItem = newData[name];
    if (!newItem) {
      uninstallData = uninstallData || {};
      uninstallData[name] = oldItem;
    } else if (newItem.path != oldItem.path || newItem.mtime != oldItem.mtime) {
      updateData = updateData || {};
      updateData[name] = newItem;
    }
  });

  Object.keys(newData).forEach(function (name) {
    if (!oldData[name]) {
      installData = installData || {};
      installData[name] = newData[name];
    }
  });

  uninstallData &&
    Object.keys(uninstallData).forEach(function (name) {
      console.log(
        colors.red(
          formatMTime(uninstallData[name].mtime) +
            ' UNINSTALL ' + name.slice(0, -1)
        )
      );
    });
  installData &&
    Object.keys(installData).forEach(function (name) {
      console.log(
        colors.green(
          formatMTime(installData[name].mtime) +
            ' INSTALL ' + name.slice(0, -1)
        )
      );
    });
  updateData &&
    Object.keys(updateData).forEach(function (name) {
      console.log(
        colors.yellow(
          formatMTime(updateData[name].mtime) +
            ' UPDATE ' + name.slice(0, -1)
        )
      );
    });
}

function readReqRules(dir, callback) {
  pluginUtil.readFile(path.join(path.join(dir, '_rules.txt')), function (err, rulesText) {
    if (err) {
      pluginUtil.readFile(
        path.join(path.join(dir, 'reqRules.txt')),
        function (_, rulesText) {
          callback(util.trim(rulesText));
        }
      );
      return;
    }
    callback(util.trim(rulesText));
  });
}

function readPackages(obj, callback) {
  var _plugins = {};
  var count = 0;
  var callbackHandler = function () {
    if (--count <= 0) {
      callback(_plugins);
    }
  };
  Object.keys(obj).forEach(function (name) {
    var pkg = allPlugins[name];
    var newPkg = obj[name];
    if (!pkg || pkg.path != newPkg.path || pkg.mtime != newPkg.mtime) {
      ++count;
      common.readJson(path.join(newPkg.path, 'package.json'), function (_, result) {
        if (result && result.version && pluginUtil.isPluginName(result.name)) {
          var conf = result.whistleConfig || '';
          var tabs = util.getInspectorTabs(conf);
          var hintList = util.getHintList(conf);
          var simpleName = name.slice(0, -1);
          newPkg.enableAuthUI = !!conf.enableAuthUI;
          newPkg.noOpt = !!(conf.noOption || conf.notOption || conf.disableOption|| conf.disabledOption);
          newPkg.updateUrl = util.getUpdateUrl(conf);
          newPkg.inheritAuth = !!conf.inheritAuth;
          newPkg.tunnelKey = util.getTunnelKey(conf);
          newPkg.version = result.version;
          newPkg.staticDir = util.getStaticDir(conf);
          newPkg.priority =
            parseInt(conf.priority, 10) ||
            parseInt(result.pluginPriority, 10) ||
            0;
          newPkg.rulesUrl = util.getCgiUrl(conf.rulesUrl);
          newPkg.valuesUrl = util.getCgiUrl(conf.valuesUrl);
          newPkg.installUrl = util.getCgiUrl(conf.installUrl);
          newPkg.favicon = util.getCgiUrl(conf.favicon);
          newPkg.installRegistry = util.getInstallRegistry(conf.installRegistry);
          newPkg.networkColumn = util.getNetworkColumn(conf);
          newPkg.networkMenus = util.getPluginMenu(
            conf.networkMenus || conf.networkMenu,
            simpleName
          );
          newPkg.rulesMenus = util.getPluginMenu(
            conf.rulesMenus || conf.rulesMenu,
            simp
... [truncated]
```

### biz/webui/lib/index.js
```
var express = require('express');
var app = express();
var path = require('path');
var http = require('http');
var https = require('https');
var parseReqUrl = require('parseurl');
var bodyParser = require('body-parser');
var fs = require('fs');
var zlib = require('zlib');
var extend = require('extend');
var LRU = require('lru-cache');
var htdocs = require('../htdocs');
var handleWeinreReq = require('../../weinre');
var setProxy = require('./proxy');
var rulesUtil = require('../../../lib/rules/util');
var getRootCAFile = require('../../../lib/https/ca').getRootCAFile;
var config = require('../../../lib/config');
var cgiUtil = require('../cgi-bin/util');
var common = require('../../../lib/util/common');
var getWorker = require('../../../lib/plugins/util').getWorker;
var loadAuthPlugins = require('../../../lib/plugins').loadAuthPlugins;
var parseUrl = require('../../../lib/util/parse-url-safe');
var loadService = require('../../../lib/service');

var sendError = cgiUtil.sendError;
var sendGzipText = cgiUtil.sendGzipText;
var parseAuth = common.parseAuth;
var createHash = common.createHash;
var PARSE_CONF = { extended: true, limit: '3mb'};
var UPLOAD_PARSE_CONF = { extended: true, limit: '30mb'};
var PLUGIN_NAMES = new LRU({ max: 360 });
var urlencodedParser = bodyParser.urlencoded(PARSE_CONF);
var jsonParser = bodyParser.json(PARSE_CONF);
var uploadUrlencodedParser = bodyParser.urlencoded(UPLOAD_PARSE_CONF);
var uploadJsonParser = bodyParser.json(UPLOAD_PARSE_CONF);
var GET_METHOD_RE = /^get$/i;
var WEINRE_RE = /^\/weinre\/.*/;
var ALLOW_PLUGIN_PATHS = ['/cgi-bin/rules/list2', '/cgi-bin/values/list2', '/cgi-bin/get-custom-certs-info'];
var SPECIAL_PATHS = ['/cgi-bin/rules/project'];
var DONT_CHECK_PATHS = ['/cgi-bin/server-info', '/cgi-bin/plugins/is-enable', '/cgi-bin/plugins/get-plugins',
  '/preview.html', '/cgi-bin/rootca', '/cgi-bin/check-update', '/cgi-bin/log/set', '/cgi-bin/status'];
var GUEST_PATHS = ['/cgi-bin/composer', '/cgi-bin/socket/data', '/cgi-bin/abort', '/cgi-bin/socket/abort',
  '/cgi-bin/socket/change-status', '/cgi-bin/sessions/export'];
var CORS_PATHS = ['/cgi-bin/status',  '/cgi-bin/rootca'];
var PLUGIN_PATH_RE = /^\/(whistle|plugin)\.([^/?#]+)(\/)?/;
var STATIC_SRC_RE = /\.(?:ico|js|css|png)$/i;
var UPLOAD_URLS = ['/cgi-bin/values/upload', '/cgi-bin/composer', '/cgi-bin/download'];
var ALLOW_CROSS_URLS = ['/cgi-bin/top', '/cgi-bin/status', '/cgi-bin/server-info',
    '/cgi-bin/rootca', '/cgi-bin/check-update', '/cgi-bin/log/set'];
var proxyEvent, util, pluginMgr;
var MAX_AGE = 60 * 60 * 24 * 3;
var MENU_HTML = fs.readFileSync(path.join(__dirname, '../../../assets/menu.html'));
var INSPECTOR_HTML = fs.readFileSync(path.join(__dirname, '../../../assets/tab.html'));
var MODAL_HTML = fs.readFileSync(path.join(__dirname, '../../../assets/modal.html'));
var MENU_URL = '???_WHISTLE_PLUGIN_EXT_CONTEXT_MENU_' + config.port + '???';
var INSPECTOR_URL = '???_WHISTLE_PLUGIN_INSPECTOR_TAB_' + config.port + '???';
var KEY_RE_G = /\${[^{}\s]+}|{\S+}/g;
var COMMENT_RE = /#[^\r\n]*$/mg;
var MAX_LEN = 1024 * 1024 * 6;
var HTTP_RE = /https?:\/\/\S/i;

function hasLogin() {
  return config.username && config.password;
}

function isTempFile(query) {
  var files = query.files;
  if (files && typeof files === 'string') {
    return false;
  }
  return common.getTempFile(query.filename);
}

function sendToService(req, res) {
  if (!hasLogin() && req.path === '/cgi-bin/temp/get' && !isTempFile(req.query)) {
    res.setHeader('Content-Type', 'application/json; charset=utf-8');
    res.end('{"ec":0,"value":"","forbidden":true}');
    return;
  }
  loadService(function(err, options) {
    if (err) {
      common.sendRes(res, 500, err.stack || err);
    } else {
      req.headers[common.WHISTLE_UID_HEADER] = config.uid;
      util.transformReq(req, res, options.port);
    }
  });
}

function doNotCheckLogin(req) {
  var path = req.path;
  return STATIC_SRC_RE.test(path) || DONT_CHECK_PATHS.indexOf(path) !== -1;
}

function getUsername() {
  return config.username || '';
}

function getPassword() {
  return config.password || '';
}

function parseCookie(str) {
  var result = {};
  str && str.split(';').forEach(function(pair) {
    var index = pair.indexOf('=');
    if (index === -1) {
      return;
    }
    var key = pair.substring(0, index).trim();
    var val = pair.substring(index + 1).trim();
    if (result[key] == null) {
      try {
        result[key] = decodeURIComponent(val);
      } catch (e) {
        result[key] = val;
      }
    }
  });
  return result;
}

function getLoginKey (req, res, auth) {
  var ip = util.getClientIp(req);
  var password = auth.password;
  if (config.encrypted) {
    password = createHash(password);
  }
  return createHash([auth.username, password, ip].join('\n'));
}

function requireLogin(req, res, msg) {
  if (config.client) {
    if (config.handleWebReq) {
      return config.handleWebReq(req, res);
    }
    return res.status(404).end();
  }
  res.setHeader('WWW-Authenticate', ' Basic realm=User Login');
  res.setHeader('Content-Type', 'text/html; charset=utf8');
  res.status(401).end(msg || 'Access denied, please <a href="javascript:;" onclick="location.reload()">try again</a>');
}

function equalAuth(auth, src) {
  return auth.name === src.username && auth.pass === src.password;
}

function verifyLogin(req, res, auth) {
  var isGuest = !auth;
  if (isGuest) {
    auth = config.guest;
    if (!auth) {
      return;
    }
    if (!auth.authKey) {
      auth.authKey = 'whistle_v_lk_' + encodeURIComponent(auth.username);
    }
  }
  var username = auth.username;
  var password = auth.password;

  if (!username && !password) {
    return true;
  }
  var authKey = auth.authKey;
  var cookies = parseCookie(req.headers.cookie);
  var lkey = cookies[authKey];
  var correctKey = getLoginKey(req, res, auth);
  if (correctKey === lkey) {
    return true;
  }
  var headerAuth = parseAuth(req.headers.authorization || req.headers['proxy-authorization']);
  var queryAuth = parseAuth(req.query.authorization);
  if (!isGuest && config.encrypted) {
    headerAuth.pass = headerAuth.pass && createHash(headerAuth.pass);
    queryAuth.pass = queryAuth.pass && createHash(queryAuth.pass);
  }
  if (equalAuth(headerAuth, auth) || equalAuth(queryAuth, auth)) {
    res.setHeader('Set-Cookie', [
      authKey + '=' + util.encodeURIComponent(correctKey),
      'Max-Age=' + MAX_AGE,
      'Path=/',
      'Expires=' + new Date(Date.now() + (MAX_AGE * 1000)).toUTCString()
    ].join('; '));
    return true;
  }
}

function checkAuth(req, res) {
  var username = getUsername();
  var auth = {
    authKey: 'whistle_lk_' + encodeURIComponent(username),
    username: username,
    password: getPassword()
  };
  if (verifyLogin(req, res, auth)) {
    return true;
  }
  if (config.specialAuth && SPECIAL_PATHS.indexOf(req.path) !== -1 &&
    config.specialAuth === req.headers['x-whistle-special-auth']) {
    return true;
  }
  requireLogin(req, res);
  return false;
}

app.disable('x-powered-by');

function readRemoteStream(req, res, authUrl) {
  var client;
  var handleError = function(err) {
    res.emit('error', err);
    client && client.destroy();
  };
  if (authUrl[0] === 'f') {
    var stream = fs.createReadStream(authUrl.substring(7));
    stream.on('error', handleError);
    return stream.pipe(res);
  }
  var options = parseUrl(authUrl);
  options.rejectUnauthorized = false;
  var httpModule = options.protocol === 'https:' ? https : http;
  var headers = extend({}, req.headers);
  delete headers.host;
  options.headers = headers;
  client = httpModule.request(options, function(svrRes) {
    svrRes.on('error', handleError);
    res.writeHead(svrRes.statusCode, svrRes.headers);
    svrRes.pipe(res);
  });
  client.on('error', handleError);
  client.end();
}

function injectFile(req, res, filepath, prepend, append, isJs) {
  fs.readFile(filepath, function(err, ctn) {
    if (err) {
      return sendError(res, err);
    }
    sendGzipText(req, res, {
      'Content-Type': (isJs ? 'application/javascript' : 'text/html') + '; charset=utf-8'
    }, concat(prepend, ctn, append));
  });
}

app.use(function(req, res, next) {
  proxyEvent.emit('_request', req.url);
  var aborted;
  var abort = function() {
    if (!aborted) {
      aborted = true;
      res.destroy();
    }
  };
  req.on('error', abort);
  res.on('error', abort).on('close', abort);
  loadAuthPlugins(req, function(status, msg, authUrl) {
    if (!status && !authUrl) {
      return next();
    }
    res.set('x-server', 'whistle');
    res.set('x-module', 'webui');
    if (!msg && !authUrl) {
      return res.redirect(status);
    }
    if (status === 401) {
      return requireLogin(req, res, msg);
    }
    res.set('Content-Type', 'text/html; charset=utf8');
    if (authUrl) {
      return readRemoteStream(req, res, authUrl);
    }
    if (status === 502) {
      return res.status(502).end(msg || 'Error');
    }
    res.status(403).end(msg || 'Forbidden');
  });
});

if (typeof config.uiMiddleware === 'function') {
  app.use(config.uiMiddleware);
}

app.use(function(req, res, next) {
  var referer = req.headers.referer;
  var options = parseReqUrl(req);
  var path = options.path;
  var index = path.indexOf('/whistle/');
  req.url = path;
  if (index === 0) {
    delete req.headers.referer;
    req.url = path.substring(8);
  } else if (PLUGIN_PATH_RE.test(options.pathname)) {
    var pluginName = RegExp['$&'];
    var len = pluginName.length - 1;
    if (len === index) {
      delete req.headers.referer;
      req.url = path.substring(len + 8);
    }
  } else {
    pluginName = config.getPluginNameByHost(req.headers.host);
    if (!pluginName) {
      if (referer) {
        var refOpts = parseUrl(referer);
        var pathname = refOpts.pathname;
        if (PLUGIN_PATH_RE.test(pathname) && RegExp.$3) {
          var name = RegExp.$2;
          req.url = '/' + RegExp.$1 + '.' + name + path;
          PLUGIN_NAMES.set(path, name);
        } else {
          pluginName = config.getPluginNameByHost(refOpts.hostname);
        }
      } else {
        pluginName = PLUGIN_NAMES.get(path);
      }
    }
    if (pluginName) {
      req.url = '/plugin.' + pluginName + path;
    }
  }

  next();
});

app.use(function(req, res, next) {
  if (req.headers.host !== 'rootca.pro') {
    return next();
  }
  var type = 'cer';
  if (!req.path.indexOf('/crt')) {
    type = 'crt';
  } else if (!req.path.indexOf('/pem')) {
    type = 'pem';
  }
  res.download(getRootCAFile(), 'rootCA.' + type);
});

function isAllowHost(host) {
  var list = config.allowOrigin;
  if (list) {
    for (var i = 0, len = list.length; i < len; i++) {
      var h = list[i];
      if (typeof h === 'string' ? host === h : h.test(host)) {
        return true;
      }
    }
  }
}

function checkInternalPath(req) {
  if (config.allowAllOrigin || ALLOW_CROSS_URLS.indexOf(req.path) !== -1) {
    return true;
  }
  var host = req.headers[common.ORIGIN_HOST_HEADER];
  return !host || isAllowHost(host);
}

function checkAllowOrigin(req) {
  var host = req.headers.origin;
  if (!host || typeof host !== 'string' ||
    req.headers['sec-fetch-site'] === 'same-origin') {
    return false;
  }
  if (config.allowAllOrigin) {
    return true;
  }
  if (CORS_PATHS.indexOf(req.path) !== -1) {
    return true;
  }
  if (!config.allowOrigin) {
    return false;
  }
  var index = host.indexOf('://');
  if (index !== -1) {
    host = host.substring(index + 3);
  }
  host = util.parseHost(host)[0];
  return host && isAllowHost(host);
}

function cgiHandler(req, res) {
  if (common.existsUpPath(req.path) || !checkInternalPath(req)) {
    return res.status(403).end('Forbidden');
  }
  if (checkAllowOrigin(req)) {
    res.setHeader('access-control-allow-origin', req.headers.origin);
    res.setHeader('access-control-allow-credentials', true);
  }
  var filepath = path.join(__dirname, '..' + req.path) + '.js';
  var handleResponse = function() {
    try {
      require(filepath)(req
... [truncated]
```

### lib/tunnel.js
```
var socks = require('sockx');
var parseUrl = require('./util/parse-url-safe');
var net = require('net');
var extend = require('extend');
var LRU = require('lru-cache');
var EventEmitter = require('events').EventEmitter;
var hparser = require('hparser');
var dispatch = require('./https');
var util = require('./util');
var rules = require('./rules');
var socketMgr = require('./socket-mgr');
var rulesUtil = require('./rules/util');
var common = require('./util/common');
var ca = require('./https/ca');
var pluginMgr = require('./plugins');
var config = require('./config');

var hasCustomCerts = ca.hasCustomCerts;
var existsCustomCert = ca.existsCustomCert;
var IP_CACHE = new LRU({ max: 600 });
var LOCALHOST = '127.0.0.1';
var X_RE = /^x/;
var STATUS_CODES = require('http').STATUS_CODES || {};
var getRawHeaderNames = hparser.getRawHeaderNames;
var formatHeaders = hparser.formatHeaders;
var getRawHeaders = hparser.getRawHeaders;
var CRONET_RE = /\bCronet\b/;
var SYS_HOST_RE = /^(?:[^/:]+\.)?(?:apple|cdn-apple|icloud|office|office365|mzstatic|apple-cloudkit|microsoft|parallels)\.(?:com|cn|com\.cn)$/;
var TUNNEL_RE = /^tunnel:\/\//;
var clientIpKey = config.CLIENT_IP_HEADER;

function emitAborted(data, reqEmitter, code) {
  data.reqError = true;
  data.res.statusCode = code || 'aborted';
  data.req.body = 'aborted';
  reqEmitter.emit('abort', data);
}

function tunnelProxy(server, proxy, type) {
  proxy.getTunnelIp = function (id) {
    return IP_CACHE.get(id);
  };
  var fromHttpServer = type === 2;
  var fromHttpsServer = type === 1;
  server.on('connect', function (req, reqSocket) {
    //ws, wss, https proxy
    var headers = req.headers;
    if (headers[config.WEBUI_HEAD]) {
      delete headers[config.WEBUI_HEAD];
      return reqSocket.destroy();
    }
    req.fromHttpServer = reqSocket.fromHttpServer = fromHttpServer;
    req.fromHttpsServer = reqSocket.fromHttpsServer = fromHttpsServer;
    var tunnelUrl = (req.fullUrl = util.setProtocol(
      util.isTunnelHost(req.url) ? req.url : headers.host,
      true
    ));
    var options;
    var socketErr;
    var _emitError;
    var _parseUrl = function (_url, port) {
      _url = _url || tunnelUrl;
      options = req.options = parseUrl(_url);
      var curPort = options.port;
      options.port = options.port || port || 443;
      if (!curPort && options.host) {
        if (options.host.indexOf(':') === -1) {
          options.host += ':' + options.port;
        } else if (net.isIPv6(options.host)) {
          options.host = '[' + options.host + ']:' + options.port;
        }
      }
      return options;
    };
    _parseUrl();
    tunnelUrl = req.fullUrl = 'tunnel://' + options.host;
    proxy.emit('_request', tunnelUrl);
    var resSocket, proxyClient, respond, reqEmitter, data, originPort;
    var reqData, resData, res, rollBackTunnel, buf;
    req.isTunnel = true;
    req.method = util.toUpperCase(req.method) || 'CONNECT';
    var clientInfo = util.parseClientInfo(req);
    reqSocket._disabledProxyRules = req._disabledProxyRules;
    reqSocket.clientIp = req.clientIp = util.getClientIp(req, clientInfo[0]);
    reqSocket.clientPort = req.clientPort = clientInfo[1] || util.getClientPort(req);
    req._remoteAddr = clientInfo[2] || util.getRemoteAddr(req);
    req._remotePort = clientInfo[3] || util.getRemotePort(req);
    delete headers[config.CLIENT_PORT_HEADER];
    var now = Date.now();
    req.reqId = reqSocket.reqId = util.getReqId(now);
    reqSocket.headers = headers;
    reqSocket.fromTunnel = req.fromTunnel;
    reqSocket.fromComposer = req.fromComposer;
    req.isPluginReq = reqSocket.isPluginReq = util.checkPluginReqOnce(req, true);
    util.onSocketEnd(reqSocket, function (err) {
      // 处理可能的证书校验出错
      if (config.captureData && !util.checkHideProp(req.enable || '', req.disable || '', 'CaptureError') && dispatch.getTunnelDataOnce(reqSocket)) {
        resData = {headers: {}};
        data = {
          id: req.reqId,
          url: options.host,
          fc: req.fromComposer ? 1 : undefined,
          startTime: now,
          dnsTime: now,
          captureError: true,
          rules: req.rules,
          req: {
            _clientId: util.getComposerClientId(headers),
            ip: req.clientIp,
            port: req.clientPort,
            method: req.method,
            httpVersion: req.httpVersion || '1.1',
            headers: headers,
            rawHeaderNames: getRawHeaderNames(req.rawHeaders) || {}
          },
          res: resData,
          isHttps: true
        };
        data.endTime = data.responseTime = data.requestTime = Date.now();
        reqEmitter = new EventEmitter();
        proxy.emit('request', reqEmitter, data);
        emitAborted(data, reqEmitter, 'captureError');
        pluginMgr.resolveWhistlePlugins(req);
        pluginMgr.postStats(req);
        pluginMgr.postStats(req, resData);
      }
      socketErr = err;
      if (req.isLogRequests) {
        --util.proc.tunnelRequests;
      }
      req.isLogRequests = false;
      if (_emitError) {
        _emitError(err);
      } else {
        reqSocket.destroy();
      }
    });
    var hostname = options.hostname;
    var isICloudDB = hostname === 'p22-ckdatabase.icloud.com';
    var isIPHost = !isICloudDB && net.isIP(hostname);
    var policy = headers[config.WHISTLE_POLICY_HEADER];
    var weakTunnel = policy == 'weakTunnel';
    var useTunnelPolicy = weakTunnel || policy == 'tunnel';
    var inspect = useTunnelPolicy;
    useTunnelPolicy = useTunnelPolicy || policy == 'connect';
    var enableTunnelAck =
      useTunnelPolicy && req.headers[common.ACK_HEADER];
    var isLocalUIUrl = !useTunnelPolicy && config.isLocalUIUrl(hostname);
    if (isLocalUIUrl ? isIPHost : util.isLocalHost(hostname)) {
      isLocalUIUrl =
        options.port == config.port || options.port == config.uiport;
    }
    var _rules = {};
    if (isICloudDB || isLocalUIUrl) {
      req.enable = req.disable = req._filters = _rules;
    } else {
      _rules = rules.initRules(req);
    }
    req.rules = reqSocket.rules = _rules;
    reqSocket._globalPluginVars = req._globalPluginVars;
    reqSocket.isLocalUIUrl = isLocalUIUrl;
    rules.resolveRulesFile(req, function () {
      var filter = req._filters;
      var disable = req.disable;
      var isDisabledProps = function() {
        return disable.intercept || disable.https || disable.capture;
      };
      var isDisableIntercept = function () {
        return (
          isICloudDB ||
          useTunnelPolicy ||
          isDisabledProps() ||
          (req.isPluginReq && policy !== 'capture')
        );
      };
      var isCustomIntercept = function () {
        return (
          filter.https ||
          filter.capture ||
          filter.intercept ||
          policy === 'intercept' ||
          policy === 'capture'
        );
      };
      var isWebPort =
        options.port == 80 || options.port == 443 || isCustomIntercept();
      var matchCustomCert;
      var isEnableIntercept = function () {
        if (isCustomIntercept()) {
          return true;
        }
        if (!rulesUtil.properties.isEnableCapture()) {
          matchCustomCert = !!existsCustomCert(hostname);
          return matchCustomCert;
        }
        var ua = headers['user-agent'];
        return ua ? !CRONET_RE.test(ua) : !SYS_HOST_RE.test(hostname);
      };
      var isIntercept = function () {
        if (isLocalUIUrl || ((!isDisableIntercept() && isEnableIntercept()) ||
          (weakTunnel && !isDisabledProps() && isCustomIntercept()))) {
          return true;
        }
        if (!isIPHost || !hasCustomCerts()) {
          return false;
        }
        reqSocket.useProxifier =
          (config.proxifier2 || (config.proxifier && isWebPort)) &&
          !disable.proxifier;
        return reqSocket.useProxifier;
      };
      var resolvedPlugin;
      if (isIntercept()) {
        if (util.isAuthCapture(req)) {
          req.justAuth = true;
          resolvedPlugin = true;
        }
      } else {
        resolvedPlugin = true;
      }
      var plugin = resolvedPlugin ? pluginMgr.resolveWhistlePlugins(req) : null;
      var handlePluginRules = function (_rulesMgr) {
        if (_rulesMgr) {
          req.pluginRules = _rulesMgr;
          req.curUrl = tunnelUrl;
          util.mergeRules(req, _rulesMgr.resolveReqRules(req));
          util.filterWeakRule(req);
          plugin = pluginMgr.getPluginByRuleUrl(util.rule.getUrl(_rules.rule));
        } else {
          util.filterWeakRule(req);
        }
        filter = req._filters;
        disable = req.disable;
      };
      if (req.whistlePlugins) {
        if (
          matchCustomCert ||
          (matchCustomCert == null && existsCustomCert(hostname))
        ) {
          req._existsCustomCert = true;
          req._enableCapture = true;
        } else if (isEnableIntercept()) {
          req._enableCapture = true;
        }
      }
      pluginMgr.getTunnelRules(req, function (_rulesMgr) {
        handlePluginRules(_rulesMgr);
        policy = headers[config.WHISTLE_POLICY_HEADER];
        if (!reqSocket._hasError && !req._authForbidden &&
          !req.fromComposer && (req._forceCapture || isIntercept())) {
          reqSocket.rulesHeaders = req.rulesHeaders;
          reqSocket.enable = req.enable;
          reqSocket.disable = req.disable;
          reqSocket.tunnelHostname = hostname;
          reqSocket.rules = _rules;
          reqSocket._pluginVars = req._pluginVars;
          dispatch(
            reqSocket,
            function (chunk) {
              if (
                isLocalUIUrl ||
                (isIPHost &&
                  util.isLocalAddress(hostname) &&
                  options.port == config.port)
              ) {
                return reqSocket.destroy();
              }
              buf = chunk;
              rollBackTunnel = true;
              ensureLoadRules();
            },
            !req.enable.socket && isWebPort
          );
          util.setEstablished(reqSocket);
          return;
        }

        ensureLoadRules();

        function ensureLoadRules() {
          if (!req.justAuth) {
            if (resolvedPlugin) {
              return handleTunnel();
            }
          } else {
            req.justAuth = false;
          }
          if (!resolvedPlugin) {
            plugin = pluginMgr.resolveWhistlePlugins(req);
          }
          pluginMgr.getTunnelRules(req, function (_rulesMgr2) {
            handlePluginRules(_rulesMgr2);
            handleTunnel();
          });
        }

        function handleTunnel() {
          if (req.isLogRequests !== false) {
            ++util.proc.tunnelRequests;
            ++util.proc.totalTunnelRequests;
            req.isLogRequests = true;
          }
          var reqRawHeaderNames = getRawHeaderNames(req.rawHeaders) || {};
          var enable = req.enable;
          inspect =
            inspect || util.isInspect(enable) || util.isCustomParser(req);
          reqData = {
            _clientId: util.getComposerClientId(headers),
            ip: req.clientIp,
            port: req.clientPort,
            method: req.method,
            httpVersion: req.httpVersion || '1.1',
            headers: headers,
            rawHeaderNames: reqRawHeaderNames
          };
          resData = { headers: {} };
          reqEmitter = new EventEmitter();
          data = {
            id: req.reqId,
            url: options.host,
            fc: req.fromComposer ? 1 : undefined,
            startTime: Date.now(),
            rules: _rules,
            req: reqData,
            res: resData,
            isHttps: true,
            inspect: inspect,
            rulesHeaders: req.rulesHeaders
          };
          if (util.showPluginReq(req) && !util.isHide(req)) {
            data.abort = emitError;
            if (req.isPluginReq) {
              data.isPR = 1;
            }
            proxy.emit('request', reqEmitter, data);
          }
          if (reqSocket
... [truncated]
```

### lib/rules/index.js
```
var Pac = require('node-pac');
var net = require('net');
var LRU = require('lru-cache');
var path = require('path');
var iconv = require('iconv-lite');
var parseUrl = require('../util/parse-url-safe');
var extend = require('extend');
var parseQuery = require('querystring').parse;
var lookup = require('./dns');
var Rules = require('./rules');
var rulesUtil = require('./util');
var util = require('../util');
var logger = require('../util/logger');
var fileMgr = require('../util/file-mgr');
var config = require('../config');


var values = rulesUtil.values;
var globalRules = rulesUtil.rules;
var tplCache = new LRU({ max: 36 });
var clientCerts = new LRU({ max: 60, maxAge: 1000 * 60 * 60 });
var rules = new Rules();
var tempRules = new Rules();
var cachedPacs = {};
var RULES_HEADER = 'x-whistle-rule-value';
var KV_HEADER = 'x-whistle-key-value';
var NAME_HEADER = 'x-whistle-rule-name';
var KEY_HEADER = 'x-whistle-rule-key';
var HOST_HEADER = 'x-whistle-rule-host';
var LOCALHOST = '127.0.0.1';
var resolveReqRules = rules.resolveReqRules.bind(rules);
var AUTH_RE = /^([^\\/]+)@/;
var PLUGIN_VAR_RE = /^[a-z\d_\-]+\./;
var COMMENT_RE = /^\s*#/;
var VALUE_RE = /^\s*``/m;
var BRACKET_RE = /[(\[]/;
var SCRIPT_RE = /\b(?:rules|values)\b/;
var SEP_CIPHER_RE = /[^a-z\d:!-]/i;
var CERT_RE = /^\s*-----/;

function isRulesContent(ctn) {
  return !BRACKET_RE.test(ctn) || COMMENT_RE.test(ctn) || VALUE_RE.test(ctn) || !SCRIPT_RE.test(ctn);
}

rules._isGlobal = true;

exports.Rules = Rules;
exports.getEnabledRules = function() {
  return rules._enabledList || [];
};
exports.getMFlag = function() {
  return rules._mflag;
};
exports.parse = rules.parse.bind(rules);
exports.append = rules.append.bind(rules);
exports.resolveSNICallback = rules.resolveSNICallback.bind(rules);
exports.resolveHost = rules.resolveHost.bind(rules);
exports.getGRuleList = rules.getGRuleList.bind(rules);
exports.resolveInternalHost = rules.resolveInternalHost.bind(rules);
exports.resolveProxy = rules.resolveProxy.bind(rules);
exports.resolveEnable = rules.resolveEnable.bind(rules);
exports.hasReqScript = rules.hasReqScript.bind(rules);
exports.resolveDisable = rules.resolveDisable.bind(rules);
exports.resolvePipe = rules.resolvePipe.bind(rules);
exports.resolveRule = rules.resolveRule.bind(rules);
exports.resolveResRules = rules.resolveResRules.bind(rules);
exports.resolveBodyFilter = rules.resolveBodyFilter.bind(rules);
exports.lookupHost = rules.lookupHost.bind(rules);
exports.resolveLocalRule = rules.resolveLocalRule.bind(rules);
exports.clearAppend = rules.clearAppend.bind(rules);
exports.resolveTplVar = Rules.resolveTplVar;

exports.disableDnsCache = function () {
  Rules.disableDnsCache();
};

var dnsResolve = function (host, callback) {
  return lookup(host, callback || util.noop, true);
};
var PROXY_HOSTS_RE = /[?&]proxyHosts?(?:&|$)/i;
var P_HOST_RE = /[?&]host=([\w.:-]+)(?:&|$)/i;

function isProxyHost(req, proxy, host) {
  if (proxy) {
    req._proxyTunnel =
      isLineProp(proxy, 'proxyTunnel') ||
      isLineProp(host, 'proxyTunnel') ||
      util.isEnable(req, 'proxyTunnel') ||
      isProxyEnable(req, 'proxyTunnel');
    if (isLineProp(proxy, 'proxyHost')) {
      return true;
    }
  }
  return isLineProp(host, 'proxyHost');
}

function isProxyEnable(req, name) {
  var props = req._proxyProps;
  if (props === undefined) {
    props = rules.resolveProxyProps(req);
    req._proxyProps = props || null;
  }
  return props && util.isEnable(props, name);
}

function isLineProp(rule, name) {
  return rule && rule.lineProps[name];
}

function resolveRulesFromList(list, fnName, req, options) {
  var rule;
  for (var i = 0, len = list.length; i < len; i++) {
    var mgr = list[i];
    var _rule = mgr && mgr[fnName](req, options);
    if (_rule) {
      if (util.isImportant(_rule)) {
        return _rule;
      }
      rule = rule || _rule;
    }
  }
  return rule;
}

exports.getProxy = function (url, req, callback) {
  if (!req) {
    return callback();
  }
  var reqRules = req.rules;
  req.curUrl = url;
  if (!reqRules) {
    return rules.lookupHost(req, callback);
  }

  delete reqRules.proxy;
  delete reqRules.pac;
  var pRules = req.pluginRules;
  var fRules = req.rulesFileMgr;
  var hRules = req.headerRulesMgr;
  var filter = extend(
    rules.resolveFilter(req),
    pRules && pRules.resolveFilter(req),
    fRules && fRules.resolveFilter(req),
    hRules && hRules.resolveFilter(req)
  );
  var ignoreProxy;
  var proxy;
  var pacRule;
  var host = rules.getHost(req, pRules, fRules, hRules);
  var hostValue = util.getMatcherValue(host) || '';
  if (config.multiEnv || req._headerRulesFirst) {
    proxy = resolveRulesFromList([pRules, hRules, rules, fRules], 'resolveProxy', req, hostValue);
  } else {
    proxy = resolveRulesFromList([pRules, rules, fRules, hRules], 'resolveProxy', req, hostValue);
  }
  var proxyHostOnly;
  var proxyHost = util.isEnable(req, 'proxyHost') || isProxyEnable(req, 'proxyHost');
  if (proxy) {
    proxyHostOnly = isLineProp(proxy, 'proxyHostOnly');
    proxyHost = proxyHost || proxyHostOnly;
    var protocol = proxy.matcher.substring(0, proxy.matcher.indexOf(':'));
    ignoreProxy =
      !filter['ignore:' + protocol] &&
      (util.isIgnored(filter, 'proxy') || util.isIgnored(filter, protocol));
    if (ignoreProxy) {
      proxy = null;
    } else {
      proxyHost = proxyHost || PROXY_HOSTS_RE.test(proxy.matcher);
    }
  }

  if (!ignoreProxy) {
    proxyHost = isProxyHost(req, proxy, host) || proxyHost; // 不能调换顺序
  }
  var setHost = function () {
    if (!host || req._isProxyReq) {
      return false;
    }
    reqRules.host = host;
    var hostname = util.removeProtocol(host.matcher, true);
    if (!net.isIP(hostname)) {
      req.curUrl = hostname || url;
      rules.lookupHost(req, function (err, ip) {
        callback(err, ip, host.port, host);
      });
    } else {
      callback(null, hostname, host.port, host);
    }
    return true;
  };
  var resolvePacRule = function () {
    if (pacRule != null) {
      return;
    }
    if (util.isIgnored(filter, 'pac')) {
      pacRule = false;
      return;
    }
    if (config.multiEnv || req._headerRulesFirst) {
      pacRule =
        (pRules && pRules.resolvePac(req)) ||
        (hRules && hRules.resolvePac(req)) ||
        rules.resolvePac(req) ||
        (fRules && fRules.resolvePac(req)) ||
        false;
    } else {
      pacRule =
        (pRules && pRules.resolvePac(req)) ||
        rules.resolvePac(req) ||
        (fRules && fRules.resolvePac(req)) ||
        (hRules && hRules.resolvePac(req)) ||
        false;
    }
    if (pacRule) {
      proxyHostOnly = isLineProp(pacRule, 'proxyHostOnly');
      proxyHost =
        proxyHost || proxyHostOnly || isLineProp(pacRule, 'proxyHost');
    }
  };
  if (host) {
    if (!proxyHost && !ignoreProxy) {
      resolvePacRule();
    }
    if (proxyHost) {
      req._phost = parseUrl(util.setProtocol(util.joinIpPort(host.matcher, host.port)));
    } else if (
      !isLineProp(proxy, 'proxyFirst') &&
      !isLineProp(host, 'proxyFirst') &&
      !util.isEnable(req, 'proxyFirst') &&
      !isProxyEnable(req, 'proxyFirst')
    ) {
      return setHost();
    }
    proxyHost = true;
    reqRules.host = host;
    req._enableProxyHost = true;
  }
  if (ignoreProxy || (proxyHostOnly && !req._phost)) {
    req.curUrl = url;
    return setHost() || rules.lookupHost(req, callback);
  }
  if (proxy) {
    if (!req._phost && P_HOST_RE.test(proxy.matcher)) {
      req._phost = parseUrl(util.setProtocol(RegExp.$1));
    }
    reqRules.proxy = proxy;
    return callback();
  }
  resolvePacRule();
  var pacUrl = util.getMatcherValue(pacRule);
  if (!pacUrl) {
    return setHost() || callback();
  }
  var auth;
  if (AUTH_RE.test(pacUrl)) {
    auth = RegExp.$1;
    pacUrl = pacUrl.substring(auth.length + 1);
  }
  if (!util.isUrl(pacUrl) && !(pacUrl = util.joinPath(pacRule.root, pacUrl))) {
    return setHost() || callback();
  }
  req._pacAuth = auth;
  var pac = cachedPacs[pacUrl];
  if (pac) {
    delete cachedPacs[pacUrl];
    cachedPacs[pacUrl] = pac;
  } else {
    var list = Object.keys(cachedPacs);
    if (list.length >= 10) {
      delete cachedPacs[list[0]];
    }
    cachedPacs[pacUrl] = pac = new Pac(pacUrl, dnsResolve);
  }
  reqRules.pac = pacRule;
  return pac.findWhistleProxyForURL(
    url.replace('tunnel:', 'https:'),
    function (err, rule) {
      if (rule) {
        tempRules._file = pacRule.file;
        tempRules.parse(pacRule.rawPattern + ' ' + rule);
        req.curUrl = url;
        if ((proxy = tempRules.resolveProxy(req, hostValue))) {
          proxyHost = isProxyHost(req, proxy) || proxyHost; // 不能调换顺序
          req._proxyTunnel =
            req._proxyTunnel || isLineProp(pacRule, 'proxyTunnel');
          var protocol = proxy.matcher.substring(0, proxy.matcher.indexOf(':'));
          if (!util.isIgnored(filter, protocol)) {
            reqRules.proxy = proxy;
            reqRules.proxy.raw = pacRule.raw;
          }
        }
      }
      if (reqRules.proxy) {
        (!proxyHost && setHost()) || callback();
      } else {
        req.curUrl = url;
        setHost() || rules.lookupHost(req, callback);
      }
      logger.error(err);
    }
  );
};

function tpl(str, data) {
  if (
    typeof str !== 'string' ||
    str.indexOf('<%') === -1 ||
    str.indexOf('%>') === -1
  ) {
    return str + '';
  }
  var key = str;
  var fn = tplCache.get(key);
  if (!fn) {
    str = str
      .replace(/[\u2028\u2029]/g, '')
      .replace(/\t/g, ' ')
      .replace(/\r?\n|\r/g, '\t')
      .split('<%')
      .join('\u2028')
      .replace(/((^|%>)[^\u2028]*)'/g, '$1\r')
      .replace(/\u2028=(.*?)%>/g, '\',$1,\'')
      .split('\u2028')
      .join('\');')
      .split('%>')
      .join('p.push(\'')
      .split('\r')
      .join('\\\'');
    try {
      fn = new Function(
        'obj',
        'var p=[],print=function(){p.push.apply(p,arguments);};' +
          'with(obj){p.push(\'' +
          str +
          '\');}return p.join(\'\');'
      );
    } catch (e) {
      fn = e;
      throw e;
    } finally {
      tplCache.set(key, fn);
    }
  } else if (typeof fn !== 'function') {
    throw fn;
  }
  return fn(data || {}).replace(/\t/g, '\n');
}

function getScriptContext(req, res, body, pattern, frameOpts) {
  var ip = req.clientIp || LOCALHOST;
  var ctx = req.scriptContenxt;
  if (!ctx) {
    var headers = extend(true, {}, req.headers);
    ctx = req.scriptContenxt = {
      Buffer: Buffer,
      pattern: pattern,
      version: config.version,
      port: config.port,
      uiHost: 'local.wproxy.org',
      uiPort: config.uiport,
      url: req.fullUrl,
      fullUrl: req.fullUrl,
      method: util.toUpperCase(req.method) || 'GET',
      httpVersion: req.httpVersion || '1.1',
      decodeBuffer: function (buf, encoding) {
        return iconv.decode(buf, encoding || 'utf8');
      },
      encodeString: function (str, encoding) {
        return iconv.encode(str, encoding || 'utf8');
      },
      encodingExists: function (encoding) {
        return iconv.encodingExists(encoding);
      },
      isLocalAddress: function (_ip) {
        return util.isLocalAddress(_ip || ip);
      },
      ip: ip,
      clientIp: ip,
      clientPort: req.clientPort,
      headers: headers,
      reqHeaders: headers,
      body: body || '',
      reqScriptData: {},
      res: null
    };
  }
  if (frameOpts) {
    ctx.ctx = {
      sendToServer: frameOpts.sendToServer,
      sendToClient: frameOpts.sendToClient,
      handleSendToClientFrame: null,
      handleSendToServerFrame: null
    };
  } else {
    ctx.rules = [];
    ctx.values = {};
  }
  ctx.value = req.globalValue;
  ctx.getValue = function (key, onlyValues) {
    var value = !onlyValues && req._inlineValues && req._inlineValues[key];
    return typeof value === 'string' ? value : values.get(key);
  };
  ctx.parseUrl = parseUrl;
  ctx.parseQuery = parseQuery;
  ctx.tpl = ctx.render = tpl;
  if (res) {
    ctx.statusCod
... [truncated]
```

### biz/webui/cgi-bin/init.js
```
var getRules = require('./rules');
var getValues = require('./values');
var util = require('./util');
var config = require('../../../lib/config');
var rulesUtil = require('../../../lib/rules/util');
var ca = require('../../../lib/https/ca');
var proxy = require('../lib/proxy');

var properties = rulesUtil.properties;
var logger = proxy.logger;
var pluginMgr = proxy.pluginMgr;

module.exports = function(req, res) {
  var lastSvrLog = logger.getLogs(0, 1)[0];

  util.sendGzip(req, res, {
    wName: config.whistleName,
    disableInstaller: config.disableInstaller,
    account: config.account,
    version: config.version,
    custom1: properties.get('Custom1'),
    custom2: properties.get('Custom2'),
    hasInvalidCerts: ca.hasInvalidCerts,
    supportH2: config.enableH2,
    lastSvrLogId: lastSvrLog && lastSvrLog.id,
    lastDataId: proxy.getLastDataId(),
    clientId: util.getClientId(),
    clientIp: util.getClientIp(req),
    mrulesClientId: config.mrulesClientId,
    mrulesTime: config.mrulesTime,
    mvaluesClientId: config.mvaluesClientId,
    mvaluesTime: config.mvaluesTime,
    latestVersion: properties.getLatestVersion('latestVersion'),
    latestClientVersion: properties.getLatestVersion('latestClientVersion'),
    server: util.getServerInfo(req),
    rules: getRules(),
    values: getValues(),
    interceptHttpsConnects: properties.isEnableCapture(),
    enableHttp2: properties.isEnableHttp2(),
    plugins: pluginMgr.getPlugins(),
    disabledPlugins: !config.notAllowedDisablePlugins && properties.get('disabledPlugins') || {},
    disabledAllPlugins: !config.notAllowedDisablePlugins && properties.get('disabledAllPlugins'),
    disabledAllRules: !config.notAllowedDisableRules && properties.get('disabledAllRules'),
    localUIHost: config.localUIHost
  });
};

```

### biz/index.js
```
var net = require('net');
var rules = require('../lib/rules');
var util = require('../lib/util');
var handleUIReq = require('./webui/lib').handleRequest;
var handleWeinreReq = require('./weinre');
var config = require('../lib/config');
var common = require('../lib/util/common');

var localIpCache = util.localIpCache;
var WEBUI_PATH = config.WEBUI_PATH;
var CUSTOM_WEBUI_PATH = /\/[\w.-]*\.whistle-path\.5b6af7b9884e1165[\w.-]*\/+/;
var CUSTOM_WEBUI_PATH_RE = /^\/[\w.-]*\.whistle-path\.5b6af7b9884e1165[\w.-]*\/+/;
var PREVIEW_PATH_RE = config.PREVIEW_PATH_RE;
var WEBUI_PATH_RE = util.escapeRegExp(WEBUI_PATH, true);
var REAL_WEBUI_HOST = new RegExp('^' + WEBUI_PATH_RE + '(__([a-z\\d.-]+)(?:__(\\d{1,5}))?__/)');
var INTERNAL_APP = new RegExp('^' + WEBUI_PATH_RE + '(log|weinre|cgi)(?:\\.(\\d{1,5}))?/');
var PLUGIN_RE = new RegExp('^' + WEBUI_PATH_RE + 'whistle\\.([a-z\\d_-]+)/');
var CUSTOM_REAL_WEBUI_HOST = new RegExp('^/[\\w.-]*\\.whistle-path\\.5b6af7b9884e1165[\\w.-]*/+(__([a-z\\d.-]+)(?:__(\\d{1,5}))?__/)');
var CUSTOM_INTERNAL_APP = new RegExp('^/[\\w.-]*\\.whistle-path\\.5b6af7b9884e1165[\\w.-]*/+(log|weinre|cgi)(?:\\.(\\d{1,5}))?/');
var CUSTOM_PLUGIN_RE = new RegExp('^/[\\w.-]*\\.whistle-path\\.5b6af7b9884e1165[\\w.-]*/+whistle\\.([a-z\\d_-]+)/');
var REAL_WEBUI_HOST_PARAM = /_whistleInternalHost_=(__([a-z\d.-]+)(?:__(\d{1,5}))?__)/;
var OUTER_PLUGIN_RE = /^(?:\/whistle)?\/((?:whistle|plugin)\.[a-z\\d_-]+)::(\d{1,5})\//;

function transformUI(req, res) {
  if (config.customUIHost && !config.keepProxyUI) {
    return res.status(404).end();
  }
  return handleUIReq(req, res);
}

module.exports = function(req, res, next) {
  var config = this.config;
  var pluginMgr = this.pluginMgr;
  var fullUrl = req.fullUrl = util.getFullUrl(req); // format request
  var headers = req.headers;
  var host = util.parseHost(headers.host);
  var port = host[1] || (req.isHttps ? 443 : 80);
  var bypass;
  host = host[0];
  req._w2hostname = host;
  var transformPort, isProxyReq, isWeinre, isOthers;
  var webUI = WEBUI_PATH;
  var realHostRe = REAL_WEBUI_HOST;
  var internalAppRe = INTERNAL_APP;
  var pluginRe = PLUGIN_RE;
  var isWebUI = req.path.indexOf(WEBUI_PATH) === 0;
  var isOld;
  if (!isWebUI && CUSTOM_WEBUI_PATH_RE.test(req.path)) {
    isWebUI = true;
    isOld = true;
    webUI = CUSTOM_WEBUI_PATH;
    realHostRe = CUSTOM_REAL_WEBUI_HOST;
    internalAppRe = CUSTOM_INTERNAL_APP;
    pluginRe = CUSTOM_PLUGIN_RE;
  }
  if (isWebUI) {
    isWebUI = !config.pureProxy;
    var realHost;
    if (isWebUI) {
      if (realHostRe.test(req.path) || REAL_WEBUI_HOST_PARAM.test(req.url)) {
        var realPath = RegExp.$1;
        var realPort = RegExp.$3;
        realHost = RegExp.$2 + (realPort ? ':' + realPort : '');
        headers[util.REAL_HOST_HEADER] = realHost;
        req.url = req.url.replace(realPath, '');
      } else {
        req.curUrl = fullUrl;
        if (realHost = rules.resolveInternalHost(req)) {
          headers[util.REAL_HOST_HEADER] = realHost;
        }
      }
      if (internalAppRe.test(req.path)) {
        transformPort = RegExp.$2;
        isWeinre = RegExp.$1 === 'weinre';
        if (transformPort) {
          isOthers = isProxyReq = transformPort != config.port;
        } else {
          isProxyReq = false;
          transformPort = config.port;
        }
        isProxyReq = isProxyReq || isOld;
      } else if (pluginRe.test(req.path)) {
        isProxyReq = !pluginMgr.getPlugin(RegExp.$1 + ':');
      } else if (!headers[config.WEBUI_HEAD]) {
        isWebUI = false;
      }
      if (!config.proxyServer && isProxyReq && !config.isLocalUIUrl(host)) {
        isWebUI = false;
        req.isPluginReq = true;
        req._isProxyReq = true;
      }
      if (isWebUI) {
        req.fromInternalPath = true;
        var hostname = (req._fwdHost && util.parseHost(req._fwdHost)[0]) || host;
        headers[common.ORIGIN_HOST_HEADER] = hostname || '*';
      }
    }
  } else {
    isWebUI = headers[config.WEBUI_HEAD];
    if (!isWebUI) {
      if (!(isWebUI = localIpCache.get(host))) {
        isWebUI = config.isLocalUIUrl(host);
        if (isWebUI ? net.isIP(host) : util.isLocalHost(host)) {
          isWebUI = util.isProxyPort(port);
        }
      }
    } else if (util.isProxyPort(port) && net.isIP(host)) {
      localIpCache.set(host, 1);
    }
    if (PREVIEW_PATH_RE.test(req.url)) {
      headers[util.INTERNAL_ID_HEADER] = util.INTERNAL_ID;
      req.url = '/preview.html?charset=' + RegExp.$1;
      isWebUI = true;
    } else if (isWebUI) {
      if (req.path.indexOf('/_/') === 0) {
        bypass = '/_/';
      } else if (req.path.indexOf('/-/') === 0) {
        bypass = '/-/';
      }
      if (bypass) {
        req.url = req.url.replace(bypass, '/');
      }
      delete headers[util.INTERNAL_ID_HEADER];
    }
  }
  // 后续有用到
  fullUrl = req.fullUrl = util.getFullUrl(req);
  if (bypass) {
    return next();
  }
  var localRule;
  req.curUrl = fullUrl;
  if (isWebUI) {
    if (isOthers) {
      util.transformReq(req, res, transformPort);
    } else {
      req.url = req.url.replace(transformPort ? internalAppRe : webUI, '/');
      if (OUTER_PLUGIN_RE.test(req.path)) {
        var outerPort = RegExp.$2;
        req.url = req.url.replace(RegExp['$&'], '/' + RegExp.$1 + '/');
        if (outerPort > 0 && outerPort < 65536 && outerPort != config.port) {
          headers.host = '127.0.0.1:' + outerPort;
          return util.transformReq(req, res, outerPort);
        }
      }
      req._hasRespond = true;
      if (isWeinre) {
        handleWeinreReq(req, res);
      } else {
        transformUI(req, res);
      }
    }
  } else if (localRule = rules.resolveLocalRule(req)) {
    req.url = localRule.url;
    if (localRule.realPort) {
      headers.host = '127.0.0.1:' + localRule.realPort;
      util.transformReq(req, res, localRule.realPort);
    } else {
      transformUI(req, res);
    }
  } else {
    next();
  }
};


```

### lib/inspectors/res.js
```
var https = require('https');
var http = require('http');
var net = require('net');
var parseUrl = require('../util/parse-url-safe');
var extend = require('extend');
var util = require('../util');
var Transform = require('pipestream').Transform;
var h2 = require('../https/h2');
var rules = require('../rules');
var pluginMgr = require('../plugins');
var hparser = require('hparser');
var config = require('../config');

var WhistleTransform = util.WhistleTransform;
var SpeedTransform = util.SpeedTransform;
var ReplacePatternTransform = util.ReplacePatternTransform;
var ReplaceStringTransform = util.ReplaceStringTransform;
var FileWriterTransform = util.FileWriterTransform;
var formatHeaders = hparser.formatHeaders;
var getRawHeaderNames = hparser.getRawHeaderNames;

var TIMEOUT = config.timeout < 16000 && config.timeout > 0 ? 0 : 16000;
var LOCALHOST = '127.0.0.1';
var CRLF = util.toBuffer('\r\n');
var MAX_RES_SIZE = 1024 * 1024 * (config.strict ? 1 : 2); // 2MB
var BIG_MAX_RES_SIZE = 1024 * 1024 * 16;
var JSON_RE = /{[\w\W]*}|\[[\w\W]*\]/;
var LIKE_JSON_RE = /^\s*[\{\[]/;
var NO_STORE_RE = /^no-store$/i;
var NO_CACHE_RE = /^(?:no|no-cache|no-store)$/i;
var X_RE = /^x/;
var clientIpKey = config.CLIENT_IP_HEADER;
var BODY_PROTOCOLS = [
  'attachment',
  'resReplace',
  'resBody',
  'resPrepend',
  'resAppend',
  'htmlBody',
  'htmlPrepend',
  'htmlAppend',
  'jsBody',
  'jsPrepend',
  'jsAppend',
  'cssBody',
  'cssPrepend',
  'cssAppend',
  'resWrite',
  'resWriteRaw',
  'resMerge'
];
var BODY_PROTOCOLS_LEN = BODY_PROTOCOLS.length;

function notAllowCache(resRules) {
  for (var i = 0; i < BODY_PROTOCOLS_LEN; i++) {
    if (resRules[BODY_PROTOCOLS[i]]) {
      return true;
    }
  }
}

function joinArr(src, dest) {
  if (!src || !dest) {
    return src || dest;
  }
  return src.concat(dest);
}

function pipeClient(req, client) {
  if (req._hasError) {
    client.destroy();
  } else if (req.noReqBody) {
    util.drain(req, function () {
      if (!req._hasError) {
        client.end();
      }
    });
  } else {
    req.pipe(client);
  }
}

function showDnsError(res, err) {
  res.response(
    util.wrapGatewayError('DNS Lookup Failed\r\n' + util.getErrorStack(err))
  );
}

function setCookies(headers, data) {
  var newCookies = data.headers['set-cookie'];
  if (!Array.isArray(newCookies)) {
    if (!newCookies || typeof newCookies !== 'string') {
      return;
    }
    newCookies = newCookies.split(',');
  }
  if (newCookies.length) {
    var cookies = headers['set-cookie'];
    var isArray = Array.isArray(cookies);
    if (!isArray && cookies) {
      isArray = true;
      cookies = [String(cookies)];
    }
    if (isArray) {
      var newNameMap = {};
      newCookies.forEach(function (cookie) {
        var index = cookie.indexOf('=');
        var name = index == -1 ? name : cookie.substring(0, index);
        newNameMap[name] = 1;
      });
      cookies.forEach(function (cookie) {
        var index = cookie.indexOf('=');
        var name = index == -1 ? name : cookie.substring(0, index);
        if (!newNameMap[name]) {
          newCookies.push(cookie);
        }
      });
    }
    headers['set-cookie'] = newCookies;
    delete data.headers['set-cookie'];
  }
}

function handleReplace(res, replacement) {
  if (!replacement) {
    return;
  }

  var type = util.getContentType(res.headers);
  if (!type || type == 'IMG') {
    return;
  }

  Object.keys(replacement).forEach(function (pattern) {
    var value = replacement[pattern];
    if (
      util.isOriginalRegExp(pattern) &&
      (pattern = util.toOriginalRegExp(pattern))
    ) {
      res.addTextTransform(new ReplacePatternTransform(pattern, value, util.isSSE(res)));
    } else if (pattern) {
      res.addTextTransform(new ReplaceStringTransform(pattern, value, util.isSSE(res)));
    }
  });
}

function getWriterFile(file, statusCode) {
  if (!file || statusCode == 200) {
    return file;
  }

  return file + '.' + statusCode;
}

function readFirstChunk(req, res, src, cb) {
  var ports = req._pipePluginPorts;
  if (!cb) {
    if (ports.reqReadPort || ports.reqWritePort) {
      delete req.headers['content-length'];
    }
    return ports.reqReadPort ? req.getPayload(res, 1) : res();
  }
  if (ports.resReadPort || ports.resWritePort) {
    delete src.headers['content-length'];
  }
  if (!ports.resReadPort) {
    return cb();
  }
  res.prepareSrc(src, function (stream) {
    util.readOneChunk(stream, cb);
  });
}

function checkH2(req, isHttps) {
  if (!config.enableH2) {
    return;
  }
  req.useH2 = req.isH2;
  var d = req.disable;
  var e = req.enable;
  if (isHttps) {
    if (d.h2 || d.http2 || d.httpsH2) {
      req.useH2 = false;
    } else if (e.h2 || e.http2 || e.httpsH2) {
      req.useH2 = true;
    }
  } else {
    if (d.httpH2) {
      req.useH2 = false;
    } else if (e.httpH2) {
      req.useH2 = true;
    }
    req.useHttpH2 = req.useH2;
  }
}

module.exports = function (req, res, next) {
  var origProto;
  var resRules = req.rules;

  req.request = function (options) {
    readFirstChunk(req, function () {
      options = options || req.options;
      req.realUrl = res.realUrl = options.isPlugin
        ? req._realUrl || req.fullUrl
        : options.href;
      var originPort = options.port;
      var originHost = options.host;
      var originDomain = options.hostname;
      var now = Date.now();
      rules.getClientCert(req, function (key, cert, isPfx, cacheKey) {
        rules.getProxy(
          options.href,
          options.isPlugin ? null : req,
          function (err, hostIp, hostPort) {
            var proxyRule = resRules.proxy;
            var proxyUrl =
              !options.isPlugin && proxyRule
                ? util.rule.getMatcher(proxyRule)
                : null;
            var headers = req.headers;
            var auth, isInternalProxy, isHttpsProxy, origPath, origProxy;
            if (!hostIp) {
              if (options.localDNS) {
                req.curUrl = '';
              } else if (proxyUrl) {
                isHttpsProxy = proxyRule.isHttps;
                isInternalProxy = proxyRule.isInternal || util.isInternalProxy(req);
                if (isInternalProxy) {
                  req._isInternalProxy = true;
                  if (options.protocol === 'https:') {
                    headers[config.HTTPS_FIELD] = 1;
                    origProto = options.protocol;
                    options.protocol = null;
                  }
                } else if (proxyRule.isHttp2https) {
                  options.protocol = 'https:';
                }
                req.curUrl = 'http:' + util.removeProtocol(proxyUrl);
              } else {
                req.curUrl = options.href;
              }
            }
            if (!req.setServerPort) {
              req.setServerPort = function (port) {
                req.serverPort = port;
              };
            }
            rules.resolveHost(req, function (err, ip, port, hostRule) {
              var setHostsInfo = function (_ip, _port, _host, withPort) {
                ip = _ip || '127.0.0.1';
                port = _port;
                req.dnsTime = Date.now() - now;
                req.hostIp = util.joinIpPort(_ip, withPort && _port);
                if (_host) {
                  resRules.host = _host;
                }
              };
              if (proxyUrl && proxyRule && hostRule) {
                proxyRule.host = hostRule;
                hostRule = null;
              }
              setHostsInfo(hostIp || ip, hostPort || port, hostRule);
              if (err) {
                showDnsError(res, err);
                return;
              }
              if (req.disable.keepalive) {
                req.disable.keepAlive = true;
              }
              var isHttps = options.protocol == 'https:';
              var proxyOptions, isProxyPort, isSocks;
              var setAgent = function (disable) {
                if (disable || req.disable.keepAlive || (isHttps && cert)) {
                  options.agent = false;
                } else {
                  options.agent = isHttps ? config.httpsAgent : config.httpAgent;
                }
              };
              checkH2(req, isHttps);
              if (proxyUrl) {
                proxyOptions = parseUrl(proxyUrl);
                proxyOptions.host = ip;
                proxyOptions.auth = proxyOptions.auth || req._pacAuth;
                isSocks = proxyRule.isSocks;
                var proxyPort = proxyOptions.port;
                if (!proxyPort) {
                  proxyPort = proxyOptions.port = isSocks ? 1080 : isHttpsProxy ? 443 : 80;
                }
                if (proxyOptions.auth) {
                  auth = 'Basic ' + util.toBuffer(proxyOptions.auth + '').toString('base64');
                } else {
                  auth = headers['proxy-authorization'];
                }
                if (
                    isHttps ||
                    (req.useH2 && !isInternalProxy) ||
                    isSocks ||
                    isHttpsProxy ||
                    req._phost
                  ) {
                  isProxyPort = util.isProxyPort(proxyPort);
                  if (isProxyPort && util.isLocalAddress(ip)) {
                    req.setServerPort(config.port);
                    res.response(
                        util.wrapResponse({
                          statusCode: 302,
                          headers: {
                            location:
                              'http://' +
                              util.joinIpPort(ip, config.port) +
                              (options.path || '')
                          }
                        })
                      );
                  } else {
                    var curServerPort = options.port || (isHttps ? 443 : 80);
                    var proxyHeaders = {
                      host: util.joinIpPort(options.hostname, curServerPort),
                      'proxy-connection': req.disable.proxyConnection
                          ? 'close'
                          : 'keep-alive'
                    };
                    pluginMgr.getTunnelKeys().forEach(function (k) {
                      var val = headers[k];
                      if (val) {
                        proxyHeaders[k] = val;
                      }
                    });
                    if (auth) {
                      proxyHeaders['proxy-authorization'] = auth;
                    }
                    if (req.disable.proxyUA) {
                      delete proxyHeaders['user-agent'];
                    } else if (headers['user-agent']) {
                      proxyHeaders['user-agent'] = headers['user-agent'];
                    }
                    if (!util.isLocalAddress(req.clientIp)) {
                      proxyHeaders[clientIpKey] = req.clientIp;
                    }
                    if (isHttps || req.useH2) {
                      util.checkIfAddInterceptPolicy(proxyHeaders, headers);
                    }
                    if (isProxyPort) {
                      proxyHeaders[config.WEBUI_HEAD] = 1;
                    }
                    if (util.isProxyPort(curServerPort) || util.isLocalPHost(req, isHttps)) {
                      headers[config.WEBUI_HEAD] = 1;
                    }
                    var clientId = req.headers[config.CLIENT_ID_HEADER];
                    if (clientId) {
                      proxyHeaders[config.CLIENT_ID_HEADER] = clientId;
                    }
                    util.setClientId(
                        proxyHeaders,
                        req.enable,
                        req.disable,
                        req.clientIp,
                        isInternalProxy
                      );
                    var phost = req._phost;
                    var opts = {
                      isSocks: isSocks,
                      isHttps: isHttps,
                      _phost: phost,
                      pr
... [truncated]
```

(+206 more files reference the changed code)
Repository Map
lib/config.js
lib/handlers/error-handler.js
lib/handlers/file-proxy.js
lib/handlers/http-proxy.js
lib/handlers/index.js
lib/https/ca.js
lib/https/h2.js
lib/https/index.js
lib/https/load-cert.js
lib/index.js
lib/init.js
lib/inspectors/data.js
lib/inspectors/index.js
lib/inspectors/log.js
lib/inspectors/req.js
lib/inspectors/res.js
lib/inspectors/rules.js
lib/inspectors/weinre.js
lib/plugins/compat.js
lib/plugins/get-plugins-sync.js
lib/plugins/get-plugins.js
lib/plugins/index.js
lib/plugins/load-plugin.js
lib/plugins/module-paths.js
lib/plugins/proxy.js
lib/plugins/shared-storage.js
lib/plugins/util.js
lib/rules/dns.js
lib/rules/index.js
lib/rules/protocols.js
lib/rules/recycle-bin.js
lib/rules/rules.js
lib/rules/storage.js
lib/rules/util.js
lib/service/compose-data.js
lib/service/composer.js
lib/service/console-log.js
lib/service/data-center.js
lib/service/extract-saz.js
lib/service/generate-saz.js
lib/service/index.js
lib/service/install.js
lib/service/service.js
lib/service/util.js
lib/socket-mgr.js
lib/tunnel.js
lib/upgrade.js
lib/util/common.js
lib/util/data-server.js
lib/util/drain.js
lib/util/file-mgr.js
lib/util/file-writer-transform.js
lib/util/http-mgr.js
lib/util/index.js
lib/util/is-utf8.js
lib/util/logger.js
lib/util/parse-url-safe.js
lib/util/parse-url.js
lib/util/patch.js
lib/util/perf.js
lib/util/process.js
lib/util/replace-pattern-transform.js
lib/util/replace-string-transform.js
lib/util/speed-transform.js
lib/util/transproto.js
lib/util/whistle-transform.js
lib/util/zlib.js
./  (3 files)
assets/js/  (3 files)
bin/  (8 files)
bin/ca/  (3 files)
biz/  (2 files)
biz/webui/  (238 files)
biz/weinre/  (2 files)
docs/.vitepress/  (1 files)
test/  (4 files)
test/assets/  (5 files)
test/plugins/  (38 files)
test/proxy/  (2 files)
test/units/  (82 files)
... (458 source files in total)
Package Manifests (Dependencies, scripts, build configuration)
### package.json
```
{
  "name": "whistle",
  "description": "HTTP, HTTP2, HTTPS, Websocket debugging proxy",
  "version": "2.10.2",
  "dataDirname": ".whistle",
  "localUIHost": "local.whistlejs.com",
  "port": 8899,
  "sockets": 256,
  "timeout": 360000,
  "author": "avenwu <avwu@qq.com>",
  "contributors": [],
  "license": "MIT",
  "bugs": {
    "url": "https://github.com/avwo/whistle/issues"
  },
  "homepage": "https://wproxy.org",
  "keywords": [
    "proxy",
    "fiddler",
    "charles",
    "websocket",
    "http2",
    "hosts",
    "debug",
    "mock"
  ],
  "bin": {
    "whistle": "./bin/whistle.js",
    "w2": "./bin/whistle.js",
    "wproxy": "./bin/whistle.js"
  },
  "repository": {
    "type": "git",
    "url": "https://github.com/avwo/whistle.git"
  },
  "dependencies": {
    "adm-zip": "0.5.16",
    "async-limiter": "2.0.0",
    "body-parser": "^1.20.3",
    "colors": "1.1.2",
    "express": "^4.21.2",
    "extend": "^3.0.2",
    "fs-extra2": "^1.0.0",
    "hagent": "^0.9.3",
    "hparser": "^0.5.0",
    "iconv-lite": "^0.4.24",
    "json5": "^2.2.3",
    "lru-cache": "^4.1.1",
    "mime": "^1.6.0",
    "multer2": "^1.1.1",
    "node-forge": "^1.3.1",
    "node-pac": "^0.5.1",
    "parseurl": "^1.3.1",
    "pfork": "^0.6.3",
    "pipestream": "^0.7.5",
    "set-global-proxy": "^0.3.0",
    "sni": "1.0.0",
    "sockx": "^0.2.3",
    "starting": "^8.0.3",
    "weinre2": "^1.3.6",
    "ws-parser": "^0.6.4",
    "xml2js": "0.5.0"
  },
  "scripts": {
    "dev": "webpack --config ./biz/webui/htdocs/src/webpack.config -w",
    "start": "node bin/whistle.js run",
    "test": "npm run lintfix && node test/index.test.js",
    "lint": "eslint *.js ./lib ./bin ./biz ./test ./docs/script",
    "lintfix": "eslint --fix *.js ./lib ./bin ./biz ./test ./docs/script",
    "cov": "node_modules/istanbul/lib/cli.js cover node_modules/.bin/tape -- test/index.test.js",
    "docs:dev": "vitepress dev docs",
    "docs": "vitepress build docs"
  },
  "engines": {
    "node": ">= 8.8"
  },
  "devDependencies": {
    "babel-core": "^6.7.6",
    "babel-eslint": "^6.1.2",
    "babel-loader": "^6.2.4",
    "babel-plugin-transform-class-properties": "^6.24.1",
    "babel-plugin-transform-object-rest-spread": "^6.26.0",
    "babel-preset-env": "^1.7.0",
    "babel-preset-react": "^6.5.0",
    "babel-runtime": "^6.26.0",
    "base64-js": "^1.3.0",
    "bootstrap": "3.3.5",
    "clipboard": "^2.0.11",
    "codemirror": "^5.65.16",
    "coveralls": "^3.1.1",
    "css-loader": "0.16.0",
    "eslint": "^2.8.0",
    "eslint-plugin-react": "^4.3.0",
    "file-loader": "0.8.4",
    "istanbul": "^0.4.5",
    "jquery": "^4.0.0",
    "js-base64": "^2.4.5",
    "qrcode": "1.2.0",
    "react": "^15.6.2",
    "react-base16-styling": "^0.5.1",
    "react-dom": "^15.6.2",
    "react-virtualized": "^9.21.2",
    "request": "^2.74.0",
    "should": "^13.2.3",
    "should-http": "^0.1.1",
    "style-loader": "0.12.3",
    "tape": "^4.6.0",
    "url-loader": "0.5.6",
    "vitepress": "^1.6.3",
    "webpack": "1.11.0",
    "ws": "^1.1.4"
  }
}

```
Context & Existing Test Patterns
Existing test files touched by the patch: none
Repository top-level entries: .babelrc, .editorconfig, .eslintignore, .eslintrc, .gitattributes, .gitignore, .npmignore, .travis.yml, CHANGELOG-en_US.md, CHANGELOG.md, LICENSE, README-en_US.md, README.md, assets, bin, biz, docs, index.d.ts, index.js, lib, package-lock.json, package.json, require.js, test
Project's own test patterns and conventions:
### test/units/ui.test.js
```

var util = require('../util.test');

module.exports = function() {
  util.request('https://local.whistlejs.com/favicon.ico?doNotParseJson');
  util.request('https://local.whistlejs.com/?doNotParseJson');
  util.request('http://rd2webui.w2.org/index.html?doNotParseJson');
  util.request('http://rd2webui.w2.org/?doNotParseJson');
  util.request('http://local.whistlejs.com/index.html?doNotParseJson');
  util.request('http://local.whistlejs.com/?doNotParseJson');
  util.request('http://local.whistlejs.com:1234/index.html?doNotParseJson');
  util.request('http://local.whistlejs.com/cgi-bin/log/get');
  util.request('http://local.whistlejs.com/cgi-bin/init');
  util.request('http://local.whistlejs.com:2345/cgi-bin/init');
  util.request('http://local.whistlejs.com/cgi-bin/get-data');
  util.request('http://local.whistlejs.com/cgi-bin/server-info');
  util.request('http://local.whistlejs.com/cgi-bin/values/list');
  util.request('http://local.whistlejs.com/cgi-bin/plugins/get-plugins');
  util.request('http://local.whistlejs.com/cgi-bin/rules/list');
  util.request('http://local.whistlejs.com/cgi-bin/rootca');
  util.request('http://local.whistlejs.com/cgi-bin/root?doNotParseJson', function(res) {
    res.statusCode.should.be.equal(404);
  });

  util.request('https://local.whistlejs.com/index.html?doNotParseJson');
  util.request('https://local.whistlejs.com:1234/index.html?doNotParseJson');
  util.request('https://local.whistlejs.com/cgi-bin/log/get');
  util.request('https://local.whistlejs.com/cgi-bin/init');
  util.request('https://local.whistlejs.com:2345/cgi-bin/init');
  util.request('https://local.whistlejs.com/cgi-bin/get-data');
  util.request('https://local.whistlejs.com/cgi-bin/server-info');
  util.request('https://local.whistlejs.com/cgi-bin/values/list');
  util.request('https://local.whistlejs.com/cgi-bin/plugins/get-plugins');
  util.request('https://local.whistlejs.com/cgi-bin/rules/list');
  util.request('https://local.whistlejs.com/whistle.test');
  util.request('http://local.whistlejs.com/whistle.test');
  util.request('https://local.whistlejs.com/plugin.test');
  util.request('http://local.whistlejs.com/plugin.test');
  util.request({
    url: 'http://local.whistlejs.com/cgi-bin/log/get',
    headers: {
      origin: 'http://wproxy.org'
    }
  });
  util.request({
    url: 'http://local.whistlejs.com/cgi-bin/values/add',
    method: 'post',
    form: {
      name: 'test',
      value: '123'
    }
  }, function() {
    util.request({
      url: 'http://local.whistlejs.com/cgi-bin/values/rename',
      method: 'post',
      form: {
        name: 'test',
        newName: '123'
      }
    }, function() {
      util.request({
        url: 'http://local.whistlejs.com/cgi-bin/values/remove',
        method: 'post',
        form: {
          name: '123'
        }
      });
    });
  });
  util.request({
    url: 'http://local.whistlejs.com/cgi-bin/values/move-to',
    method: 'post',
    form: {
      to: 'test',
      from: 'abc'
    }
  });
  util.request({
    url: 'http://local.whistlejs.com/cgi-bin/rules/add',
    method: 'post',
    form: {
      name: 'test',
      value: '/test/ file://xxx'
    }
  });
  util.request({
    url: 'http://local.whistlejs.com/cgi-bin/rules/enable-default',
    method: 'post'
  });
  util.request({
    url: 'http://local.whistlejs.com/cgi-bin/rules/remove',
    method: 'post',
    form: {
      name: 'test',
      value: '/test/ file://xxx'
    }
  });
  util.request({
    url: 'http://local.whistlejs.com/cgi-bin/rules/rename',
    method: 'post',
    form: {
      name: 'test',
      newName: 'sssss'
    }
  });
  util.request({
    url: 'http://local.whistlejs.com/cgi-bin/rules/select',
    method: 'post',
    form: {
      name: 'test'
    }
  });
  util.request({
    url: 'http://local.whistlejs.com/cgi-bin/rules/unselect',
    method: 'post'
  });
  util.request({
    url: 'http://local.whistlejs.com/cgi-bin/rules/allow-multiple-choice',
    method: 'post'
  });
  util.request({
    url: 'http://local.whistlejs.com/cgi-bin/composer',
    method: 'post',
    form: {
      url: 'http://test.whistlejs.com/'
    }
  });
  util.request({
    url: 'http://local.whistlejs.com/cgi-bin/intercept-https-connects',
    method: 'post'
  });
  util.request({
    url: 'http://local.whistlejs.com/cgi-bin/hide-https-connects',
    method: 'post'
  });
  util.request({
    url: 'http://local.whistlejs.com/cgi-bin/do-not-show-again',
    method: 'post'
  });
  util.request({
    url: 'http://local.whistlejs.com/cgi-bin/check-update',
    method: 'post'
  });
  util.request({
    url: 'http://local.whistlejs.com/cgi-bin/rules/move-to',
    method: 'post'
  });
  util.request({
    url: 'http://local.whistlejs.com/cgi-bin/rules/get-sys-hosts',
    method: 'post'
  });


  util.request('http://local.wproxy.org:1234/index.html?doNotParseJson');
  util.request('http://local.wproxy.org:1234/index.html?doNotParseJson');
  util.request('http://local.wproxy.org:1234/cgi-bin/log/get');
  util.request('http://local.wproxy.org:1234/cgi-bin/init');
  util.request('http://local.wproxy.org:1234/cgi-bin/get-data');
  util.request('http://local.wproxy.org:1234/cgi-bin/server-info');
  util.request('http://local.wproxy.org:1234/cgi-bin/values/list');
  util.request('http://local.wproxy.org:1234/cgi-bin/plugins/get-plugins');
  util.request('http://local.wproxy.org:1234/cgi-bin/rules/list');

  util.request('https://local.wproxy.org:1234/index.html?doNotParseJson');
  util.request('https://local.wproxy.org:1234/index.html?doNotParseJson');
  util.request('https://local.wproxy.org:1234/cgi-bin/log/get');
  util.request('https://local.wproxy.org:1234/cgi-bin/init');
  util.request('https://local.wproxy.org:1234/cgi-bin/get-data');
  util.request('https://local.wproxy.org:1234/cgi-bin/server-info');
  util.request('https://local.wproxy.org:1234/cgi-bin/values/list');
  util.request('https://local.wproxy.org:1234/cgi-bin/plugins/get-plugins');
  util.request('https://local.wproxy.org:1234/cgi-bin/rules/list');
  util.request('https://local.wproxy.org:1234/whistle.test');
  util.request('http://local.wproxy.org:1234/whistle.test');
  util.request('https://local.wproxy.org:1234/plugin.test');
  util.request('http://local.wproxy.org:1234/plugin.test');
  util.request({
    url: 'http://local.wproxy.org:1234/cgi-bin/values/add',
    method: 'post',
    form: {
      name: 'test',
      value: '123'
    }
  }, function() {
    util.request({
      url: 'http://local.wproxy.org:1234/cgi-bin/values/rename',
      method: 'post',
      form: {
        name: 'test',
        newName: '123'
      }
    }, function() {
      util.request({
        url: 'http://local.wproxy.org:1234/cgi-bin/values/remove',
        method: 'post',
        form: {
          name: '123'
        }
      });
    });
  });
  util.request({
    url: 'http://local.wproxy.org:1234/cgi-bin/values/move-to',
    method: 'post',
    form: {
      to: 'test',
      from: 'abc'
    }
  });
  util.request({
    url: 'http://local.wproxy.org:1234/cgi-bin/rules/add',
    method: 'post',
    form: {
      name: 'test',
      value: '/test/ file://xxx'
    }
  });
  util.request({
    url: 'http://local.wproxy.org:1234/cgi-bin/rules/enable-default',
    method: 'post'
  });
  util.request({
    url: 'http://local.wproxy.org:1234/cgi-bin/rules/remove',
    method: 'post',
    form: {
      name: 'test',
      value: '/test/ file://xxx'
    }
  });
  util.request({
    url: 'http://local.wproxy.org:1234/cgi-bin/rules/rename',
    method: 'post',
    form: {
      name: 'test',
      newName: 'sssss'
    }
  });
  util.request({
    url: 'http://local.wproxy.org:1234/cgi-bin/rules/select',
    method: 'post',
    form: {
      name: 'test'
    }
  });
  util.request({
    url: 'http://local.wproxy.org:1234/cgi-bin/rules/unselect',
    method: 'post'
  });
  util.request({
    url: 'http://local.wproxy.org:1234/cgi-bin/rules/allow-multiple-choice',
    method: 'post'
  });
  util.request({
    url: 'http://local.wproxy.org:1234/cgi-bin/composer',
    method: 'post',
    form: {
      url: 'http://test.whistlejs.com/'
    }
  });
  util.request({
    url: 'http://local.wproxy.org:1234/cgi-bin/intercept-https-connects',
    method: 'post'
  });
  util.request({
    url: 'http://local.wproxy.org:1234/cgi-bin/hide-https-connects',
    method: 'post'
  });
  util.request({
    url: 'http://local.wproxy.org:1234/cgi-bin/do-not-show-again',
    method: 'post'
  });
  util.request({
    url: 'http://local.wproxy.org:1234/cgi-bin/check-update',
    method: 'post'
  });
  util.request({
    url: 'http://local.wproxy.org:1234/cgi-bin/rules/move-to',
    method: 'post'
  });
  util.request({
    url: 'http://local.wproxy.org:1234/cgi-bin/rules/get-sys-hosts',
    method: 'post'
  });


  util.request('http://local.whistle.com/index.html?doNotParseJson');
  util.request('http://local.whistle.com:1234/index.html?doNotParseJson');
  util.request('http://local.whistle.com/cgi-bin/log/get');
  util.request('http://local.whistle.com/cgi-bin/init');
  util.request('http://local.whistle.com:2345/cgi-bin/init');
  util.request('http://local.whistle.com/cgi-bin/get-data');
  util.request('http://local.whistle.com/cgi-bin/server-info');
  util.request('http://local.whistle.com/cgi-bin/values/list');
  util.request('http://local.whistle.com/cgi-bin/plugins/get-plugins');
  util.request('http://local.whistle.com/cgi-bin/rules/list');

  util.request('https://local.whistle.com/index.html?doNotParseJson');
  util.request('https://local.whistle.com:1234/index.html?doNotParseJson');
  util.request('https://local.whistle.com/cgi-bin/log/get');
  util.request('https://local.whistle.com/cgi-bin/init');
  util.request('https://local.whistle.com:2345/cgi-bin/init');
  util.request('https://local.whistle.com/cgi-bin/get-data');
  util.request('https://local.whistle.com/cgi-bin/server-info');
  util.request('https://local.whistle.com/cgi-bin/values/list');
  util.request('https://local.whistle.com/cgi-bin/plugins/get-plugins');
  util.request('https://local.whistle.com/cgi-bin/rules/list');
  util.request('https://local.whistle.com/whistle.test');
  util.request('http://local.whistle.com/whistle.test');
  util.request('https://local.whistle.com/plugin.test');
  util.request('http://local.whistle.com/plugin.test');
  util.request({
    url: 'http://local.whistle.com/cgi-bin/values/add',
    method: 'post',
    form: {
      name: 'test',
      value: '123'
    }
  }, function() {
    util.request({
      url: 'http://local.whistle.com/cgi-bin/values/rename',
      method: 'post',
      form: {
        name: 'test',
        newName: '123'
      }
    }, function() {
      util.request({
        url: 'http://local.whistle.com/cgi-bin/values/remove',
        method: 'post',
        form: {
          name: '123'
        }
      });
    });
  });
  util.request({
    url: 'http://local.whistle.com/cgi-bin/values/move-to',
    method: 'post',
    form: {
      to: 'test',
      from: 'abc'
    }
  });
  util.request({
    url: 'http://local.whistle.com/cgi-bin/rules/add',
    method: 'post',
    form: {
      name: 'test',
      value: '/test/ file://xxx'
    }
  });
  util.request({
    url: 'http://local.whistle.com/cgi-bin/rules/enable-default',
    method: 'post'
  });
  util.request({
    url: 'http://local.whistle.com/cgi-bin/rules/remove',
    method: 'post',
    form: {
      name: 'test',
      value: '/test/ file://xxx'
    }
  });
  util.request({
    url: 'http://local.whistle.com/cgi-bin/rules/rename',
    method: 'post',
    form: {
      name: 'test',
      newName: 'sssss'
    }
  });
  util.request({
    url: 'http://local.whistle.com/cgi-bin/rules/select',
    method: 'post',
    form: {
      name: 'test'
    }
  });
  util.request({
    url: 'http://local.whistle.com/cgi-bin/rules/unselect',
    method: 'post'
  });
  util.request({
    url: 'http://local.whistle.com/cgi-bin/rules/allow-multiple-choice',
    method: 'post'
  });
  uti
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

