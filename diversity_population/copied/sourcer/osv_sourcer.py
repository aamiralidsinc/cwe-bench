#!/usr/bin/env python3
"""Sourcer 1 ("osv"): mine OSV bulk dumps for security-fix task candidates.

Run with  python3 -I osv_sourcer.py <stage> [options]   (see README.md).

Stages (each is incremental and safe to re-run):
    fetch-dumps   download <ECOSYSTEM>/all.zip into the data directory
    parse         read the dumps, group aliases, write one index entry per advisory
    diffs         fetch <commit>.patch for pending entries, store per-commit metrics
    remetrics     re-parse every cached patch (after patchmetrics changes; no network)
    resignal      recompute advisory text signals from the dumps (no network)
    classify      reject or score every entry whose diff is known (no network)
    parents       resolve full sha + parent sha for the best candidates (commit web page)
    repo-meta     stars / size for the best candidates (unauthenticated API, bounded)
    propose       propose 16 candidates by the difficulty rules plus 4 controls, for review
    show          print one advisory and its fix diff for a human/agent read
    finalise      write shortlist-20.tsv / .md from review/annotations.tsv
    stats         print funnel counts
    export        write index/candidates.tsv

All downloaded material is untrusted data.  It lives in the data directory
(default ~/.tb-graders/cwe/sourcer-data), outside this code directory, and is
only ever parsed as JSON / text.  Standard library only.
"""
import argparse
import calendar
import csv
import email.utils
import gzip
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:               # needed under `python3 -I`; HERE is our own code
    sys.path.insert(0, HERE)

import index_db                        # noqa: E402
import patchmetrics                    # noqa: E402

SOURCER = "osv"
DEFAULT_DATA = os.path.expanduser("~/.tb-graders/cwe/sourcer-data")
DEFAULT_INDEX = os.path.join(HERE, "index", "candidates.sqlite")
DUMP_URL = "https://osv-vulnerabilities.storage.googleapis.com/%s/all.zip"
ECOSYSTEMS = ["PyPI", "npm", "Go", "crates.io", "Maven", "RubyGems", "Packagist"]
MAX_DUMP_BYTES = 600 * 1024 * 1024     # skip any single dump larger than this
MAX_PATCH_BYTES = 3 * 1024 * 1024      # a larger patch is an "enormous refactor" by definition
USER_AGENT = "cwe-bench-sourcer/0.1 (security-fix benchmark research; polite, cached)"

ECO_LANG = {"PyPI": "Python", "npm": "JavaScript", "Go": "Go", "crates.io": "Rust",
            "Maven": "Java", "RubyGems": "Ruby", "Packagist": "PHP"}

# --------------------------------------------------------------------------
# CWE knowledge
# --------------------------------------------------------------------------
CWE_NAMES = {
    20: "Improper Input Validation", 22: "Path Traversal", 23: "Relative Path Traversal",
    36: "Absolute Path Traversal", 59: "Link Following", 73: "External Control of File Name or Path",
    74: "Injection", 77: "Command Injection", 78: "OS Command Injection",
    79: "Cross-site Scripting", 80: "Basic XSS", 88: "Argument Injection", 89: "SQL Injection",
    90: "LDAP Injection", 91: "XML Injection", 93: "CRLF Injection", 94: "Code Injection",
    95: "Eval Injection", 96: "Static Code Injection", 98: "PHP Remote File Inclusion",
    113: "HTTP Response Splitting", 116: "Improper Encoding or Escaping of Output",
    117: "Log Injection", 119: "Memory Buffer Bounds", 120: "Classic Buffer Overflow",
    125: "Out-of-bounds Read", 129: "Improper Validation of Array Index",
    130: "Improper Handling of Length Parameter", 134: "Format String",
    138: "Improper Neutralization of Special Elements", 150: "Improper Neutralization of Escape Sequences",
    158: "Improper Neutralization of Null Byte", 172: "Encoding Error",
    176: "Improper Handling of Unicode Encoding", 178: "Improper Handling of Case Sensitivity",
    179: "Incorrect Behavior Order: Early Validation", 180: "Validate Before Canonicalize",
    182: "Collapse of Data into Unsafe Value", 184: "Incomplete List of Disallowed Inputs",
    185: "Incorrect Regular Expression", 190: "Integer Overflow", 191: "Integer Underflow",
    200: "Exposure of Sensitive Information", 201: "Sensitive Information in Sent Data",
    203: "Observable Discrepancy", 204: "Observable Response Discrepancy",
    208: "Observable Timing Discrepancy", 209: "Error Message Information Exposure",
    212: "Improper Removal of Sensitive Information", 213: "Exposure Due to Incompatible Policies",
    248: "Uncaught Exception", 250: "Execution with Unnecessary Privileges",
    252: "Unchecked Return Value", 266: "Incorrect Privilege Assignment",
    269: "Improper Privilege Management", 270: "Privilege Context Switching Error",
    276: "Incorrect Default Permissions", 277: "Insecure Inherited Permissions",
    280: "Improper Handling of Insufficient Permissions", 281: "Improper Preservation of Permissions",
    284: "Improper Access Control", 285: "Improper Authorization", 287: "Improper Authentication",
    288: "Authentication Bypass Using an Alternate Path", 289: "Authentication Bypass by Alternate Name",
    290: "Authentication Bypass by Spoofing", 294: "Authentication Bypass by Capture-replay",
    295: "Improper Certificate Validation", 297: "Certificate Host Mismatch",
    303: "Incorrect Implementation of Authentication Algorithm",
    305: "Authentication Bypass by Primary Weakness", 306: "Missing Authentication for Critical Function",
    307: "Improper Restriction of Excessive Authentication Attempts",
    312: "Cleartext Storage of Sensitive Information", 319: "Cleartext Transmission",
    321: "Hard-coded Cryptographic Key", 322: "Key Exchange without Entity Authentication",
    323: "Reusing a Nonce", 325: "Missing Cryptographic Step", 326: "Inadequate Encryption Strength",
    327: "Broken or Risky Cryptographic Algorithm", 328: "Weak Hash", 330: "Insufficiently Random Values",
    331: "Insufficient Entropy", 338: "Cryptographically Weak PRNG",
    340: "Predictable Numbers or Identifiers", 345: "Insufficient Verification of Data Authenticity",
    346: "Origin Validation Error", 347: "Improper Verification of Cryptographic Signature",
    348: "Use of Less Trusted Source", 349: "Acceptance of Extraneous Untrusted Data",
    350: "Reliance on Reverse DNS Resolution", 352: "Cross-Site Request Forgery",
    354: "Improper Validation of Integrity Check Value", 358: "Improperly Implemented Security Check",
    359: "Exposure of Private Personal Information", 362: "Race Condition",
    367: "TOCTOU Race Condition", 369: "Divide By Zero", 377: "Insecure Temporary File",
    378: "Temporary File with Insecure Permissions", 384: "Session Fixation",
    400: "Uncontrolled Resource Consumption", 401: "Memory Leak", 404: "Improper Resource Shutdown",
    405: "Asymmetric Resource Consumption", 407: "Inefficient Algorithmic Complexity",
    409: "Decompression Bomb", 410: "Insufficient Resource Pool", 415: "Double Free",
    416: "Use After Free", 425: "Forced Browsing", 426: "Untrusted Search Path",
    427: "Uncontrolled Search Path Element", 428: "Unquoted Search Path",
    434: "Unrestricted File Upload", 436: "Interpretation Conflict",
    440: "Expected Behavior Violation", 441: "Confused Deputy",
    444: "HTTP Request/Response Smuggling", 451: "UI Misrepresentation",
    454: "External Initialization of Trusted Variables", 459: "Incomplete Cleanup",
    470: "Unsafe Reflection", 472: "External Control of Assumed-Immutable Web Parameter",
    476: "NULL Pointer Dereference", 488: "Exposure of Data Element to Wrong Session",
    494: "Download of Code Without Integrity Check", 497: "Exposure of System Information",
    501: "Trust Boundary Violation", 502: "Deserialization of Untrusted Data",
    522: "Insufficiently Protected Credentials", 523: "Unprotected Transport of Credentials",
    524: "Cache Containing Sensitive Information", 532: "Sensitive Information in Log File",
    538: "Sensitive Information in Externally-Accessible File", 539: "Persistent Cookies with Sensitive Information",
    540: "Sensitive Information in Source Code", 548: "Directory Listing",
    552: "Files Accessible to External Parties", 565: "Reliance on Cookies without Validation",
    566: "Authorization Bypass Through User-Controlled SQL Primary Key",
    573: "Improper Following of Specification", 601: "Open Redirect",
    602: "Client-Side Enforcement of Server-Side Security", 610: "Externally Controlled Reference",
    611: "XML External Entity", 613: "Insufficient Session Expiration",
    614: "Sensitive Cookie Without Secure Attribute", 617: "Reachable Assertion",
    620: "Unverified Password Change", 639: "Authorization Bypass Through User-Controlled Key (IDOR)",
    640: "Weak Password Recovery", 641: "Improper Restriction of Names for Files",
    642: "External Control of Critical State Data", 643: "XPath Injection",
    644: "Improper Neutralization of HTTP Headers", 648: "Incorrect Use of Privileged APIs",
    649: "Reliance on Obfuscation without Integrity Checking",
    653: "Improper Isolation or Compartmentalization", 657: "Violation of Secure Design Principles",
    662: "Improper Synchronization", 665: "Improper Initialization",
    667: "Improper Locking", 668: "Exposure of Resource to Wrong Sphere",
    669: "Incorrect Resource Transfer Between Spheres", 670: "Always-Incorrect Control Flow",
    672: "Operation on a Resource after Expiration", 674: "Uncontrolled Recursion",
    680: "Integer Overflow to Buffer Overflow", 681: "Incorrect Conversion between Numeric Types",
    682: "Incorrect Calculation", 684: "Incorrect Provision of Specified Functionality",
    688: "Function Call With Incorrect Variable", 691: "Insufficient Control Flow Management",
    693: "Protection Mechanism Failure", 696: "Incorrect Behavior Order",
    697: "Incorrect Comparison", 703: "Improper Check of Exceptional Conditions",
    704: "Incorrect Type Conversion", 706: "Use of Incorrectly-Resolved Name or Reference",
    707: "Improper Neutralization", 708: "Incorrect Ownership Assignment",
    732: "Incorrect Permission Assignment", 749: "Exposed Dangerous Method",
    754: "Improper Check for Unusual Conditions", 755: "Improper Handling of Exceptional Conditions",
    757: "Algorithm Downgrade", 758: "Reliance on Undefined Behavior",
    759: "One-Way Hash without Salt", 760: "One-Way Hash with Predictable Salt",
    770: "Allocation of Resources Without Limits", 772: "Missing Release of Resource",
    774: "File Descriptors Without Limits", 776: "XML Entity Expansion",
    778: "Insufficient Logging", 783: "Operator Precedence Logic Error",
    784: "Reliance on Cookies in a Security Decision", 787: "Out-of-bounds Write",
    789: "Memory Allocation with Excessive Size", 798: "Hard-coded Credentials",
    799: "Improper Control of Interaction Frequency", 807: "Reliance on Untrusted Inputs in a Security Decision",
    822: "Untrusted Pointer Dereference", 824: "Uninitialized Pointer",
    829: "Inclusion of Functionality from Untrusted Control Sphere",
    833: "Deadlock", 834: "Excessive Iteration", 835: "Infinite Loop",
    836: "Password Hash Instead of Password", 838: "Inappropriate Encoding for Output Context",
    840: "Business Logic Errors", 841: "Improper Enforcement of Behavioral Workflow",
    842: "Placement of User into Incorrect Group", 843: "Type Confusion",
    862: "Missing Authorization", 863: "Incorrect Authorization",
    908: "Use of Uninitialized Resource", 909: "Missing Initialization",
    912: "Hidden Functionality", 913: "Improper Control of Dynamically-Managed Code Resources",
    914: "Improper Control of Dynamically-Identified Variables",
    915: "Mass Assignment", 916: "Password Hash With Insufficient Effort",
    917: "Expression Language Injection", 918: "Server-Side Request Forgery",
    922: "Insecure Storage of Sensitive Information", 923: "Improper Restriction of Communication Channel",
    924: "Improper Enforcement of Message Integrity", 939: "Improper Authorization in Custom URL Scheme Handler",
    940: "Improper Verification of Source of a Communication Channel",
    941: "Incorrectly Specified Destination", 942: "Permissive Cross-domain Policy",
    943: "Improper Neutralization in Data Query Logic", 1004: "Sensitive Cookie Without HttpOnly",
    1021: "Clickjacking", 1022: "Use of Web Link to Untrusted Target",
    1023: "Incomplete Comparison with Missing Factors", 1025: "Comparison Using Wrong Factors",
    1035: "Using Components with Known Vulnerabilities", 1050: "Excessive Platform Resource Consumption",
    1059: "Insufficient Technical Documentation", 1104: "Use of Unmaintained Third Party Components",
    1173: "Improper Use of Validation Framework", 1188: "Insecure Default Initialization",
    1220: "Insufficient Granularity of Access Control", 1236: "CSV Injection",
    1240: "Use of a Risky Cryptographic Primitive", 1254: "Incorrect Comparison Logic Granularity",
    1259: "Improper Restriction of Security Token Assignment",
    1284: "Improper Validation of Specified Quantity", 1285: "Improper Validation of Specified Index",
    1286: "Improper Validation of Syntactic Correctness", 1287: "Improper Validation of Specified Type",
    1288: "Improper Validation of Consistency within Input",
    1289: "Improper Validation of Unsafe Equivalence in Input",
    1295: "Debug Messages Revealing Unnecessary Information",
    1321: "Prototype Pollution", 1323: "Improper Management of Sensitive Trace Data",
    1325: "Improperly Controlled Sequential Memory Allocation", 1327: "Binding to an Unrestricted IP Address",
    1333: "Inefficient Regular Expression Complexity (ReDoS)", 1336: "Template Injection",
    1385: "Missing Origin Validation in WebSockets", 1390: "Weak Authentication",
    1391: "Use of Weak Credentials", 1392: "Use of Default Credentials",
    1393: "Use of Default Password", 1395: "Dependency on Vulnerable Third-Party Component",
    1426: "Improper Validation of Generative AI Output", 1427: "Improper Neutralization of Input Used for LLM Prompting",
}

# CWE ids too generic to name a weakness; skipped when picking the primary CWE of an entry.
GENERIC_CWES = {20, 200, 284, 693, 707, 74, 664, 668, 1035, 1395}

# --------------------------------------------------------------------------
# advisory text signals
# --------------------------------------------------------------------------
RE_FIX_BYPASS = re.compile(
    r"incomplete (fix|patch|mitigation|remediation)|insufficient (fix|patch|mitigation)|"
    r"(fix|patch|mitigation)(es)? (for|of|to) (CVE-\d{4}-\d+|GHSA-[\w-]+)[^.]{0,80}"
    r"(incomplete|insufficient|bypass|did not|does not|not sufficient|not complete)|"
    r"bypass(es|ed|ing)?( of)?( the)? (previous|earlier|prior|original|existing|initial) (fix|patch)|"
    r"(previous|earlier|prior|original|initial) (fix|patch)[^.]{0,100}"
    r"(incomplete|insufficient|bypass|did not|does not|only|missed|still)|"
    r"bypass(es|ed|ing)? (of |for |the |a )*(fix|patch|CVE-\d{4}-\d+|GHSA-[\w-]+)|"
    r"(fix|patch) bypass|did not (fully|completely) (fix|address|resolve|mitigate)|"
    r"not (fully|completely) (fixed|addressed|resolved|mitigated|patched)|"
    r"variant of (CVE-\d{4}-\d+|GHSA-[\w-]+)|follow[- ]up (fix|to|patch)|"
    r"regression (of|in|from) (CVE-\d{4}-\d+|GHSA-[\w-]+|the fix)|"
    r"remain(s|ed)? (vulnerable|exploitable|unpatched|affected)|"
    r"still (vulnerable|exploitable|bypassable|possible to|allows?|be bypassed)|"
    r"same (root cause|class of bug|vulnerability class) as|sibling (of|to|endpoint|code path)|"
    r"(other|another|additional|remaining) (code path|call site|endpoint|sink)s?[^.]{0,60}"
    r"(not|un)(covered|patched|protected|fixed)", re.I)
RE_BYPASS_WORD = re.compile(r"\bbypass", re.I)
# signal 1 wording: the same check has to hold in several places
RE_MULTI_SITE = re.compile(
    r"sibling|(other|another|additional|remaining|multiple|several|every|each|all|both|two|three|four|"
    r"five|\d+) (\w+ ){0,3}(code paths?|call sites?|callers?|endpoints?|handlers?|routes?|sinks?|"
    r"entry points?|paths|locations|places|methods|functions|transports?|listeners?|loaders?|"
    r"fetchers?|readers?|branches)|same (root cause|pattern|flaw|bug|issue|check|class of) |"
    r"applied (only )?to (only )?(one|some|a subset)|was applied to .{0,60} but not|"
    r"only (one|some) of the|not (applied|enforced|checked|validated) (in|on|for|by) (the )?other|"
    r"inconsistent(ly)? (enforce|appl|check|validat)|systemic", re.I)
# signal 2 wording: the cause sits in another layer than the place the symptom shows
RE_CAUSE_LAYER = re.compile(
    r"at the source|upstream of|second[- ]order|stored and later|later (used|rendered|"
    r"read|executed|interpolated|consumed|passed)|when (it is |they are )?(created|stored|saved|"
    r"registered|imported|negotiated)|pars(er|ing) differen|differential|interpretation "
    r"conflict|interprets? .{0,40} differently|normali[sz]|canonicali[sz]|"
    r"before (the |any )?(check|validation|authori[sz]ation)|after (the |any )?(check|validation)|"
    r"check[- ]then[- ]act|time[- ]of[- ]check|TOCTOU|re-?resolv|does not pin|never pins|"
    r"negotiat|downstream (parser|consumer|backend|service|component)|"
    r"backend (sees|parses|reads|receives)|generated (code|source|class|file)|compiled into|"
    r"trust boundary|confused deputy|(different|another|separate|lower|higher) layer", re.I)
# signal 3 wording: a defence existed and did not work
_DEFENCE_NOUN = (r"(check|validation|validator|guard|filter|sanitizer|sanitiser|sanitization|"
                 r"allow-?list|deny-?list|block-?list|restriction|protection|mitigation|"
                 r"verification|sandbox|policy|gate|limit|acl|waf|rule|escaping|containment|"
                 r"signature|constraint)")
RE_DEFENCE = re.compile(
    r"bypass(es|ed|ing)? (of |the |this |that |a |an |existing |its |any |\w+ ){0,3}" + _DEFENCE_NOUN +
    r"|" + _DEFENCE_NOUN + r"s? (\w+ ){0,2}(is|was|are|were|can be|could be) (\w+ ){0,1}"
    r"(bypass|circumvent|evad|skipp|incomplete|insufficient|ineffective|lexical|never|not )|"
    r"(incomplete|insufficient|ineffective|inadequate|flawed|broken|faulty) " + _DEFENCE_NOUN +
    r"|does not (account|consider|handle|cover|inspect)|doesn't (account|consider|handle|cover)|"
    r"only (checks?|validates?|applies|blocks?|handles?|covers?|inspects?|strips?|enforces?|"
    r"filters?|rejects?|considers?)|(existing|current|added|introduced) " + _DEFENCE_NOUN +
    r"|unanchored|lexical(ly)?|fails? open|sole security control|assert(ion)?[- ]based|"
    r"case[- ]sensitiv|circumvent|evade|slips? past", re.I)
RE_SEMANTIC = re.compile(
    r"canonicali[sz]|normali[sz]|symlink|symbolic link|hard ?link|TOCTOU|time[- ]of[- ]check|"
    r"race condition|\brace\b|pars(er|ing) differen|differential|smuggl|unicode|homoglyph|"
    r"case[- ]insensitiv|double[- ](url[- ])?(en|de)cod|percent[- ](en|de)cod|url[- ](en|de)cod|"
    r"deseriali[sz]|unmarshal|pickle|gadget|prototype pollution|__proto__|mass assignment|"
    r"dns rebinding|ipv6|ipv4-mapped|decimal ip|redirect|allow[- ]?list|deny[- ]?list|"
    r"block[- ]?list|sandbox|escape|tenant|cross-tenant|scope|ownership|session|nonce|replay|"
    r"signature|constant[- ]time|timing|ordering|before (the )?(check|validation)|"
    r"after (the )?(check|validation)|trailing (dot|slash|space)|null byte|backslash|"
    r"path separator|dot[- ]segment|\.\./|relative path|absolute path|host header|"
    r"x-forwarded|origin check|wildcard|regex anchor|unanchored|prefix (match|check)|"
    r"startswith|suffix (match|check)|endswith|substring", re.I)
RE_HTTP = re.compile(
    r"\b(endpoint|route|HTTP|HTTPS|REST|GraphQL|gRPC|API request|request header|webhook|"
    r"web (interface|UI|server|application|app)|upload|cookie|login|OAuth|OIDC|SAML|"
    r"POST|GET|PUT|DELETE|PATCH|query parameter|request body|URL|websocket|unauthenticated "
    r"(remote )?(attacker|user)|remote attacker|server)\b")
RE_CLI = re.compile(r"\b(CLI|command[- ]line|subcommand|command line tool|shell command|"
                    r"when (running|invoking|executing) `|archive|tarball|zip file|"
                    r"extract(s|ing|ion)?|unpack)\b", re.I)
SERVICES = [
    ("postgres", re.compile(r"postgres", re.I)),
    ("mysql/mariadb", re.compile(r"mysql|mariadb", re.I)),
    ("redis", re.compile(r"\bredis\b|valkey", re.I)),
    ("mongodb", re.compile(r"mongo", re.I)),
    ("elasticsearch/opensearch", re.compile(r"elasticsearch|opensearch", re.I)),
    ("kafka", re.compile(r"\bkafka\b", re.I)),
    ("rabbitmq/amqp", re.compile(r"rabbitmq|\bamqp\b", re.I)),
    ("ldap", re.compile(r"\bldap\b|active directory", re.I)),
    ("s3/object-store", re.compile(r"\bs3\b|minio|object stor", re.I)),
    ("smtp", re.compile(r"\bsmtp\b|mail server", re.I)),
    ("identity-provider", re.compile(r"\boidc\b|\bsaml\b|keycloak|identity provider|\bidp\b", re.I)),
    ("kubernetes/container-runtime", re.compile(r"kubernetes|\bk8s\b|kubelet|containerd|docker daemon|docker socket", re.I)),
    ("database (unspecified)", re.compile(r"\bdatabase\b|\bSQL\b", re.I)),
]

# --------------------------------------------------------------------------
# environment filters (stage 4)
# --------------------------------------------------------------------------
ENV_RULES = [
    ("kernel", re.compile(r"(^|[-_/ ])(linux[-_ ]kernel|kernel[-_ ]module|kmod|ebpf)([-_/ ]|$)", re.I), "name"),
    ("firmware_or_embedded", re.compile(r"firmware|esp32|esp8266|arduino|stm32|zephyr|\brtos\b|"
                                        r"microcontroller|bootloader|openwrt", re.I), "name+summary"),
    ("mobile_app", re.compile(r"\bandroid\b|\bios\b|react[-_ ]native|\bflutter\b|\bexpo\b|cordova|"
                              r"capacitor|\bxamarin\b|ionic", re.I), "name"),
    ("mobile_app", re.compile(r"\b(Android|iOS) (app|application|client)\b|mobile app", re.I), "summary"),
    ("browser_extension", re.compile(r"browser[- ]extension|chrome[- ]extension|firefox add-?on|"
                                     r"webextension|userscript", re.I), "name+summary"),
    ("desktop_gui", re.compile(r"(^|[/ :])(electron|tauri|nw\.js|wails)($|[ /])|\belectron app\b|"
                               r"desktop (app|application|client)", re.I), "name+summary"),
    ("gpu_only", re.compile(r"\bcuda\b|\bgpu\b|nvidia|tensorrt|\bopencl\b", re.I), "name+summary"),
    ("windows_only", re.compile(r"\b(on|for|in|under) (Microsoft )?Windows\b|Windows[- ]only|"
                                r"\bWindows\b[^.]{0,40}\b(only|specific|hosts?|systems?|platforms?)\b|"
                                r"\bNTFS\b|\bUNC path|\.lnk\b|\bPowerShell\b|cmd\.exe|\bDLL\b|"
                                r"\bWin32\b|drive letter", re.I), "summary"),
    ("windows_only", re.compile(r"only (affects?|impacts?|exploitable on|applies to|on) (Microsoft )?Windows|"
                                r"Windows[- ]only|Windows[- ]specific|"
                                r"(Linux|macOS|Unix|POSIX)[^.]{0,40}(is|are) not affected", re.I), "details"),
    ("macos_only", re.compile(r"\b(on|for) macOS\b|macOS[- ]only|only (affects?|on) macOS", re.I), "summary"),
    ("hardware", re.compile(r"\bbluetooth\b|\bBLE\b|serial port|\bGPIO\b|hardware wallet|\bTPM\b|"
                            r"\bSGX\b|smart ?card|\bUSB\b", re.I), "summary"),
]
ENV_LANGS = {"Swift": "mobile_app", "Objective-C": "mobile_app", "Dart": "mobile_app"}
RE_TOY = re.compile(r"(^|[-_/.])(demo|demos|example|examples|sample|samples|tutorial|tutorials|"
                    r"playground|poc|ctf|vulnerable|vuln|dvwa|hello[-_]?world|test[-_]?repo|"
                    r"homework|coursework|bootcamp|learning|workshop|kata)([-_/.]|$)", re.I)

RE_COMMIT_URL = re.compile(
    r"github\.com/([A-Za-z0-9][A-Za-z0-9-]*)/([A-Za-z0-9_.-]+)/"
    r"(?:pull/\d+/commits|commits?)/([0-9a-fA-F]{7,40})(?![0-9a-zA-Z])")
RE_PR_URL = re.compile(r"github\.com/([A-Za-z0-9][A-Za-z0-9-]*)/([A-Za-z0-9_.-]+)/pull/(\d+)")
RE_REPO_URL = re.compile(r"github\.com[/:]([A-Za-z0-9][A-Za-z0-9-]*)/([A-Za-z0-9_.-]+)")
RE_SAFE_REPO = re.compile(r"^[a-z0-9][a-z0-9-]*/[a-z0-9_.-]+$")
NOT_REPO_OWNERS = {"advisories", "github", "orgs", "security", "sponsors", "features", "about"}

PARSE_REJECTS = ("withdrawn", "no_cwe", "no_github_repo", "no_fix_commit",
                 "no_fix_commit_pr_only")


def log(msg):
    sys.stderr.write(time.strftime("%H:%M:%S ") + msg + "\n")
    sys.stderr.flush()


def safe_repo(owner, name):
    if name.endswith(".git"):
        name = name[:-4]
    repo = (owner + "/" + name).lower()
    if not RE_SAFE_REPO.match(repo) or name in (".", "..") or owner.lower() in NOT_REPO_OWNERS:
        return ""
    return repo


# --------------------------------------------------------------------------
# polite HTTP
# --------------------------------------------------------------------------
class RateLimited(Exception):
    pass


class Fetcher(object):
    def __init__(self, delay, timeout=25):
        self.delay = delay
        self.timeout = timeout
        self.last = 0.0
        self.requests = 0
        self.rate_limit_hits = 0

    def get(self, url, max_bytes, accept=None):
        """-> (status, bytes, headers).  status 'ok' | 'http_<code>' | 'too_large' | 'error:<kind>'.
        Raises RateLimited after repeated 429/abuse responses so the stage can stop cleanly."""
        backoff = 60
        for attempt in range(4):
            wait = self.delay - (time.time() - self.last)
            if wait > 0:
                time.sleep(wait)
            self.last = time.time()
            self.requests += 1
            headers = {"User-Agent": USER_AGENT}
            if accept:
                headers["Accept"] = accept
            # diversity_population copy: optional token for api.github.com only (read from the environment)
            if url.startswith("https://api.github.com/") and os.environ.get("GITHUB_TOKEN"):
                headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
            req = urllib.request.Request(url, headers=headers)
            try:
                resp = urllib.request.urlopen(req, timeout=self.timeout)
                try:
                    data = resp.read(max_bytes + 1)
                    hdrs = dict(resp.headers.items())
                finally:
                    resp.close()
                if len(data) > max_bytes:
                    return "too_large", b"", hdrs
                return "ok", data, hdrs
            except urllib.error.HTTPError as e:
                hdrs = dict(e.headers.items()) if e.headers else {}
                if e.code == 429 or (e.code == 403 and hdrs.get("Retry-After")):
                    self.rate_limit_hits += 1
                    if attempt == 3:
                        raise RateLimited(url)
                    try:
                        pause = int(hdrs.get("Retry-After", ""))
                    except ValueError:
                        pause = backoff
                    pause = min(max(pause, 30), 900)
                    log("rate limited (HTTP %d); sleeping %ds" % (e.code, pause))
                    time.sleep(pause)
                    backoff *= 2
                    continue
                if 500 <= e.code < 600 and attempt < 2:
                    time.sleep(10)
                    continue
                return "http_%d" % e.code, b"", hdrs
            except Exception as e:                      # timeouts, resets, DNS
                if attempt < 1:
                    time.sleep(3)
                    continue
                return "error:%s" % type(e).__name__, b"", {}
        return "error:retries", b"", {}


# --------------------------------------------------------------------------
# stage: fetch-dumps
# --------------------------------------------------------------------------
def stage_fetch_dumps(args, idx):
    out = os.path.join(args.data, "dumps")
    os.makedirs(out, exist_ok=True)
    counts = {}
    for eco in args.ecosystems:
        url = DUMP_URL % eco
        dest = os.path.join(out, eco + ".zip")
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                size = int(r.headers.get("Content-Length") or 0)
                remote_mod = r.headers.get("Last-Modified", "")
        except Exception as e:
            log("%s: HEAD failed (%s); skipped" % (eco, e))
            counts[eco] = "head_failed"
            continue
        if size > MAX_DUMP_BYTES:
            log("%s: dump is %d MB, over the %d MB cap; skipped" %
                (eco, size >> 20, MAX_DUMP_BYTES >> 20))
            counts[eco] = "skipped_too_large:%d" % size
            continue
        if os.path.exists(dest) and os.path.getsize(dest) == size and not args.force:
            log("%s: already have %d bytes (remote Last-Modified %s)" % (eco, size, remote_mod))
            counts[eco] = "cached:%d" % size
            continue
        log("%s: downloading %d MB" % (eco, size >> 20))
        tmp = dest + ".part"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=120) as r, open(tmp, "wb") as f:
            while True:
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                f.write(chunk)
        os.replace(tmp, dest)
        counts[eco] = "downloaded:%d" % size
    return counts


# --------------------------------------------------------------------------
# stage: parse
# --------------------------------------------------------------------------
def text_signals(text):
    sig = {}
    m = RE_FIX_BYPASS.search(text)
    if m:
        sig["fix_bypass"] = m.group(0)[:80]
    if RE_BYPASS_WORD.search(text):
        sig["bypass_word"] = 1
    for key, rx in (("multi_site_text", RE_MULTI_SITE), ("cause_layer_text", RE_CAUSE_LAYER),
                    ("defence_text", RE_DEFENCE)):
        hits = sorted(set(m.group(0).lower()[:40] for m in rx.finditer(text)))
        if hits:
            sig[key] = hits[:4]
    sem = sorted(set(x.group(0).lower() for x in RE_SEMANTIC.finditer(text)))
    if sem:
        sig["semantic_kw"] = sem[:8]
    http = len(RE_HTTP.findall(text))
    cli = len(RE_CLI.findall(text))
    sig["http_hits"] = http
    sig["cli_hits"] = cli
    if http >= 2 and http >= cli:
        sig["entry_guess"] = "http"
    elif cli >= 1 and cli > http:
        sig["entry_guess"] = "cli"
    elif http == 1:
        sig["entry_guess"] = "http?"
    else:
        sig["entry_guess"] = "library?"
    for kind, rx, where in ENV_RULES:           # details-only platform rules are applied here,
        if where == "details" and rx.search(text):   # because details are not kept in the index
            sig["platform_only"] = kind
    svc = [name for name, rx in SERVICES if rx.search(text)]
    if svc:
        sig["services_guess"] = svc
    named = named_locations(text)
    if named:
        sig["named"] = named
    return sig


# --------------------------------------------------------------------------
# S2a: the locations an advisory names (functions, files, endpoints, commands)
# --------------------------------------------------------------------------
_SRC_EXT = sorted((e.lstrip(".") for e, lang in patchmetrics.LANG_BY_EXT.items()
                   if lang and lang != "Template"), key=len, reverse=True)
_EXT_ALT = "|".join(re.escape(e) for e in _SRC_EXT)
RE_FENCE = re.compile(r"```.*?(```|$)", re.S)
RE_NOISE_SECTION = re.compile(       # sections whose names are PoC code, credits or links
    r"^#{1,6}\s*(poc|proof[- ]of[- ]concept|steps to reproduce|reproduc\w*|exploit\w*|"
    r"references?|credits?|attribution|acknowledg\w*|timeline|workarounds?|resources?|"
    r"disclosure|reporter|thanks)\b.*?(?=^#{1,6}\s|\Z)", re.I | re.M | re.S)
RE_BACKTICK = re.compile(r"`([^`\n]{2,120})`")
RE_BLOB_URL = re.compile(r"github\.com/[\w.-]+/[\w.-]+/blob/[^/\s]+/([^\s#?)\]>\"']+)")
RE_URL = re.compile(r"https?://\S+")
RE_PATH = re.compile(r"(?<![\w/.-])((?:[\w.-]+/)*[\w-][\w.-]*\.(?:%s))(?![\w/])" % _EXT_ALT)
RE_CALL_PROSE = re.compile(r"(?<![\w.$#:])([A-Za-z_$][\w$]*(?:(?:\.|#|::|->)[A-Za-z_$][\w$]*)*)"
                           r"\((?:\)|[^()\n]{0,40}\))")
RE_ENDPOINT = re.compile(r"\b(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+`?(/[\w./{}:<>*-]*)")
RE_IDENT = re.compile(r"^@?[A-Za-z_$][\w$]*(?:(?:\.|#|::|->)[A-Za-z_$][\w$]*)*(?:\(.*\))?$")
RE_CAMEL = re.compile(r"^_*[a-z][a-z0-9]*[A-Z]\w*$|^_*[A-Z][a-z0-9]+[A-Z]\w*$")
RE_CONSTANT = re.compile(r"^[A-Z0-9_]+$")
CMD_STOP = {"pip", "pip3", "npm", "npx", "yarn", "pnpm", "go", "cargo", "gem", "bundle", "composer",
            "mvn", "gradle", "docker", "curl", "wget", "git", "python", "python3", "node", "sudo",
            "apt", "apt-get", "brew", "echo", "cat", "ls", "cd", "export", "set", "java", "ruby",
            "php", "bash", "sh", "kubectl", "helm", "uv", "poetry", "deno", "bun", "nc", "ssh"}
FS_ROOTS = {"etc", "tmp", "var", "usr", "home", "proc", "dev", "bin", "root", "opt", "sys",
            "private", "users", "windows", "c:"}
NAME_STOP = {"main", "run", "init", "get", "set", "call", "new", "md5", "sha1", "sha256", "len",
             "str", "string", "open", "read", "write", "print", "eval", "exec", "join", "json",
             "parse", "format", "require", "import", "include", "send", "fetch", "log", "test",
             "url", "http", "https", "true", "false", "null", "none", "nil", "self", "this",
             "toString", "hasOwnProperty", "constructor", "valueOf", "apply", "bind", "push",
             "append", "replace", "split", "strip", "trim", "lower", "upper", "encode", "decode",
             "startswith", "endswith", "startsWith", "endsWith", "includes", "contains", "equals",
             "close", "flush", "map", "filter", "reduce", "keys", "values", "items", "resolve",
             "then", "catch", "setTimeout", "assert", "alert", "fn", "func", "function"}
TLDS = {"com", "org", "net", "io", "dev", "app", "example", "local", "localhost", "co", "uk"}


FRAMEWORK_JS = {"node", "vue", "next", "nuxt", "three", "chart", "express", "react", "angular",
                "d3", "socket", "moment", "ember", "backbone", "deno", "bun", "solid", "svelte",
                "alpine", "htmx", "p5", "pdf", "highlight", "marked", "handlebars", "lodash",
                "underscore", "jquery", "nest", "fastify", "koa", "hapi", "electron", "ckeditor",
                "tiptap", "quill", "dompurify", "sanitize-html", "markdown-it", "showdown"}


def _is_file_name(p):
    """'src/webob/response.py' or 'negotiation.rs' yes; 'Node.js', 'e.g.c' no."""
    if "/" in p:
        return True
    stem = p.rsplit(".", 1)[0].lower()
    return stem not in FRAMEWORK_JS and not re.match(r"^(e\.g|i\.e|etc|vs|v?\d[\d.]*)$", stem)


def _ident_key(raw):
    """'Response._make_location_absolute()' -> ('_make_location_absolute', 'Response')."""
    s = re.sub(r"\(.*$", "", raw.lstrip("@"))
    parts = [p for p in re.split(r"\.|#|::|->", s) if p]
    if not parts:
        return "", ""
    return parts[-1], (parts[-2] if len(parts) >= 2 else "")


def _keep_ident(raw, called):
    """Is this identifier a code location (function/method/class), not a value or word?"""
    if raw.startswith("@"):                       # annotation / decorator / mention
        return False
    meth, owner = _ident_key(raw)
    if not meth or meth in NAME_STOP or len(meth) < 3 or RE_CONSTANT.match(meth):
        return False
    if owner and (meth.lower() in TLDS or meth.lower() in _SRC_EXT):
        return False                              # example.com, response.py
    if called or owner:
        return True
    return bool(RE_CAMEL.match(meth))             # fetchToken, SshBlockCipher; not 'issuer'


def named_locations(text):
    """Locations an advisory names: {'func': [...], 'file': [...], 'endpoint': [...],
    'command': [...]}.  Code blocks and PoC / credits / reference sections are ignored."""
    files, funcs, endpoints, commands = [], [], [], []

    def add(lst, v, cap=15):
        if v and v not in lst and len(lst) < cap:
            lst.append(v)

    for m in RE_BLOB_URL.finditer(text):                 # links to source lines name a file
        p = m.group(1)
        if re.search(r"\.(%s)$" % _EXT_ALT, p):
            add(files, p)
    body = RE_NOISE_SECTION.sub("\n", RE_FENCE.sub("\n", text))
    body = RE_URL.sub(" ", body)
    for m in RE_ENDPOINT.finditer(body):
        add(endpoints, m.group(1).rstrip(".,;:`"))
    for m in RE_BACKTICK.finditer(body):
        s = m.group(1).strip()
        after = body[m.end():m.end() + 24].lower()
        if not s:
            continue
        words = s.split()
        if len(words) > 1:
            if (2 <= len(words) <= 5 and words[0].lower() not in CMD_STOP and
                    all(re.match(r"^[a-z0-9][\w.-]*$", w) for w in words) and
                    not any(w.startswith("-") for w in words[:2])):
                add(commands, s)
            continue
        if re.match(r"^--?[A-Za-z][\w-]+(=.*)?$", s):
            continue                                       # a flag, not a location
        if s.startswith("/") and not re.search(r"\.(%s)$" % _EXT_ALT, s):
            segs = [x for x in s.split("/") if x]
            if segs and segs[0].lower() not in FS_ROOTS and re.search(r"[A-Za-z]{3}", s) \
                    and not s.startswith("//") and not re.search(r"\s|\.\.|%[0-9a-fA-F]{2}", s) \
                    and not re.search(r"\.(com|org|net|io)\b", s):
                add(endpoints, s.rstrip(".,;:"))
            continue
        if re.search(r"\.(%s)$" % _EXT_ALT, s) and re.match(r"^[\w./-]+$", s):
            if _is_file_name(s):
                add(files, s.lstrip("./"))
            continue
        if RE_IDENT.match(s):
            called = "(" in s or bool(re.match(r"\s*(\(|function|method|handler|class|"
                                               r"module|endpoint|route|middleware)\b", after))
            if _keep_ident(s, called):
                add(funcs, re.sub(r"\(.*$", "", s.lstrip("@")))
    prose = RE_BACKTICK.sub(" ", body)
    for m in RE_CALL_PROSE.finditer(prose):
        if _keep_ident(m.group(1), True):
            add(funcs, m.group(1))
    for m in RE_PATH.finditer(prose):
        if _is_file_name(m.group(1)):
            add(files, m.group(1).lstrip("./"))
    out = {}
    for k, v in (("func", funcs), ("file", files), ("endpoint", endpoints), ("command", commands)):
        if v:
            out[k] = v
    return out


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def s2a_signal(sig, shape, repo="", packages=""):
    """S2a named-location disparity.  -> dict(state, named, touched, examples).

    state: 'unknown'   the advisory names no location (or the fix's sites are not recorded)
           'disparity' it names locations and the fix touches none of them
           'partial'   the fix touches some named location and also changes code elsewhere
           'on_named'  every changed site lies in a named function or named file
    'Touched' is lenient (so 'disparity' is conservative): a named function or class equals a
    hunk-header name, the enclosing definition of a changed line, or a changed file's basename;
    a named file matches a changed file's path suffix or basename; an endpoint or command matches
    when one of its segments names a changed definition, file or directory."""
    named = sig.get("named") or {}
    units = shape.get("units")
    if units is None:
        return {"state": "unknown", "why": "fix sites not recorded"}
    own = set()
    for p in (packages or "").split(" | "):
        nm = p.split(":", 1)[-1]
        own.update([_norm(nm), _norm(nm.split("/")[-1])])
    if repo:
        own.update([_norm(repo.split("/")[-1])])
    funcs = []
    for f in named.get("func", []):
        meth, owner = _ident_key(f)
        if _norm(meth) and _norm(meth) not in own:
            funcs.append((f, _norm(meth), _norm(owner)))
    files = [(f, f.lower().lstrip("/"), _norm(f.split("/")[-1].split(".")[0]))
             for f in named.get("file", [])]
    cmds = []
    for c in named.get("command", []):
        w = c.split()
        if _norm(w[0]) in own or _norm(w[0]) == _norm((repo or "").split("/")[-1]):
            cmds.append((c, [_norm(x) for x in w[1:] if len(_norm(x)) >= 2]))
    eps = []
    for e in named.get("endpoint", []):
        segs = [_norm(s) for s in e.split("/") if s and not re.match(r"^[{:<*]|^\d+$|^v\d+$", s)]
        segs = [s for s in segs if len(s) >= 3 and s not in ("api", "admin")]
        if segs:
            eps.append((e, segs))
    n_named = len(funcs) + len(files) + len(cmds) + len(eps)
    if not n_named:
        return {"state": "unknown", "why": "advisory names no location"}
    if not units:
        return {"state": "unknown", "why": "no code-changing site", "named": n_named}
    changed = list(shape.get("changed_files") or sorted(set(u[0] for u in units)))
    stems = set(_norm(p.split("/")[-1].split(".")[0]) for p in changed)
    dirs = set(_norm(d) for p in changed for d in p.split("/")[:-1])
    names = set(_norm(u[1]) for u in units if u[1])
    for v in (shape.get("hunk_funcs") or {}).values():
        names.update(_norm(x) for x in v)
    touched = []
    for f, meth, owner in funcs:
        if meth in names or meth in stems or (owner and (owner in names or owner in stems)):
            touched.append(f)
    for f, low, stem in files:
        if any(p.lower().endswith(low) for p in changed) or ("/" not in low and stem in stems):
            touched.append(f)
    for c, ws in cmds:
        if ws and all(w in dirs or w in stems or w in names for w in ws):
            touched.append(c)
    for e, segs in eps:
        if any(s in names or s in stems or s in dirs for s in segs):
            touched.append(e)
    ex = [x[0] for x in funcs[:3]] + [x[0] for x in files[:2]] + [x[0] for x in eps[:2]] + \
        [x[0] for x in cmds[:1]]
    if not touched:
        return {"state": "disparity", "named": n_named, "touched": [], "examples": ex[:5]}
    # exact coverage of every changed site: its definition (or the hunk header) is a named
    # function/class, or its file is a named file / a file named after a named class
    cov_names = set(m for _f, m, _o in funcs) | set(o for _f, _m, o in funcs if o)
    cov_files = set(low for _f, low, _s in files)
    cov_stems = set(s for _f, low, s in files if "/" not in low) | set(
        o for _f, _m, o in funcs if o)
    heads = shape.get("hunk_funcs") or {}

    def covered(u):
        path, name = u[0], u[1]
        if _norm(name) in cov_names:
            return True
        if any(_norm(h) in cov_names for h in heads.get(path, [])) and not name:
            return True
        if any(path.lower().endswith(f) for f in cov_files if "/" in f):
            return True
        return _norm(path.split("/")[-1].split(".")[0]) in cov_stems

    state = "on_named" if all(covered(u) for u in units) else "partial"
    return {"state": state, "named": n_named, "touched": touched[:6], "examples": ex[:5]}


def reduce_record(rec, eco):
    """Keep only what the funnel needs from one OSV record."""
    ds = rec.get("database_specific") or {}
    cwes = []
    for c in ds.get("cwe_ids") or []:
        if isinstance(c, str) and re.match(r"^CWE-\d+$", c.strip()):
            cwes.append(c.strip())
    packages, git_commits, pkg_repos = [], [], []
    for aff in rec.get("affected") or []:
        pkg = aff.get("package") or {}
        if pkg.get("name"):
            packages.append("%s:%s" % (pkg.get("ecosystem", eco), pkg["name"]))
        for rng in aff.get("ranges") or []:
            if rng.get("type") != "GIT":
                continue
            m = RE_REPO_URL.search(rng.get("repo") or "")
            repo = safe_repo(m.group(1), m.group(2)) if m else ""
            if not repo:
                continue
            for ev in rng.get("events") or []:
                sha = ev.get("fixed") or ""
                if re.match(r"^[0-9a-fA-F]{7,40}$", sha):
                    git_commits.append((repo, sha.lower()))
    ref_commits, prs = [], []
    for ref in rec.get("references") or []:
        url = ref.get("url") or ""
        m = RE_COMMIT_URL.search(url)
        if m:
            repo = safe_repo(m.group(1), m.group(2))
            if repo:
                ref_commits.append((repo, m.group(3).lower(), ref.get("type") or ""))
            continue
        m = RE_PR_URL.search(url)
        if m:
            repo = safe_repo(m.group(1), m.group(2))
            if repo:
                prs.append((repo, m.group(3)))
            continue
        if ref.get("type") == "PACKAGE":
            m = RE_REPO_URL.search(url)
            if m:
                repo = safe_repo(m.group(1), m.group(2))
                if repo:
                    pkg_repos.append(repo)
    cvss = ""
    for s in rec.get("severity") or []:
        if str(s.get("type", "")).startswith("CVSS"):
            cvss = s.get("score") or cvss
    return {
        "id": rec.get("id", ""),
        "aliases": [a for a in rec.get("aliases") or [] if isinstance(a, str)],
        "published": rec.get("published") or "",
        "modified": rec.get("modified") or "",
        "withdrawn": rec.get("withdrawn") or "",
        "summary": (rec.get("summary") or "").strip(),
        "details": rec.get("details") or "",
        "cwes": cwes,
        "severity": ds.get("severity") or "",
        "cvss": cvss,
        "packages": packages,
        "ecosystems": [eco],
        "ref_commits": ref_commits,
        "git_commits": git_commits,
        "prs": prs,
        "pkg_repos": pkg_repos,
    }


def dedupe_shas(shas):
    """Drop abbreviated shas that are a prefix of a longer one; keep order."""
    out = []
    for s in sorted(set(shas), key=lambda x: -len(x)):
        if not any(o.startswith(s) for o in out):
            out.append(s)
    order = dict((s, i) for i, s in enumerate(shas))
    return sorted(out, key=lambda s: order.get(s, 0))


def stage_parse(args, idx):
    counts = {"records_read": 0, "malware_skipped": 0, "records_kept": 0, "groups": 0,
              "already_indexed": 0, "new_entries": 0, "bad_json": 0}
    per_eco = {}
    recs = {}
    for eco in args.ecosystems:
        path = os.path.join(args.data, "dumps", eco + ".zip")
        if not os.path.exists(path):
            log("%s: no dump at %s (run fetch-dumps); skipped" % (eco, path))
            continue
        n = mal = 0
        with zipfile.ZipFile(path) as z:
            for name in z.namelist():
                if not name.endswith(".json"):
                    continue
                n += 1
                if name.startswith("MAL-"):
                    mal += 1
                    continue
                try:
                    rec = json.loads(z.read(name).decode("utf-8", "replace"))
                except Exception:
                    counts["bad_json"] += 1
                    continue
                if not isinstance(rec, dict) or not rec.get("id") or str(rec["id"]).startswith("MAL-"):
                    continue
                red = reduce_record(rec, eco)
                old = recs.get(red["id"])
                if old:                                   # same advisory in a second ecosystem dump
                    old["ecosystems"] = sorted(set(old["ecosystems"] + [eco]))
                    old["packages"] = sorted(set(old["packages"] + red["packages"]))
                else:
                    recs[red["id"]] = red
        per_eco[eco] = {"records": n, "malware": mal}
        counts["records_read"] += n
        counts["malware_skipped"] += mal
        log("%s: %d records, %d malware skipped" % (eco, n, mal))
    counts["records_kept"] = len(recs)
    counts["per_ecosystem"] = per_eco

    # union-find over id + aliases, so GHSA / CVE / PYSEC / GO / RUSTSEC copies become one entry
    parent = {}

    def find(x):
        while parent.setdefault(x, x) != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for rid, r in recs.items():
        for a in r["aliases"]:
            ra, rb = find(rid.upper()), find(a.upper())
            if ra != rb:
                parent[ra] = rb
    groups = {}
    for rid in recs:
        groups.setdefault(find(rid.upper()), []).append(rid)
    counts["groups"] = len(groups)

    def rank(rid):                                         # GHSA carries CWE + severity
        return (0 if rid.startswith("GHSA-") else 1, rid)

    for members in groups.values():
        members.sort(key=rank)
        all_ids = []
        for rid in members:
            for i in [rid] + recs[rid]["aliases"]:
                if i.upper() not in all_ids:
                    all_ids.append(i.upper())
        if any(idx.seen_id(i) for i in all_ids):
            counts["already_indexed"] += 1
            continue
        rs = [recs[m] for m in members]
        head = rs[0]
        cwes, packages, ecos = [], [], []
        commits, prs, pkg_repos = [], [], []
        for r in rs:
            for c in r["cwes"]:
                if c not in cwes:
                    cwes.append(c)
            for p in r["packages"]:
                if p not in packages:
                    packages.append(p)
            for e in r["ecosystems"]:
                if e not in ecos:
                    ecos.append(e)
            commits += [(repo, sha, "reference") for repo, sha, _t in r["ref_commits"]]
            commits += [(repo, sha, "git_range") for repo, sha in r["git_commits"]]
            prs += r["prs"]
            pkg_repos += r["pkg_repos"]
        published = min([r["published"] for r in rs if r["published"]] or [""])
        modified = max([r["modified"] for r in rs if r["modified"]] or [""])
        details = max((r["details"] for r in rs), key=len)
        summary = head["summary"] or next((r["summary"] for r in rs if r["summary"]), "")
        if not summary:
            summary = details.strip().split("\n")[0][:200]
        severity = next((r["severity"] for r in rs if r["severity"]), "")
        cvss = next((r["cvss"] for r in rs if r["cvss"]), "")
        withdrawn = bool(head["withdrawn"]) or all(r["withdrawn"] for r in rs)

        # choose the repository: the one most fix commits point at; ties go to the package repo
        by_repo = {}
        for repo, sha, _src in commits:
            by_repo.setdefault(repo, []).append(sha)
        repo, shas, other_repos = "", [], []
        if by_repo:
            repo = max(by_repo, key=lambda r: (len(set(by_repo[r])), r in pkg_repos))
            shas = dedupe_shas(by_repo[repo])
            other_repos = sorted(r for r in by_repo if r != repo)
        elif pkg_repos:
            repo = pkg_repos[0]
        elif prs:
            repo = prs[0][0]

        sig = text_signals(summary + "\n" + details)
        sig["details_len"] = len(details)
        if prs:
            sig["prs"] = sorted(set("%s#%s" % p for p in prs))[:6]
        if other_repos:
            sig["commits_in_other_repos"] = other_repos[:5]

        if withdrawn:
            status, reason = "rejected", "withdrawn"
        elif not cwes:
            status, reason = "rejected", "no_cwe"
        elif not repo:
            status, reason = "rejected", "no_github_repo"
        elif not shas:
            status, reason = "rejected", ("no_fix_commit_pr_only" if prs else "no_fix_commit")
        elif published[:10] >= args.since:
            status, reason = "pending", None
        else:
            status, reason = "deferred", "outside_recency_window"
        counts["parse_" + (reason or "in_window")] = counts.get("parse_" + (reason or "in_window"), 0) + 1

        fields = {
            "primary_id": members[0],
            "cve": " ".join(i for i in all_ids if i.startswith("CVE-")),
            "ecosystems": " ".join(ecos),
            "packages": " | ".join(packages[:8]),
            "repo": repo or None,
            "fix_commits": " ".join(shas) or None,
            "n_fix_commits": len(shas),
            "cwe_ids": " ".join(cwes),
            "published": published[:10],
            "modified": modified[:10],
            "severity": severity,
            "cvss": cvss,
            "summary": summary[:400],
            "adv_signals": json.dumps(sig, sort_keys=True),
            "status": status,
            "reject_reason": reason,
        }
        src_of = dict((sha, src) for r_, sha, src in commits if r_ == repo)
        eid = idx.add_entry(SOURCER, all_ids, fields, commits=[], commit_source="reference")
        for sha in shas:
            # a commit another entry already owns stays with its first owner (seen_commit)
            idx.db.execute(
                "INSERT OR IGNORE INTO commits (repo, sha, entry_id, source) VALUES (?, ?, ?, ?)",
                (repo, sha, eid, src_of.get(sha, "reference")))
        counts["new_entries"] += 1
    idx.commit()

    # widening the window later only needs this update
    cur = idx.db.execute(
        "UPDATE entries SET status = 'pending', reject_reason = NULL, updated_at = ? "
        "WHERE status = 'deferred' AND published >= ?", (index_db.now(), args.since))
    counts["deferred_promoted_to_pending"] = cur.rowcount
    idx.commit()
    return counts


# --------------------------------------------------------------------------
# stage: diffs
# --------------------------------------------------------------------------
def patch_cache_path(data, repo, sha):
    owner, name = repo.split("/", 1)
    return os.path.join(data, "patches", owner, name, sha + ".patch.gz")


def load_patch(data, repo, sha):
    p = patch_cache_path(data, repo, sha)
    if os.path.exists(p):
        with gzip.open(p, "rb") as f:
            return f.read().decode("utf-8", "replace")
    return None


def prescore(row):
    """Order of the fetch queue, from advisory-only signals (the diff is not known yet).

    Favoured weakness class, languages the target models are weakest in, and wording that
    points at signals 1-4 come first; newest first within a tie."""
    sig = json.loads(row["adv_signals"] or "{}")
    p = weights()["prescore"]
    s = 0
    if p["add_weakness_points"]:
        s += weakness_points(row["cwe_ids"], row["summary"] or "", row["packages"] or "")[0]
    ecos = (row["ecosystems"] or "").split()
    s += max([p["ecosystem_points"].get(e, 0) for e in ecos] or [0])
    if sig.get("fix_bypass"):
        s += p["earlier_fix_incomplete"]
    if sig.get("defence_text"):
        s += p["defence_wording"]
    if sig.get("multi_site_text"):
        s += p["multi_site_wording"]
    if sig.get("cause_layer_text"):
        s += p["cause_layer_wording"]
    if (row["n_fix_commits"] or 0) > 4:
        s += p["more_than_4_fix_commits"]
    return s


def stage_diffs(args, idx):
    counts = {"entries_considered": 0, "commits_fetched": 0, "from_cache": 0, "http_404": 0,
              "too_large": 0, "errors": 0, "entries_completed": 0, "stopped_early": ""}
    rows = idx.db.execute(
        "SELECT * FROM entries WHERE status = 'pending' AND repo IS NOT NULL").fetchall()
    rows.sort(key=lambda r: (prescore(r), r["published"] or ""), reverse=True)
    first = {idx.seen_id(i.upper()) for i in args.first} - {None}
    if first:
        rows.sort(key=lambda r: r["entry_id"] not in first)
    fetcher = Fetcher(args.delay)
    started = time.time()
    done_requests = 0
    try:
        for row in rows:
            todo = idx.db.execute(
                "SELECT sha, fetch_status FROM commits WHERE repo = ? AND entry_id = ? "
                "ORDER BY length(sha) DESC, rowid", (row["repo"], row["entry_id"])).fetchall()
            if not todo:
                continue
            counts["entries_considered"] += 1
            have = sum(1 for t in todo if t["fetch_status"]
                       and not str(t["fetch_status"]).startswith("error"))
            for t in todo:
                if have >= args.max_commits:
                    break
                is_error = str(t["fetch_status"] or "").startswith("error")
                if t["fetch_status"] and not (args.retry_errors and is_error):
                    continue
                if args.only_errors and not is_error:
                    continue
                if args.max_requests and done_requests >= args.max_requests:
                    counts["stopped_early"] = "max_requests"
                    break
                if args.max_minutes and time.time() - started > args.max_minutes * 60:
                    counts["stopped_early"] = "max_minutes"
                    break
                sha = t["sha"]
                text = load_patch(args.data, row["repo"], sha)
                if text is not None:
                    status = "ok"
                    counts["from_cache"] += 1
                else:
                    url = "https://github.com/%s/commit/%s.patch" % (row["repo"], sha)
                    try:
                        status, data, _h = fetcher.get(url, MAX_PATCH_BYTES)
                    except RateLimited:
                        counts["stopped_early"] = "rate_limited"
                        break
                    done_requests += 1
                    if status == "ok":
                        text = data.decode("utf-8", "replace")
                        p = patch_cache_path(args.data, row["repo"], sha)
                        os.makedirs(os.path.dirname(p), exist_ok=True)
                        with gzip.open(p + ".part", "wb") as f:
                            f.write(data)
                        os.replace(p + ".part", p)
                        counts["commits_fetched"] += 1
                    elif status == "http_404":
                        counts["http_404"] += 1
                    elif status == "too_large":
                        counts["too_large"] += 1
                    else:
                        counts["errors"] += 1
                fields = {"fetch_status": status, "fetched_at": index_db.now()}
                if status == "ok":
                    m = patchmetrics.parse_patch(text)
                    full = sha if len(sha) == 40 else None
                    if not full and m["n_patches"] == 1 and m["shas"][0].startswith(sha):
                        full = m["shas"][0]
                    fields.update({
                        "full_sha": full, "n_patches": m["n_patches"],
                        "is_merge": 1 if (m["n_patches"] > 1 or
                                          (m["shas"] and len(sha) == 40 and m["shas"][0] != sha)) else 0,
                        "subject": m["subject"], "commit_date": m["commit_date"],
                        "src_files": m["src_files"], "src_added": m["src_added"],
                        "src_removed": m["src_removed"], "src_hunks": m["src_hunks"],
                        "test_files": m["test_files"], "other_files": m["other_files"],
                        "language": m["language"],
                        "file_breakdown": json.dumps(m["breakdown"], sort_keys=True),
                        "src_paths": json.dumps(m["src_paths"]),
                        "shape": json.dumps(m["shape"], sort_keys=True),
                    })
                idx.update_commit(row["repo"], sha, **fields)
                idx.commit()
                have += 1
            if counts["stopped_early"]:
                break
            counts["entries_completed"] += 1
            if (counts["entries_completed"] % 100) == 0:
                log("diffs: %d entries done, %d requests, %d rate-limit pauses" %
                    (counts["entries_completed"], fetcher.requests, fetcher.rate_limit_hits))
    except KeyboardInterrupt:          # Ctrl-C / SIGINT: keep the counts, stay resumable
        counts["stopped_early"] = "interrupted"
    counts["http_requests"] = fetcher.requests
    counts["rate_limit_hits"] = fetcher.rate_limit_hits
    return counts


# --------------------------------------------------------------------------
# stages: remetrics / resignal  (no network: recompute from the cache and the dumps)
# --------------------------------------------------------------------------
def stage_remetrics(args, idx):
    """Re-parse every cached patch so the commits table matches the current patchmetrics."""
    counts = {"reparsed": 0, "cache_missing": 0}
    rows = idx.db.execute("SELECT repo, sha FROM commits WHERE fetch_status = 'ok'").fetchall()
    for r in rows:
        text = load_patch(args.data, r["repo"], r["sha"])
        if text is None:
            counts["cache_missing"] += 1
            continue
        m = patchmetrics.parse_patch(text)
        idx.update_commit(
            r["repo"], r["sha"], src_files=m["src_files"], src_added=m["src_added"],
            src_removed=m["src_removed"], src_hunks=m["src_hunks"], test_files=m["test_files"],
            other_files=m["other_files"], language=m["language"],
            file_breakdown=json.dumps(m["breakdown"], sort_keys=True),
            src_paths=json.dumps(m["src_paths"]), shape=json.dumps(m["shape"], sort_keys=True))
        counts["reparsed"] += 1
        if counts["reparsed"] % 500 == 0:
            idx.commit()
    idx.commit()
    return counts


def stage_resignal(args, idx):
    """Recompute adv_signals from the advisory text in the dumps (details are not in the index)."""
    counts = {"updated": 0, "advisory_not_in_dumps": 0}
    zips = {}
    rows = idx.db.execute(
        "SELECT entry_id, primary_id, ecosystems, adv_signals FROM entries WHERE sourcer = ? AND "
        "status != 'deferred' AND (reject_reason IS NULL OR reject_reason NOT IN (%s))"
        % ", ".join("'%s'" % r for r in PARSE_REJECTS), (SOURCER,)).fetchall()
    for r in rows:
        adv = None
        for eco in (r["ecosystems"] or "").split() or ECOSYSTEMS:
            if eco not in zips:
                path = os.path.join(args.data, "dumps", eco + ".zip")
                zips[eco] = zipfile.ZipFile(path) if os.path.exists(path) else None
            if zips[eco] is None:
                continue
            try:
                adv = json.loads(zips[eco].read(r["primary_id"] + ".json").decode("utf-8", "replace"))
                break
            except KeyError:
                continue
        if adv is None:
            counts["advisory_not_in_dumps"] += 1
            continue
        old = json.loads(r["adv_signals"] or "{}")
        sig = text_signals((adv.get("summary") or "") + "\n" + (adv.get("details") or ""))
        for k in ("details_len", "prs", "commits_in_other_repos"):
            if k in old:
                sig[k] = old[k]
        idx.db.execute("UPDATE entries SET adv_signals = ? WHERE entry_id = ?",
                       (json.dumps(sig, sort_keys=True), r["entry_id"]))
        counts["updated"] += 1
    idx.commit()
    return counts


# --------------------------------------------------------------------------
# stage: classify (reject or score)
# --------------------------------------------------------------------------
def commit_epoch(date_header):
    """'Wed, 18 Feb 2026 19:02:54 -0800' -> epoch seconds, or None."""
    try:
        return email.utils.parsedate_to_datetime(date_header).timestamp()
    except Exception:
        return None


def primary_cwe(cwe_ids):
    nums = [int(c[4:]) for c in (cwe_ids or "").split()]
    for n in nums:
        if n not in GENERIC_CWES:
            return n
    return nums[0] if nums else 0


def env_reject(row, language, sig):
    if sig.get("platform_only"):
        return sig["platform_only"]
    names = " ".join([row["repo"] or "", row["packages"] or ""])
    summary = row["summary"] or ""
    for kind, rx, where in ENV_RULES:
        if where == "name":
            hay = names
        elif where == "summary":
            hay = summary
        elif where == "details":
            continue
        else:
            hay = names + " " + summary
        if rx.search(hay):
            return kind
    if language in ENV_LANGS:
        return ENV_LANGS[language]
    return ""


# Weakness classes the target models are weakest in (signal 5).  First match wins.
CLASS_CWES = [
    ("auth_session", {287, 288, 289, 290, 294, 295, 297, 303, 304, 305, 306, 307, 308, 309, 346,
                      352, 384, 521, 522, 523, 565, 613, 620, 640, 784, 798, 836, 940, 1390, 1391,
                      1392, 1393}),
    ("authz", {266, 269, 276, 277, 280, 281, 284, 285, 425, 441, 566, 639, 653, 668, 732, 862,
               863, 1220}),
    ("integrity", {345, 347, 353, 354, 426, 494, 502, 649, 829, 830, 913, 915, 924, 323, 325}),
    ("logic_design", {178, 179, 180, 182, 183, 362, 367, 436, 444, 501, 602, 642, 657, 670, 691,
                      696, 697, 706, 799, 807, 840, 841, 1023, 1289}),
]
# One dangerous call or one missing escape (LOW signal when fixed at one spot).
SINK_CWES = {74, 77, 78, 79, 80, 88, 89, 90, 91, 93, 94, 95, 96, 113, 116, 117, 643, 917, 943,
             1236, 1336}
LANG_TIER = {"Java": "weakest", "Kotlin": "weakest", "Scala": "weakest", "Rust": "weakest",
             "Go": "weak", "Ruby": "weak", "PHP": "weak", "C": "weak", "C++": "weak",
             "JavaScript": "strong", "TypeScript": "strong", "Python": "python"}


def weakness_class(cwe_ids):
    """Descriptive hand-made class (kept for reference; scoring uses weakness_points)."""
    nums = [int(c[4:]) for c in (cwe_ids or "").split()]
    for name, members in CLASS_CWES:
        if any(n in members for n in nums):
            return name
    return "other"


# --------------------------------------------------------------------------
# weights.json: every point value the screener uses lives there
# --------------------------------------------------------------------------
WEIGHTS_PATH = os.path.join(HERE, "weights.json")
_WEIGHTS = None


def weights():
    """weights.json, loaded once, with the OWASP map and LLM regexes prepared."""
    global _WEIGHTS
    if _WEIGHTS is None:
        with open(WEIGHTS_PATH) as f:
            w = json.load(f)
        if w.get("version") not in (2, 3):
            raise SystemExit("%s: expected version 2 or 3" % WEIGHTS_PATH)
        omap = w["owasp_map"]
        with open(os.path.normpath(os.path.join(HERE, omap["file"]))) as f:
            cats = json.load(f)["categories"]
        w["_cat_of"] = {c: k for k, v in cats.items() for c in v["cwes"]}
        w["_cat_of"].update({int(c): k for c, k in omap["extra"].items()})
        w["_abstraction"], w["_ancestors"] = {}, {}
        with open(os.path.normpath(os.path.join(HERE, omap["hierarchy_file"]))) as f:
            for line in f.read().splitlines()[1:]:          # MITRE CWE Research view (CWE-1000)
                cid, _name, abstraction, _status, _parent, _pillar, _depth, path = line.split("\t")
                w["_abstraction"][int(cid)] = abstraction
                w["_ancestors"][int(cid)] = [int(a) for a in reversed(path.split(">")[:-1])]
        t25 = w["weakness"]["top25_label"]
        with open(os.path.normpath(os.path.join(HERE, t25["file"]))) as f:
            w["_top25"] = {int(l.split("\t")[1]): int(l.split("\t")[0])
                           for l in f.read().splitlines()[1:] if l.strip()}
        al = w["weakness"]["attack_label"]
        w["_attack"] = {}                                   # CWE -> labelled attack classes
        with open(os.path.normpath(os.path.join(HERE, al["file"]))) as f:
            for r in csv.DictReader(f, delimiter="\t"):
                hits = [c for col, wanted in al["classes"].items()
                        for c in r[col].split(";") if c in wanted]
                if hits:
                    w["_attack"][int(r["cwe"])] = hits
        lil, eco = w["weakness"]["llm_in_the_loop"], w["weakness"]["llm_ecosystem"]
        w["_lil_summary"] = re.compile(lil["summary_regex"], re.I)
        w["_eco_summary"] = re.compile(eco["summary_regex"], re.I)
        w["_eco_package"] = re.compile(r"(?<![A-Za-z0-9])(?:%s)(?![A-Za-z0-9])"
                                       % eco["package_regex"], re.I)
        _WEIGHTS = w
    return _WEIGHTS


def owasp_category(cwe_num):
    """-> (category or None, the CWE it came from). Direct OWASP 2025 mapping first, then the
    nearest ancestor in MITRE's Research view that is mapped (weights: ancestor_fallback)."""
    W = weights()
    if cwe_num in W["_cat_of"]:
        return W["_cat_of"][cwe_num], cwe_num
    if W["owasp_map"].get("ancestor_fallback"):
        for a in W["_ancestors"].get(cwe_num, []):
            if a in W["_cat_of"]:
                return W["_cat_of"][a], a
    return None, None


def weakness_points(cwe_ids, summary="", packages=""):
    """-> (points, parts, category).  S5: OWASP 2025 category points + per-CWE adjustment for
    the best-scoring CWE, plus the abstract-only and LLM-in-the-loop bonuses (weights.json)."""
    W = weights()
    w = W["weakness"]
    nums = [int(c[4:]) for c in (cwe_ids or "").split() if c[4:].isdigit()]
    adjs = sorted(((k, v) for k, v in w["cwe_adjustments"].items()
                   if not k.startswith("_") and k != "disputed"), key=lambda kv: -kv[1]["points"])
    parts = {}
    # Category: the best CWE that maps (directly or via an ancestor); 'unmapped' only if none does.
    mapped = []
    for n in nums:
        cat, via = owasp_category(n)
        if cat:
            mapped.append((w["category_points"][cat], n, cat, via))
    if mapped:
        pts, n, cat, via = max(mapped)
        label = "OWASP %s (CWE-%d)" % (cat, n) if via == n else \
            "OWASP %s (CWE-%d via ancestor CWE-%d)" % (cat, n, via)
        parts[label] = pts
    else:
        cat = "unmapped"
        parts["OWASP unmapped (no CWE maps, nor any ancestor)"] = w["category_points"]["unmapped"]
    # Per-CWE adjustment: the highest over all CWEs (exact CWE only, never inherited).
    best_adj = None
    for n in nums:
        if n in w["cwe_adjustments"]["disputed"]["cwes"]:
            cand = (0, n, "disputed")
        else:
            cand = next(((spec["points"], n, name) for name, spec in adjs if n in spec["cwes"]), None)
        if cand and (best_adj is None or cand[0] > best_adj[0]):
            best_adj = cand
    if best_adj and best_adj[0]:
        parts["CWE-%d %s" % (best_adj[1], best_adj[2].replace("_", " "))] = best_adj[0]
    elif best_adj:
        parts["CWE-%d sources disagree" % best_adj[1]] = 0
    # No specific weakness named: every CWE is a known-broad one, Pillar level, or not a weakness
    # entry at all (a MITRE category such as 264).
    ab = w["abstract_only"]
    if nums and all(n in ab["cwes"] or W["_abstraction"].get(n) in ab["abstractions"]
                    or n not in W["_abstraction"] for n in nums):
        parts["only broad CWEs (no specific weakness named)"] = ab["points"]
    in_top25 = sorted((W["_top25"][n], n) for n in nums if n in W["_top25"])
    if in_top25:                                     # label (0 points unless weights change)
        parts["CWE Top 25 2025: %s" % ", ".join("#%d CWE-%d" % rn for rn in in_top25)] = \
            w["top25_label"]["points"]
    attack = sorted({c for n in nums for c in W["_attack"].get(n, [])})
    if attack:                                       # label (0 points unless weights change)
        parts["Attack class: %s" % ", ".join(attack)] = w["attack_label"]["points"]
    if W["_lil_summary"].search(summary or ""):
        parts["LLM-in-the-loop (model output drives the action)"] = w["llm_in_the_loop"]["points"]
    elif W["_eco_summary"].search(summary or "") or W["_eco_package"].search(packages or ""):
        parts["LLM ecosystem (label)"] = w["llm_ecosystem"]["points"]
    return sum(parts.values()), parts, cat


def compute_signals(row, c, sig, siblings):
    """Every computed (c_*) signal column for one entry, from its fix commit and advisory text."""
    shape = json.loads(c["shape"] or "{}") if "shape" in c.keys() else {}
    fix_sites = shape.get("fix_sites", c["src_hunks"] or 0)
    site_files = shape.get("site_files", c["src_files"] or 0)
    same = shape.get("same_check_sites", 0)
    removed_checks = shape.get("removed_check_lines", 0)
    span = shape.get("hunk_span", 0)
    code_added = shape.get("code_added", c["src_added"] or 0)
    code_removed = shape.get("code_removed", c["src_removed"] or 0)
    cwes = [int(x[4:]) for x in (row["cwe_ids"] or "").split()]
    wpoints, wparts, klass = weakness_points(row["cwe_ids"], row["summary"] or "",
                                             row["packages"] or "")
    favoured = 1 if wpoints >= weights()["weakness"]["favoured_threshold"] else 0
    compact = 1 if (fix_sites <= 1 or (site_files <= 1 and fix_sites <= 2 and span <= 30)) else 0
    multi = 1 if (same >= 2 or (fix_sites >= 4 and site_files >= 2)) else 0
    out = {
        "c_fix_sites": fix_sites,
        "c_site_files": site_files,
        "c_same_check_sites": same,
        "c_same_check_name": shape.get("same_check_name", ""),
        "c_multi_site": multi,
        "c_cause_layer_hint": 1 if sig.get("cause_layer_text") else 0,
        # both must hold: the advisory says a defence failed AND the fix rewrote a condition
        "c_defence_present": 1 if ((sig.get("defence_text") or sig.get("fix_bypass"))
                                   and removed_checks >= 1) else 0,
        "c_modified_check_lines": removed_checks,
        "c_bypass_incomplete": 1 if sig.get("fix_bypass") else 0,
        "c_sibling_advisories": siblings,
        "c_class": klass,                        # OWASP Top 10:2025 category of the best CWE
        "c_favoured_class": favoured,            # weakness points >= favoured_threshold
        "c_single_compact_hunk": compact,
        "c_far_apart": 1 if (site_files >= 2 or span > 80) else 0,
        "c_restructured": 1 if (code_removed >= 5 and
                                code_removed >= 0.2 * max(1, code_added + code_removed)) else 0,
        "c_single_sink": 1 if (any(n in SINK_CWES for n in cwes) and not favoured
                               and site_files <= 1 and same < 2) else 0,
        "c_one_site_guard": 1 if (compact and code_removed <= 2) else 0,
        "c_compact_small_repo": (None if not row["repo_size_kb"] else
                                 (1 if (compact and row["repo_size_kb"] < 20000) else 0)),
        "lang_tier": LANG_TIER.get(c["language"] or "", "other"),
        # transient (leading underscore): used by score_entry, never written to the index
        "_changed_lines": (code_added or 0) + (code_removed or 0),
        "_weakness": (wpoints, wparts),
        # S2 computed parts (no index column: they live in score_detail; inputs are in
        # adv_signals['named'] and the commit's shape JSON)
        "_s2a": s2a_signal(sig, shape, row["repo"] or "", row["packages"] or ""),
        "_s2b": shape.get("s2b"),
    }
    return out


def score_entry(row, cs, sig, judged=None):
    """-> (score, detail).  cs = compute_signals(...).  judged = annotation row or None.

    With `judged`, the reader's verdict on signals 1, 2, 3 and 7 replaces the computed proxy
    (a "no" scores 0 even when the proxy fired).  Total changed lines are not scored."""
    d = {}
    W = weights()

    def yes(key):
        return judged is not None and str(judged.get(key, "")).strip() in ("1", "yes", "y")

    # 1. multi-site trust decision (strongest)
    ms = W["multi_site"]
    if judged is not None:
        if yes("j_multi_site"):
            d["S1 multi-site trust decision (JUDGEMENT)"] = ms["judged"]
    elif cs["c_same_check_sites"] >= 3:
        d["S1 same new check added at 3+ sites (%s)" % cs["c_same_check_name"]] = \
            ms["same_new_check_3plus_sites"]
    elif cs["c_same_check_sites"] == 2:
        d["S1 same new check added at 2 sites (%s)" % cs["c_same_check_name"]] = \
            ms["same_new_check_2_sites"]
    elif cs["c_multi_site"]:
        d["S1 4+ code sites in 2+ files"] = ms["four_plus_sites_in_two_plus_files"]
    if judged is None and sig.get("multi_site_text") and "S1" not in " ".join(d):
        d["S1 advisory wording names sibling sites"] = ms["advisory_names_sibling_sites"]
    # 2. cause in a different layer from the symptom
    co = W["cause_other_layer"]
    if judged is not None:
        if yes("j_cause_other_layer"):
            d["S2 cause in another layer than the symptom (JUDGEMENT)"] = co["judged"]
    elif cs["c_cause_layer_hint"]:
        d["S2 advisory wording suggests cause in another layer"] = co["advisory_hint"]
    # 2a/2b. computed S2 (added 2026-10-16; 0 points until validated, shown as labels)
    sd = W.get("symptom_fix_disparity")
    if sd:
        sup = " (computed; JUDGEMENT supersedes)" if judged is not None else ""
        pts = (lambda k: 0 if judged is not None else sd.get(k, 0))
        a = cs.get("_s2a") or {"state": "unknown"}
        st = a.get("state", "unknown")
        if st == "disparity":
            d["S2a fix touches none of the %d locations the advisory names (%s)%s" % (
                a.get("named", 0), ", ".join(a.get("examples", [])[:3]), sup)] = pts("s2a_disparity")
        elif st == "on_named":
            d["S2a fix lands only on locations the advisory names (%s)%s" % (
                ", ".join(a.get("touched", [])[:3]), sup)] = pts("s2a_on_named")
        elif st == "partial":
            d["S2a fix touches named locations (%s) and code elsewhere%s" % (
                ", ".join(a.get("touched", [])[:3]), sup)] = pts("s2a_partial")
        else:
            d["S2a unknown: %s%s" % (a.get("why", "advisory names no location"), sup)] = \
                pts("s2a_unknown")
        b = cs.get("_s2b") or {}
        if b.get("fires"):
            calls = b.get("check_calls_producer")
            d["S2b fix changes a check (%s) and a data producer (%s) in another %s; %s roles; "
              "check->producer call: %s%s" % (
                  ", ".join(b.get("check_files", [])[:2]), ", ".join(b.get("producer_files", [])[:2]),
                  "directory" if b.get("diff_dir") else "file in the same directory",
                  "strict (both by name)" if b.get("strict") else "loose",
                  {None: "not searched", 1: "yes", 0: "no"}.get(calls, calls), sup)] = (
                pts("s2b_check_and_producer_in_other_file")
                + (pts("s2b_bonus_other_directory") if b.get("diff_dir") else 0)
                + (pts("s2b_bonus_strict_roles") if b.get("strict") else 0)
                + (pts("s2b_check_does_not_call_producer") if calls == 0 else 0))
    # 3. a defence was present and did not work
    de = W["defence_ineffective"]
    if judged is not None:
        if yes("j_defence_ineffective"):
            d["S3 existing defence was ineffective (JUDGEMENT)"] = de["judged"]
    elif cs["c_defence_present"]:
        d["S3 advisory says a defence failed and the fix rewrote a condition"] = \
            de["advisory_and_condition_rewritten"]
    elif sig.get("defence_text"):
        d["S3 advisory wording only: a defence failed"] = de["advisory_wording_only"]
    # 4. bypass / incomplete earlier fix / repeated advisories
    bs = W["bypass_and_siblings"]
    if cs["c_bypass_incomplete"]:
        d["S4 advisory says an earlier fix was incomplete or bypassed"] = bs["earlier_fix_incomplete"]
    if cs["c_sibling_advisories"] >= 3:
        d["S4 3+ sibling advisories (same package, shared CWE, 120 days)"] = \
            bs["sibling_advisories_3plus"]
    elif cs["c_sibling_advisories"] >= 1:
        d["S4 sibling advisory (same package, shared CWE, 120 days)"] = bs["sibling_advisory_1plus"]
    # 5. weakness: OWASP 2025 category + per-CWE evidence (+ abstract-only, LLM-in-the-loop)
    wpoints, wparts = cs.get("_weakness") or weakness_points(
        row["cwe_ids"], row["summary"] or "", row["packages"] or "")[:2]
    for k, v in wparts.items():                 # zero-point parts kept: they show what was checked
        d["S5 " + k] = v
    # 6. fix shape: the strongest predictor of repair failure (PatchEval and others)
    fs = W["fix_shape"]
    if cs["c_site_files"] >= 2:
        d["S6 fix touches 2+ files"] = fs["two_plus_files"]
    if cs["c_fix_sites"] >= 3:
        d["S6 fix has 3+ hunks"] = fs["three_plus_hunks"]
        if cs["c_far_apart"]:
            d["S6 3+ hunks far apart"] = fs["three_plus_hunks_far_apart"]
    if (cs.get("_changed_lines") or 0) >= 50:
        d["S6 50+ changed source lines"] = fs["fifty_plus_changed_source_lines"]
    if cs["c_restructured"]:
        d["S6 code deleted or restructured, not only added"] = fs["code_deleted_or_restructured"]
    if cs["c_single_compact_hunk"]:
        d["S6 single compact hunk"] = fs["single_compact_hunk"]
    spread = sum(v for k, v in d.items() if v > 0 and k[:2] in ("S1", "S6"))
    if spread > fs["cap_with_multi_site"]:
        d["S1+S6 cap (spread-out fix counted once)"] = fs["cap_with_multi_site"] - spread
    # 7. over-broad repair would break legitimate use (reader only)
    if yes("j_overbroad_breaks_legit"):
        d["S7 over-broad repair breaks covered legitimate use (JUDGEMENT)"] = \
            W["overbroad_repair"]["judged"]
    # 8. undisclosed siblings / alternate paths (v3): judged, else computed by `siblings`
    us = W.get("undisclosed_siblings")
    if us:
        if yes("j_undisclosed_siblings"):
            d["S8 undisclosed sibling sites or alternate path (JUDGEMENT)"] = us["judged"]
        elif (row["c_other_call_sites"] if "c_other_call_sites" in row.keys() else None) is not None:
            n = row["c_other_call_sites"] or 0
            if n >= 2:
                d["S8 %d other call sites of the guard/sink not touched by the fix" % n] = \
                    us["computed_other_call_sites_2plus"]
            elif n == 1:
                d["S8 1 other call site of the guard/sink not touched by the fix"] = \
                    us["computed_other_call_sites_1"]
    # LOW signals
    lo = W["low_signals"]
    if cs["c_single_sink"]:
        d["LOW single obvious sink fixed at one spot"] = lo["single_obvious_sink_one_spot"]
    if cs["c_one_site_guard"]:
        d["LOW one-site added-only guard"] = lo["one_site_added_only_guard"]
    if cs["c_compact_small_repo"]:
        d["LOW compact fix in a small repository"] = lo["compact_fix_small_repo"]
    size_kb = row["repo_size_kb"]
    if size_kb and size_kb > 1500000:
        d["build risk: repository over 1.5 GB"] = lo["repo_over_1_5_gb"]
    return float(sum(d.values())), d


def stage_classify(args, idx):
    counts = {"evaluated": 0, "candidate": 0, "still_pending": 0}
    # sibling map: (package, cwe) -> published dates of every non-withdrawn advisory
    sib = {}
    for r in idx.db.execute("SELECT entry_id, packages, cwe_ids, published, reject_reason "
                            "FROM entries"):
        if r["reject_reason"] == "withdrawn" or not r["packages"]:
            continue
        pkg = r["packages"].split(" | ")[0]
        for c in (r["cwe_ids"] or "").split():
            sib.setdefault((pkg, c), []).append((r["published"] or "", r["entry_id"]))

    def day(s):
        try:
            return calendar.timegm(time.strptime(s[:10], "%Y-%m-%d")) / 86400.0
        except Exception:
            return None

    ann = read_annotations(args.annotations)
    rows = idx.db.execute(
        "SELECT * FROM entries WHERE status IN ('pending', 'candidate', 'shortlisted') OR "
        "(status = 'rejected' AND reject_reason NOT IN (%s) AND reject_reason NOT LIKE 'manual:%%')"
        % ", ".join("'%s'" % r for r in PARSE_REJECTS)).fetchall()
    for row in rows:
        commits = idx.db.execute(
            "SELECT * FROM commits WHERE repo = ? AND entry_id = ? ORDER BY rowid",
            (row["repo"], row["entry_id"])).fetchall()
        fetched = [c for c in commits if c["fetch_status"]]
        if not commits:
            # every fix commit already belongs to an earlier entry (same fix, another advisory)
            owner = None
            for sha in (row["fix_commits"] or "").split():
                owner = idx.seen_commit(row["repo"], sha)
                if owner and owner != row["entry_id"]:
                    break
            orow = idx.db.execute("SELECT status, reject_reason FROM entries WHERE entry_id = ?",
                                  (owner,)).fetchone() if owner else None
            if orow and (orow["status"] == "deferred" or orow["reject_reason"] in PARSE_REJECTS):
                # the first owner will never be inspected: hand its commits to this entry
                for sha in (row["fix_commits"] or "").split():
                    idx.db.execute("UPDATE commits SET entry_id = ? WHERE repo = ? AND sha = ? "
                                   "AND entry_id = ?", (row["entry_id"], row["repo"], sha, owner))
                if row["status"] == "rejected":
                    idx.update_entry(row["entry_id"], status="pending", reject_reason=None)
                counts["commit_ownership_moved"] = counts.get("commit_ownership_moved", 0) + 1
                counts["still_pending"] += 1
                continue
            idx.update_entry(row["entry_id"], status="rejected",
                             reject_reason="duplicate_fix_commit_of_entry_%s" % owner)
            counts["reject_duplicate_fix_commit"] = counts.get("reject_duplicate_fix_commit", 0) + 1
            continue
        # a network error is not a verdict: such commits count as not fetched yet
        fetched = [c for c in fetched if not str(c["fetch_status"]).startswith("error")]
        if not fetched:
            if row["status"] != "pending":
                idx.update_entry(row["entry_id"], status="pending", reject_reason=None,
                                 score=None, score_detail=None)
            counts["still_pending"] += 1
            continue
        counts["evaluated"] += 1
        sig = json.loads(row["adv_signals"] or "{}")
        ok = [c for c in fetched if c["fetch_status"] == "ok"]
        reason = ""
        best = None
        stale_dropped = 0
        if not ok:
            kinds = sorted(set(c["fetch_status"] for c in fetched))
            if kinds == ["too_large"]:
                reason = "enormous_refactor(patch>3MB)"
            else:
                reason = "fix_commit_unavailable(%s)" % ",".join(kinds)
        else:
            usable = [c for c in ok if (c["src_files"] or 0) > 0 and
                      (c["src_added"] + c["src_removed"]) <= args.max_lines]
            if usable:
                # an advisory sometimes also links the commit that introduced the flaw, or an
                # old feature commit: ignore commits much older than the newest one referenced
                stamps = dict((c["sha"], commit_epoch(c["commit_date"])) for c in ok)
                known = [v for v in stamps.values() if v]
                if known:
                    newest = max(known)
                    recent = [c for c in usable
                              if not stamps[c["sha"]] or newest - stamps[c["sha"]] <= 120 * 86400]
                    if len(recent) < len(usable):
                        stale_dropped = len(usable) - len(recent)
                    usable = recent
                if usable:
                    best = max(usable, key=lambda c: c["src_added"] + c["src_removed"])
                    age = None
                    d_pub, t_fix = day(row["published"] or ""), commit_epoch(best["commit_date"])
                    if d_pub and t_fix:
                        age = d_pub - t_fix / 86400.0
                    if age is not None and age > args.max_fix_age_days:
                        reason = "stale_fix_commit(dated %s)" % time.strftime(
                            "%Y-%m-%d", time.gmtime(t_fix))
                else:
                    reason = "no_recent_source_commit(only stale or non-source commits referenced)"
            else:
                with_src = [c for c in ok if (c["src_files"] or 0) > 0]
                if with_src:
                    reason = "enormous_refactor(%d source lines)" % min(
                        c["src_added"] + c["src_removed"] for c in with_src)
                else:
                    bd = {}
                    for c in ok:
                        for k, v in json.loads(c["file_breakdown"] or "{}").items():
                            bd[k] = bd.get(k, 0) + v
                    kinds = set(k for k, v in bd.items() if v)
                    if not kinds:
                        reason = "no_source_change(empty_or_unparsed_patch)"
                    elif kinds <= {"manifest", "lockfile"}:
                        reason = "dependency_or_manifest_only"
                    elif kinds <= {"doc"}:
                        reason = "docs_only"
                    elif kinds <= {"test"}:
                        reason = "tests_only"
                    elif kinds <= {"manifest", "lockfile", "config", "ci", "doc"}:
                        reason = "manifest_config_docs_only"
                    else:
                        reason = "no_source_change(%s)" % "+".join(sorted(kinds))
        if not reason:
            env = env_reject(row, best["language"], sig)
            if env:
                reason = "not_plain_linux_docker:%s" % env
            elif RE_TOY.search(row["repo"] or ""):
                reason = "toy_or_demo_repo(name)"
            elif row["repo_stars"] is not None and row["repo_stars"] < args.min_stars:
                reason = "toy_or_low_adoption(stars=%d)" % row["repo_stars"]
        keep_status = row["status"]
        if reason:
            idx.update_entry(row["entry_id"], status="rejected", reject_reason=reason,
                             score=None, score_detail=None)
            key = "reject_" + re.sub(r"\(.*\)$", "", reason)
            counts[key] = counts.get(key, 0) + 1
            continue
        # siblings: other advisories, same first package, shared CWE, within 120 days
        pkg = (row["packages"] or "").split(" | ")[0]
        d0 = day(row["published"] or "")
        sibs = set()
        for c in (row["cwe_ids"] or "").split():
            for pub, eid in sib.get((pkg, c), []):
                d1 = day(pub)
                if eid != row["entry_id"] and d0 and d1 and abs(d0 - d1) <= 120:
                    sibs.add(eid)
        cs = compute_signals(row, best, sig, len(sibs))
        score, detail = score_entry(row, cs, sig)
        judged = ann.get((row["primary_id"] or "").upper())
        jcols = {"j_read": None, "j_multi_site": None, "j_sites_touched": None,
                 "j_sibling_sites": None, "j_cause_other_layer": None,
                 "j_defence_ineffective": None, "j_overbroad_breaks_legit": None,
                 "j_tempting_wrong_fix": None, "score_read": None}
        if judged and judged.get("j_multi_site", "").strip() != "":
            def flag(k):
                return 1 if judged.get(k, "").strip() in ("1", "yes", "y") else 0
            score_read, detail_read = score_entry(row, cs, sig, judged)
            jcols = {"j_read": 1, "j_multi_site": flag("j_multi_site"),
                     "j_sites_touched": judged.get("j_sites_touched", ""),
                     "j_sibling_sites": judged.get("j_sibling_sites", ""),
                     "j_cause_other_layer": flag("j_cause_other_layer"),
                     "j_defence_ineffective": flag("j_defence_ineffective"),
                     "j_overbroad_breaks_legit": flag("j_overbroad_breaks_legit"),
                     "j_tempting_wrong_fix": judged.get("tempting_wrong_fix", ""),
                     "score_read": score_read}
            detail = {"computed": detail, "read": detail_read}
        unfetched = len(commits) - len(fetched)
        notes = []
        if unfetched:
            notes.append("%d referenced fix commits not fetched (cap)" % unfetched)
        if best["is_merge"]:
            notes.append("fix commit is a merge commit (%d patches)" % (best["n_patches"] or 0))
        if stale_dropped:
            notes.append("%d referenced commit(s) over 120 days older than the newest were "
                         "ignored as not the fix" % stale_dropped)
        if len(ok) > 1:
            notes.append("metrics describe the largest of %d fetched fix commits" % len(ok))
        if row["repo_flags"]:
            notes.append("repository flags: %s" % row["repo_flags"])
        if sig.get("commits_in_other_repos"):
            notes.append("advisory also references commits in: %s" %
                         ", ".join(sig["commits_in_other_repos"]))
        fix_sha = best["full_sha"] or best["sha"]
        parent = best["parent_sha"]
        idx.update_entry(
            row["entry_id"],
            status="candidate" if keep_status in ("pending", "rejected") else keep_status,
            reject_reason=None, score=score, score_detail=json.dumps(detail, sort_keys=True),
            fix_commit=fix_sha, parent_commit=parent,
            fix_commit_date=(time.strftime("%Y-%m-%d", time.gmtime(commit_epoch(best["commit_date"])))
                             if commit_epoch(best["commit_date"]) else None),
            src_files=best["src_files"], src_added=best["src_added"],
            src_removed=best["src_removed"], src_hunks=best["src_hunks"],
            test_files=best["test_files"], tests_in_fix=1 if best["test_files"] else 0,
            other_files=best["other_files"],
            language=best["language"] or ECO_LANG.get((row["ecosystems"] or "").split(" ")[0], ""),
            file_breakdown=best["file_breakdown"], notes="; ".join(notes) or None,
            **dict([kv for kv in cs.items() if not kv[0].startswith("_")] + list(jcols.items())))
        counts["candidate"] += 1
    idx.commit()
    return counts


# --------------------------------------------------------------------------
# stage: parents  (commit web page -> full sha + first parent)
# --------------------------------------------------------------------------
def stage_parents(args, idx):
    counts = {"resolved": 0, "failed": 0, "requests": 0, "stopped_early": ""}
    rows = idx.db.execute(
        "SELECT * FROM entries WHERE status IN ('candidate', 'shortlisted') AND "
        "parent_commit IS NULL ORDER BY (status = 'shortlisted') DESC, score DESC, "
        "published DESC LIMIT ?", (args.limit,)).fetchall()
    if args.ids:
        rows = [idx.db.execute("SELECT * FROM entries WHERE entry_id = ?",
                               (idx.seen_id(i),)).fetchone() for i in args.ids]
        rows = [r for r in rows if r and not r["parent_commit"]]
    fetcher = Fetcher(args.delay)
    cache_dir = os.path.join(args.data, "commit-parents")
    os.makedirs(cache_dir, exist_ok=True)
    for row in rows:
        sha = row["fix_commit"]
        c = idx.db.execute("SELECT * FROM commits WHERE repo = ? AND (sha = ? OR full_sha = ?)",
                           (row["repo"], sha, sha)).fetchone()
        if not c:
            continue
        cache = os.path.join(cache_dir, row["repo"].replace("/", "__") + "__" + c["sha"] + ".json")
        info = None
        if os.path.exists(cache):
            with open(cache) as f:
                info = json.load(f)
        else:
            url = "https://github.com/%s/commit/%s" % (row["repo"], c["sha"])
            try:
                status, data, _h = fetcher.get(url, 6 * 1024 * 1024)
            except RateLimited:
                counts["stopped_early"] = "rate_limited"
                break
            counts["requests"] += 1
            if status == "ok":
                html = data.decode("utf-8", "replace")
                full = None
                for m in re.finditer(r'"oid":"([0-9a-f]{40})"', html):
                    if m.group(1).startswith(c["sha"][:7]):
                        full = m.group(1)
                        break
                m = re.search(r'"parents":\[((?:"[0-9a-f]{40}",?)*)\]', html)
                parents = re.findall(r"[0-9a-f]{40}", m.group(1)) if m else []
                info = {"full_sha": full, "parents": parents}
                with open(cache, "w") as f:
                    json.dump(info, f)
        if info and info.get("parents"):
            full = info.get("full_sha") or (c["sha"] if len(c["sha"]) == 40 else None)
            idx.update_commit(row["repo"], c["sha"], parent_sha=info["parents"][0],
                              full_sha=full or c["full_sha"],
                              is_merge=1 if len(info["parents"]) > 1 else (c["is_merge"] or 0))
            idx.update_entry(row["entry_id"], parent_commit=info["parents"][0],
                             fix_commit=full or row["fix_commit"])
            counts["resolved"] += 1
        else:
            counts["failed"] += 1
        idx.commit()
    return counts


# --------------------------------------------------------------------------
# stage: repo-meta  (unauthenticated api.github.com, hard-bounded, cached)
# --------------------------------------------------------------------------
def stage_repo_meta(args, idx):
    counts = {"looked_up": 0, "from_cache": 0, "failed": 0, "stopped_early": ""}
    rows = idx.db.execute(
        "SELECT repo, max(score) AS s FROM entries WHERE status IN ('candidate', 'shortlisted') "
        "AND repo_stars IS NULL GROUP BY repo ORDER BY (max(status) = 'shortlisted') DESC, s DESC, "
        "max(published) DESC").fetchall()
    cache_dir = os.path.join(args.data, "repo-meta")
    os.makedirs(cache_dir, exist_ok=True)
    fetcher = Fetcher(max(args.delay, 1.0))
    budget = min(args.limit, 55)        # unauthenticated limit is 60 requests/hour; stay under it
    if os.environ.get("GITHUB_TOKEN"):  # diversity_population copy: authenticated limit is 5,000/hour
        budget = args.limit
    for row in rows:
        repo = row["repo"]
        cache = os.path.join(cache_dir, repo.replace("/", "__") + ".json")
        info = None
        if os.path.exists(cache):
            with open(cache) as f:
                info = json.load(f)
            counts["from_cache"] += 1
        else:
            if counts["looked_up"] + counts["failed"] >= budget:
                counts["stopped_early"] = "budget"
                break
            try:
                status, data, hdrs = fetcher.get("https://api.github.com/repos/" + repo,
                                                 2 * 1024 * 1024,
                                                 accept="application/vnd.github+json")
            except RateLimited:
                counts["stopped_early"] = "rate_limited"
                break
            if status != "ok":
                counts["failed"] += 1
                counts.setdefault("failed_statuses", {})
                counts["failed_statuses"][status] = counts["failed_statuses"].get(status, 0) + 1
                if status == "http_403":       # primary rate limit reached: stop, do not retry
                    counts["stopped_early"] = "api_rate_limit(403)"
                    break
                if status == "http_404":
                    info = {"stars": -1, "size_kb": 0, "flags": "repo_not_found"}
                    with open(cache, "w") as f:
                        json.dump(info, f)
                else:
                    continue
            else:
                try:
                    j = json.loads(data.decode("utf-8", "replace"))
                except ValueError:
                    counts["failed"] += 1
                    continue
                flags = []
                if j.get("archived"):
                    flags.append("archived")
                if j.get("fork"):
                    flags.append("fork")
                info = {"stars": j.get("stargazers_count"), "size_kb": j.get("size"),
                        "flags": ",".join(flags), "language": j.get("language"),
                        "default_branch": j.get("default_branch"),
                        "description": (j.get("description") or "")[:200]}
                with open(cache, "w") as f:
                    json.dump(info, f)
                counts["looked_up"] += 1
                remaining = hdrs.get("X-RateLimit-Remaining") or hdrs.get("x-ratelimit-remaining")
                if remaining is not None and int(remaining) <= 2:
                    counts["stopped_early"] = "api_rate_limit_nearly_used"
        if info:
            idx.db.execute("UPDATE entries SET repo_stars = ?, repo_size_kb = ?, repo_flags = ?, "
                           "updated_at = ? WHERE repo = ?",
                           (info.get("stars"), info.get("size_kb"), info.get("flags") or "",
                            index_db.now(), repo))
            idx.commit()
        if counts["stopped_early"]:
            break
    return counts


# --------------------------------------------------------------------------
# shortlist: propose / show / finalise
# --------------------------------------------------------------------------
ANNOT_COLS = ["primary_id", "verdict", "role", "j_multi_site", "j_sites_touched",
              "j_sibling_sites", "j_cause_other_layer", "j_defence_ineffective",
              "j_overbroad_breaks_legit", "entry_point", "services", "flaw",
              "tempting_wrong_fix", "why_hard", "note"]
LANG_BUCKET = {"Python": "Python", "JavaScript": "JS/TS", "TypeScript": "JS/TS", "Go": "Go",
               "Java": "Java", "Kotlin": "Java", "Scala": "Java", "Groovy": "Java",
               "Ruby": "Ruby", "PHP": "PHP", "Rust": "Rust", "C": "C/C++", "C++": "C/C++"}
STRONG_LANGS = ("Python", "JS/TS")      # the languages the target models handle best


def read_annotations(path):
    out = {}
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as f:
        header = None
        for line in f:
            line = line.rstrip("\n")
            if not line.strip() or line.startswith("#"):
                continue
            cells = line.split("\t")
            if header is None:
                header = cells
                continue
            row = dict(zip(header, cells + [""] * (len(header) - len(cells))))
            out[row["primary_id"].strip().upper()] = row
    return out


def parse_quota(text):
    q = {}
    for part in text.split(","):
        k, v = part.split("=")
        q[k.strip()] = int(v)
    return q


def effective_score(r):
    return r["score_read"] if r["score_read"] is not None else (r["score"] or 0)


def strong_signal_count(r):
    """How many of signals 1-5 the computed columns show (used to gate Python and JS/TS)."""
    return sum(1 for k in ("c_multi_site", "c_cause_layer_hint", "c_defence_present",
                           "c_bypass_incomplete", "c_favoured_class") if r[k])


def stage_propose(args, idx):
    """Proposal only: 16 by the difficulty rules + 4 controls the rules predict are easy."""
    ann = read_annotations(args.annotations)
    lang_quota = parse_quota(args.lang_quota)
    rows = idx.db.execute(
        "SELECT * FROM entries WHERE status IN ('candidate', 'shortlisted')").fetchall()
    rows.sort(key=lambda r: (-effective_score(r), -(r["tests_in_fix"] or 0), r["published"] or ""))
    main, controls, used_repo, used_cwe, used_lang = [], [], set(), {}, {}

    def verdict(r):
        a = ann.get((r["primary_id"] or "").upper())
        return ((a["verdict"].strip().lower(), (a.get("role") or "main").strip().lower())
                if a else ("", ""))

    def take(r, bucket):
        bucket.append(r)
        used_repo.add(r["repo"])
        if bucket is main:
            cwe = primary_cwe(r["cwe_ids"])
            lang = LANG_BUCKET.get(r["language"] or "", "Other")
            used_cwe[cwe] = used_cwe.get(cwe, 0) + 1
            used_lang[lang] = used_lang.get(lang, 0) + 1

    for r in rows:                                    # reviewer's keeps come first
        v, role = verdict(r)
        if v == "keep" and r["repo"] not in used_repo:
            take(r, controls if role == "control" else main)
    for r in rows:                                    # fill the 16 by score
        if len(main) >= args.n_main:
            break
        if verdict(r)[0] or r["repo"] in used_repo or effective_score(r) < args.min_score:
            continue
        lang = LANG_BUCKET.get(r["language"] or "", "Other")
        if used_lang.get(lang, 0) >= lang_quota.get(lang, 0):
            continue
        if used_cwe.get(primary_cwe(r["cwe_ids"]), 0) >= args.max_per_cwe:
            continue
        if lang in STRONG_LANGS and strong_signal_count(r) < 3:
            continue
        take(r, main)
    easy = [r for r in rows if LANG_BUCKET.get(r["language"] or "") in STRONG_LANGS
            and r["c_single_compact_hunk"] and (r["c_single_sink"] or r["c_one_site_guard"])
            and not r["c_multi_site"] and not r["c_bypass_incomplete"]
            and not r["c_favoured_class"] and not r["c_defence_present"]]
    easy.sort(key=lambda r: (effective_score(r), -(r["tests_in_fix"] or 0)))
    for r in easy:                                    # fill the 4 controls, easiest first
        if len(controls) >= args.n_controls:
            break
        if verdict(r)[0] or r["repo"] in used_repo:
            continue
        take(r, controls)
    out = args.out or os.path.join(HERE, "review", "proposed.tsv")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    cols = ["role", "primary_id", "reviewed", "score", "score_read", "language", "cwe", "class",
            "sites", "same_check", "S1", "S2h", "S3", "S4", "compact", "sink", "src_files",
            "lines", "tests", "published", "repo", "stars", "summary"]
    with open(out, "w", encoding="utf-8") as f:
        f.write("\t".join(cols) + "\n")
        for role, bucket in (("main", main), ("control", controls)):
            for r in bucket:
                f.write("\t".join(str(x) for x in [
                    role, r["primary_id"], verdict(r)[0], r["score"],
                    "" if r["score_read"] is None else r["score_read"], r["language"],
                    "CWE-%d" % primary_cwe(r["cwe_ids"]), r["c_class"], r["c_fix_sites"],
                    r["c_same_check_sites"], r["c_multi_site"], r["c_cause_layer_hint"],
                    r["c_defence_present"], r["c_bypass_incomplete"], r["c_single_compact_hunk"],
                    r["c_single_sink"], r["src_files"],
                    (r["src_added"] or 0) + (r["src_removed"] or 0), r["tests_in_fix"],
                    r["published"], r["repo"], "" if r["repo_stars"] is None else r["repo_stars"],
                    (r["summary"] or "").replace("\t", " ")[:90]]) + "\n")
    for line in open(out, encoding="utf-8"):
        sys.stdout.write(line)
    return {"main": len(main), "controls": len(controls), "by_language": used_lang,
            "by_cwe": dict(("CWE-%d" % k, v) for k, v in used_cwe.items())}


def find_advisory(data, primary_id, ecosystems):
    for eco in ecosystems:
        path = os.path.join(data, "dumps", eco + ".zip")
        if not os.path.exists(path):
            continue
        with zipfile.ZipFile(path) as z:
            try:
                return json.loads(z.read(primary_id + ".json").decode("utf-8", "replace"))
            except KeyError:
                continue
    return None


def stage_show(args, idx):
    for any_id in args.ids:
        eid = idx.seen_id(any_id)
        if not eid:
            print("not in index: %s" % any_id)
            continue
        r = idx.db.execute("SELECT * FROM entries WHERE entry_id = ?", (eid,)).fetchone()
        print("=" * 100)
        for k in ("primary_id", "ids", "packages", "repo", "cwe_ids", "published", "severity",
                  "status", "reject_reason", "score", "score_detail", "fix_commits", "fix_commit",
                  "parent_commit", "language", "src_files", "src_added", "src_removed",
                  "src_hunks", "test_files", "file_breakdown", "repo_stars", "repo_size_kb",
                  "notes", "adv_signals"):
            print("%-14s %s" % (k, r[k]))
        adv = find_advisory(args.data, r["primary_id"], (r["ecosystems"] or "").split() or ECOSYSTEMS)
        if adv:
            print("-" * 100)
            print("SUMMARY: " + (adv.get("summary") or ""))
            print((adv.get("details") or "")[:args.details_chars])
            print("REFERENCES:")
            for ref in adv.get("references") or []:
                print("  %s %s" % (ref.get("type"), ref.get("url")))
        if args.no_diff:
            continue
        for c in idx.db.execute("SELECT * FROM commits WHERE repo = ? AND entry_id = ? "
                                "AND fetch_status = 'ok'", (r["repo"], eid)):
            if args.primary_only and (c["full_sha"] or c["sha"]) != r["fix_commit"] \
                    and c["sha"] != r["fix_commit"]:
                continue
            print("-" * 100)
            print("COMMIT %s  %s  src %s files +%s -%s  tests %s" % (
                c["sha"], c["subject"], c["src_files"], c["src_added"], c["src_removed"],
                c["test_files"]))
            text = load_patch(args.data, r["repo"], c["sha"]) or ""
            shown = 0
            emit = False
            per_file = 0
            for line in text.split("\n"):
                m = re.match(r"^diff --git a/(.+?) b/(.+)$", line)
                if m:
                    cat, _lang = patchmetrics.classify_path(m.group(2))
                    emit = cat == "source" or (args.with_tests and cat == "test")
                    per_file = 0
                    print("### %s [%s]" % (m.group(2), cat))
                    continue
                if line.startswith("From ") and re.match(r"^From [0-9a-f]{40} ", line):
                    emit = False
                    continue
                if emit and shown < args.diff_lines and per_file < args.file_lines:
                    if line.startswith(("+", "-", "@@")):
                        print(line[:args.width])
                        shown += 1
                        per_file += 1
            if shown >= args.diff_lines:
                print("... (diff truncated at %d changed lines)" % args.diff_lines)
    return {}


SHORTLIST_COLS = [
    "n", "role", "advisory_id", "cve", "repo_url", "language", "lang_tier", "cwe_id", "cwe_name",
    "all_cwe_ids", "weakness_class", "fix_commit_url", "vulnerable_parent_commit", "published",
    "fix_commit_date", "severity", "src_files_changed", "src_lines_added", "src_lines_removed",
    "src_hunks", "tests_in_fix", "n_fix_commits_referenced", "repo_stars", "score_computed",
    "score_read",
    # computed from the diff and the advisory text
    "c_fix_sites", "c_same_check_sites", "c_same_check_name", "c_multi_site",
    "c_cause_layer_hint", "c_defence_present", "c_bypass_incomplete", "c_sibling_advisories",
    "c_favoured_class", "c_single_compact_hunk", "c_far_apart", "c_restructured",
    "c_single_sink", "c_one_site_guard",
    # the reader's judgement after reading advisory + diff
    "S1_multi_site_JUDGEMENT", "sites_touched_JUDGEMENT", "sibling_sites_exist_JUDGEMENT",
    "S2_cause_other_layer_JUDGEMENT", "S3_defence_ineffective_JUDGEMENT",
    "S7_overbroad_breaks_legit_JUDGEMENT", "entry_point_GUESS", "services_GUESS",
    "flaw_one_line", "tempting_wrong_fix_JUDGEMENT", "why_hard_or_why_control_JUDGEMENT",
    "caveats",
]


def stage_finalise(args, idx):
    ann = read_annotations(args.annotations)
    keeps = [a for a in ann.values() if a["verdict"].strip().lower() == "keep"]
    drops = [a for a in ann.values() if a["verdict"].strip().lower() == "drop"]
    counts = {"keep": len(keeps), "drop": len(drops), "written": 0}
    for a in drops:          # recorded in the index so no later run proposes them again
        eid = idx.seen_id(a["primary_id"])
        if eid:
            idx.update_entry(eid, status="rejected", shortlist_role=None,
                             reject_reason="manual:" + (a.get("note") or "dropped on reading")[:200])
    idx.db.execute("UPDATE entries SET status = 'candidate', shortlist_role = NULL "
                   "WHERE status = 'shortlisted'")
    picked = {"main": [], "control": []}
    for a in keeps:
        eid = idx.seen_id(a["primary_id"])
        if not eid:
            log("annotation for unknown id %s ignored" % a["primary_id"])
            continue
        r = idx.db.execute("SELECT * FROM entries WHERE entry_id = ?", (eid,)).fetchone()
        if r["status"] != "candidate":
            log("%s is %s (%s) in the index; not shortlisted" %
                (a["primary_id"], r["status"], r["reject_reason"]))
            continue
        role = "control" if (a.get("role") or "").strip().lower() == "control" else "main"
        picked[role].append((r, a))
    picked["main"].sort(key=lambda ra: (-effective_score(ra[0]), ra[0]["primary_id"]))
    picked["control"].sort(key=lambda ra: (effective_score(ra[0]), ra[0]["primary_id"]))
    rows = [("main", r, a) for r, a in picked["main"][:args.n_main]] + \
           [("control", r, a) for r, a in picked["control"][:args.n_controls]]
    out_rows = []
    for n, (role, r, a) in enumerate(rows, 1):
        idx.update_entry(r["entry_id"], status="shortlisted", reject_reason=None,
                         shortlist_role=role)
        cwe = primary_cwe(r["cwe_ids"])
        caveats = []
        if not r["parent_commit"]:
            caveats.append("parent commit not resolved")
        if r["notes"]:
            caveats.append(r["notes"])
        if a.get("note"):
            caveats.append(a["note"])

        def yn(v):
            return "" if v is None else ("yes" if v else "no")
        out_rows.append([
            n, role, r["primary_id"], r["cve"] or "", "https://github.com/" + r["repo"],
            r["language"], r["lang_tier"], "CWE-%d" % cwe,
            CWE_NAMES.get(cwe, "(name not in local table)"), r["cwe_ids"], r["c_class"],
            "https://github.com/%s/commit/%s" % (r["repo"], r["fix_commit"]),
            r["parent_commit"] or "UNRESOLVED", r["published"], r["fix_commit_date"] or "",
            r["severity"], r["src_files"], r["src_added"], r["src_removed"], r["src_hunks"],
            "yes" if r["tests_in_fix"] else "no", r["n_fix_commits"],
            "" if r["repo_stars"] is None else r["repo_stars"], r["score"],
            "" if r["score_read"] is None else r["score_read"],
            r["c_fix_sites"], r["c_same_check_sites"], r["c_same_check_name"] or "",
            r["c_multi_site"], r["c_cause_layer_hint"], r["c_defence_present"],
            r["c_bypass_incomplete"], r["c_sibling_advisories"], r["c_favoured_class"],
            r["c_single_compact_hunk"], r["c_far_apart"], r["c_restructured"],
            r["c_single_sink"], r["c_one_site_guard"],
            yn(r["j_multi_site"]), r["j_sites_touched"] or "", r["j_sibling_sites"] or "",
            yn(r["j_cause_other_layer"]), yn(r["j_defence_ineffective"]),
            yn(r["j_overbroad_breaks_legit"]), a.get("entry_point", ""), a.get("services", ""),
            a.get("flaw", ""), a.get("tempting_wrong_fix", ""), a.get("why_hard", ""),
            "; ".join(caveats)])
    idx.commit()
    total = args.n_main + args.n_controls
    tsv = os.path.join(HERE, "shortlist-%d.tsv" % total)
    with open(tsv, "w", encoding="utf-8") as f:
        f.write("\t".join(SHORTLIST_COLS) + "\n")
        for row in out_rows:
            f.write("\t".join(str(x).replace("\t", " ").replace("\n", " ") for x in row) + "\n")
    md = os.path.join(HERE, "shortlist-%d.md" % total)
    n_main = sum(1 for row in out_rows if row[1] == "main")
    n_ctl = len(out_rows) - n_main
    with open(md, "w", encoding="utf-8") as f:
        f.write("# Sourcer 1 (OSV) shortlist: %d candidates + %d controls\n\n" % (n_main, n_ctl))
        f.write("Generated %s by `osv_sourcer.py finalise` from the index and "
                "`review/annotations.tsv`.\n\n" % index_db.now())
        f.write("- Nothing here has been built, run or exploited.\n"
                "- **main** rows were chosen by the difficulty rules. **control** rows are ones "
                "the rules predict are too easy (single sink or one-site guard, compact, "
                "Python or JS/TS); they are there to test the rules, not as tasks we expect to "
                "survive.\n"
                "- Columns named `c_*` are computed from the fix diff and the advisory text. "
                "Columns marked JUDGEMENT are one reader's verdict after reading the advisory "
                "and the diff. Columns marked GUESS (entry point, services) are a reading of "
                "the advisory, not a test result.\n"
                "- Line counts are non-blank added/removed lines in non-test source files of "
                "the one fix commit linked.\n\n")
        f.write("| # | Role | Advisory / CVE | Repo | Lang | CWE (class) | Published | Files, +/-, "
                "hunks | Tests | S1 multi-site | S2 other layer | S3 defence failed | Score "
                "(computed / read) |\n")
        f.write("|---|---|---|---|---|---|---|---|---|---|---|---|---|\n")
        for row in out_rows:
            d = dict(zip(SHORTLIST_COLS, row))
            f.write("| %s | %s | %s %s | [%s](%s) | %s | %s %s (%s) | %s | %s, +%s/-%s, %s | %s | "
                    "%s | %s | %s | %s / %s |\n" % (
                        d["n"], d["role"], d["advisory_id"], d["cve"],
                        d["repo_url"].replace("https://github.com/", ""), d["repo_url"],
                        d["language"], d["cwe_id"], md_cell(d["cwe_name"]), d["weakness_class"],
                        d["published"], d["src_files_changed"], d["src_lines_added"],
                        d["src_lines_removed"], d["src_hunks"], d["tests_in_fix"],
                        d["S1_multi_site_JUDGEMENT"], d["S2_cause_other_layer_JUDGEMENT"],
                        d["S3_defence_ineffective_JUDGEMENT"], d["score_computed"],
                        d["score_read"]))
        f.write("\nS1, S2, S3 in the table are JUDGEMENT.\n\n## Per candidate\n")
        for row in out_rows:
            d = dict(zip(SHORTLIST_COLS, row))
            f.write("\n### %s. %s%s (%s)\n\n" % (
                d["n"], "CONTROL: " if d["role"] == "control" else "", d["advisory_id"],
                d["cve"] or "no CVE"))
            f.write("- Role: **%s**\n" % d["role"])
            f.write("- Repo: %s (%s, tier %s; stars: %s)\n" % (
                d["repo_url"], d["language"], d["lang_tier"],
                d["repo_stars"] if d["repo_stars"] != "" else "not looked up"))
            f.write("- CWE: %s %s (all listed: %s); class: %s\n" % (
                d["cwe_id"], d["cwe_name"], d["all_cwe_ids"], d["weakness_class"]))
            f.write("- Fix commit: %s (dated %s)\n" % (d["fix_commit_url"], d["fix_commit_date"]))
            f.write("- Vulnerable (parent) commit: `%s`\n" % d["vulnerable_parent_commit"])
            f.write("- Published: %s; severity: %s; fix commits referenced by the advisory: %s\n" %
                    (d["published"], d["severity"], d["n_fix_commits_referenced"]))
            f.write("- Fix size: %s source files, +%s/-%s lines, %s hunks; tests in fix: %s\n" % (
                d["src_files_changed"], d["src_lines_added"], d["src_lines_removed"],
                d["src_hunks"], d["tests_in_fix"]))
            f.write("- Computed signals: fix sites %s; same new check at %s sites%s; multi-site %s; "
                    "cause-layer wording %s; defence-failed %s; bypass/incomplete %s; sibling "
                    "advisories %s; favoured class %s; single compact hunk %s; far apart %s; "
                    "restructured %s; single sink %s; one-site guard %s\n" % (
                        d["c_fix_sites"], d["c_same_check_sites"],
                        (" (`%s`)" % d["c_same_check_name"]) if d["c_same_check_name"] else "",
                        d["c_multi_site"], d["c_cause_layer_hint"], d["c_defence_present"],
                        d["c_bypass_incomplete"], d["c_sibling_advisories"],
                        d["c_favoured_class"], d["c_single_compact_hunk"], d["c_far_apart"],
                        d["c_restructured"], d["c_single_sink"], d["c_one_site_guard"]))
            f.write("- JUDGEMENT: S1 multi-site %s (sites touched: %s; sibling sites exist: %s); "
                    "S2 cause in another layer %s; S3 existing defence ineffective %s; "
                    "S7 over-broad repair breaks legitimate use %s\n" % (
                        d["S1_multi_site_JUDGEMENT"], d["sites_touched_JUDGEMENT"],
                        d["sibling_sites_exist_JUDGEMENT"], d["S2_cause_other_layer_JUDGEMENT"],
                        d["S3_defence_ineffective_JUDGEMENT"],
                        d["S7_overbroad_breaks_legit_JUDGEMENT"]))
            f.write("- Score: computed %s, with reading %s\n" % (d["score_computed"], d["score_read"]))
            f.write("- Entry point (GUESS): %s\n" % d["entry_point_GUESS"])
            f.write("- Services probably needed (GUESS): %s\n" % d["services_GUESS"])
            f.write("- Flaw: %s\n" % d["flaw_one_line"])
            f.write("- Tempting wrong fix (JUDGEMENT): %s\n" % d["tempting_wrong_fix_JUDGEMENT"])
            f.write("- %s (JUDGEMENT): %s\n" % (
                "Why predicted easy" if d["role"] == "control" else "Why hard",
                d["why_hard_or_why_control_JUDGEMENT"]))
            if d["caveats"]:
                f.write("- Caveats: %s\n" % d["caveats"])
    counts["written"] = len(out_rows)
    counts["main"] = n_main
    counts["controls"] = n_ctl
    counts["files"] = [tsv, md]
    return counts


def md_cell(s):
    return str(s).replace("|", "/")


# --------------------------------------------------------------------------
# stats / export
# --------------------------------------------------------------------------
def stage_stats(args, idx):
    db = idx.db
    out = {}
    out["entries_total"] = db.execute("SELECT count(*) FROM entries").fetchone()[0]
    out["by_status"] = dict(db.execute("SELECT status, count(*) FROM entries GROUP BY status").fetchall())
    out["with_cwe_repo_commit"] = db.execute(
        "SELECT count(*) FROM entries WHERE reject_reason IS NULL OR reject_reason NOT IN (%s)"
        % ", ".join("'%s'" % r for r in PARSE_REJECTS)).fetchone()[0]
    out["with_cwe_repo_commit_in_window"] = db.execute(
        "SELECT count(*) FROM entries WHERE status != 'deferred' AND (reject_reason IS NULL OR "
        "reject_reason NOT IN (%s))" % ", ".join("'%s'" % r for r in PARSE_REJECTS)).fetchone()[0]
    out["entries_with_diff_fetched"] = db.execute(
        "SELECT count(DISTINCT entry_id) FROM commits WHERE fetch_status IS NOT NULL").fetchone()[0]
    out["commits_by_fetch_status"] = dict(db.execute(
        "SELECT coalesce(fetch_status, 'not_fetched'), count(*) FROM commits GROUP BY 1").fetchall())
    reasons = {}
    for reason, n in db.execute("SELECT reject_reason, count(*) FROM entries "
                                "WHERE status = 'rejected' GROUP BY 1"):
        key = re.sub(r"\(.*\)$", "", reason or "")
        key = re.sub(r"^duplicate_fix_commit_of_entry_.*", "duplicate_fix_commit", key)
        key = re.sub(r"^manual:.*", "manual_review_drop", key)
        reasons[key] = reasons.get(key, 0) + n
    out["rejected_by_reason"] = dict(sorted(reasons.items(), key=lambda kv: -kv[1]))
    out["window"] = dict(zip(("min_published_inspected", "max_published_inspected"), db.execute(
        "SELECT min(published), max(published) FROM entries WHERE status IN "
        "('pending', 'candidate', 'shortlisted') OR (status = 'rejected' AND reject_reason NOT IN (%s))"
        % ", ".join("'%s'" % r for r in PARSE_REJECTS)).fetchone()))
    out["candidates_by_language"] = dict(db.execute(
        "SELECT language, count(*) FROM entries WHERE status IN ('candidate', 'shortlisted') "
        "GROUP BY 1 ORDER BY 2 DESC").fetchall())
    sigcols = ["c_multi_site", "c_cause_layer_hint", "c_defence_present", "c_bypass_incomplete",
               "c_favoured_class", "c_far_apart", "c_restructured", "c_single_compact_hunk",
               "c_single_sink", "c_one_site_guard", "c_compact_small_repo", "j_read",
               "j_multi_site", "j_cause_other_layer", "j_defence_ineffective",
               "j_overbroad_breaks_legit"]
    row = db.execute("SELECT count(*), %s, sum(c_same_check_sites >= 3), "
                     "sum(c_sibling_advisories >= 1) FROM entries WHERE status IN "
                     "('candidate', 'shortlisted')" % ", ".join("sum(%s)" % c for c in sigcols)
                     ).fetchone()
    out["pool_signal_counts"] = dict(zip(
        ["pool_size"] + sigcols + ["c_same_check_sites>=3", "c_sibling_advisories>=1"], row))
    s2 = {"S2a disparity": 0, "S2a partial": 0, "S2a on_named": 0, "S2a unknown": 0,
          "S2b fires": 0, "S2b strict": 0}
    for (det,) in db.execute("SELECT score_detail FROM entries WHERE status IN "
                             "('candidate', 'shortlisted')"):
        d = json.loads(det or "{}")
        d = d.get("computed", d)
        for k in d:
            if k.startswith("S2a "):
                s2["S2a " + ("disparity" if "touches none" in k else "on_named" if "lands only"
                             in k else "partial" if "code elsewhere" in k else "unknown")] += 1
            elif k.startswith("S2b "):
                s2["S2b fires"] += 1
                s2["S2b strict"] += 1 if "strict (both by name)" in k else 0
    out["pool_s2_computed"] = s2
    out["pool_by_class"] = dict(db.execute(
        "SELECT c_class, count(*) FROM entries WHERE status IN ('candidate', 'shortlisted') "
        "GROUP BY 1").fetchall())
    out["pool_by_lang_tier"] = dict(db.execute(
        "SELECT lang_tier, count(*) FROM entries WHERE status IN ('candidate', 'shortlisted') "
        "GROUP BY 1").fetchall())
    out["last_runs"] = [dict(r) for r in db.execute(
        "SELECT run_id, stage, started_at, finished_at, counts FROM runs ORDER BY run_id DESC LIMIT ?",
        (args.runs,))]
    print(json.dumps(out, indent=1))
    return {}


def stage_export(args, idx):
    path = os.path.join(os.path.dirname(args.index), "candidates.tsv")
    idx.export_tsv(path)
    return {"tsv": path}


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--data", default=DEFAULT_DATA, help="untrusted download directory")
    ap.add_argument("--index", default=DEFAULT_INDEX, help="SQLite candidate index")
    sub = ap.add_subparsers(dest="stage")

    p = sub.add_parser("fetch-dumps")
    p.add_argument("--ecosystems", nargs="+", default=ECOSYSTEMS)
    p.add_argument("--force", action="store_true")

    p = sub.add_parser("parse")
    p.add_argument("--ecosystems", nargs="+", default=ECOSYSTEMS)
    p.add_argument("--since", default="2026-06-01", help="recency window start (published date)")

    p = sub.add_parser("diffs")
    p.add_argument("--delay", type=float, default=1.2, help="seconds between requests")
    p.add_argument("--max-commits", type=int, default=3, help="fix commits fetched per entry")
    p.add_argument("--max-requests", type=int, default=0)
    p.add_argument("--max-minutes", type=float, default=0)
    p.add_argument("--retry-errors", action="store_true",
                   help="fetch again commits whose last attempt ended in a network error")
    p.add_argument("--first", nargs="*", default=[],
                   help="advisory ids (any alias) to fetch before the rest of the queue")
    p.add_argument("--only-errors", action="store_true",
                   help="with --retry-errors: do nothing else")

    sub.add_parser("remetrics")
    sub.add_parser("resignal")

    p = sub.add_parser("classify")
    p.add_argument("--max-lines", type=int, default=1500)
    p.add_argument("--min-stars", type=int, default=25)
    p.add_argument("--annotations", default=os.path.join(HERE, "review", "annotations.tsv"))
    p.add_argument("--max-fix-age-days", type=int, default=365,
                   help="reject when the fix commit is this much older than the advisory")

    p = sub.add_parser("parents")
    p.add_argument("--limit", type=int, default=60)
    p.add_argument("--delay", type=float, default=1.5)
    p.add_argument("--ids", nargs="*", default=[])

    p = sub.add_parser("repo-meta")
    p.add_argument("--limit", type=int, default=55)
    p.add_argument("--delay", type=float, default=1.0)

    p = sub.add_parser("propose")
    p.add_argument("--n-main", type=int, default=16)
    p.add_argument("--n-controls", type=int, default=4)
    p.add_argument("--annotations", default=os.path.join(HERE, "review", "annotations.tsv"))
    p.add_argument("--lang-quota",
                   default="Java=3,Rust=2,Go=4,PHP=2,Ruby=1,C/C++=1,Python=3,JS/TS=3")
    p.add_argument("--max-per-cwe", type=int, default=4)
    p.add_argument("--min-score", type=float, default=0)
    p.add_argument("--out", default="")

    p = sub.add_parser("show")
    p.add_argument("ids", nargs="+")
    p.add_argument("--details-chars", type=int, default=3500)
    p.add_argument("--diff-lines", type=int, default=260)
    p.add_argument("--file-lines", type=int, default=90)
    p.add_argument("--width", type=int, default=170)
    p.add_argument("--no-diff", action="store_true")
    p.add_argument("--with-tests", action="store_true")
    p.add_argument("--primary-only", action="store_true")

    p = sub.add_parser("finalise")
    p.add_argument("--n-main", type=int, default=16)
    p.add_argument("--n-controls", type=int, default=4)
    p.add_argument("--annotations", default=os.path.join(HERE, "review", "annotations.tsv"))

    p = sub.add_parser("stats")
    p.add_argument("--runs", type=int, default=8)

    sub.add_parser("export")

    args = ap.parse_args()
    if not args.stage:
        ap.print_help()
        return 2
    args.data = os.path.abspath(os.path.expanduser(args.data))
    if os.path.commonpath([args.data, HERE]) == HERE:
        sys.exit("refusing to keep untrusted downloads inside the code directory")
    idx = index_db.Index(args.index)
    stages = {
        "fetch-dumps": stage_fetch_dumps, "parse": stage_parse, "diffs": stage_diffs,
        "remetrics": stage_remetrics, "resignal": stage_resignal,
        "classify": stage_classify, "parents": stage_parents, "repo-meta": stage_repo_meta,
        "propose": stage_propose, "show": stage_show, "finalise": stage_finalise,
        "stats": stage_stats, "export": stage_export,
    }
    quiet = args.stage in ("show", "stats")
    run_id = None
    if not quiet:
        run_id = idx.start_run(SOURCER, args.stage, dict(
            (k, v) for k, v in vars(args).items() if k not in ("data", "index")))
    counts = {}
    try:
        counts = stages[args.stage](args, idx) or {}
    except KeyboardInterrupt:
        counts = {"interrupted": True}
    finally:
        idx.commit()
        if run_id is not None:
            idx.finish_run(run_id, counts)
            if args.stage not in ("export", "propose"):
                idx.export_tsv(os.path.join(os.path.dirname(args.index), "candidates.tsv"))
    if not quiet:
        sys.stderr.write(json.dumps({args.stage: counts}, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
