<!-- label=GHSA-rjg7-r26h-cfp2 call=1 hash=db653417b4 -->
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
- OSV ID: GHSA-rjg7-r26h-cfp2
- CVE: CVE-2026-54494
- CWE: CWE-918
- Ecosystem / Package: Packagist / phanan/koel
- Repository: https://github.com/koel/koel
- Official Summary: Koel: Full-read SSRF via podcast enclosure URL: isPublicHost() filter_var guard does not reject NAT64 (64:ff9b::/96) or 6to4 (2002::/16) IPv6-transition wrappers of internal IPv4

# Reference Patch (Historical human fix; hidden from evaluated agents)
```diff
diff --git a/app/Ai/Tools/AddRadioStation.php b/app/Ai/Tools/AddRadioStation.php
index 737cae2bf1096c55a2aa03f67e001d1d73c22559..863b57d4b092d832e8b1379b5e7da6ac2467a86f 100644
--- a/app/Ai/Tools/AddRadioStation.php
+++ b/app/Ai/Tools/AddRadioStation.php
@@ -43,6 +43,7 @@ class AddRadioStation implements Tool
 
         $validator = Validator::make(['url' => $request['url']], [
             'url' => [
+                'bail',
                 'required',
                 'url',
                 Rule::unique('radio_stations')->where(static fn (Builder $query) => $query->where('user_id', $userId)),
diff --git a/app/Helpers/Network.php b/app/Helpers/Network.php
deleted file mode 100644
index 248a54473374739bf30822e30fde4cfd6b8aa008..0000000000000000000000000000000000000000
--- a/app/Helpers/Network.php
+++ /dev/null
@@ -1,69 +0,0 @@
-<?php
-
-namespace App\Helpers;
-
-use Illuminate\Support\Uri;
-use Throwable;
-
-class Network
-{
-    private const array SAFE_URL_SCHEMES = ['http', 'https'];
-
-    /**
-     * Check if a URL is safe to reach: HTTP/HTTPS scheme + a public host.
-     * Does NOT perform any network calls beyond DNS resolution.
-     * For full validation including effective-URL-after-redirect, use the SafeUrl validation rule.
-     */
-    public function isSafeUrl(string $url): bool
-    {
-        try {
-            $uri = Uri::of($url);
-        } catch (Throwable) {
-            return false;
-        }
-
-        if (!in_array($uri->scheme(), self::SAFE_URL_SCHEMES, true)) {
-            return false;
-        }
-
-        $host = $uri->host();
-
-        return $host !== '' && $this->isPublicHost($host);
-    }
-
-    /**
-     * Check if a host resolves only to public (non-private, non-reserved) IP addresses.
-     * Validates both A (IPv4) and AAAA (IPv6) records. All resolved IPs must be public.
-     */
-    public function isPublicHost(string $host): bool
-    {
-        if (filter_var($host, FILTER_VALIDATE_IP)) {
-            return (
-                filter_var($host, FILTER_VALIDATE_IP, FILTER_FLAG_NO_PRIV_RANGE | FILTER_FLAG_NO_RES_RANGE) !== false
-            );
-        }
-
-        try {
-            $records = array_merge(dns_get_record($host, DNS_A) ?: [], dns_get_record($host, DNS_AAAA) ?: []);
-        } catch (Throwable) {
-            return false;
-        }
-
-        if ($records === []) {
-            return false;
-        }
-
-        foreach ($records as $record) {
-            $ip = $record['ip'] ?? $record['ipv6'] ?? null;
-
-            if (
-                !$ip
-                || filter_var($ip, FILTER_VALIDATE_IP, FILTER_FLAG_NO_PRIV_RANGE | FILTER_FLAG_NO_RES_RANGE) === false
-            ) {
-                return false;
-            }
-        }
-
-        return true;
-    }
-}
diff --git a/app/Helpers/SafeHttp.php b/app/Helpers/SafeHttp.php
deleted file mode 100644
index 0c2560415d28e46d31321ca6d146cfd0ad87a05f..0000000000000000000000000000000000000000
--- a/app/Helpers/SafeHttp.php
+++ /dev/null
@@ -1,80 +0,0 @@
-<?php
-
-namespace App\Helpers;
-
-use App\Exceptions\UnsafeUrlException;
-use GuzzleHttp\Client;
-use GuzzleHttp\HandlerStack;
-use GuzzleHttp\Middleware;
-use Psr\Http\Message\RequestInterface;
-use Psr\Http\Message\ResponseInterface;
-use Psr\Http\Message\UriInterface;
-
-/**
- * Defenses for SSRF on outbound HTTP. Every call site that follows redirects
- * needs per-hop validation: an attacker-controlled URL can pass the initial
- * SafeUrl check, then 302 to 127.0.0.1, 169.254.169.254, etc.
- *
- * Consumers using Laravel Http facade: `Http::withOptions(SafeHttp::redirectOptions())`.
- * Consumers needing a PSR-18 client (e.g. Poddle): `SafeHttp::guzzleClient()`.
- *
- * Note: this addresses redirect-SSRF only. DNS rebinding via TOCTOU between
- * the validator's DNS lookup and the HTTP client's connect-time lookup is a
- * separate concern that requires IP pinning (e.g. curl's CURLOPT_RESOLVE) and
- * is tracked separately.
- */
-class SafeHttp
-{
-    public function __construct(
-        private readonly Network $network,
-    ) {}
-
-    /**
-     * Returns the `allow_redirects` options that re-validate every redirect
-     * target via Network::isSafeUrl, throwing UnsafeUrlException on a private
-     * or reserved target.
-     *
-     * @return array<string, mixed>
-     */
-    public function redirectOptions(int $max = 5): array
-    {
-        return [
-            'allow_redirects' => [
-                'max' => $max,
-                'on_redirect' => function (
-                    RequestInterface $request,
-                    ResponseInterface $response,
-                    UriInterface $uri,
-                ): void {
-                    if (!$this->network->isSafeUrl((string) $uri)) {
-                        throw UnsafeUrlException::forUrl((string) $uri);
-                    }
-                },
-            ],
-        ];
-    }
-
-    /**
-     * Build a PSR-18 client that applies the same per-redirect-hop validation
-     * via Guzzle middleware. Use for libraries that take an injected client
-     * (e.g. PhanAn\Poddle\Poddle::fromUrl()).
-     */
-    public function guzzleClient(int $timeoutInSeconds = 30): Client
-    {
-        $stack = HandlerStack::create();
-
-        $stack->push(Middleware::mapRequest(function (RequestInterface $request): RequestInterface {
-            if (!$this->network->isSafeUrl((string) $request->getUri())) {
-                throw UnsafeUrlException::forUrl((string) $request->getUri());
-            }
-
-            return $request;
-        }));
-
-        return new Client([
-            'handler' => $stack,
-            'timeout' => $timeoutInSeconds,
-            ...$this->redirectOptions(),
-        ]);
-    }
-}
diff --git a/app/Http/Requests/API/Radio/RadioStationStoreRequest.php b/app/Http/Requests/API/Radio/RadioStationStoreRequest.php
index e3436d0f8b20aadad389708db5af6077d27621f7..a233ebc20a795f12dfa993fe8432e6664621ae1b 100644
--- a/app/Http/Requests/API/Radio/RadioStationStoreRequest.php
+++ b/app/Http/Requests/API/Radio/RadioStationStoreRequest.php
@@ -24,6 +24,7 @@ class RadioStationStoreRequest extends Request
     {
         return [
             'url' => [
+                'bail',
                 'required',
                 'url',
                 Rule::unique('radio_stations')->where(function ($query) {
diff --git a/app/Http/Requests/API/Radio/RadioStationUpdateRequest.php b/app/Http/Requests/API/Radio/RadioStationUpdateRequest.php
index ec18b5730496d5311341b2bcf82038759ba8f48e..8336e22074d3a99228f2c5028655bac696f0d512 100644
--- a/app/Http/Requests/API/Radio/RadioStationUpdateRequest.php
+++ b/app/Http/Requests/API/Radio/RadioStationUpdateRequest.php
@@ -24,6 +24,7 @@ class RadioStationUpdateRequest extends Request
     {
         return [
             'url' => [
+                'bail',
                 'required',
                 'url',
                 Rule::unique('radio_stations')
diff --git a/app/Http/Requests/Subsonic/CreateInternetRadioStationRequest.php b/app/Http/Requests/Subsonic/CreateInternetRadioStationRequest.php
index d4f79e88c678423b9af10a40458f8b435b5c1d27..c3010a6f8ee08e4c88e94ae4377bce6c46dfb969 100644
--- a/app/Http/Requests/Subsonic/CreateInternetRadioStationRequest.php
+++ b/app/Http/Requests/Subsonic/CreateInternetRadioStationRequest.php
@@ -17,7 +17,7 @@ class CreateInternetRadioStationRequest extends Request
     public function rules(): array
     {
         return [
-            'streamUrl' => ['required', 'url', new SafeUrl(), new HasAudioContentType()],
+            'streamUrl' => ['bail', 'required', 'url', new SafeUrl(), new HasAudioContentType()],
             'name' => ['required', 'string'],
             'homepageUrl' => ['nullable', 'string'],
         ];
diff --git a/app/Http/Requests/Subsonic/UpdateInternetRadioStationRequest.php b/app/Http/Requests/Subsonic/UpdateInternetRadioStationRequest.php
index d0b62c42f7b6f9e1fff5a6b5643f494c2b0d4775..e13a69c8be7d0508a6483a39001396594d7caa7b 100644
--- a/app/Http/Requests/Subsonic/UpdateInternetRadioStationRequest.php
+++ b/app/Http/Requests/Subsonic/UpdateInternetRadioStationRequest.php
@@ -19,7 +19,7 @@ class UpdateInternetRadioStationRequest extends Request
     {
         return [
             'id' => ['required', 'string'],
-            'streamUrl' => ['required', 'url', new SafeUrl(), new HasAudioContentType()],
+            'streamUrl' => ['bail', 'required', 'url', new SafeUrl(), new HasAudioContentType()],
             'name' => ['required', 'string'],
             'homepageUrl' => ['nullable', 'string'],
         ];
diff --git a/app/Providers/AppServiceProvider.php b/app/Providers/AppServiceProvider.php
index 76caf306e13cd651cc563d6af64c9928d5cf7b5a..66e2632fd5a6151656a5bd1ebbcd37f2b3bf31d3 100644
--- a/app/Providers/AppServiceProvider.php
+++ b/app/Providers/AppServiceProvider.php
@@ -3,7 +3,6 @@
 namespace App\Providers;
 
 use App\Enums\Acl\Role;
-use App\Helpers\SafeHttp;
 use App\Models\Album;
 use App\Models\Artist;
 use App\Models\Genre;
@@ -34,7 +33,6 @@ use Illuminate\Http\Resources\Json\JsonResource;
 use Illuminate\Support\Facades\Gate;
 use Illuminate\Support\Facades\Route;
 use Illuminate\Support\ServiceProvider;
-use Psr\Http\Client\ClientInterface;
 use SpotifyWebAPI\Session as SpotifySession;
 
 class AppServiceProvider extends ServiceProvider
@@ -77,11 +75,6 @@ class AppServiceProvider extends ServiceProvider
 
         $this->app->bind(LicenseServiceInterface::class, LicenseService::class);
 
-        // PSR-18 client used by libraries that fetch external URLs (e.g. Poddle).
-        // Backed by SafeHttp so every redirect hop is re-validated against the
-        // SafeUrl rules — closes the redirect-SSRF leg of GHSA-6qvr-wjmv-v8mm.
-        $this->app->bind(ClientInterface::class, static fn (): ClientInterface => app(SafeHttp::class)->guzzleClient());
-
         $this->app->bind(ScannerCacheStrategyContract::class, static function () {
             // Use a no-cache strategy for unit tests to ensure consistent results
             return app()->runningUnitTests() ? app(ScannerNoCacheStrategy::class) : app(ScannerCacheStrategy::class);
diff --git a/app/Rules/HasAudioContentType.php b/app/Rules/HasAudioContentType.php
index 98be9659b5e2f67eb0553768f2304f7e1c80d230..ec2100d7cadac0b008b18d63ed034ea8dba50b07 100644
--- a/app/Rules/HasAudioContentType.php
+++ b/app/Rules/HasAudioContentType.php
@@ -2,20 +2,26 @@
 
 namespace App\Rules;
 
-use App\Helpers\SafeHttp;
+use App\Exceptions\UnsafeUrlException;
+use App\Services\Network\SafeHttp;
 use Closure;
 use Illuminate\Contracts\Validation\ValidationRule;
-use Illuminate\Support\Facades\Http;
 use Illuminate\Support\Str;
 use Illuminate\Translation\PotentiallyTranslatedString;
 use Throwable;
 
 /**
- * Validates that a URL serves audio content.
- * Should be used after SafeUrl to ensure the URL is safe to reach.
+ * Validates that a URL serves audio content. Pair with SafeUrl + 'bail' on the
+ * field so this rule never runs on a URL the safety check has already rejected.
  */
 class HasAudioContentType implements ValidationRule
 {
+    public function __construct(
+        private ?SafeHttp $http = null,
+    ) {
+        $this->http ??= app(SafeHttp::class);
+    }
+
     /** @param Closure(string, ?string=): PotentiallyTranslatedString $fail */
     public function validate(string $attribute, mixed $value, Closure $fail): void
     {
@@ -23,6 +29,10 @@ class HasAudioContentType implements ValidationRule
 
         try {
             $contentType = $this->resolveContentType($url);
+        } catch (UnsafeUrlException) {
+            $fail('The :attribute must point to a public URL.');
+
+            return;
         } catch (Throwable) {
             $fail("The $attribute couldn't be reached.");
 
@@ -41,23 +51,22 @@ class HasAudioContentType implements ValidationRule
      */
     private function resolveContentType(string $url): string
     {
-        $redirectOptions = app(SafeHttp::class)->redirectOptions();
-
-        // Try HEAD first — fast and lightweight
+        // Try HEAD first — fast and lightweight. Let UnsafeUrlException propagate
+        // (don't fall back to GET on safety failures — the URL is blocked, not
+        // just HEAD-incompatible).
         try {
-            $response = Http::withOptions($redirectOptions)->head($url);
+            $response = $this->http->head($url);
 
             if ($response->successful()) {
                 return $response->header('Content-Type');
             }
+        } catch (UnsafeUrlException $e) {
+            throw $e;
         } catch (Throwable) { // @mago-expect lint:no-empty-catch-clause -- HEAD may time out or fail on streaming servers; fall through to GET below.
         }
 
-        // Fall back to GET with ICY headers — streaming servers often only respond to GET
-        $response = Http::withHeaders(['Icy-MetaData' => '1'])->withOptions([
-            ...$redirectOptions,
-            'stream' => true,
-        ])->get($url);
+        // Fall back to GET as a stream with ICY headers — Shoutcast/Icecast only respond to GET
+        $response = $this->http->getAsStream($url, ['Icy-MetaData' => '1']);
 
         return $response->header('Content-Type');
     }
diff --git a/app/Rules/SafeUrl.php b/app/Rules/SafeUrl.php
index ac201a527741c5238d2b04c932ad270f0e0920db..251b5270fc1a1f29926ce5b99811b9b2dd00a030 100644
--- a/app/Rules/SafeUrl.php
+++ b/app/Rules/SafeUrl.php
@@ -3,28 +3,27 @@
 namespace App\Rules;
 
 use App\Exceptions\UnsafeUrlException;
-use App\Helpers\Network;
-use App\Helpers\SafeHttp;
+use App\Services\Network\SafeHttp;
 use Closure;
 use Illuminate\Contracts\Validation\ValidationRule;
-use Illuminate\Support\Facades\Http;
 use Illuminate\Support\Uri;
 use Illuminate\Translation\PotentiallyTranslatedString;
 use Throwable;
 
 /**
- * Validates that a URL does not resolve to a private or reserved IP address,
- * preventing SSRF attacks against internal services.
- * Also follows redirects and validates the effective URL.
+ * Validates that a URL is safe to fetch — its host (and every redirect target's
+ * host) resolves only to public IP addresses. Delegates the SSRF guarantees to
+ * SafeHttp; the rule itself just translates UnsafeUrlException into the
+ * appropriate validation failure message.
  */
 class SafeUrl implements ValidationRule
 {
     private const array ALLOWED_SCHEMES = ['http', 'https'];
 
     public function __construct(
-        private ?Network $network = null,
+        private ?SafeHttp $safeHttp = null,
     ) {
-        $this->network ??= app(Network::class);
+        $this->safeHttp ??= app(SafeHttp::class);
     }
 
     /** @param Closure(string, ?string=): PotentiallyTranslatedString $fail */
@@ -44,39 +43,19 @@ class SafeUrl implements ValidationRule
             return;
         }
 
-        if (!$this->network->isPublicHost($uri->host())) {
-            $fail('The :attribute must point to a public URL.');
-
-            return;
-        }
-
-        $redirectOptions = app(SafeHttp::class)->redirectOptions();
-
         try {
-            $response = Http::withOptions($redirectOptions)->head((string) $value);
+            $this->safeHttp->head((string) $value);
         } catch (UnsafeUrlException) {
             $fail('The :attribute must point to a public URL.');
-
-            return;
         } catch (Throwable) {
-            // Some streaming servers don't support HEAD — try GET
+            // Some streaming servers don't support HEAD — try GET as a stream.
             try {
-                $response = Http::withOptions([...$redirectOptions, 'stream' => true])->get((string) $value);
+                $this->safeHttp->getAsStream((string) $value);
             } catch (UnsafeUrlException) {
                 $fail('The :attribute must point to a public URL.');
-
-                return;
             } catch (Throwable) {
                 $fail("The $attribute couldn't be reached.");
-
-                return;
             }
         }
-
-        $effectiveHost = $response->effectiveUri()?->getHost();
-
-        if ($effectiveHost && !$this->network->isPublicHost($effectiveHost)) {
-            $fail('The :attribute must point to a public URL.');
-        }
     }
 }
diff --git a/app/Services/DownloadService.php b/app/Services/DownloadService.php
index e570884c02d8089184b57525cd5779645e5fd7a5..f048f36b1d24d35804aa3f8cabf76329a7e5fe7f 100644
--- a/app/Services/DownloadService.php
+++ b/app/Services/DownloadService.php
@@ -7,6 +7,7 @@ use App\Exceptions\DownloadLimitExceededException;
 use App\Models\Song;
 use App\Models\User;
 use App\Repositories\SongRepository;
+use App\Services\Network\SafeHttp;
 use App\Services\SongStorages\CloudStorage;
 use App\Services\SongStorages\SongStorageFactory;
 use App\Values\Downloadable;
@@ -20,6 +21,7 @@ class DownloadService
 {
     public function __construct(
         private readonly SongRepository $songRepository,
+        private readonly SafeHttp $http,
         #[Config('koel.download.limit')]
         private readonly int $downloadLimit = 0,
     ) {}
@@ -102,7 +104,7 @@ class DownloadService
         }
 
         if ($song->isEpisode()) {
-            return EpisodePlayable::getForEpisode($song)->path;
+            return EpisodePlayable::getForEpisode($song, $this->http)->path;
         }
 
         $localPath = SongStorageFactory::make($song->storage)->getLocalPath($song->path);
diff --git a/app/Services/Network/Network.php b/app/Services/Network/Network.php
new file mode 100644
index 0000000000000000000000000000000000000000..0c3a96f0b3ef36d55e3cddfdd5773c8940513d4d
--- /dev/null
+++ b/app/Services/Network/Network.php
@@ -0,0 +1,96 @@
+<?php
+
+namespace App\Services\Network;
+
+use Illuminate\Support\Arr;
+use Illuminate\Support\Uri;
+use IPLib\Factory;
+use IPLib\Range\Type as RangeType;
+use Throwable;
+
+class Network
+{
+    /**
+     * Check if a URL is safe to reach: HTTP/HTTPS scheme + a public host.
+     * Does NOT perform any network calls beyond DNS resolution.
+     * For full validation including effective-URL-after-redirect, use the SafeUrl validation rule.
+     */
+    public function isSafeUrl(string $url): bool
+    {
+        try {
+            $uri = Uri::of($url);
+        } catch (Throwable) {
+            return false;
+        }
+
+        if (!in_array($uri->scheme(), ['http', 'https'], true)) {
+            return false;
+        }
+
+        return $this->isPublicHost($uri->host());
+    }
+
+    /**
+     * Check if a host resolves only to public (non-private, non-reserved) IP addresses.
+     * Validates both A (IPv4) and AAAA (IPv6) records. All resolved IPs must be public.
+     */
+    public function isPublicHost(?string $host): bool
+    {
+        return $host && $this->resolveToPublicIps($host);
+    }
+
+    /**
+     * Resolve a host to its public IP addresses. Returns an empty list if the
+     * host can't be resolved, has no records, or has *any* non-public record —
+     * fail-closed semantics: a mixed public/private answer rejects the whole
+     * host. The strict behavior is needed by `isPublicHost()` consumers that
+     * don't go through curl (e.g. RadioStreamProxy uses fopen, which does its
+     * own DNS lookup and could land on the private record).
+     *
+     * Callers that DO go through curl additionally feed the returned list to
+     * CURLOPT_RESOLVE to pin connect-time DNS onto the validated IPs, closing
+     * the DNS-rebinding TOCTOU window between validation and connect.
+     *
+     * "Public" means ip-lib's RangeType::T_PUBLIC — excludes private, loopback,
+     * link-local, multicast, broadcast, reserved, documentation, NAT64
+     * (T_RESERVED), 6to4 wrappers of private IPv4 (classified by embedded v4),
+     * Teredo, CGNAT.
+     *
+     * @return list<string>
+     */
+    public function resolveToPublicIps(string $host): array
+    {
+        $literal = Factory::parseAddressString($host);
+
+        if ($literal) {
+            return $literal->getRangeType() === RangeType::T_PUBLIC ? [$host] : [];
+        }
+
+        try {
+            $a = dns_get_record($host, DNS_A);
+            $aaaa = dns_get_record($host, DNS_AAAA);
+        } catch (Throwable) {
+            return [];
+        }
+
+        if ($a === false || $aaaa === false) {
+            // dns_get_record returning false is a resolver failure — fail closed
+            // rather than treating it as "host has no records".
+            return [];
+        }
+
+        $ips = [];
+
+        foreach (array_merge($a, $aaaa) as $record) {
+            $ip = Arr::get($record, 'ip') ?? Arr::get($record, 'ipv6');
+
+            if (!$ip || Factory::parseAddressString($ip)?->getRangeType() !== RangeType::T_PUBLIC) {
+                return [];
+            }
+
+            $ips[] = $ip;
+        }
+
+        return $ips;
+    }
+}
diff --git a/app/Services/Network/SafeHttp.php b/app/Services/Network/SafeHttp.php
new file mode 100644
index 0000000000000000000000000000000000000000..44cf178e37b6f9d6cff6997612df65aa541851a9
--- /dev/null
+++ b/app/Services/Network/SafeHttp.php
@@ -0,0 +1,152 @@
+<?php
+
+namespace App\Services\Network;
+
+use App\Exceptions\UnsafeUrlException;
+use Closure;
+use GuzzleHttp\Client;
+use GuzzleHttp\HandlerStack;
+use Illuminate\Http\Client\PendingRequest;
+use Illuminate\Http\Client\Response;
+use Illuminate\Support\Facades\Http;
+use Psr\Http\Message\RequestInterface;
+
+/**
+ * SSRF-hardened wrapper around Laravel's Http facade. Use it anywhere you fetch
+ * a URL that came from outside your trust boundary. Both legs of the SSRF threat
+ * model are closed for every request including each redirect hop:
+ *
+ *  - Redirect SSRF: every redirect target's host is re-resolved and re-validated.
+ *  - DNS rebinding (TOCTOU): the resolved IPs are pinned into curl via
+ *    CURLOPT_RESOLVE before each connect, so curl can't ask DNS again and get a
+ *    different (private) IP.
+ *
+ * Both protections live in a single Guzzle middleware. Guzzle re-traverses the
+ * handler stack for each redirect hop, so the middleware fires on the initial
+ * request AND every redirect target — no manual redirect loop needed.
+ *
+ * Throws UnsafeUrlException whenever any request URL's host fails to resolve to
+ * public IPs (initial URL or any redirect target).
+ *
+ * For PSR-18 consumers (e.g. PhanAn\Poddle\Poddle::fromUrl()), use
+ * SafeHttp::getPinnedGuzzleClient($url) instead.
+ */
+class SafeHttp
+{
+    public function __construct(
+        private readonly Network $network,
+    ) {}
+
+    /** Issue a HEAD request against the URL with full SSRF protection. */
+    public function head(string $url, array $headers = []): Response
+    {
+        return $this->buildRequest($headers)->head($url);
+    }
+
+    /** Issue a GET request against the URL with full SSRF protection. */
+    public function get(string $url, array $headers = []): Response
+    {
+        return $this->buildRequest($headers)->get($url);
+    }
+
+    /**
+     * GET the URL as a stream (response body lazily read). Use for arbitrarily
+     * large or unbounded payloads — e.g. live radio streams whose content type
+     * we want to inspect without buffering the body.
+     */
+    public function getAsStream(string $url, array $headers = []): Response
+    {
+        return $this->buildRequest($headers, ['stream' => true])->get($url);
+    }
+
+    /** Download the URL into a file path on disk, with full SSRF protection. */
+    public function download(string $url, string $sinkPath, array $headers = []): Response
+    {
+        return $this->buildRequest($headers)->sink($sinkPath)->get($url);
+    }
+
+    /**
+     * Build a PSR-18 client whose handler stack applies the same hop-by-hop
+     * pinning + validation as the Laravel Http methods above. Use for libraries
+     * that take an injected client (e.g. PhanAn\Poddle\Poddle::fromUrl()).
+     */
+    public function getPinnedGuzzleClient(string $url, bool $trackRedirects = false, int $timeoutInSeconds = 30): Client
+    {
+        $allowRedirects = ['max' => 5];
+
+        if ($trackRedirects) {
+            $allowRedirects['track_redirects'] = true;
+        }
+
+        return new Client([
+            'handler' => $this->buildHandlerStack(),
+            'timeout' => $timeoutInSeconds,
+            'allow_redirects' => $allowRedirects,
+        ]);
+    }
+
+    /**
+     * @param array<string, string> $headers
+     * @param array<string, mixed> $extraOptions
+     */
+    private function buildRequest(array $headers, array $extraOptions = []): PendingRequest
+    {
+        // withMiddleware pushes onto Laravel's existing handler stack — required
+        // so Http::fake() in tests still intercepts. Setting `handler` via
+        // withOptions would *replace* Laravel's stack and break the fake.
+        $request = Http::withMiddleware($this->pinAndValidateMiddleware());
+
+        if ($extraOptions !== []) {
+            $request = $request->withOptions($extraOptions);
+        }
+
+        return $headers === [] ? $request : $request->withHeaders($headers);
+    }
+
+    /**
+     * Guzzle handler stack with the pin-and-validate middleware. Used only by
+     * getPinnedGuzzleClient (no Laravel Http::fake involvement there).
+     */
+    private function buildHandlerStack(): HandlerStack
+    {
+        $stack = HandlerStack::create();
+        $stack->push($this->pinAndValidateMiddleware(), 'safe_http_pin');
+
+        return $stack;
+    }
+
+    /**
+     * Middleware that, for every outbound request: resolves the host's public
+     * IPs, throws UnsafeUrlException if any are private/reserved or DNS fails,
+     * and appends CURLOPT_RESOLVE entries to the transfer options so curl uses
+     * the validated IPs instead of doing a fresh (rebindable) DNS lookup.
+     */
+    private function pinAndValidateMiddleware(): Closure
+    {
+        $network = $this->network;
+
+        return static function (callable $next) use ($network): Closure {
+            return static function (RequestInterface $request, array $options) use ($next, $network) {
+                $uri = $request->getUri();
+                $host = $uri->getHost();
+
+                $ips = $network->resolveToPublicIps($host);
+
+                throw_unless($ips, UnsafeUrlException::forUrl((string) $uri));
+
+                // IP literals don't trigger a DNS lookup, so nothing to pin.
+                if (!filter_var($host, FILTER_VALIDATE_IP)) {
+                    $port = $uri->getPort() ?? ($uri->getScheme() === 'https' ? 443 : 80);
+
+                    $options['curl'] ??= [];
+                    $options['curl'][CURLOPT_RESOLVE] = [
+                        ...($options['curl'][CURLOPT_RESOLVE] ?? []),
+                        ...array_map(static fn (string $ip): string => "{$host}:{$port}:{$ip}", $ips),
+                    ];
+                }
+
+                return $next($request, $options);
+            };
+        };
+    }
+}
diff --git a/app/Services/Podcast/PodcastService.php b/app/Services/Podcast/PodcastService.php
index 11ab7e7d91a0a758f192a8c38c19ecbca43ea8c2..a95791d719d9020260e76b1f67efb8559d5af6bd 100644
--- a/app/Services/Podcast/PodcastService.php
+++ b/app/Services/Podcast/PodcastService.php
@@ -6,8 +6,6 @@ use App\Events\UserUnsubscribedFromPodcast;
 use App\Exceptions\FailedToParsePodcastFeedException;
 use App\Exceptions\UnsafePodcastFeedUrlException;
 use App\Exceptions\UserAlreadySubscribedToPodcastException;
-use App\Helpers\Network;
-use App\Helpers\SafeHttp;
 use App\Helpers\Uuid;
 use App\Models\Podcast;
 use App\Models\PodcastUserPivot;
@@ -15,13 +13,14 @@ use App\Models\Song as Episode;
 use App\Models\User;
 use App\Repositories\PodcastRepository;
 use App\Repositories\SongRepository;
+use App\Services\Network\Network;
+use App\Services\Network\SafeHttp;
 use Carbon\Carbon;
 use GuzzleHttp\Client;
 use GuzzleHttp\RedirectMiddleware;
 use GuzzleHttp\RequestOptions;
 use Illuminate\Support\Arr;
 use Illuminate\Support\Facades\DB;
-use Illuminate\Support\Facades\Http;
 use Illuminate\Support\Facades\Log;
 use PhanAn\Poddle\Poddle;
 use PhanAn\Poddle\Values\Episode as EpisodeValue;
@@ -225,9 +224,7 @@ class PodcastService
         }
 
         try {
-            $lastModified = Http::withOptions($this->safeHttp->redirectOptions())
-                ->head($podcast->url)
-                ->header('Last-Modified');
+            $lastModified = $this->safeHttp->head($podcast->url)->header('Last-Modified');
 
             if (!$lastModified) {
                 return true;
@@ -254,7 +251,7 @@ class PodcastService
             return null;
         }
 
-        $client ??= $this->safeHttp->guzzleClient();
+        $client ??= $this->safeHttp->getPinnedGuzzleClient($url, trackRedirects: true);
 
         try {
             $response = $client->request($method, $url, [
@@ -263,10 +260,6 @@ class PodcastService
                     'Origin' => '*',
                 ],
                 RequestOptions::HTTP_ERRORS => false,
-                RequestOptions::ALLOW_REDIRECTS => [
-                    ...$this->safeHttp->redirectOptions()['allow_redirects'],
-                    'track_redirects' => true,
-                ],
             ]);
 
             $redirects = Arr::wrap($response->getHeader(RedirectMiddleware::HISTORY_HEADER));
@@ -307,6 +300,6 @@ class PodcastService
             throw UnsafePodcastFeedUrlException::create($url);
         }
 
-        return Poddle::fromUrl($url, 5 * 60, $this->client);
+        return Poddle::fromUrl($url, 5 * 60, $this->client ?? $this->safeHttp->getPinnedGuzzleClient($url));
     }
 }
diff --git a/app/Services/Radio/RadioStreamProxy.php b/app/Services/Radio/RadioStreamProxy.php
index cc4eb55961f76aaa0885055f232e817416d63f60..2ffd9777335bf3e07d23cd555a8c6a9f3dc56b3d 100644
--- a/app/Services/Radio/RadioStreamProxy.php
+++ b/app/Services/Radio/RadioStreamProxy.php
@@ -2,8 +2,8 @@
 
 namespace App\Services\Radio;
 
-use App\Helpers\Network;
 use App\Models\RadioStation;
+use App\Services\Network\Network;
 
 class RadioStreamProxy
 {
diff --git a/app/Services/Streamer/Adapters/PodcastStreamerAdapter.php b/app/Services/Streamer/Adapters/PodcastStreamerAdapter.php
index 5c8f0d1f05e2f308a92158100c4e29be672d75ff..b35a767d442175b2c74ecb59b0a6da8aa862cd7e 100644
--- a/app/Services/Streamer/Adapters/PodcastStreamerAdapter.php
+++ b/app/Services/Streamer/Adapters/PodcastStreamerAdapter.php
@@ -3,6 +3,7 @@
 namespace App\Services\Streamer\Adapters;
 
 use App\Models\Song as Episode;
+use App\Services\Network\SafeHttp;
 use App\Services\Podcast\PodcastService;
 use App\Services\Streamer\Adapters\Concerns\StreamsLocalPath;
 use App\Values\Podcast\EpisodePlayable;
@@ -15,6 +16,7 @@ class PodcastStreamerAdapter implements StreamerAdapter
 
     public function __construct(
         private readonly PodcastService $podcastService,
+        private readonly SafeHttp $http,
     ) {}
 
     /** @inheritDoc */
@@ -28,6 +30,6 @@ class PodcastStreamerAdapter implements StreamerAdapter
             return response()->redirectTo($streamableUrl);
         }
 
-        $this->streamLocalPath(EpisodePlayable::getForEpisode($song)->path);
+        $this->streamLocalPath(EpisodePlayable::getForEpisode($song, $this->http)->path);
     }
 }
diff --git a/app/Values/Podcast/EpisodePlayable.php b/app/Values/Podcast/EpisodePlayable.php
index fd85c20fd69320edeb1f0b813fe8cf513d0de94e..cf0aed767c123066a30b31eab1b7fe8348eaa6f3 100644
--- a/app/Values/Podcast/EpisodePlayable.php
+++ b/app/Values/Podcast/EpisodePlayable.php
@@ -2,17 +2,12 @@
 
 namespace App\Values\Podcast;
 
-use App\Exceptions\UnsafeUrlException;
-use App\Helpers\Network;
 use App\Models\Song as Episode;
+use App\Services\Network\SafeHttp;
 use Illuminate\Contracts\Support\Arrayable;
 use Illuminate\Contracts\Support\Jsonable;
 use Illuminate\Support\Facades\Cache;
 use Illuminate\Support\Facades\File;
-use Illuminate\Support\Facades\Http;
-use Psr\Http\Message\RequestInterface;
-use Psr\Http\Message\ResponseInterface;
-use Psr\Http\Message\UriInterface;
 
 final class EpisodePlayable implements Arrayable, Jsonable
 {
@@ -31,43 +26,20 @@ final class EpisodePlayable implements Arrayable, Jsonable
         return File::isReadable($this->path) && $this->checksum === File::hash($this->path);
     }
 
-    public static function getForEpisode(Episode $episode): self
+    public static function getForEpisode(Episode $episode, SafeHttp $safeHttp): self
     {
         /** @var self|null $cached */
         $cached = Cache::get("episode-playable.{$episode->id}");
 
-        return $cached?->valid() ? $cached : self::createForEpisode($episode);
+        return $cached?->valid() ? $cached : self::createForEpisode($episode, $safeHttp);
     }
 
-    private static function createForEpisode(Episode $episode): self
+    private static function createForEpisode(Episode $episode, SafeHttp $safeHttp): self
     {
         $file = artifact_path("episodes/{$episode->id}.mp3");
 
         if (!File::exists($file)) {
-            $network = app(Network::class);
-            $url = (string) $episode->path;
-
-            if (!$network->isSafeUrl($url)) {
-                throw UnsafeUrlException::forUrl($url);
-            }
-
-            Http::sink($file)
-                ->withOptions([
-                    'allow_redirects' => [
-                        'max' => 5,
-                        'on_redirect' => static function (
-                            RequestInterface $request,
-                            ResponseInterface $response,
-                            UriInterface $uri,
-                        ) use ($network): void {
-                            if (!$network->isSafeUrl((string) $uri)) {
-                                throw UnsafeUrlException::forUrl((string) $uri);
-                            }
-                        },
-                    ],
-                ])
-                ->get($url)
-                ->throw();
+            $safeHttp->download((string) $episode->path, $file)->throw();
         }
 
         $playable = new self($file, File::hash($file));
diff --git a/composer.json b/composer.json
index a5c4c96e0fb9d76244d120b90b098fd204f75731..e7cf3e7f748f8ce1f487b196bfe132b8c92eae50 100644
--- a/composer.json
+++ b/composer.json
@@ -53,7 +53,8 @@
     "enshrined/svg-sanitize": "^0.22.0",
     "phanan/poddle": "^1.2.4",
     "laravel/ai": "^0.7.0",
-    "league/flysystem-webdav": "^3.0"
+    "league/flysystem-webdav": "^3.0",
+    "mlocati/ip-lib": "^1.22"
   },
   "require-dev": {
     "roave/security-advisories": "dev-latest",
diff --git a/composer.lock b/composer.lock
index cd9b4ec6ec446125c9f31c3f4fe3a07287d52864..50eb62740c62622eefd94142a3d97f2b6fc0366d 100644
--- a/composer.lock
+++ b/composer.lock
@@ -4,7 +4,7 @@
         "Read more about it at https://getcomposer.org/doc/01-basic-usage.md#installing-dependencies",
         "This file is @generated automatically"
     ],
-    "content-hash": "d1437db343f05b61a0d00a522e577eee",
+    "content-hash": "ebc7649de19d849bafc5c7861481228b",
     "packages": [
         {
             "name": "algolia/algoliasearch-client-php",
@@ -4039,6 +4039,77 @@
             },
             "time": "2022-08-16T15:18:17+00:00"
         },
+        {
+            "name": "mlocati/ip-lib",
+            "version": "1.22.0",
+            "source": {
+                "type": "git",
+                "url": "https://github.com/mlocati/ip-lib.git",
+                "reference": "4e40ffd3bf9989db19403d89c4d8be44b87b8a91"
+            },
+            "dist": {
+                "type": "zip",
+                "url": "https://api.github.com/repos/mlocati/ip-lib/zipball/4e40ffd3bf9989db19403d89c4d8be44b87b8a91",
+                "reference": "4e40ffd3bf9989db19403d89c4d8be44b87b8a91",
+                "shasum": ""
+            },
+            "require": {
+                "php": ">=5.3.3"
+            },
+            "require-dev": {
+                "ext-pdo_sqlite": "*",
+                "phpunit/phpunit": "^4.8 || ^5.7 || ^6.5 || ^7.5 || ^8.5 || ^9.5"
+            },
+            "type": "library",
+            "autoload": {
+                "psr-4": {
+                    "IPLib\\": "src/"
+                }
+            },
+            "notification-url": "https://packagist.org/downloads/",
+            "license": [
+                "MIT"
+            ],
+            "authors": [
+                {
+                    "name": "Michele Locati",
+                    "email": "mlocati@gmail.com",
+                    "homepage": "https://github.com/mlocati",
+                    "role": "Author"
+                }
+            ],
+            "description": "Handle IPv4, IPv6 addresses and ranges",
+            "homepage": "https://github.com/mlocati/ip-lib",
+            "keywords": [
+                "IP",
+                "address",
+                "addresses",
+                "ipv4",
+                "ipv6",
+                "manage",
+                "managing",
+                "matching",
+                "network",
+                "networking",
+                "range",
+                "subnet"
+            ],
+            "support": {
+                "issues": "https://github.com/mlocati/ip-lib/issues",
+                "source": "https://github.com/mlocati/ip-lib/tree/1.22.0"
+            },
+            "funding": [
+                {
+                    "url": "https://github.com/sponsors/mlocati",
+                    "type": "github"
+                },
+                {
+                    "url": "https://paypal.me/mlocati",
+                    "type": "other"
+                }
+            ],
+            "time": "2025-10-15T12:35:09+00:00"
+        },
         {
             "name": "monolog/monolog",
             "version": "3.10.0",
diff --git a/tests/Fakes/FakeNetwork.php b/tests/Fakes/FakeNetwork.php
index d9f47bd2465dbe68cddd7dbf8019d87332da572a..2fbbbf864014f693469691aa50cb7d4dd3fb6988 100644
--- a/tests/Fakes/FakeNetwork.php
+++ b/tests/Fakes/FakeNetwork.php
@@ -2,9 +2,7 @@
 
 namespace Tests\Fakes;
 
-use App\Helpers\Network;
-use Illuminate\Support\Uri;
-use Throwable;
+use App\Services\Network\Network;
 
 /**
  * Skips DNS resolution so tests don't need real internet connectivity.
@@ -13,33 +11,28 @@ use Throwable;
  */
 class FakeNetwork extends Network
 {
-    private const array SAFE_SCHEMES = ['http', 'https'];
-
-    public function isSafeUrl(string $url): bool
+    /**
+     * Return a synthetic public IP for any non-IP host that would otherwise
+     * require DNS, and apply the literal-IP privacy check inline (no recursion
+     * back into isPublicHost). The pinned IP is never actually contacted in
+     * tests because Http::fake intercepts before curl runs.
+     *
+     * @return list<string>
+     */
+    public function resolveToPublicIps(string $host): array
     {
-        try {
-            $uri = Uri::of($url);
-        } catch (Throwable) {
-            return false;
-        }
-
-        if (!in_array($uri->scheme(), self::SAFE_SCHEMES, true)) {
-            return false;
+        if ($host === '') {
+            return [];
         }
 
-        $host = $uri->host();
-
-        return $host !== '' && $this->isPublicHost($host);
-    }
-
-    public function isPublicHost(string $host): bool
-    {
         if (filter_var($host, FILTER_VALIDATE_IP)) {
             return (
-                filter_var($host, FILTER_VALIDATE_IP, FILTER_FLAG_NO_PRIV_RANGE | FILTER_FLAG_NO_RES_RANGE) !== false
+                filter_var($host, FILTER_VALIDATE_IP, FILTER_FLAG_NO_PRIV_RANGE | FILTER_FLAG_NO_RES_RANGE)
+                    ? [$host]
+                    : []
             );
         }
 
-        return $host !== '';
+        return ['203.0.113.1'];
     }
 }
diff --git a/tests/Feature/RadioStationTest.php b/tests/Feature/RadioStationTest.php
index 4ea06c0d0cfb175d971165e5aef0e6cfa08c649f..8d8ed203837a130eadd4e3d0f0c31e22645a38b4 100644
--- a/tests/Feature/RadioStationTest.php
+++ b/tests/Feature/RadioStationTest.php
@@ -6,6 +6,7 @@ use App\Helpers\Ulid;
 use App\Http\Resources\RadioStationResource;
 use App\Models\Organization;
 use App\Models\RadioStation;
+use Illuminate\Http\Client\Request;
 use Illuminate\Support\Facades\Http;
 use PHPUnit\Framework\Attributes\Test;
 use Tests\TestCase;
@@ -23,6 +24,26 @@ class RadioStationTest extends TestCase
         Http::fake(['*' => Http::response('', 200, ['Content-Type' => 'audio/mpeg'])]);
     }
 
+    #[Test]
+    public function createWithPrivateUrlDoesNotProbeIt(): void
+    {
+        // bail on the validation rules must stop HasAudioContentType from probing
+        // a URL that SafeUrl has already rejected. Without bail, the HEAD/GET
+        // probe lands on the private host — SSRF (GHSA-jr4p-4xjh-fwvw).
+        $user = create_user();
+
+        $this->postAs(
+            '/api/radio/stations',
+            [
+                'url' => 'http://127.0.0.1/stream',
+                'name' => 'Internal',
+            ],
+            $user,
+        )->assertUnprocessable();
+
+        Http::assertNotSent(static fn (Request $request): bool => str_contains($request->url(), '127.0.0.1'));
+    }
+
     #[Test]
     public function create(): void
     {
diff --git a/tests/Integration/Services/Podcast/PodcastServiceTest.php b/tests/Integration/Services/Podcast/PodcastServiceTest.php
index eb4a13b13be269b68f4781fffd15e019555eab97..ad88a8ae48861d22f4ace7336ebfe50426cdef3b 100644
--- a/tests/Integration/Services/Podcast/PodcastServiceTest.php
+++ b/tests/Integration/Services/Podcast/PodcastServiceTest.php
@@ -277,7 +277,10 @@ class PodcastServiceTest extends TestCase
         ]);
 
         $handlerStack = HandlerStack::create($mock);
-        $client = new Client(['handler' => $handlerStack]);
+        $client = new Client([
+            'handler' => $handlerStack,
+            'allow_redirects' => ['track_redirects' => true],
+        ]);
 
         self::assertSame('https://assets.example.com/episode.mp3', $this->service->getStreamableUrl(
             'https://example.com/episode.mp3',
diff --git a/tests/Integration/Values/EpisodePlayableTest.php b/tests/Integration/Values/EpisodePlayableTest.php
index 8685533b5edb93f124d93515173c8f6f2c64ac24..6926a9485ea0054f8bf7dfd1344402d3b6348ac4 100644
--- a/tests/Integration/Values/EpisodePlayableTest.php
+++ b/tests/Integration/Values/EpisodePlayableTest.php
@@ -4,6 +4,7 @@ namespace Tests\Integration\Values;
 
 use App\Exceptions\UnsafeUrlException;
 use App\Models\Song;
+use App\Services\Network\SafeHttp;
 use App\Values\Podcast\EpisodePlayable;
 use Illuminate\Support\Facades\Cache;
 use Illuminate\Support\Facades\Http;
@@ -12,6 +13,15 @@ use Tests\TestCase;
 
 class EpisodePlayableTest extends TestCase
 {
+    private SafeHttp $safeHttp;
+
+    public function setUp(): void
+    {
+        parent::setUp();
+
+        $this->safeHttp = app(SafeHttp::class);
+    }
+
     #[Test]
     public function createAndRetrieved(): void
     {
@@ -24,14 +34,14 @@ class EpisodePlayableTest extends TestCase
                 'path' => 'https://example.com/episode.mp3',
             ]);
 
-        $playable = EpisodePlayable::getForEpisode($episode);
+        $playable = EpisodePlayable::getForEpisode($episode, $this->safeHttp);
 
         Http::assertSentCount(1);
         self::assertSame('acbd18db4cc2f85cedef654fccc4a4d8', $playable->checksum);
 
         self::assertTrue(Cache::has("episode-playable.{$episode->id}"));
 
-        $retrieved = EpisodePlayable::getForEpisode($episode);
+        $retrieved = EpisodePlayable::getForEpisode($episode, $this->safeHttp);
 
         // No extra HTTP request should be made.
         Http::assertSentCount(1);
@@ -56,7 +66,7 @@ class EpisodePlayableTest extends TestCase
         self::expectException(UnsafeUrlException::class);
 
         try {
-            EpisodePlayable::getForEpisode($episode);
+            EpisodePlayable::getForEpisode($episode, $this->safeHttp);
         } finally {
             Http::assertNothingSent();
         }
@@ -77,7 +87,7 @@ class EpisodePlayableTest extends TestCase
         self::expectException(UnsafeUrlException::class);
 
         try {
-            EpisodePlayable::getForEpisode($episode);
+            EpisodePlayable::getForEpisode($episode, $this->safeHttp);
         } finally {
             // The redirect target must never be requested.
             Http::assertNotSent(static fn ($request) => str_contains($request->url(), '169.254.169.254'));
diff --git a/tests/TestCase.php b/tests/TestCase.php
index 6cdfbb19c6f9e3a4a7f03404143c08c072e14fb8..ac12f2a58d1000fc659c0c6d85ae601695282390 100644
--- a/tests/TestCase.php
+++ b/tests/TestCase.php
@@ -3,13 +3,13 @@
 namespace Tests;
 
 use App\Facades\License;
-use App\Helpers\Network;
 use App\Helpers\Ulid;
 use App\Helpers\Uuid;
 use App\Models\Album;
 use App\Observers\AlbumObserver;
 use App\Services\License\CommunityLicenseService;
 use App\Services\MediaBrowser;
+use App\Services\Network\Network;
 use Illuminate\Filesystem\Filesystem;
 use Illuminate\Foundation\Testing\LazilyRefreshDatabase;
 use Illuminate\Foundation\Testing\TestCase as BaseTestCase;
diff --git a/tests/Unit/Helpers/SafeHttpTest.php b/tests/Unit/Helpers/SafeHttpTest.php
deleted file mode 100644
index d47582d051285e26da5aee305f25f22776d81037..0000000000000000000000000000000000000000
--- a/tests/Unit/Helpers/SafeHttpTest.php
+++ /dev/null
@@ -1,76 +0,0 @@
-<?php
-
-namespace Tests\Unit\Helpers;
-
-use App\Exceptions\UnsafeUrlException;
-use App\Helpers\SafeHttp;
-use GuzzleHttp\Client;
-use GuzzleHttp\Exception\GuzzleException;
-use GuzzleHttp\Handler\MockHandler;
-use GuzzleHttp\HandlerStack;
-use GuzzleHttp\Psr7\Response;
-use PHPUnit\Framework\Attributes\Test;
-use Tests\TestCase;
-
-class SafeHttpTest extends TestCase
-{
-    private SafeHttp $safeHttp;
-
-    public function setUp(): void
-    {
-        parent::setUp();
-
-        $this->safeHttp = app(SafeHttp::class);
-    }
-
-    #[Test]
-    public function guzzleClientRejectsPreflightUnsafeUrl(): void
-    {
-        $this->expectException(UnsafeUrlException::class);
-
-        $this->safeHttp->guzzleClient()->request('GET', 'http://127.0.0.1/admin');
-    }
-
-    #[Test]
-    public function redirectOptionsRejectRedirectToPrivateHost(): void
-    {
-        // Build a Guzzle client that emits a 302 to a private host, then would
-        // emit a 200 (which we must never reach). Apply only the redirect options
-        // — no pre-flight middleware — to isolate the on_redirect leg.
-        $mock = new MockHandler([
-            new Response(302, ['Location' => 'http://127.0.0.1/admin']),
-            new Response(200, [], 'should be unreachable'),
-        ]);
-
-        $client = new Client(['handler' => HandlerStack::create($mock)]);
-
-        $this->expectException(UnsafeUrlException::class);
-
-        try {
-            $client->request('GET', 'https://public.example.com/feed', $this->safeHttp->redirectOptions());
-        } catch (GuzzleException $e) {
-            // Guzzle wraps middleware exceptions; unwrap to surface the real cause.
-            if ($e->getPrevious() instanceof UnsafeUrlException) {
-                throw $e->getPrevious();
-            }
-
-            throw $e;
-        }
-    }
-
-    #[Test]
-    public function redirectOptionsAllowRedirectToPublicHost(): void
-    {
-        $mock = new MockHandler([
-            new Response(302, ['Location' => 'https://other.example.com/feed']),
-            new Response(200, [], 'ok'),
-        ]);
-
-        $client = new Client(['handler' => HandlerStack::create($mock)]);
-
-        $response = $client->request('GET', 'https://public.example.com/feed', $this->safeHttp->redirectOptions());
-
-        self::assertSame(200, $response->getStatusCode());
-        self::assertSame('ok', (string) $response->getBody());
-    }
-}
diff --git a/tests/Unit/Helpers/NetworkTest.php b/tests/Unit/Services/Network/NetworkTest.php
similarity index 58%
rename from tests/Unit/Helpers/NetworkTest.php
rename to tests/Unit/Services/Network/NetworkTest.php
index d5c37e1fe08e1993685cb13f4b6291e428212a1a..238ae882b71d0e9aedf5b2fe1df72f812ede5991 100644
--- a/tests/Unit/Helpers/NetworkTest.php
+++ b/tests/Unit/Services/Network/NetworkTest.php
@@ -1,8 +1,8 @@
 <?php
 
-namespace Tests\Unit\Helpers;
+namespace Tests\Unit\Services\Network;
 
-use App\Helpers\Network;
+use App\Services\Network\Network;
 use PHPUnit\Framework\Attributes\DataProvider;
 use PHPUnit\Framework\Attributes\Test;
 use Tests\TestCase;
@@ -80,4 +80,54 @@ class NetworkTest extends TestCase
     {
         self::assertFalse($this->network->isSafeUrl($url));
     }
+
+    /** @return array<string, array{string}> */
+    public static function provideIpv6TransitionWrappers(): array
+    {
+        return [
+            'NAT64 well-known of loopback' => ['64:ff9b::7f00:1'],
+            'NAT64 well-known of AWS metadata' => ['64:ff9b::a9fe:a9fe'],
+            'NAT64 well-known of private 10.x' => ['64:ff9b::a00:1'],
+            '6to4 of private 10.0.0.1' => ['2002:a00:1::'],
+            '6to4 of loopback' => ['2002:7f00:1::'],
+            '6to4 of AWS metadata' => ['2002:a9fe:a9fe::'],
+        ];
+    }
+
+    #[Test, DataProvider('provideIpv6TransitionWrappers')]
+    public function rejectsIpv6TransitionWrappersOfPrivateIps(string $wrapper): void
+    {
+        self::assertFalse($this->network->isPublicHost($wrapper));
+        self::assertSame([], $this->network->resolveToPublicIps($wrapper));
+    }
+
+    #[Test]
+    public function resolveToPublicIpsReturnsIpsForPublicIpLiteral(): void
+    {
+        self::assertSame(['8.8.8.8'], $this->network->resolveToPublicIps('8.8.8.8'));
+    }
+
+    #[Test]
+    public function resolveToPublicIpsReturnsEmptyForPrivateIpLiteral(): void
+    {
+        self::assertSame([], $this->network->resolveToPublicIps('127.0.0.1'));
+    }
+
+    #[Test]
+    public function resolveToPublicIpsReturnsIpsForPublicHost(): void
+    {
+        $ips = $this->network->resolveToPublicIps('example.com');
+
+        self::assertNotEmpty($ips);
+
+        foreach ($ips as $ip) {
+            self::assertNotFalse(filter_var($ip, FILTER_VALIDATE_IP));
+        }
+    }
+
+    #[Test]
+    public function resolveToPublicIpsReturnsEmptyForUnresolvableHost(): void
+    {
+        self::assertSame([], $this->network->resolveToPublicIps('this-host-does-not-exist.invalid'));
+    }
 }
diff --git a/tests/Unit/Services/Network/SafeHttpTest.php b/tests/Unit/Services/Network/SafeHttpTest.php
new file mode 100644
index 0000000000000000000000000000000000000000..72d32d58f92f097295020829367b4f05730a7daa
--- /dev/null
+++ b/tests/Unit/Services/Network/SafeHttpTest.php
@@ -0,0 +1,72 @@
+<?php
+
+namespace Tests\Unit\Services\Network;
+
+use App\Exceptions\UnsafeUrlException;
+use App\Services\Network\SafeHttp;
+use Illuminate\Support\Facades\Http;
+use PHPUnit\Framework\Attributes\Test;
+use Tests\TestCase;
+
+class SafeHttpTest extends TestCase
+{
+    private SafeHttp $safeHttp;
+
+    public function setUp(): void
+    {
+        parent::setUp();
+
+        $this->safeHttp = app(SafeHttp::class);
+    }
+
+    #[Test]
+    public function headRejectsPrivateIpLiteral(): void
+    {
+        $this->expectException(UnsafeUrlException::class);
+
+        $this->safeHttp->head('http://127.0.0.1/admin');
+    }
+
+    #[Test]
+    public function getRejectsPrivateIpLiteral(): void
+    {
+        $this->expectException(UnsafeUrlException::class);
+
+        $this->safeHttp->get('http://169.254.169.254/latest/meta-data/');
+    }
+
+    #[Test]
+    public function headRejectsRedirectToPrivateHost(): void
+    {
+        Http::fake([
+            '8.8.8.8/*' => Http::response('', 302, ['Location' => 'http://127.0.0.1/admin']),
+            '*' => Http::response('', 200),
+        ]);
+
+        $this->expectException(UnsafeUrlException::class);
+
+        $this->safeHttp->head('https://8.8.8.8/feed');
+    }
+
+    #[Test]
+    public function headFollowsRedirectsAcrossPublicHosts(): void
+    {
+        Http::fake([
+            '8.8.8.8/*' => Http::response('', 302, ['Location' => 'https://1.1.1.1/feed']),
+            '1.1.1.1/*' => Http::response('', 200),
+        ]);
+
+        self::assertTrue($this->safeHttp->head('https://8.8.8.8/feed')->successful());
+    }
+
+    #[Test]
+    public function pinnedGuzzleClientRejectsPrivateIp(): void
+    {
+        // The pinned Guzzle client (used by Poddle, getStreamableUrl) shares
+        // the same pin-and-validate middleware. Verify the standalone branch
+        // throws on a private target, not just the Laravel Http path.
+        $this->expectException(UnsafeUrlException::class);
+
+        $this->safeHttp->getPinnedGuzzleClient('http://127.0.0.1/feed')->request('GET', 'http://127.0.0.1/feed');
+    }
+}
diff --git a/tests/Unit/Services/Radio/RadioStreamProxyTest.php b/tests/Unit/Services/Radio/RadioStreamProxyTest.php
index 8e5ab3441c32bfb071adb84a68c4039127b531f9..7746b818987b3b733439d53130457079bd95d503 100644
--- a/tests/Unit/Services/Radio/RadioStreamProxyTest.php
+++ b/tests/Unit/Services/Radio/RadioStreamProxyTest.php
@@ -2,7 +2,7 @@
 
 namespace Tests\Unit\Services\Radio;
 
-use App\Helpers\Network;
+use App\Services\Network\Network;
 use App\Services\Radio\RadioStreamProxy;
 use Mockery;
 use PHPUnit\Framework\Attributes\Test;

Pre-Patch Source Files (Vulnerable state of files modified by patch)
### app/Ai/Tools/AddRadioStation.php
```
<?php

namespace App\Ai\Tools;

use App\Ai\AiAssistantResult;
use App\Ai\AiRequestContext;
use App\Rules\HasAudioContentType;
use App\Rules\SafeUrl;
use App\Services\RadioService;
use App\Values\Radio\RadioStationCreateData;
use Illuminate\Contracts\JsonSchema\JsonSchema;
use Illuminate\Database\Query\Builder;
use Illuminate\Support\Facades\Validator;
use Illuminate\Validation\Rule;
use Laravel\Ai\Contracts\Tool;
use Laravel\Ai\Tools\Request;
use Stringable;

class AddRadioStation implements Tool
{
    public function __construct(
        private readonly AiRequestContext $context,
        private readonly AiAssistantResult $result,
        private readonly RadioService $radioService,
    ) {}

    public function description(): Stringable|string
    {
        return 'Add a new radio station. Use this when the user wants to add a radio station with a streaming URL.';
    }

    public function schema(JsonSchema $schema): array
    {
        return [
            'name' => $schema->string()->required()->description('The station name'),
            'url' => $schema->string()->required()->description('The streaming URL of the radio station'),
        ];
    }

    public function handle(Request $request): Stringable|string
    {
        $userId = $this->context->user->id;

        $validator = Validator::make(['url' => $request['url']], [
            'url' => [
                'required',
                'url',
                Rule::unique('radio_stations')->where(static fn (Builder $query) => $query->where('user_id', $userId)),
                new SafeUrl(),
                new HasAudioContentType(),
            ],
        ]);

        if ($validator->fails()) {
            return sprintf('Cannot add radio station: %s', $validator->errors()->first('url'));
        }

        $station = $this->radioService->createRadioStation(
            RadioStationCreateData::make(url: $request['url'], name: $request['name'], description: ''),
            $this->context->user,
        );

        $this->result->action = 'add_radio_station';
        $this->result->data = [
            'station' => $station,
        ];

        return sprintf('Radio station "%s" added successfully.', $station->name);
    }
}

```

### app/Helpers/Network.php
```
<?php

namespace App\Helpers;

use Illuminate\Support\Uri;
use Throwable;

class Network
{
    private const array SAFE_URL_SCHEMES = ['http', 'https'];

    /**
     * Check if a URL is safe to reach: HTTP/HTTPS scheme + a public host.
     * Does NOT perform any network calls beyond DNS resolution.
     * For full validation including effective-URL-after-redirect, use the SafeUrl validation rule.
     */
    public function isSafeUrl(string $url): bool
    {
        try {
            $uri = Uri::of($url);
        } catch (Throwable) {
            return false;
        }

        if (!in_array($uri->scheme(), self::SAFE_URL_SCHEMES, true)) {
            return false;
        }

        $host = $uri->host();

        return $host !== '' && $this->isPublicHost($host);
    }

    /**
     * Check if a host resolves only to public (non-private, non-reserved) IP addresses.
     * Validates both A (IPv4) and AAAA (IPv6) records. All resolved IPs must be public.
     */
    public function isPublicHost(string $host): bool
    {
        if (filter_var($host, FILTER_VALIDATE_IP)) {
            return (
                filter_var($host, FILTER_VALIDATE_IP, FILTER_FLAG_NO_PRIV_RANGE | FILTER_FLAG_NO_RES_RANGE) !== false
            );
        }

        try {
            $records = array_merge(dns_get_record($host, DNS_A) ?: [], dns_get_record($host, DNS_AAAA) ?: []);
        } catch (Throwable) {
            return false;
        }

        if ($records === []) {
            return false;
        }

        foreach ($records as $record) {
            $ip = $record['ip'] ?? $record['ipv6'] ?? null;

            if (
                !$ip
                || filter_var($ip, FILTER_VALIDATE_IP, FILTER_FLAG_NO_PRIV_RANGE | FILTER_FLAG_NO_RES_RANGE) === false
            ) {
                return false;
            }
        }

        return true;
    }
}

```

### app/Helpers/SafeHttp.php
```
<?php

namespace App\Helpers;

use App\Exceptions\UnsafeUrlException;
use GuzzleHttp\Client;
use GuzzleHttp\HandlerStack;
use GuzzleHttp\Middleware;
use Psr\Http\Message\RequestInterface;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\UriInterface;

/**
 * Defenses for SSRF on outbound HTTP. Every call site that follows redirects
 * needs per-hop validation: an attacker-controlled URL can pass the initial
 * SafeUrl check, then 302 to 127.0.0.1, 169.254.169.254, etc.
 *
 * Consumers using Laravel Http facade: `Http::withOptions(SafeHttp::redirectOptions())`.
 * Consumers needing a PSR-18 client (e.g. Poddle): `SafeHttp::guzzleClient()`.
 *
 * Note: this addresses redirect-SSRF only. DNS rebinding via TOCTOU between
 * the validator's DNS lookup and the HTTP client's connect-time lookup is a
 * separate concern that requires IP pinning (e.g. curl's CURLOPT_RESOLVE) and
 * is tracked separately.
 */
class SafeHttp
{
    public function __construct(
        private readonly Network $network,
    ) {}

    /**
     * Returns the `allow_redirects` options that re-validate every redirect
     * target via Network::isSafeUrl, throwing UnsafeUrlException on a private
     * or reserved target.
     *
     * @return array<string, mixed>
     */
    public function redirectOptions(int $max = 5): array
    {
        return [
            'allow_redirects' => [
                'max' => $max,
                'on_redirect' => function (
                    RequestInterface $request,
                    ResponseInterface $response,
                    UriInterface $uri,
                ): void {
                    if (!$this->network->isSafeUrl((string) $uri)) {
                        throw UnsafeUrlException::forUrl((string) $uri);
                    }
                },
            ],
        ];
    }

    /**
     * Build a PSR-18 client that applies the same per-redirect-hop validation
     * via Guzzle middleware. Use for libraries that take an injected client
     * (e.g. PhanAn\Poddle\Poddle::fromUrl()).
     */
    public function guzzleClient(int $timeoutInSeconds = 30): Client
    {
        $stack = HandlerStack::create();

        $stack->push(Middleware::mapRequest(function (RequestInterface $request): RequestInterface {
            if (!$this->network->isSafeUrl((string) $request->getUri())) {
                throw UnsafeUrlException::forUrl((string) $request->getUri());
            }

            return $request;
        }));

        return new Client([
            'handler' => $stack,
            'timeout' => $timeoutInSeconds,
            ...$this->redirectOptions(),
        ]);
    }
}

```

### app/Http/Requests/API/Radio/RadioStationStoreRequest.php
```
<?php

namespace App\Http\Requests\API\Radio;

use App\Http\Requests\API\Request;
use App\Rules\HasAudioContentType;
use App\Rules\SafeUrl;
use App\Rules\ValidImageData;
use App\Values\Radio\RadioStationCreateData;
use Illuminate\Validation\Rule;

/**
 * @property-read string $name
 * @property-read string $url
 * @property-read ?string $logo
 * @property-read ?string $description
 * @property-read ?bool $is_public
 * @property-read ?string $homepage_url
 */
class RadioStationStoreRequest extends Request
{
    /** @inheritdoc */
    public function rules(): array
    {
        return [
            'url' => [
                'required',
                'url',
                Rule::unique('radio_stations')->where(function ($query) {
                    return $query->where('user_id', $this->user()->id);
                }),
                new SafeUrl(),
                new HasAudioContentType(),
            ],
            'name' => ['required', 'string', 'max:191'],
            'logo' => ['nullable', new ValidImageData()],
            'description' => ['sometimes', 'nullable', 'string'],
            'is_public' => ['boolean', 'nullable'],
            'homepage_url' => ['sometimes', 'nullable', 'url'],
        ];
    }

    public function toDto(): RadioStationCreateData
    {
        return RadioStationCreateData::make(
            url: $this->url,
            name: $this->name,
            description: $this->string('description'),
            logo: $this->logo,
            isPublic: $this->is_public,
            homepageUrl: $this->homepage_url,
        );
    }
}

```

### app/Http/Requests/API/Radio/RadioStationUpdateRequest.php
```
<?php

namespace App\Http\Requests\API\Radio;

use App\Http\Requests\API\Request;
use App\Rules\HasAudioContentType;
use App\Rules\SafeUrl;
use App\Rules\ValidImageData;
use App\Values\Radio\RadioStationUpdateData;
use Illuminate\Validation\Rule;

/**
 * @property-read string $url
 * @property-read string $name
 * @property-read ?string $logo
 * @property-read ?string $description
 * @property-read ?bool $is_public
 * @property-read ?string $homepage_url
 */
class RadioStationUpdateRequest extends Request
{
    /** @inheritdoc */
    public function rules(): array
    {
        return [
            'url' => [
                'required',
                'url',
                Rule::unique('radio_stations')
                    ->where(function ($query) {
                        return $query->where('user_id', $this->user()->id);
                    })
                    ->ignore($this->route('station')->id), // @phpstan-ignore-line
                new SafeUrl(),
                new HasAudioContentType(),
            ],
            'name' => ['required', 'string', 'max:191'],
            'logo' => ['nullable', 'sometimes', new ValidImageData()],
            'description' => ['string', 'sometimes', 'nullable'],
            'is_public' => ['boolean'],
            'homepage_url' => ['sometimes', 'nullable', 'url'],
        ];
    }

    public function toDto(): RadioStationUpdateData
    {
        return RadioStationUpdateData::make(
            name: $this->name,
            url: $this->url,
            description: $this->string('description'),
            logo: $this->has('logo') ? $this->string('logo') : null,
            isPublic: $this->boolean('is_public'),
            homepageUrl: $this->homepage_url,
        );
    }
}

```

### app/Http/Requests/Subsonic/CreateInternetRadioStationRequest.php
```
<?php

namespace App\Http\Requests\Subsonic;

use App\Http\Requests\Request;
use App\Rules\HasAudioContentType;
use App\Rules\SafeUrl;

/**
 * @property string $streamUrl
 * @property string $name
 * @property ?string $homepageUrl
 */
class CreateInternetRadioStationRequest extends Request
{
    /** @inheritdoc */
    public function rules(): array
    {
        return [
            'streamUrl' => ['required', 'url', new SafeUrl(), new HasAudioContentType()],
            'name' => ['required', 'string'],
            'homepageUrl' => ['nullable', 'string'],
        ];
    }
}

```

### app/Http/Requests/Subsonic/UpdateInternetRadioStationRequest.php
```
<?php

namespace App\Http\Requests\Subsonic;

use App\Http\Requests\Request;
use App\Rules\HasAudioContentType;
use App\Rules\SafeUrl;

/**
 * @property string $id
 * @property string $streamUrl
 * @property string $name
 * @property ?string $homepageUrl
 */
class UpdateInternetRadioStationRequest extends Request
{
    /** @inheritdoc */
    public function rules(): array
    {
        return [
            'id' => ['required', 'string'],
            'streamUrl' => ['required', 'url', new SafeUrl(), new HasAudioContentType()],
            'name' => ['required', 'string'],
            'homepageUrl' => ['nullable', 'string'],
        ];
    }
}

```

### app/Providers/AppServiceProvider.php
```
<?php

namespace App\Providers;

use App\Enums\Acl\Role;
use App\Helpers\SafeHttp;
use App\Models\Album;
use App\Models\Artist;
use App\Models\Genre;
use App\Models\Playlist;
use App\Models\Podcast;
use App\Models\RadioStation;
use App\Models\Song;
use App\Models\User;
use App\Services\Contracts\Encyclopedia;
use App\Services\DotenvEditor;
use App\Services\Geolocation\Contracts\GeolocationService;
use App\Services\Geolocation\IPinfoService;
use App\Services\Integrations\LastfmService;
use App\Services\Integrations\MusicBrainzService;
use App\Services\Integrations\NullEncyclopedia;
use App\Services\Integrations\SpotifyService;
use App\Services\License\Contracts\LicenseServiceInterface;
use App\Services\License\LicenseService;
use App\Services\Scanners\Contracts\ScannerCacheStrategy as ScannerCacheStrategyContract;
use App\Services\Scanners\ScannerCacheStrategy;
use App\Services\Scanners\ScannerNoCacheStrategy;
use Illuminate\Database\DatabaseManager;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\Relation;
use Illuminate\Database\Schema\Builder;
use Illuminate\Database\SQLiteConnection;
use Illuminate\Http\Resources\Json\JsonResource;
use Illuminate\Support\Facades\Gate;
use Illuminate\Support\Facades\Route;
use Illuminate\Support\ServiceProvider;
use Psr\Http\Client\ClientInterface;
use SpotifyWebAPI\Session as SpotifySession;

class AppServiceProvider extends ServiceProvider
{
    public function boot(Builder $schema, DatabaseManager $db): void
    {
        // Fix utf8mb4-related error starting from Laravel 5.4
        $schema->defaultStringLength(191);

        Model::preventLazyLoading(!app()->isProduction());

        self::enableOnDeleteCascadeForSqliteConnections($db);

        // disable wrapping JSON resource in a `data` key
        JsonResource::withoutWrapping();

        self::grantAllPermissionsToSuperAdminRole();

        $this->app->bind(SpotifySession::class, static function () {
            return SpotifyService::enabled()
                ? new SpotifySession(
                    config('koel.services.spotify.client_id'),
                    config('koel.services.spotify.client_secret'),
                )
                : null;
        });

        $this->app->bind(Encyclopedia::class, static function () {
            // Prefer Last.fm over MusicBrainz, and fall back to a null encyclopedia.
            if (LastfmService::enabled()) {
                return app(LastfmService::class);
            }

            if (MusicBrainzService::enabled()) {
                return app(MusicBrainzService::class);
            }

            return app(NullEncyclopedia::class);
        });

        $this->app->bind(LicenseServiceInterface::class, LicenseService::class);

        // PSR-18 client used by libraries that fetch external URLs (e.g. Poddle).
        // Backed by SafeHttp so every redirect hop is re-validated against the
        // SafeUrl rules — closes the redirect-SSRF leg of GHSA-6qvr-wjmv-v8mm.
        $this->app->bind(ClientInterface::class, static fn (): ClientInterface => app(SafeHttp::class)->guzzleClient());

        $this->app->bind(ScannerCacheStrategyContract::class, static function () {
            // Use a no-cache strategy for unit tests to ensure consistent results
            return app()->runningUnitTests() ? app(ScannerNoCacheStrategy::class) : app(ScannerCacheStrategy::class);
        });

        Route::bind('genre', static function (string $value): ?Genre {
            if ($value === Genre::NO_GENRE_PUBLIC_ID) {
                return null;
            }

            return Genre::query()->where('public_id', $value)->firstOrFail();
        });

        Relation::morphMap([
            'playable' => Song::class,
            'album' => Album::class,
            'artist' => Artist::class,
            'podcast' => Podcast::class,
            'radio-station' => RadioStation::class,
            'playlist' => Playlist::class,
        ]);

        $this->app->bind(GeolocationService::class, static function (): GeolocationService {
            return app(IPinfoService::class);
        });

        $this->app
            ->when(DotenvEditor::class)
            ->needs('$path')
            ->give(static fn () => app()->environmentFilePath());
    }

    public function register(): void
    {
        if (class_exists('Laravel\Tinker\TinkerServiceProvider')) {
            $this->app->register('Laravel\Tinker\TinkerServiceProvider');
        }
    }

    private static function enableOnDeleteCascadeForSqliteConnections(DatabaseManager $db): void
    {
        if ($db->connection() instanceof SQLiteConnection) {
            $db->statement($db->raw('PRAGMA foreign_keys = ON')->getValue($db->getQueryGrammar()));
        }
    }

    private static function grantAllPermissionsToSuperAdminRole(): void
    {
        Gate::after(static fn (User $user) => $user->hasRole(Role::ADMIN));
    }
}

```

### app/Rules/HasAudioContentType.php
```
<?php

namespace App\Rules;

use App\Helpers\SafeHttp;
use Closure;
use Illuminate\Contracts\Validation\ValidationRule;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Str;
use Illuminate\Translation\PotentiallyTranslatedString;
use Throwable;

/**
 * Validates that a URL serves audio content.
 * Should be used after SafeUrl to ensure the URL is safe to reach.
 */
class HasAudioContentType implements ValidationRule
{
    /** @param Closure(string, ?string=): PotentiallyTranslatedString $fail */
    public function validate(string $attribute, mixed $value, Closure $fail): void
    {
        $url = (string) $value;

        try {
            $contentType = $this->resolveContentType($url);
        } catch (Throwable) {
            $fail("The $attribute couldn't be reached.");

            return;
        }

        if (!$contentType || !Str::startsWith($contentType, 'audio/')) {
            $fail("The $attribute doesn't look like a valid radio station URL.");
        }
    }

    /**
     * Resolve the Content-Type of a URL.
     * Many streaming servers (Shoutcast/Icecast) don't support HEAD requests,
     * so we fall back to a GET with streaming headers if HEAD fails.
     */
    private function resolveContentType(string $url): string
    {
        $redirectOptions = app(SafeHttp::class)->redirectOptions();

        // Try HEAD first — fast and lightweight
        try {
            $response = Http::withOptions($redirectOptions)->head($url);

            if ($response->successful()) {
                return $response->header('Content-Type');
            }
        } catch (Throwable) { // @mago-expect lint:no-empty-catch-clause -- HEAD may time out or fail on streaming servers; fall through to GET below.
        }

        // Fall back to GET with ICY headers — streaming servers often only respond to GET
        $response = Http::withHeaders(['Icy-MetaData' => '1'])->withOptions([
            ...$redirectOptions,
            'stream' => true,
        ])->get($url);

        return $response->header('Content-Type');
    }
}

```

### app/Rules/SafeUrl.php
```
<?php

namespace App\Rules;

use App\Exceptions\UnsafeUrlException;
use App\Helpers\Network;
use App\Helpers\SafeHttp;
use Closure;
use Illuminate\Contracts\Validation\ValidationRule;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Uri;
use Illuminate\Translation\PotentiallyTranslatedString;
use Throwable;

/**
 * Validates that a URL does not resolve to a private or reserved IP address,
 * preventing SSRF attacks against internal services.
 * Also follows redirects and validates the effective URL.
 */
class SafeUrl implements ValidationRule
{
    private const array ALLOWED_SCHEMES = ['http', 'https'];

    public function __construct(
        private ?Network $network = null,
    ) {
        $this->network ??= app(Network::class);
    }

    /** @param Closure(string, ?string=): PotentiallyTranslatedString $fail */
    public function validate(string $attribute, mixed $value, Closure $fail): void
    {
        try {
            $uri = Uri::of((string) $value);
        } catch (Throwable) {
            $fail('The :attribute is not a valid URL.');

            return;
        }

        if (!in_array($uri->scheme(), self::ALLOWED_SCHEMES, true)) {
            $fail('The :attribute must use HTTP or HTTPS.');

            return;
        }

        if (!$this->network->isPublicHost($uri->host())) {
            $fail('The :attribute must point to a public URL.');

            return;
        }

        $redirectOptions = app(SafeHttp::class)->redirectOptions();

        try {
            $response = Http::withOptions($redirectOptions)->head((string) $value);
        } catch (UnsafeUrlException) {
            $fail('The :attribute must point to a public URL.');

            return;
        } catch (Throwable) {
            // Some streaming servers don't support HEAD — try GET
            try {
                $response = Http::withOptions([...$redirectOptions, 'stream' => true])->get((string) $value);
            } catch (UnsafeUrlException) {
                $fail('The :attribute must point to a public URL.');

                return;
            } catch (Throwable) {
                $fail("The $attribute couldn't be reached.");

                return;
            }
        }

        $effectiveHost = $response->effectiveUri()?->getHost();

        if ($effectiveHost && !$this->network->isPublicHost($effectiveHost)) {
            $fail('The :attribute must point to a public URL.');
        }
    }
}

```

### app/Services/DownloadService.php
```
<?php

namespace App\Services;

use App\Enums\DownloadableType;
use App\Exceptions\DownloadLimitExceededException;
use App\Models\Song;
use App\Models\User;
use App\Repositories\SongRepository;
use App\Services\SongStorages\CloudStorage;
use App\Services\SongStorages\SongStorageFactory;
use App\Values\Downloadable;
use App\Values\Podcast\EpisodePlayable;
use App\Values\SongZipArchive;
use Illuminate\Container\Attributes\Config;
use Illuminate\Database\Eloquent\Collection;
use Illuminate\Support\Facades\File;

class DownloadService
{
    public function __construct(
        private readonly SongRepository $songRepository,
        #[Config('koel.download.limit')]
        private readonly int $downloadLimit = 0,
    ) {}

    /**
     * @throws DownloadLimitExceededException
     */
    public function assertWithinDownloadLimit(
        DownloadableType $type,
        User $user,
        array|string|int|null $id = null,
    ): void {
        if ($this->downloadLimit === 0) {
            return;
        }

        $count = match ($type) {
            DownloadableType::Songs => count((array) $id),
            DownloadableType::Album => $this->songRepository->getByAlbum($id, $user)->count(),
            DownloadableType::Artist => $this->songRepository->getByArtist($id, $user)->count(),
            DownloadableType::Playlist => $this->songRepository->getByPlaylist($id, $user)->count(),
            DownloadableType::Favorites => $this->songRepository->getFavorites($user)->count(),
        };

        $this->assertWithinLimit($count);
    }

    /**
     * @param Collection<Song>|array<array-key, Song> $songs
     */
    public function getDownloadable(Collection $songs): ?Downloadable
    {
        $this->assertWithinLimit($songs->count());

        if ($songs->count() === 1) {
            return optional(
                $this->getLocalPathOrDownloadableUrl($songs->first()), // @phpstan-ignore-line
                Downloadable::make(...),
            );
        }

        return Downloadable::make(
            (new SongZipArchive())
                ->addSongs($songs)
                ->finish()
                ->getPath(),
        );
    }

    private function assertWithinLimit(int $count): void
    {
        throw_if(
            $this->downloadLimit > 0 && $count > $this->downloadLimit,
            new DownloadLimitExceededException($this->downloadLimit),
        );
    }

    public function getLocalPathOrDownloadableUrl(Song $song): ?string
    {
        if (!$song->storage->supported()) {
            return null;
        }

        if ($song->isEpisode()) {
            // If the song is an episode, get the episode's media URL ("path").
            return $song->path;
        }

        $storage = SongStorageFactory::make($song->storage);

        return $storage instanceof CloudStorage
            ? $storage->getPresignedUrl($song->storage_metadata->getPath())
            : $storage->getLocalPath($song->path);
    }

    public function getLocalPath(Song $song): ?string
    {
        if (!$song->storage->supported()) {
            return null;
        }

        if ($song->isEpisode()) {
            return EpisodePlayable::getForEpisode($song)->path;
        }

        $localPath = SongStorageFactory::make($song->storage)->getLocalPath($song->path);

        return File::exists($localPath) ? $localPath : null;
    }
}

```

### app/Services/Network/Network.php
[new file in patch, binary, or unreadable in pre-patch tree]

### app/Services/Network/SafeHttp.php
[new file in patch, binary, or unreadable in pre-patch tree]

### app/Services/Podcast/PodcastService.php
```
<?php

namespace App\Services\Podcast;

use App\Events\UserUnsubscribedFromPodcast;
use App\Exceptions\FailedToParsePodcastFeedException;
use App\Exceptions\UnsafePodcastFeedUrlException;
use App\Exceptions\UserAlreadySubscribedToPodcastException;
use App\Helpers\Network;
use App\Helpers\SafeHttp;
use App\Helpers\Uuid;
use App\Models\Podcast;
use App\Models\PodcastUserPivot;
use App\Models\Song as Episode;
use App\Models\User;
use App\Repositories\PodcastRepository;
use App\Repositories\SongRepository;
use Carbon\Carbon;
use GuzzleHttp\Client;
use GuzzleHttp\RedirectMiddleware;
use GuzzleHttp\RequestOptions;
use Illuminate\Support\Arr;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use PhanAn\Poddle\Poddle;
use PhanAn\Poddle\Values\Episode as EpisodeValue;
use PhanAn\Poddle\Values\EpisodeCollection;
use Psr\Http\Client\ClientInterface;
use Throwable;
use Webmozart\Assert\Assert;

// @mago-ignore lint:cyclomatic-complexity
class PodcastService
{
    public function __construct(
        private readonly PodcastRepository $podcastRepository,
        private readonly SongRepository $songRepository,
        private readonly Network $network,
        private readonly SafeHttp $safeHttp,
        private ?ClientInterface $client = null,
    ) {}

    public function addPodcast(string $url, User $user): Podcast
    {
        // Since downloading and parsing a feed can be time-consuming, try setting the execution time to 5 minutes
        // @mago-ignore lint:no-ini-set,no-error-control-operator
        @ini_set('max_execution_time', 300);

        $podcast = $this->podcastRepository->findOneByUrl($url);

        if ($podcast) {
            if ($this->isPodcastObsolete($podcast)) {
                $this->refreshPodcast($podcast);
            }

            $this->subscribeUserToPodcast($user, $podcast);

            return $podcast;
        }

        try {
            $parser = $this->createParser($url);
            $channel = $parser->getChannel();

            return DB::transaction(function () use ($url, $podcast, $parser, $channel, $user) {
                /** @var Podcast $podcast */
                $podcast = Podcast::query()->create([
                    'url' => $url,
                    'title' => $channel->title,
                    'description' => $channel->description,
                    'author' => $channel->metadata->author,
                    'link' => $channel->link,
                    'language' => $channel->language,
                    'explicit' => $channel->explicit,
                    'image' => $channel->image,
                    'categories' => $channel->categories,
                    'metadata' => $channel->metadata,
                    'added_by' => $user->id,
                    'last_synced_at' => now(),
                ]);

                $this->synchronizeEpisodes($podcast, $parser->getEpisodes(true));
                $this->subscribeUserToPodcast($user, $podcast);

                return $podcast;
            });
        } catch (UserAlreadySubscribedToPodcastException|UnsafePodcastFeedUrlException $exception) {
            throw $exception;
        } catch (Throwable $exception) {
            Log::error($exception);
            throw FailedToParsePodcastFeedException::create($url, $exception);
        }
    }

    public function refreshPodcast(Podcast $podcast): Podcast
    {
        $parser = $this->createParser($podcast->url);
        $channel = $parser->getChannel();

        // Some feeds have a stale pubDate (set once at creation) but an updated lastBuildDate.
        // We use the most recent of the two to determine if new content is available.
        // Carbon::parse() is used instead of createFromFormat(RFC1123) because RSS feeds use
        // varied timezone formats (GMT, EST, +0000) that strict RFC1123 parsing would reject.
        $pubDate = self::parseFeedDate($parser->xmlReader->value('rss.channel.pubDate')->first());
        $lastBuildDate = self::parseFeedDate($parser->xmlReader->value('rss.channel.lastBuildDate')->first());

        $feedDate = collect([$pubDate, $lastBuildDate])->filter()->sortDesc()->first();

        if ($feedDate?->isBefore($podcast->last_synced_at)) {
            return $podcast;
        }

        $this->synchronizeEpisodes($podcast, $parser->getEpisodes(true));

        $podcast->update([
            'title' => $channel->title,
            'description' => $channel->description,
            'author' => $channel->metadata->author,
            'link' => $channel->link,
            'language' => $channel->language,
            'explicit' => $channel->explicit,
            'image' => $channel->image,
            'categories' => $channel->categories,
            'metadata' => $channel->metadata,
            'last_synced_at' => now(),
        ]);

        return $podcast->refresh();
    }

    private function synchronizeEpisodes(Podcast $podcast, EpisodeCollection $episodeCollection): void
    {
        $existingEpisodeGuids = $this->songRepository->getEpisodeGuidsByPodcast($podcast);
        $records = [];
        $ids = [];

        /** @var EpisodeValue $episodeValue */
        foreach ($episodeCollection as $episodeValue) {
            if (in_array($episodeValue->guid->value, $existingEpisodeGuids, true)) {
                continue;
            }

            $enclosureUrl = (string) $episodeValue->enclosure->url;

            if (!$this->network->isSafeUrl($enclosureUrl)) {
                Log::warning(sprintf(
                    'Skipping podcast episode "%s" with unsafe enclosure URL: %s',
                    $episodeValue->title,
                    $enclosureUrl,
                ));

                continue;
            }

            $id = Uuid::generate();
            $ids[] = $id;
            $records[] = [
                'id' => $id,
                'podcast_id' => $podcast->id,
                'title' => $episodeValue->title,
                'lyrics' => '',
                'path' => $enclosureUrl,
                'created_at' => $episodeValue->metadata->pubDate ?: now(),
                'updated_at' => $episodeValue->metadata->pubDate ?: now(),
                'episode_metadata' => $episodeValue->metadata->toJson(),
                'episode_guid' => $episodeValue->guid,
                'length' => $episodeValue->metadata->duration ?? 0,
                'mtime' => time(),
                'is_public' => true,
            ];
        }

        // We use insert() instead of $podcast->episodes()->createMany() for better performance,
        // as the latter would trigger a separate query for each episode.
        Episode::query()->insert($records);

        // Since insert() doesn't trigger model events, Scout operations will not be called.
        // We have to manually update the search index.
        Episode::query()->whereIn('id', $ids)->searchable(); // @phpstan-ignore-line
    }

    public function subscribeUserToPodcast(User $user, Podcast $podcast): void
    {
        throw_if(
            $user->subscribedToPodcast($podcast),
            UserAlreadySubscribedToPodcastException::create($user, $podcast),
        );

        $user->podcasts()->attach($podcast);

        // Refreshing so that $podcast->subscribers are updated
        $podcast->refresh();
    }

    public function updateEpisodeProgress(User $user, Episode $episode, int $position): void
    {
        Assert::true($user->subscribedToPodcast($episode->podcast));

        /** @var PodcastUserPivot $subscription */
        $subscription = $episode->podcast->subscribers->sole('id', $user->id)->pivot;

        $state = $subscription->state->toArray();
        $state['current_episode'] = $episode->id;
        $state['progresses'][$episode->id] = $position;

        $subscription->update(['state' => $state]);
    }

    public function unsubscribeUserFromPodcast(User $user, Podcast $podcast): void
    {
        $user->podcasts()->detach($podcast);
        event(new UserUnsubscribedFromPodcast($user, $podcast));
    }

    public function isPodcastObsolete(Podcast $podcast): bool
    {
        if (abs($podcast->last_synced_at->diffInHours(now())) < 12) {
            // If we have recently synchronized the podcast, consider it "fresh"
            return false;
        }

        if (!$this->network->isSafeUrl($podcast->url)) {
            return true;
        }

        try {
            $lastModified = Http::withOptions($this->safeHttp->redirectOptions())
                ->head($podcast->url)
                ->header('Last-Modified');

            if (!$lastModified) {
                return true;
            }

            return Carbon::createFromFormat(Carbon::RFC1123, $lastModified)->isAfter($podcast->last_synced_at);
        } catch (Throwable $e) {
            Log::warning(sprintf('Failed to check Last-Modified for podcast %s: %s', $podcast->url, $e->getMessage()), [
                'exception' => $e,
            ]);

            return true;
        }
    }

    /**
     * Get a directly streamable (CORS-friendly) URL by following redirects if necessary.
     */
    public function getStreamableUrl(string|Episode $url, ?Client $client = null, string $method = 'OPTIONS'): ?string
    {
        $url = $url instanceof Episode ? $url->path : $url;

        if (!$this->network->isSafeUrl($url)) {
            return null;
        }

        $client ??= $this->safeHttp->guzzleClient();

        try {
            $response = $client->request($method, $url, [
                RequestOptions::HEADERS => [
                    'User-Agent' => 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15',
                    'Origin' => '*',
                ],
                RequestOptions::HTTP_ERRORS => false,
                RequestOptions::ALLOW_REDIRECTS => [
                    ...$this->safeHttp->redirectOptions()['allow_redirects'],
                    'track_redirects' => true,
                ],
            ]);

            $redirects = Arr::wrap($response->getHeader(RedirectMiddleware::HISTORY_HEADER));

            // Sometimes the podcast server disallows OPTIONS requests. We'll try again with a HEAD request.
            if ($response->getStatusCode() >= 400 && $response->getStatusCode() < 500 && $method !== 'HEAD') {
                return $this->getStreamableUrl($url, $client, 'HEAD');
            }

            if (in_array('*', Arr::wrap($response->getHeader('Access-Control-Allow-Origin')), true)) {
                // If there were redirects, the last one is the final URL.
                return $redirects ? Arr::last($redirects) : $url;
            }

            return null;
        } catch (Throwable) {
            return null;
        }
    }

    public function deletePodcast(Podcast $podcast): void
    {
        $podcast->delete();
    }

    private static function parseFeedDate(?string $date): ?Carbon
    {
        if (!$date) {
            return null;
        }

        return rescue(static fn (): Carbon => Carbon::parse($date));
    }

    private function createParser(string $url): Poddle
    {
        if (!$this->network->isSafeUrl($url)) {
            throw UnsafePodcastFeedUrlException::create($url);
        }

        return Poddle::fromUrl($url, 5 * 60, $this->client);
    }
}

```

### app/Services/Radio/RadioStreamProxy.php
```
<?php

namespace App\Services\Radio;

use App\Helpers\Network;
use App\Models\RadioStation;

class RadioStreamProxy
{
    public function __construct(
        private readonly Network $network,
    ) {}

    /**
     * Open a stream to the radio station URL, requesting ICY metadata.
     * Falls back to a plain connection if ICY request fails.
     *
     * @return resource|false
     */
    public function openStream(string $url)
    {
        if (!$this->network->isSafeUrl($url)) {
            return false;
        }

        // Disable redirect-following at the wrapper level. SafeUrl validates the
        // initial URL, so the only way the stream socket could reach a private
        // host is via a redirect at connect time — close that door entirely.
        $context = stream_context_create([
            'http' => [
                'header' => "Icy-MetaData: 1\r\n",
                'timeout' => 5,
                'follow_location' => 0,
                'max_redirects' => 0,
            ],
        ]);

        $plainContext = stream_context_create([
            'http' => [
                'timeout' => 5,
                'follow_location' => 0,
                'max_redirects' => 0,
            ],
        ]);

        set_error_handler(static fn () => true);

        try {
            $stream = fopen($url, 'r', false, $context);

            if ($stream !== false) {
                return $stream;
            }

            return fopen($url, 'r', false, $plainContext);
        } finally {
            restore_error_handler();
        }
    }

    /**
     * Extract the icy-metaint value from the response headers.
     */
    public function extractIcyMetaInt(array $headers): int
    {
        foreach ($headers as $header) {
            if (stripos($header, 'icy-metaint:') === 0) {
                return (int) trim(substr($header, strlen('icy-metaint:')));
            }
        }

        return 0;
    }

    /**
     * Proxy the stream without ICY metadata parsing.
     *
     * @param resource $stream
     */
    public function proxyRawStream($stream): void
    {
        while (!feof($stream) && !connection_aborted()) {
            echo fread($stream, 8192);
            flush();
        }

        fclose($stream);
    }

    /**
     * Proxy the stream while extracting ICY metadata blocks.
     *
     * @param resource $stream
     */
    public function proxyWithMetadata($stream, RadioStation $station, int $icyMetaInt): void
    {
        $bytesUntilMeta = $icyMetaInt;

        while (!feof($stream) && !connection_aborted()) {
            $chunkSize = min($bytesUntilMeta, 8192);
            $data = fread($stream, $chunkSize);

            if ($data === false) {
                break;
            }

            $bytesRead = strlen($data);
            echo $data;
            flush();
            $bytesUntilMeta -= $bytesRead;

            if ($bytesUntilMeta === 0) {
                $this->processMetadataBlock($stream, $station);
                $bytesUntilMeta = $icyMetaInt;
            }
        }

        fclose($stream);
    }

    /**
     * Read and process a single ICY metadata block from the stream.
     *
     * @param resource $stream
     */
    private function processMetadataBlock($stream, RadioStation $station): void
    {
        $lengthByte = fread($stream, 1);

        if ($lengthByte === false || strlen($lengthByte) === 0) {
            return;
        }

        $metadataLength = ord($lengthByte) * 16;

        if ($metadataLength === 0) {
            return;
        }

        $metadataBlock = fread($stream, $metadataLength);

        if ($metadataBlock === false) {
            return;
        }

        $parsed = RadioStreamMetadata::parseIcyBlock($metadataBlock);

        if ($parsed['stream_title'] !== null) {
            RadioStreamMetadata::cache($station, $parsed['stream_title']);
        }
    }
}

```

### app/Services/Streamer/Adapters/PodcastStreamerAdapter.php
```
<?php

namespace App\Services\Streamer\Adapters;

use App\Models\Song as Episode;
use App\Services\Podcast\PodcastService;
use App\Services\Streamer\Adapters\Concerns\StreamsLocalPath;
use App\Values\Podcast\EpisodePlayable;
use App\Values\RequestedStreamingConfig;
use Webmozart\Assert\Assert;

class PodcastStreamerAdapter implements StreamerAdapter
{
    use StreamsLocalPath;

    public function __construct(
        private readonly PodcastService $podcastService,
    ) {}

    /** @inheritDoc */
    public function stream(Episode $song, ?RequestedStreamingConfig $config = null)
    {
        Assert::true($song->isEpisode());

        $streamableUrl = $this->podcastService->getStreamableUrl($song);

        if ($streamableUrl) {
            return response()->redirectTo($streamableUrl);
        }

        $this->streamLocalPath(EpisodePlayable::getForEpisode($song)->path);
    }
}

```

### app/Values/Podcast/EpisodePlayable.php
```
<?php

namespace App\Values\Podcast;

use App\Exceptions\UnsafeUrlException;
use App\Helpers\Network;
use App\Models\Song as Episode;
use Illuminate\Contracts\Support\Arrayable;
use Illuminate\Contracts\Support\Jsonable;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\File;
use Illuminate\Support\Facades\Http;
use Psr\Http\Message\RequestInterface;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\UriInterface;

final class EpisodePlayable implements Arrayable, Jsonable
{
    private function __construct(
        public readonly string $path,
        public readonly string $checksum,
    ) {}

    public static function make(string $path, string $sum): self
    {
        return new self($path, $sum);
    }

    public function valid(): bool
    {
        return File::isReadable($this->path) && $this->checksum === File::hash($this->path);
    }

    public static function getForEpisode(Episode $episode): self
    {
        /** @var self|null $cached */
        $cached = Cache::get("episode-playable.{$episode->id}");

        return $cached?->valid() ? $cached : self::createForEpisode($episode);
    }

    private static function createForEpisode(Episode $episode): self
    {
        $file = artifact_path("episodes/{$episode->id}.mp3");

        if (!File::exists($file)) {
            $network = app(Network::class);
            $url = (string) $episode->path;

            if (!$network->isSafeUrl($url)) {
                throw UnsafeUrlException::forUrl($url);
            }

            Http::sink($file)
                ->withOptions([
                    'allow_redirects' => [
                        'max' => 5,
                        'on_redirect' => static function (
                            RequestInterface $request,
                            ResponseInterface $response,
                            UriInterface $uri,
                        ) use ($network): void {
                            if (!$network->isSafeUrl((string) $uri)) {
                                throw UnsafeUrlException::forUrl((string) $uri);
                            }
                        },
                    ],
                ])
                ->get($url)
                ->throw();
        }

        $playable = new self($file, File::hash($file));
        Cache::forever("episode-playable.{$episode->id}", $playable);

        return $playable;
    }

    /** @inheritDoc */
    public function toArray(): array
    {
        return [
            'path' => $this->path,
            'checksum' => $this->checksum,
        ];
    }

    /** @inheritDoc */
    public function toJson($options = 0): string
    {
        return json_encode($this->toArray(), $options);
    }
}

```

### composer.json
```
{
  "name": "koel/koel",
  "description": "Audio streaming solution that works.",
  "keywords": [
    "audio",
    "stream",
    "mp3"
  ],
  "license": "MIT",
  "type": "project",
  "require": {
    "php": ">=8.3",
    "laravel/framework": "^13.0",
    "james-heinrich/getid3": "^1.9",
    "guzzlehttp/guzzle": "^7.2",
    "pusher/pusher-php-server": "^7.2",
    "predis/predis": "~1.0",
    "ext-exif": "*",
    "ext-gd": "*",
    "ext-fileinfo": "*",
    "ext-json": "*",
    "ext-SimpleXML": "*",
    "daverandom/resume": "^0.0.3",
    "laravel/helpers": "^1.7",
    "teamtnt/laravel-scout-tntsearch-driver": "^15.1.0",
    "algolia/algoliasearch-client-php": "^3.3",
    "webmozart/assert": "^1.10",
    "laravel/sanctum": "^4.0",
    "laravel/scout": "^11.0",
    "jwilsson/spotify-web-api-php": "^5.2",
    "meilisearch/meilisearch-php": "^0.24.0",
    "http-interop/http-factory-guzzle": "^1.2",
    "league/flysystem-aws-s3-v3": "^3.0",
    "spatie/flysystem-dropbox": "^3.0",
    "saloonphp/saloon": "^4.0",
    "saloonphp/laravel-plugin": "^4.0",
    "laravel/socialite": "^5.12",
    "laravel/ui": "^4.5",
    "nunomaduro/collision": "^v8.8",
    "league/flysystem-sftp-v3": "^3.0",
    "spatie/laravel-ray": "^1.36",
    "tiben/crontab-manager": "*",
    "owen-it/laravel-auditing": "^14.0",
    "fileeye/mimemap": "^2.2",
    "ezyang/htmlpurifier": "^4.18",
    "jaybizzle/crawler-detect": "^1.3",
    "laravel/nightwatch": "^1.13",
    "intervention/image-laravel": "^1.5",
    "laravel/prompts": "^0.3.6",
    "laravel/tinker": "^3.0",
    "fakerphp/faker": "^1.24",
    "spatie/laravel-permission": "^6.21",
    "enshrined/svg-sanitize": "^0.22.0",
    "phanan/poddle": "^1.2.4",
    "laravel/ai": "^0.7.0",
    "league/flysystem-webdav": "^3.0"
  },
  "require-dev": {
    "roave/security-advisories": "dev-latest",
    "mockery/mockery": "~1.0",
    "phpunit/phpunit": "^11.0",
    "php-mock/php-mock-mockery": "^1.3",
    "larastan/larastan": "^3.7",
    "phlak/semver": "^5.0",
    "laravel/boost": "^2.0",
    "opcodesio/log-viewer": "^3.19",
    "carthage-software/mago": "^1.8.0"
  },
  "suggest": {
    "ext-zip": "Allow downloading multiple songs as Zip archives"
  },
  "autoload": {
    "classmap": [
      "database"
    ],
    "psr-4": {
      "App\\": "app/",
      "Database\\Seeders\\": "database/seeders/"
    },
    "files": [
      "app/Helpers.php"
    ]
  },
  "autoload-dev": {
    "classmap": [
      "tests/TestCase.php"
    ],
    "psr-4": {
      "Tests\\": "tests/",
      "Database\\Factories\\": "database/factories/"
    },
    "files": [
      "tests/Helpers.php"
    ]
  },
  "scripts": {
    "post-autoload-dump": [
      "Illuminate\\Foundation\\ComposerScripts::postAutoloadDump",
      "@php artisan package:discover"
    ],
    "post-install-cmd": [
      "@php artisan clear-compiled",
      "@php artisan cache:clear",
      "@php -r \"if (!file_exists('.env')) copy('.env.example', '.env');\"",
      "@php -r \"if (!file_exists('./public/.htaccess')) copy('.htaccess.example', './public/.htaccess');\""
    ],
    "pre-update-cmd": [
      "@php artisan clear-compiled"
    ],
    "post-update-cmd": [
      "@php artisan cache:clear",
      "@php artisan boost:update --ansi"
    ],
    "post-root-package-install": [
      "@php -r \"copy('.env.example', '.env');\""
    ],
    "post-create-project-cmd": [
      "@php artisan key:generate"
    ],
    "koel:init": "@php scripts/koel-init.php",
    "test": "@php artisan test",
    "coverage": "@php artisan test --coverage-clover=coverage.xml",
    "cs": "mago format --check",
    "cs:fix": "mago format",
    "lint": "mago lint",
    "analyze": "phpstan analyse --memory-limit 1G --configuration phpstan.neon.dist --ansi",
    "dev": [
      "Composer\\Config::disableProcessTimeout",
      "npx concurrently -k -c \"#93c5fd,#c4b5fd,#fdba74\" \"php artisan serve\" \"php artisan queue:listen --tries=1\" \"vp dev\" --names=server,queue,vite --restart-tries=3"
    ]
  },
  "repositories": [
    {
      "type": "vcs",
      "url": "https://github.com/phanan-forks/laravel-scout-tntsearch-driver"
    }
  ],
  "config": {
    "preferred-install": "dist",
    "optimize-autoloader": true,
    "allow-plugins": {
      "php-http/discovery": true,
      "carthage-software/mago": true
    },
    "platform": {
      "php": "8.3.0"
    }
  },
  "minimum-stability": "stable",
  "prefer-stable": false
}

```

### composer.lock
```
{
    "_readme": [
        "This file locks the dependencies of your project to a known state",
        "Read more about it at https://getcomposer.org/doc/01-basic-usage.md#installing-dependencies",
        "This file is @generated automatically"
    ],
    "content-hash": "d1437db343f05b61a0d00a522e577eee",
    "packages": [
        {
            "name": "algolia/algoliasearch-client-php",
            "version": "3.4.2",
            "source": {
                "type": "git",
                "url": "https://github.com/algolia/algoliasearch-client-php.git",
                "reference": "7505959737f7944507be7ef476752ad761873c4a"
            },
            "dist": {
                "type": "zip",
                "url": "https://api.github.com/repos/algolia/algoliasearch-client-php/zipball/7505959737f7944507be7ef476752ad761873c4a",
                "reference": "7505959737f7944507be7ef476752ad761873c4a",
                "shasum": ""
            },
            "require": {
                "ext-curl": "*",
                "ext-json": "*",
                "ext-mbstring": "*",
                "php": "^7.3 || ^8.0",
                "psr/http-message": "^1.1 || ^2.0",
                "psr/log": "^1.0 || ^2.0 || ^3.0",
                "psr/simple-cache": "^1.0 || ^2.0 || ^3.0"
            },
            "require-dev": {
                "friendsofphp/php-cs-fixer": "^2.0",
                "fzaninotto/faker": "^1.8",
                "phpunit/phpunit": "^8.0 || ^9.0",
                "symfony/yaml": "^2.0 || ^4.0"
            },
            "suggest": {
                "guzzlehttp/guzzle": "If you prefer to use Guzzle HTTP client instead of the Http Client implementation provided by the package"
            },
            "bin": [
                "bin/algolia-doctor"
            ],
            "type": "library",
            "extra": {
                "branch-alias": {
                    "dev-2.0": "2.0.x-dev"
                }
            },
            "autoload": {
                "files": [
                    "src/Http/Psr7/functions.php",
                    "src/functions.php"
                ],
                "psr-4": {
                    "Algolia\\AlgoliaSearch\\": "src/"
                }
            },
            "notification-url": "https://packagist.org/downloads/",
            "license": [
                "MIT"
            ],
            "authors": [
                {
                    "name": "Algolia Team",
                    "email": "contact@algolia.com"
                }
            ],
            "description": "Algolia Search API Client for PHP",
            "keywords": [
                "algolia",
                "api",
                "client",
                "php",
                "search"
            ],
            "support": {
                "issues": "https://github.com/algolia/algoliasearch-client-php/issues",
                "source": "https://github.com/algolia/algoliasearch-client-php/tree/3.4.2"
            },
            "time": "2025-01-22T11:13:54+00:00"
        },
        {
            "name": "aws/aws-crt-php",
            "version": "v1.2.7",
            "source": {
                "type": "git",
                "url": "https://github.com/awslabs/aws-crt-php.git",
                "reference": "d71d9906c7bb63a28295447ba12e74723bd3730e"
            },
            "dist": {
                "type": "zip",
                "url": "https://api.github.com/repos/awslabs/aws-crt-php/zipball/d71d9906c7bb63a28295447ba12e74723bd3730e",
                "reference": "d71d9906c7bb63a28295447ba12e74723bd3730e",
                "shasum": ""
            },
            "require": {
                "php": ">=5.5"
            },
            "require-dev": {
                "phpunit/phpunit": "^4.8.35||^5.6.3||^9.5",
                "yoast/phpunit-polyfills": "^1.0"
            },
            "suggest": {
                "ext-awscrt": "Make sure you install awscrt native extension to use any of the functionality."
            },
            "type": "library",
            "autoload": {
                "classmap": [
                    "src/"
                ]
            },
            "notification-url": "https://packagist.org/downloads/",
            "license": [
                "Apache-2.0"
            ],
            "authors": [
                {
                    "name": "AWS SDK Common Runtime Team",
                    "email": "aws-sdk-common-runtime@amazon.com"
                }
            ],
            "description": "AWS Common Runtime for PHP",
            "homepage": "https://github.com/awslabs/aws-crt-php",
            "keywords": [
                "amazon",
                "aws",
                "crt",
                "sdk"
            ],
            "support": {
                "issues": "https://github.com/awslabs/aws-crt-php/issues",
                "source": "https://github.com/awslabs/aws-crt-php/tree/v1.2.7"
            },
            "time": "2024-10-18T22:15:13+00:00"
        },
        {
            "name": "aws/aws-sdk-php",
            "version": "3.382.0",
            "source": {
                "type": "git",
                "url": "https://github.com/aws/aws-sdk-php.git",
                "reference": "5b4c1958d7ff9e3284b755d257a1aa1926745f6a"
            },
            "dist": {
                "type": "zip",
                "url": "https://api.github.com/repos/aws/aws-sdk-php/zipball/5b4c1958d7ff9e3284b755d257a1aa1926745f6a",
                "reference": "5b4c1958d7ff9e3284b755d257a1aa1926745f6a",
                "shasum": ""
            },
            "require": {
                "aws/aws-crt-php": "^1.2.3",
                "ext-json": "*",
                "ext-pcre": "*",
                "ext-simplexml": "*",
                "guzzlehttp/guzzle": "^7.4.5",
                "guzzlehttp/promises": "^2.0",
                "guzzlehttp/psr7": "^2.4.5",
                "mtdowling/jmespath.php": "^2.8.0",
                "php": ">=8.1",
                "psr/http-message": "^1.0 || ^2.0",
                "symfony/filesystem": "^v5.4.45 || ^v6.4.3 || ^v7.1.0 || ^v8.0.0"
            },
            "require-dev": {
                "andrewsville/php-token-reflection": "^1.4",
                "aws/aws-php-sns-message-validator": "~1.0",
                "behat/behat": "~3.0",
                "composer/composer": "^2.7.8",
                "dms/phpunit-arraysubset-asserts": "^v0.5.0",
                "doctrine/cache": "~1.4",
                "ext-dom": "*",
                "ext-openssl": "*",
                "ext-sockets": "*",
                "phpunit/phpunit": "^10.0",
                "psr/cache": "^2.0 || ^3.0",
                "psr/simple-cache": "^2.0 || ^3.0",
                "sebastian/comparator": "^1.2.3 || ^4.0 || ^5.0",
                "yoast/phpunit-polyfills": "^2.0"
            },
            "suggest": {
                "aws/aws-php-sns-message-validator": "To validate incoming SNS notifications",
                "doctrine/cache": "To use the DoctrineCacheAdapter",
                "ext-curl": "To send requests using cURL",
                "ext-openssl": "Allows working with CloudFront private distributions and verifying received SNS messages",
                "ext-pcntl": "To use client-side monitoring",
                "ext-sockets": "To use client-side monitoring"
            },
            "type": "library",
            "extra": {
                "branch-alias": {
                    "dev-master": "3.0-dev"
                }
            },
            "autoload": {
                "files": [
                    "src/functions.php"
                ],
                "psr-4": {
                    "Aws\\": "src/"
                },
                "exclude-from-classmap": [
                    "src/data/"
                ]
            },
            "notification-url": "https://packagist.org/downloads/",
            "license": [
                "Apache-2.0"
            ],
            "authors": [
                {
                    "name": "Amazon Web Services",
                    "homepage": "https://aws.amazon.com"
                }
            ],
            "description": "AWS SDK for PHP - Use Amazon Web Services in your PHP project",
            "homepage": "https://aws.amazon.com/sdk-for-php",
            "keywords": [
                "amazon",
                "aws",
                "cloud",
                "dynamodb",
                "ec2",
                "glacier",
                "s3",
                "sdk"
            ],
            "support": {
                "forum": "https://github.com/aws/aws-sdk-php/discussions",
                "issues": "https://github.com/aws/aws-sdk-php/issues",
                "source": "https://github.com/aws/aws-sdk-php/tree/3.382.0"
            },
            "time": "2026-05-22T18:09:49+00:00"
        },
        {
            "name": "brick/math",
            "version": "0.14.8",
            "source": {
                "type": "git",
                "url": "https://github.com/brick/math.git",
                "reference": "63422359a44b7f06cae63c3b429b59e8efcc0629"
            },
            "dist": {
                "type": "zip",
                "url": "https://api.github.com/repos/brick/math/zipball/63422359a44b7f06cae63c3b429b59e8efcc0629",
                "reference": "63422359a44b7f06cae63c3b429b59e8efcc0629",
                "shasum": ""
            },
            "require": {
                "php": "^8.2"
            },
            "require-dev": {
                "php-coveralls/php-coveralls": "^2.2",
                "phpstan/phpstan": "2.1.22",
                "phpunit/phpunit": "^11.5"
            },
            "type": "library",
            "autoload": {
                "psr-4": {
                    "Brick\\Math\\": "src/"
                }
            },
            "notification-url": "https://packagist.org/downloads/",
            "license": [
                "MIT"
            ],
            "description": "Arbitrary-precision arithmetic library",
            "keywords": [
                "Arbitrary-precision",
                "BigInteger",
                "BigRational",
                "arithmetic",
                "bigdecimal",
                "bignum",
                "bignumber",
                "brick",
                "decimal",
                "integer",
                "math",
                "mathematics",
                "rational"
            ],
            "support": {
                "issues": "https://github.com/brick/math/issues",
                "source": "https://github.com/brick/math/tree/0.14.8"
            },
            "funding": [
                {
                    "url": "https://github.com/BenMorel",
                    "type": "github"
                }
            ],
            "time": "2026-02-10T14:33:43+00:00"
        },
        {
            "name": "carbonphp/carbon-doctrine-types",
            "version": "3.2.0",
            "source": {
                "type": "git",
                "url": "https://github.com/CarbonPHP/carbon-doctrine-types.git",
                "reference": "18ba5ddfec8976260ead6e866180bd5d2f71aa1d"
            },
            "dist": {
                "type": "zip",
                "url": "https://api.github.com/repos/CarbonPHP/carbon-doctrine-types/zipball/18ba5ddfec8976260ead6e866180bd5d2f71aa1d",
                "reference": "18ba5ddfec8976260ead6e866180bd5d2f71aa1d",
                "shasum": ""
            },
            "require": {
                "php": "^8.1"
            },
            "conflict": {
                "doctrine/dbal": "<4.0.0 || >=5.0.0"
            },
            "require-dev": {
                "doctrine/dbal": "^4.0.0",
                "nesbot/carbon": "^2.71.0 || ^3.0.0",
                "phpunit/phpunit": "^10.3"
            },
            "type": "library",
            "autoload": {
                "psr-4": {
                    "Carbon\\Doctrine\\": "src/Carbon/Doctrine/"
                }
            },
            "notification-url": "https://packagist.org/downloads/",
            "license": [
                "MIT"
            ],
            "authors": [
                {
                    "name": "KyleKatarn",
                    "email": "kylekatarnls@gmail.com"
                }
            ],
            "description": "Types to use Carbon in Doctrine",
            "keywords": [
                "carbon",
                "date",
                "datetime",
                "doctrine",
                "time"
            ],
            "support": {
                "issues": "https://github.com/CarbonPHP/carbon-doctrine-types/issues",
                "source": "https://github.com/CarbonPHP/carbon-doctrine-types/tree/3.2.0"
            },
            "funding": [
                {
                    "url": "https://github.com/kylekatarnls",
                    "type": "github"
                },
                {
                    "url": "https://opencollective.com/Carbon",
                    "type": "open_collective"
                },
                {
                    "url": "https://tidelift.com/funding/github/packagist/nesbot/carbon",
                    "type": "tidelift"
                }
            ],
            "time": "2024-02-09T16:56:22+00:00"
        },
        {
            "name": "clue/stream-filter",
            "version": "v1.7.0",
            "source": {
                "type": "git",
                "url": "https://github.com/clue/stream-filter.git",
                "reference": "049509fef80032cb3f051595029ab75b49a3c2f7"
            },
            "dist": {
                "type": "zip",
                "url": "https://api.github.com/repos/clue/stream-filter/zipball/049509fef80032cb3f051595029ab75b49a3c2f7",
                "reference": "049509fef80032cb3f051595029ab75b49a3c2f7",
                "shasum": ""
            },
            "require": {
                "php": ">=5.3"
            },
            "require-dev": {
                "phpunit/phpunit": "^9.6 || ^5.7 || ^4.8.36"
            },
            "type": "library",
            "autoload": {
                "files": [
                    "src/functions_include.php"
                ],
                "psr-4": {
                    "Clue\\StreamFilter\\": "src/"
                }
            },
            "notification-url": "https://packagist.org/downloads/",
            "license": [
                "MIT"
            ],
            "authors": [
                {
                    "name": "Christian Lück",
                    "email": "christian@clue.engineering"
                }
            ],
            "description": "A simple and modern approach to stream filtering in PHP",
            "homepage": "https://github.com/clue/stream-filter",
            "keywords": [
                "bucket brigade",
                "callback",
                "filter",
                "php_user_filter",
                "stream",
                "stream_filter_append",
                "stream_filter_register"
            ],
            "support": {
                "issues": "https://github.com/clue/stream-filter/issues",
                "source": "https://github.com/clue/stream-filter/tree/v1.7.0"
            },
            "funding": [
                {
                    "url": "https://clue.engineering/support",
                    "type": "custom"
                },
                {
                    "url": "https://github.com/clue",
                    "type": "github"
                }
            ],
            "time": "2023-12-20T15:40:13+00:00"
        },
        {
            "name": "daverandom/resume",
            "version": "v0.0.3",
            "source": {
                "type": "git",
                "url": "https://github.com/DaveRandom/Resume.git",
                "reference": "3d1c11b6c4315dd8d25d6f567c5ea392c7c60edb"
            },
            "dist": {
                "type": "zip",
                "url": "https://api.github.com/repos/DaveRandom/Resume/zipball/3d1c11b6c4315dd8d25d6f567c5ea392c7c60edb",
                "reference": "3d1c11b6c4315dd8d25d6f567c5ea392c7c60edb",
                "shasum": ""
            },
            "require": {
                "php": ">=7.0"
            },
            "require-dev": {
                "phpunit/phpunit": "^6.2"
            },
            "type": "library",
            "autoload": {
                "files": [
                    "src/functions.php"
                ],
                "psr-4": {
                    "DaveRandom\\Resume\\": "src/"
                }
            },
            "notification-url": "https://packagist.org/downloads/",
            "license": [
                "mit"
            ],
            "authors": [
                {
                    "name": "Chris Wright",
                    "email": "me@daverandom.com"
                }
            ],
            "description": "Tiny library to facilitate resumable downloads",
            "support": {
                "issues": "https://github.com/DaveRandom/Resume/issues",
                "source": "https://github.com/DaveRandom/Resume/tree/master"
            },
            "time": "2018-01-28T03:18:55+00:00"
        },
        {
            "name": "dflydev/dot-access-data",
            "version": "v3.0.3",
            "source": {
                "type": "git",
                "url": "https://github.com/dflydev/dflydev-dot-access-data.git",
                "reference": "a23a2bf4f31d3518f3ecb38660c95715dfead60f"
            },
            "dist": {
                "type": "zip",
                "url": "https://api.github.com/repos/dflydev/dflydev-dot-access-data/zipball/a23a2bf4f31d3518f3ecb38660c95715dfead60f",
                "reference": "a23a2bf4f31d3518f3ecb38660c95715dfead60f",
                "shasum": ""
            },
            "require": {
                "php": "^7.1 || ^8.0"
            },
            "require-dev": {
                "phpstan/phpstan": "^0.12.42",
                "phpunit/phpunit": "^7.5 || ^8.5 || ^9.3",
                "scrutinizer/ocular": "1.6.0",
                "squizlabs/php_codesniffer": "^3.5",
                "vimeo/psalm": "^4.0.0"
            },
            "type": "library",
            "extra": {
                "branch-alias": {
                    "dev-main": "3.x-dev"
                }
            },
            "autoload": {
                "psr-4": {
                    "Dflydev\\DotAccessData\\": "src/"
                }
            },
            "notification-url": "https://packagist.org/downloads/",
            "license": [
                "MIT"
            ],
            "authors": [
                {
                    "name": "Dragonfly Development Inc.",
                    "email": "info@dflydev.com",
                    "homepage": "http://dflydev.com"
                },
                {
                    "name": "Beau Simensen",
                    "email": "beau@dflydev.com",
                    "homepage": "http://beausimensen.com"
                },
                {
                    "name": "Carlos Frutos",
                    "email": "carlos@kiwing.it",
                    "homepage": "https://github.com/cfrutos"
                },
                {
                    "name": "Colin O'Dell",
                    "email": "colinodell@gmail.com",
                    "homepage": "https://www.colinodell.com"
                }
            ],
            "description": "Given a deep data structure, access data by dot notation.",
            "homepage": "https://github.com/dflydev/dflydev-dot-access-data",
            "keywords": [
                "access",
                "data",
                "dot",
                "notation"
            ],
            "support": {
                "issues": "https://github.com/dflydev/dflydev-dot-access-data/issues",
                "source": "https://github.com/dflydev/dflydev-dot-access-data/tree/v3.0.3"
            },
            "time": "2024-07-08T12:26:09+00:00"
        },
        {
            "name": "doctrine/inflector",
            "version": "2.1.0",
            "source": {
                "type": "git",
                "url": "https://github.com/doctrine/inflector.git",
                "reference": "6d6c96277ea252fc1304627204c3d5e6e15faa3b"
            },
            "dist": {
                "type": "zip",
                "url": "https://api.github.com/repos/doctrine/inflector/zipball/6d6c96277ea252fc1304627204c3d5e6e15faa3b",
                "reference": "6d6c96277ea252fc1304627204c3d5e6e15faa3b",
                "shasum": ""
            },
            "require": {
                "php": "^7.2 || ^8.0"
            },
            "require-dev": {
                "doctrine/coding-standard": "^12.0 || ^13.0",
                "phpstan/phpstan": "^1.12 || ^2.0",
                "phpstan/phpstan-phpunit": "^1.4 || ^2.0",
                "phpstan/phpstan-strict-rules": "^1.6 || ^2.0",
                "phpunit/phpunit": "^8.5 || ^12.2"
            },
            "type": "library",
            "autoload": {
                "psr-4": {
                    "Doctrine\\Inflector\\": "src"
                }
            },
            "notification-url": "https://packagist.org/downloads/",
            "license": [
                "MIT"
            ],
            "authors": [
                {
                    "name": "Guilherme Blanco",
                    "email": "guilhermeblanco@gmail.com"
                },
                {
                    "name": "Roman Borschel",
                    "email": "roman@code-factory.org"
                },
                {
                    "name": "Benjamin Eberlei",
                    "email": "kontakt@beberlei.de"
                },
                {
                    "name": "Jonathan Wage",
                    "email": "jonwage@gmail.com"
                },
                {
                    "name": "Johannes Schmitt",
                    "email": "schmittjoh@gmail.com"
                }
            ],
            "description": "PHP Doctrine Inflector is a small library that can perform string manipulations with regard to upper/lowercase and singular/plural forms of words.",
            "homepage": "https://www.doctrine-project.org/projects/inflector.html",
            "keywords": [
                "inflection",
                "inflector",
                "lowercase",
                "manipulation",
                "php",
                "plural",
                "singular",
                "strings",
                "uppercase",
                "words"
            ],
            "support": {
                "issues": "https://github.com/doctrine/inflector/issues",
                "source": "https://github.com/doctrine/inflector/tree/2.1.0"
            },
            "funding": [
                {
                    "url": "https://www.doctrine-project.org/sponsorship.html",
                    "type": "custom"
                },
                {
                    "url": "https://www.patreon.com/phpdoctrine",
                    "type": "patreon"
                },
                {
                    "url": "https://tidelift.com/funding/github/packagist/doctrine%2Finflector",
                    "type": "tidelift"
                }
            ],
            "time": "2025-08-10T19:31:58+00:00"
        },
        {
            "name": "doctrine/lexer",
            "version": "3.0.1",
            "source": {
                "type": "git",
                "url": "https://github.com/doctrine/lexer.git",
                "reference": "31ad66abc0fc9e1a1f2d9bc6a42668d2fbbcd6dd"
            },
            "dist": {
                "type": "zip",
                "url": "https://api.github.com/repos/doctrine/lexer/zipball/31ad66abc0fc9e1a1f2d9bc6a42668d2fbbcd6dd",
                "reference": "31ad66abc0fc9e1a1f2d9bc6a42668d2fbbcd6dd",
                "shasum": ""
            },
            "require": {
                "php": "^8.1"
            },
            "require-dev": {
                "doctrine/coding-standard": "^12",
                "phpstan/phpstan": "^1.10",
                "phpunit/phpunit": "^10.5",
                "psalm/plugin-phpunit": "^0.18.3",
                "vimeo/psalm": "^5.21"
            },
            "type": "library",
            "autoload": {
                "psr-4": {
                    "Doctrine\\Common\\Lexer\\": "src"
                }
            },
            "notification-url": "https://packagist.org/downloads/",
            "license": [
                "MIT"
            ],
            "authors": [
                {
                    "name": "Guilherme Blanco",
                    "email": "guilhermeblanco@gmail.com"
                },
                {
                    "name": "Roman Borschel",
                    "email": "roman@code-factory.org"
                },
                {
                    "name": "Johannes Schmitt",
                    "email": "schmittjoh@gmail.com"
                }
            ],
            "description": "PHP Doctrine Lexer parser library that can be used in Top-Down, Recursive Descent Parsers.",
            "homepage": "https://www.doctrine-project.org/projects/lexer.html",
            "keywords": [
                "annotations",
                "docblock",
                "lexer",
                "parser",
                "php"
            ],
            "support": {
                "issues": "https://github.com/doctrine/lexer/issues",
                "source": "https://github.com/doctrine/lexer/tree/3.0.1"
            },
            "funding": [
                {
                    "url": "https://www.doctrine-project.org/sponsorship.html",
                    "type": "custom"
                },
                {
                    "url": "https://www.patreon.com/phpdoctrine",
                    "type": "patreon"
                },
                {
                    "url": "https://tidelift.com/funding/github/packagist/doctrine%2Flexer",
                    "type": "tidelift"
                }
            ],
            "time": "2024-02-05T11:56:58+00:00"
        },
        {
            "name": "dragonmantank/cron-expression",
            "version": "v3.6.0",
            "source": {
                "type": "git",
                "url": "https://github.com/dragonmantank/cron-expression.git",
                "reference": "d61a8a9604ec1f8c3d150d09db6ce98b32675013"
            },
            "dist": {
                "type": "zip",
                "url": "https://api.github.com/repos/dragonmantank/cron-expression/zipball/d61a8a9604ec1f8c3d150d09db6ce98b32675013",
                "reference": "d61a8a9604ec1f8c3d150d09db6ce98b32675013",
                "shasum": ""
            },
            "require": {
                "php": "^8.2|^8.3|^8.4|^8.5"
            },
            "replace": {
                "mtdowling/cron-expression": "^1.0"
            },
            "require-dev": {
                "phpstan/extension-installer": "^1.4.3",
                "phpstan/phpstan": "^1.12.32|^2.1.31",
                "phpunit/phpunit": "^8.5.48|^9.0"
            },
            "type": "library",
            "extra": {
                "branch-alias": {
                    "dev-master": "3.x-dev"
                }
            },
            "autoload": {
                "psr-4": {
                    "Cron\\": "src/Cron/"
                }
            },
            "notification-url": "https://packagist.org/downloads/",
            "license": [
                "MIT"
            ],
            "authors": [
                {
                    "name": "Chris Tankersley",
                    "email": "chris@ctankersley.com",
                    "homepage": "https://github.com/dragonmantank"
                }
            ],
            "description": "CRON for PHP: Calculate the next or previous run date and determine if a CRON expression is due",
            "keywords": [
                "cron",
                "schedule"
            ],
            "support": {
                "issues": "https://github.com/dragonmantank/cron-expression/issues",
                "source": "https://github.com/dragonmantank/cron-expression/tree/v3.6.0"
            },
            "funding": [
                {
                    "url": "https://github.com/dragonmantank",
                    "type": "github"
                }
            ],
            "time": "2025-10-31T18:51:33+00:00"
        },
        {
            "name": "egulias/email-validator",
            "version": "4.0.4",
            "source": {
                "type": "git",
                "url": "https://github.com/egulias/EmailValidator.git",
                "reference": "d42c8731f0624ad6bdc8d3e5e9a4524f68801cfa"
            },
            "dist": {
                "type": "zip",
                "url": "https://api.github.com/repos/egulias/EmailValidator/zipball/d42c8731f0624ad6bdc8d3e5e9a4524f68801cfa",
                "reference": "d42c8731f0624ad6bdc8d3e5e9a4524f68801cfa",
                "shasum": ""
            },
            "require": {
                "doctrine/lexer": "^2.0 || ^3.0",
                "php": ">=8.1",
                "symfony/polyfill-intl-idn": "^1.26"
            },
            "require-dev": {
                "phpunit/phpunit": "^10.2",
                "vimeo/psalm": "^5.12"
            },
            "suggest": {
                "ext-intl": "PHP Internationalization Libraries are required to use the SpoofChecking validation"
            },
            "type": "library",
            "extra": {
                "branch-alias": {
                    "dev-master": "4.0.x-dev"
                }
            },
            "autoload": {
                "psr-4": {
                    "Egulias\\EmailValidator\\": "src"
                }
            },
            "notification-url": "https://packagist.org/downloads/",
            "license": [
                "MIT"
            ],
            "authors": [
                {
                    "name": "Eduardo Gulias Davis"
                }
            ],
            "description": "A library for validating emails against several RFCs",
            "homepage": "https://github.com/egulias/EmailValidator",
            "keywords": [
                "email",
                "emailvalidation",
                "emailvalidator",
                "validation",
                "validator"
            ],
            "support": {
                "issues": "https://github.com/egulias/EmailValidator/issues",
                "source": "https://github.com/egulias/EmailValidator/tree/4.0.4"
            },
            "funding": [
                {
                    "url": "https://github.com/egulias",
                    "type": "github"
                }
            ],
            "time": "2025-03-06T22:45:56+00:00"
        },
        {
            "name": "enshrined/svg-sanitize",
            "version": "0.22.0",
            "source": {
                "type": "git",
                "url": "https://github.com/darylldoyle/svg-sanitizer.git",
                "reference": "0afa95ea74be155a7bcd6c6fb60c276c39984500"
            },
            "dist": {
                "type": "zip",
                "url": "https://api.github.com/repos/darylldoyle/svg-sanitizer/zipball/0afa95ea74be155a7bcd6c6fb60c276c39984500",
                "reference": "0afa95ea74be155a7bcd6c6fb60c276c39984500",
                "shasum": ""
            },
            "require": {
                "ext-dom": "*",
                "ext-libxml": "*",
                "php": "^7.1 || ^8.0"
            },
            "require-dev": {
                "phpunit/phpunit": "^6.5 || ^8.5"
            },
            "type": "library",
            "autoload": {
                "psr-4": {
                    "enshrined\\svgSanitize\\": "src"
                }
            },
            "notification-url": "https://packagist.org/downloads/",
            "license": [
                "GPL-2.0-or-later"
            ],
            "authors": [
                {
                    "name": "Daryll Doyle",
                    "email": "daryll@enshrined.co.uk"
                }
            ],
            "description": "An SVG sanitizer for PHP",
            "support": {
                "issues": "https://github.com/darylldoyle/svg-sanitizer/issues",
                "source": "https://github.com/darylldoyle/svg-sanitizer/tree/0.22.0"
            },
            "time": "2025-08-12T10:13:48+00:00"
        },
        {
            "name": "ezyang/htmlpurifier",
            "version": "v4.19.0",
            "source": {
                "type": "git",
                "url": "https://github.com/ezyang/htmlpurifier.git",
                "reference": "b287d2a16aceffbf6e0295559b39662612b77fcf"
            },
            "dist": {
                "type": "zip",
                "url": "https://api.github.com/repos/ezyang/htmlpurifier/zipball/b287d2a16aceffbf6e0295559b39662612b77fcf",
                "reference": "b287d2a16aceffbf6e0295559b39662612b77fcf",
                "shasum": ""
            },
            "require": {
                "php": "~5.6.0 || ~7.0.0 || ~7.1.0 || ~7.2.0 || ~7.3.0 || ~7.4.0 || ~8.0.0 || ~8.1.0 || ~8.2.0 || ~8.3.0 || ~8.4.0 || ~8.5.0"
            },
            "require-dev": {
                "cerdic/css-tidy": "^1.7 || ^2.0",
                "simpletest/simpletest": "dev-master"
            },
            "suggest": {
                "cerdic/css-tidy": "If you want to use the filter 'Filter.ExtractStyleBlocks'.",
                "ext-bcmath": "Used for unit conversion and imagecrash protection",
                "ext-iconv": "Converts text to and from non-UTF-8 encodings",
                "ext-tidy": "Used for pretty-printing HTML"
            },
            "type": "library",
            "autoload": {
                "files": [
                    "library/HTMLPurifier.composer.php"
                ],
                "psr-0": {
                    "HTMLPurifier": "library/"
                },
                "exclude-from-classmap": [
                    "/library/HTMLPurifier/Language/"
                ]
            },
            "notification-url": "https://packagist.org/downloads/",
            "license": [
                "LGPL-2.1-or-later"
            ],
            "authors": [
                {
                    "name": "Edward Z. Yang",
                    "email": "admin@htmlpurifier.org",
                    "homepage": "http://ezyang.com"
                }
            ],
            "description": "Standards compliant HTML filter written in PHP",
            "homepage": "http://htmlpurifier.org/",
            "keywords": [
                "html"
            ],
            "support": {
                "issues": "https://github.com/ezyang/htmlpurifier/issues",
                "source": "https://github.com/ezyang/htmlpurifier/tree/v4.19.0"
            },
            "time": "2025-10-17T16:34:55+00:00"
        },
        {
            "name": "fakerphp/faker",
            "version": "v1.24.1",
            "source": {
                "type": "git",
                "url": "https://github.com/FakerPHP/Faker.git",
                "reference": "e0ee18eb1e6dc3cda3ce9fd97e5a0689a88a64b5"
            },
            "dist": {
                "type": "zip",
                "url": "https://api.github.com/repos/FakerPHP/Faker/zipball/e0ee18eb1e6dc3cda3ce9fd97e5a0689a88a64b5",
                "reference": "e0ee18eb1e6dc3cda3ce9fd97e5a0689a88a64b5",
                "shasum": ""
            },
            "require": {
                "php": "^7.4 || ^8.0",
                "psr/container": "^1.0 || ^2.0",
                "symfony/deprecation-contracts": "^2.2 || ^3.0"
            },
            "conflict": {
                "fzaninotto/faker": "*"
            },
            "require-dev": {
                "bamarni/composer-bin-plugin": "^1.4.1",
                "doctrine/persistence": "^1.3 || ^2.0",
                "ext-intl": "*",
                "phpunit/phpunit": "^9.5.26",
                "symfony/phpunit-bridge": "^5.4.16"
            },
            "suggest": {
                "doctrine/orm": "Required to use Faker\\ORM\\Doctrine",
                "ext-curl": "Required by Faker\\Provider\\Image to download images.",
                "ext-dom": "Required by Faker\\Provider\\HtmlLorem for generating random HTML.",
                "ext-iconv": "Required by Faker\\Provider\\ru_RU\\Text::realText() for generating real Russian text.",
                "ext-mbstring": "Required for multibyte Unicode string functionality."
            },
            "type": "library",
            "autoload": {
                "psr-4": {
                    "Faker\\": "src/Faker/"
                }
            },
            "notification-url": "https://packagist.org/downloads/",
            "license": [
                "MIT"
            ],
            "authors": [
                {
                    "name": "François Zaninotto"
                }
            ],
            "description": "Faker is a PHP library that generates fake data for you.",
            "keywords": [
                "data",
                "faker",
                "fixtures"
            ],
            "support": {
                "issues": "https://github.com/FakerPHP/Faker/issues",
                "source": "https://github.com/FakerPHP/Faker/tree/v1.24.1"
            },
            "time": "2024-11-21T13:46:39+00:00"
        },
        {
            "name": "fileeye/mimemap",
            "version": "2.2.5",
            "source": {
                "type": "git",
                "url": "https://github.com/FileEye/MimeMap.git",
                "reference": "d85461d6663501d29d1838d1ad65222a1ce44d7b"
            },
            "dist": {
                "type": "zip",
                "url": "https://api.github.com/repos/FileEye/MimeMap/zipball/d85461d6663501d29d1838d1ad65222a1ce44d7b",
                "reference": "d85461d6663501d29d1838d1ad65222a1ce44d7b",
                "shasum": ""
            },
            "require": {
                "php": ">=8.1"
            },
            "require-dev": {
                "composer-runtime-api": "^2.0.0",
                "sebastian/comparator": ">=5",
                "sebastian/diff": ">=5",
                "symfony/console": ">=6.4",
                "symfony/filesystem": ">=6.4",
                "symfony/var-dumper": ">=6.4",
                "symfony/yaml": ">=6.4"
            },
            "bin": [
                "bin/fileeye-mimemap"
            ],
            "type": "library",
            "extra": {
                "branch-alias": {
                    "dev-master": "2.x-dev"
                }
            },
            "autoload": {
                "psr-4": {
                    "FileEye\\MimeMap\\": "src/"
                }
            },
            "notification-url": "https://packagist.org/downloads/",
            "license": [
                "LGPL-3.0-or-later"
            ],
            "description": "A PHP library to handle MIME Content-Type fields and their related file extensions.",
            "homepage": "https://github.com/FileEye/MimeMap",
            "keywords": [
                "mime",
                "mime-database",
                "mime-parser",
                "mime-type"
            ],
            "support": {
                "issues": "https://github.com/FileEye/MimeMap/issues",
                "source": "https://github.com/FileEye/MimeMap/tree/2.2.5"
            },
            "time": "2026-03-22T21:57:45+00:00"
        },
        {
            "name": "filp/whoops",
            "version": "2.18.4",
            "source": {
                "type": "git",
                "url": "https://github.com/filp/whoops.git",
                "reference": "d2102955e48b9fd9ab24280a7ad12ed552752c4d"
            },
            "dist": {
    
... [truncated, file is 591523 chars]
```
Callers & Entry Points (How public input reaches the modified code)
(none)
Repository Map
commitlint.config.js
postcss.config.cjs
tailwind.config.js
vite.config.sw.js
vite.config.ts
docs/  (1 files)
docs/.vitepress/  (11 files)
public/  (1 files)
resources/assets/  (877 files)
... (895 source files in total)
Package Manifests (Dependencies, scripts, build configuration)
### package.json
```
{
  "name": "koel",
  "author": "Phan An <me@phanan.net>",
  "homepage": "https://koel.dev",
  "license": "MIT",
  "description": "A personal music streaming server that works",
  "keywords": [
    "music",
    "audio",
    "stream"
  ],
  "repository": {
    "type": "git",
    "url": "https://github.com/koel/koel"
  },
  "dependencies": {
    "@fortawesome/fontawesome-svg-core": "^6.7.2",
    "@fortawesome/free-brands-svg-icons": "^6.7.2",
    "@fortawesome/free-regular-svg-icons": "^6.7.2",
    "@fortawesome/free-solid-svg-icons": "^6.7.2",
    "@fortawesome/vue-fontawesome": "^3.0.8",
    "@laravel/echo-vue": "^2.1.6",
    "butterchurn": "^2.6.7",
    "butterchurn-presets": "^2.4.7",
    "dompurify": "^3.4.0",
    "events": "^3.3.0",
    "fuse.js": "^7.1.0",
    "idb": "^8.0.3",
    "ismobilejs": "^0.4.1",
    "ky": "^1.14.3",
    "lodash-es": "^4.18.1",
    "lucide-vue-next": "^0.452.0",
    "marked": "^17.0.4",
    "nouislider": "^14.7.0",
    "nprogress": "^0.2.0",
    "qrcode": "^1.5.4",
    "sketch-js": "^1.1.3",
    "style-observer": "^0.1.2",
    "three": "^0.146.0",
    "tiny-typed-emitter": "^2.1.0",
    "vue": "^3.5.29",
    "vue-advanced-cropper": "^2.8.9",
    "youtube-player": "^5.6.0"
  },
  "devDependencies": {
    "@commitlint/cli": "^19.8.1",
    "@commitlint/config-conventional": "^19.8.1",
    "@faker-js/faker": "^9.8.0",
    "@floating-ui/dom": "^1.7.2",
    "@tailwindcss/postcss": "^4.3.0",
    "@tailwindcss/vite": "^4.3.0",
    "@testing-library/user-event": "^14.6.1",
    "@testing-library/vue": "^6.6.1",
    "@types/lodash-es": "^4.17.12",
    "@types/nprogress": "^0.2.3",
    "@types/pusher-js": "^4.2.2",
    "@types/three": "^0.144.0",
    "@types/youtube-player": "^5.5.11",
    "@vitejs/plugin-vue": "^6.0.4",
    "@vueuse/components": "^13.4.0",
    "@vueuse/core": "^13.4.0",
    "@vueuse/integrations": "^13.4.0",
    "autoprefixer": "^10.4.21",
    "factoria": "^5.0.0",
    "fake-indexeddb": "^6.2.5",
    "jest-serializer-vue": "^2.0.2",
    "jsdom": "^26.1.0",
    "laravel-echo": "^2.1.6",
    "laravel-vite-plugin": "^2.1.0",
    "postcss": "^8.5.10",
    "postcss-mixins": "^10.0.1",
    "postcss-nested": "^6.2.0",
    "pusher-js": "^4.4.0",
    "rollup-plugin-visualizer": "^6.0.3",
    "tailwindcss": "^4.3.0",
    "typescript": "^5.8.3",
    "vite": "npm:@voidzero-dev/vite-plus-core@^0.1.11",
    "vite-plus": "^0.1.11",
    "vitepress": "^1.6.3",
    "vitepress-plugin-llms": "^1.11.0",
    "vitest": "npm:@voidzero-dev/vite-plus-test@^0.1.11",
    "vue-tsc": "^3.2.5"
  },
  "engines": {
    "node": "^20.19.0 || >=22.12.0"
  },
  "scripts": {
    "check": "vp check resources/assets",
    "check:fix": "vp check --fix resources/assets",
    "typecheck": "vue-tsc --noEmit -p resources/assets/tsconfig.typecheck.json",
    "test": "vp test",
    "test:unit": "vp test",
    "build:sw": "vp build --config vite.config.sw.js",
    "build": "vp build && pnpm run build:sw",
    "dev": "node -e \"console.warn('Command \\\"pnpm dev\\\" has been removed. Use \\\"composer dev\\\" instead.')\"",
    "docs:dev": "vitepress dev docs",
    "docs:build": "vitepress build docs",
    "docs:preview": "vitepress preview docs",
    "prepare": "vp config"
  },
  "type": "module",
  "pnpm": {
    "overrides": {
      "form-data@<2.5.4": ">=2.5.4",
      "@rolldown/pluginutils": "1.0.0-rc.9",
      "vite": "npm:@voidzero-dev/vite-plus-core@^0.1.11",
      "vitest": "npm:@voidzero-dev/vite-plus-test@^0.1.11"
    }
  },
  "packageManager": "pnpm@10.32.1"
}

```

### composer.json
```
{
  "name": "koel/koel",
  "description": "Audio streaming solution that works.",
  "keywords": [
    "audio",
    "stream",
    "mp3"
  ],
  "license": "MIT",
  "type": "project",
  "require": {
    "php": ">=8.3",
    "laravel/framework": "^13.0",
    "james-heinrich/getid3": "^1.9",
    "guzzlehttp/guzzle": "^7.2",
    "pusher/pusher-php-server": "^7.2",
    "predis/predis": "~1.0",
    "ext-exif": "*",
    "ext-gd": "*",
    "ext-fileinfo": "*",
    "ext-json": "*",
    "ext-SimpleXML": "*",
    "daverandom/resume": "^0.0.3",
    "laravel/helpers": "^1.7",
    "teamtnt/laravel-scout-tntsearch-driver": "^15.1.0",
    "algolia/algoliasearch-client-php": "^3.3",
    "webmozart/assert": "^1.10",
    "laravel/sanctum": "^4.0",
    "laravel/scout": "^11.0",
    "jwilsson/spotify-web-api-php": "^5.2",
    "meilisearch/meilisearch-php": "^0.24.0",
    "http-interop/http-factory-guzzle": "^1.2",
    "league/flysystem-aws-s3-v3": "^3.0",
    "spatie/flysystem-dropbox": "^3.0",
    "saloonphp/saloon": "^4.0",
    "saloonphp/laravel-plugin": "^4.0",
    "laravel/socialite": "^5.12",
    "laravel/ui": "^4.5",
    "nunomaduro/collision": "^v8.8",
    "league/flysystem-sftp-v3": "^3.0",
    "spatie/laravel-ray": "^1.36",
    "tiben/crontab-manager": "*",
    "owen-it/laravel-auditing": "^14.0",
    "fileeye/mimemap": "^2.2",
    "ezyang/htmlpurifier": "^4.18",
    "jaybizzle/crawler-detect": "^1.3",
    "laravel/nightwatch": "^1.13",
    "intervention/image-laravel": "^1.5",
    "laravel/prompts": "^0.3.6",
    "laravel/tinker": "^3.0",
    "fakerphp/faker": "^1.24",
    "spatie/laravel-permission": "^6.21",
    "enshrined/svg-sanitize": "^0.22.0",
    "phanan/poddle": "^1.2.4",
    "laravel/ai": "^0.7.0",
    "league/flysystem-webdav": "^3.0"
  },
  "require-dev": {
    "roave/security-advisories": "dev-latest",
    "mockery/mockery": "~1.0",
    "phpunit/phpunit": "^11.0",
    "php-mock/php-mock-mockery": "^1.3",
    "larastan/larastan": "^3.7",
    "phlak/semver": "^5.0",
    "laravel/boost": "^2.0",
    "opcodesio/log-viewer": "^3.19",
    "carthage-software/mago": "^1.8.0"
  },
  "suggest": {
    "ext-zip": "Allow downloading multiple songs as Zip archives"
  },
  "autoload": {
    "classmap": [
      "database"
    ],
    "psr-4": {
      "App\\": "app/",
      "Database\\Seeders\\": "database/seeders/"
    },
    "files": [
      "app/Helpers.php"
    ]
  },
  "autoload-dev": {
    "classmap": [
      "tests/TestCase.php"
    ],
    "psr-
```
Context & Existing Test Patterns
Existing test files touched by the patch: tests/Fakes/FakeNetwork.php, tests/Feature/RadioStationTest.php, tests/Integration/Services/Podcast/PodcastServiceTest.php, tests/Integration/Values/EpisodePlayableTest.php, tests/TestCase.php, tests/Unit/Helpers/SafeHttpTest.php, tests/Unit/Services/Network/NetworkTest.php, tests/Unit/Services/Network/SafeHttpTest.php, tests/Unit/Services/Radio/RadioStreamProxyTest.php
Repository top-level entries: .cursor, .editorconfig, .env.example, .github, .gitignore, .htaccess.example, .junie, .mcp.json, .oxfmtrc.json, .version, .vite-hooks, .vscode, AGENTS.md, CLAUDE.md, CODE_OF_CONDUCT.md, Caddyfile.example, LICENSE.md, README.md, api-docs, app, artisan, boost.json, bootstrap, commitlint.config.js, composer.json, composer.lock, config, database, docs, mago.toml, nginx.conf.example, package.json, phpstan.neon.dist, phpunit.xml.dist, pnpm-lock.yaml, postcss.config.cjs, public, resources, routes, scripts, server.php, storage, tailwind.config.js, tests, vite.config.sw.js, vite.config.ts
Project's own test patterns and conventions:
### tests/Unit/Services/Radio/RadioStreamProxyTest.php
```
<?php

namespace Tests\Unit\Services\Radio;

use App\Helpers\Network;
use App\Services\Radio\RadioStreamProxy;
use Mockery;
use PHPUnit\Framework\Attributes\Test;
use Tests\TestCase;

class RadioStreamProxyTest extends TestCase
{
    #[Test]
    public function openStreamRefusesUnsafeUrl(): void
    {
        $network = Mockery::mock(Network::class);
        $network->expects('isSafeUrl')->with('http://127.0.0.1/stream')->andReturnFalse();

        $proxy = new RadioStreamProxy($network);

        self::assertFalse($proxy->openStream('http://127.0.0.1/stream'));
    }
}

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

