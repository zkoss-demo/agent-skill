# Requirements: serve static files from the webapp docroot

**Target component:** `zk-preview-launcher` (the ZK preview render helper).
**Status:** implemented in launcher 1.0.3 and verified locally on 2026-09-01. §11 records what was
measured. §7 carries one deliberate non-goal (symbolic links) that started life as a requirement.
**Written:** 2026-08-31. The §3 "current behaviour" measurements were taken on that date against the
published launcher **1.0.2**, and are what this document was written to change; the §11 measurements
were taken against the **1.0.3** build. Both are reproducible with the commands given inline.

This document is self-contained. Everything needed to reproduce the defect, judge the design and
verify the fix is written out here; nothing is deferred to another document.

---

## 1. Summary

Up to and including launcher **1.0.2**, the preview launcher was handed a webapp docroot and served
`.zul` pages out of it but **no other file from that directory** — not images, not stylesheets, not
scripts. A page containing `<image src="/img/logo.png"/>` rendered with an empty box even when
`img/logo.png` existed at exactly that path inside the docroot the launcher was given.

The request was to add a static file handler for the docroot, confined to it, with the security
properties spelled out in §6. **Launcher 1.0.3 implements it**; §11 records the verification, and
§7 records the one requirement that was consciously dropped along the way.

## 2. What the launcher is, and how it is invoked

The launcher is a self-contained jar that boots an embedded HTTP server, mounts a ZK runtime built
from a caller-supplied classpath, and renders `.zul` pages so a headless browser can screenshot
them. It is consumed by a command-line tool that spawns it as a child process, drives a browser at
the port it reports, and shuts it down.

Invocation, verbatim, as the consuming tool produces it:

```
<java17+> -jar zk-preview-launcher.jar \
  --classpath <one os-pathsep-joined list of jars, output roots and resource roots> \
  --webapp    <absolute path to the docroot> \
  --port      0 \
  [--isolation off --controller-timeout <seconds>]
```

* `--port 0` asks for an ephemeral port. The launcher prints `PREVIEW_PORT=<n>` on stdout, and the
  caller parses that line to learn where to connect.
* `--isolation off` is appended only when the caller wants Composers and ViewModels to execute;
  it is absent by default.
* The jar's main class is `org.zkoss.zkpreview.Main`. Its HTTP server is
  `org.zkoss.zkpreview.PreviewHttpServer` — a hand-written server, not Jetty or Tomcat, which is
  why there is no `DefaultServlet` to inherit static file behaviour from.

Reference build used for every measurement below:

| Item | Value |
|---|---|
| Launcher | `zk-preview-launcher-1.0.2.jar` |
| SHA-256 | `d451589f8d0e447599a96240fb17cef5b39e1575596bdc71a5bd9ad7b0d3fb7e` |
| Published at | `https://github.com/zkoss/zkidea/releases/download/v1.0.2/zk-preview-launcher-1.0.2.jar` |
| Main class bytecode | class file version 61 (requires Java 17 or newer) |
| JDK used | Azul Zulu 24 |
| ZK on the classpath | 10.3.0.1-Eval (zkmax, zkex, zkbind, zul, zk, zhtml, zuti, plus zkcharts 12.2.0.0-Eval) |
| Docroot used | a Maven `src/main/webapp` directory |

## 3. The behaviour this document was written to change (launcher 1.0.2)

Everything in this section describes **1.0.2**, the build in use when the document was written. It is
kept as the before-picture and as the reproduction recipe. For what 1.0.3 does, see §11.

Reproduce by starting the launcher on a fixed port against any webapp docroot:

```bash
java -jar zk-preview-launcher.jar \
     --classpath "<cp>" --webapp "<docroot>" --port 18899
```

then placing these files in the docroot under `spec-probe/` — `p.zul` (a two-line ZK page),
`p.zhtml`, `a.css`, `a.js`, `a.png`, `a.json`, `a.txt` — and requesting each with
`curl -s -o /dev/null -w "%{http_code} %{content_type} %{size_download}\n"`.

| Request | Status | Content-Type | Body bytes |
|---|---|---|---|
| `/spec-probe/p.zul` (file exists) | **200** | `text/html;charset=UTF-8` | 1287 |
| `/nope.zul` (file does **not** exist) | **200** | `text/html;charset=UTF-8` | **0** |
| `/spec-probe/p.zhtml` | 404 | `text/plain;charset=UTF-8` | 0 |
| `/spec-probe/a.css` | **404** | `text/plain;charset=UTF-8` | 0 |
| `/spec-probe/a.js` | **404** | `text/plain;charset=UTF-8` | 0 |
| `/spec-probe/a.png` | **404** | `text/plain;charset=UTF-8` | 0 |
| `/spec-probe/a.json` | **404** | `text/plain;charset=UTF-8` | 0 |
| `/spec-probe/a.txt` | **404** | `text/plain;charset=UTF-8` | 0 |
| `/spec-probe/` (a directory) | 404 | `text/plain;charset=UTF-8` | 0 |
| `/` | 404 | `text/plain;charset=UTF-8` | 0 |
| `/zkau/web/zul/less/font/ZK85Icons.woff` | **200** | `font/woff` | 10648 |
| `/zkau/web/js/zk/zk.wpd` | 404 | `text/plain;charset=UTF-8` | 0 |

Two things this table establishes:

1. **Only `.zul` and ZK classpath resources under `/zkau/web/` are served.** The five static files
   sit inside the very directory passed as `--webapp`, at exactly the requested paths, and all five
   return 404. The failure is not path resolution — it is that no handler exists.
2. **Classpath resource serving already works correctly, including MIME typing.** The woff file is
   returned with `font/woff` and the correct byte count, which is a useful precedent for §5.

Response headers on a served `.zul`, for reference:

```
HTTP/1.1 200 OK
X-zk-preview-controllers: skipped
Pragma: no-cache
Date: Mon, 31 Aug 2026 08:12:24 GMT
Content-type: text/html;charset=UTF-8
Content-length: 1287
Cache-control: no-store, no-cache, must-revalidate
```

(The launcher also sets `X-zk-preview-controller-failure` when a Composer or ViewModel threw.)

Path traversal, measured against the current build with `curl --path-as-is`:

| Request | Status |
|---|---|
| `/../../../../etc/passwd` | 404 |
| `/spec-probe/../../../../etc/passwd` | 404 |
| `/%2e%2e/%2e%2e/etc/passwd` | 404 |

On 1.0.2 these were safe only because nothing read the filesystem for these paths at all. **A static
handler ends that accidental safety, which is why §6 is a requirement and not advice** — and why the
encoding cases were re-probed against 1.0.3 in §11 rather than assumed.

## 4. Why this matters

The consuming tool renders a page to a PNG and asks an automated reviewer to compare that image
against the design it was built from. On 1.0.2, because no docroot asset was ever served, every image
on every page was blank in that PNG. The reviewer therefore could not use "an image did not draw" as
a signal at all — a real broken path and a correct one looked identical.

The tool's own guidance had to compensate with a blanket instruction to ignore missing assets. In a
six-run evaluation of that guidance, that instruction was quoted to close a genuine, one-word markup
bug as unfixable, and one page shipped with every icon on it rendered as an empty box. The blanket
instruction is the direct consequence of this gap: with static serving in place, a blank asset
becomes a real signal and the instruction can be deleted.

Secondary effects, all from the same cause:

* A page's own stylesheet (`<link href="/css/app.css">`) never loads, so the screenshot shows
  unstyled or half-styled output that does not represent the page.
* A page's own script never loads.
* A mistyped asset path is indistinguishable from a correct one.

## 5. Functional requirements

**R1 — Serve regular files from the docroot.** A `GET` for a path that resolves to a regular file
inside the docroot returns `200` with that file's exact bytes and a correct `Content-Length`.

**R2 — Correct `Content-Type`, by extension.** At minimum:

| Extension | Content-Type |
|---|---|
| `.css` | `text/css` |
| `.js`, `.mjs` | `text/javascript` |
| `.json` | `application/json` |
| `.png` | `image/png` |
| `.jpg`, `.jpeg` | `image/jpeg` |
| `.gif` | `image/gif` |
| `.svg` | `image/svg+xml` |
| `.webp` | `image/webp` |
| `.ico` | `image/vnd.microsoft.icon` |
| `.woff` | `font/woff` |
| `.woff2` | `font/woff2` |
| `.ttf` | `font/ttf` |
| `.eot` | `application/vnd.ms-fontobject` |
| `.txt` | `text/plain` |
| `.html`, `.htm` | `text/html` |
| `.map` | `application/json` |
| anything else | `application/octet-stream` |

Text types must carry `;charset=UTF-8`. Binary types must not.

**R3 — Handler precedence, existing handlers unchanged.** Resolve in this order, first match wins:
1. the existing `.zul` page handler,
2. the existing `/zkau/**` classpath resource handler,
3. the new static file handler.

The static handler must never see a request the first two would have answered. In particular a
`.zul` file must continue to be rendered as a page, never returned as source text.

**R4 — `HEAD` behaves as `GET` without a body**, returning the same status and `Content-Length`.
Methods other than `GET` and `HEAD` return `405` with an `Allow: GET, HEAD` header.

**R5 — A genuinely missing file returns `404`** with an empty body, matching the current shape.

**R6 — Directories are not served and not listed.** A request resolving to a directory returns
`404`. Do not fall back to `index.html` or `index.zul`, and never emit a directory listing — the
listing would disclose the contents of a developer's working tree to anything that can reach the
port.

**R7 — Never cache.** Static responses carry the same no-cache headers the `.zul` handler already
sends: `Cache-control: no-store, no-cache, must-revalidate` and `Pragma: no-cache`. The caller
re-renders the same URL repeatedly while editing files, and a cached asset would silently show a
previous version. Do not implement `ETag` or `If-Modified-Since` handling; a `304` would produce the
same stale-image failure.

**R8 — Stream large files.** Do not read a whole file into memory before writing it. Assets of tens
of megabytes are normal in a webapp and the launcher runs with default heap.

**R9 — Concurrency.** Asset requests arrive in parallel with, and during, the page request that
triggered them. Serving them must not block or deadlock the page handler.

## 6. Security requirements

The launcher binds to a local port and serves whatever it is pointed at. Today it reads no file for
an arbitrary path, so traversal is impossible by construction; a static handler ends that, and these
requirements replace it.

**S1 — Confinement of the requested path.** Normalise the resolved path (resolving `.` and `..`)
and serve it only if the normalised path is inside the docroot. Compare on path components, not on
string prefixes — a docroot of `/home/u/app` must not admit `/home/u/app-secrets/x`. Symbolic links
are deliberately **not** resolved as part of this check; see §7.

**S2 — Decode before validating.** Percent-decode the request path first, then validate, so
`%2e%2e%2f` is rejected on the same code path as `../`. Reject over-long or malformed encodings
rather than repairing them. Reject any path containing a NUL byte. On Windows, reject backslash as
a separator rather than normalising it.

**S3 — `WEB-INF` and `META-INF` are never served.** A request whose resolved path has a
`WEB-INF` or `META-INF` component returns `404`, case-insensitively, at any depth. These directories
hold `web.xml`, `zk.xml`, and in a built webapp the application's own classes and jars.

**S4 — No dotfiles.** Any path component beginning with `.` returns `404`. This keeps `.git/`,
`.env` and editor state out of reach.

**S5 — Bind to loopback only.** Confirm the listening socket is bound to `127.0.0.1` and not to
`0.0.0.0`. With static serving added, a wildcard bind would expose a developer's working tree to the
local network. If the current bind is already loopback, this is a regression test, not a change.

## 7. Out of scope

* Range requests (`Accept-Ranges`, `206`). The consumer screenshots a first paint; partial content
  is never requested.
* Compression (`Content-Encoding`). Everything is local.
* Conditional requests and caching — explicitly excluded by R7.
* Serving `.zhtml` as a rendered page. It currently returns `404` and this document does not ask for
  that to change; note only that `.zhtml` must not accidentally start being served as *source text*
  by the new static handler. Decide deliberately: either keep it `404`, or render it — but not
  "return the raw file".
* Directory indexes, by R6.
* **Symbolic links. Explicitly unsupported, and this is a decision rather than an oversight.**
  A symlink inside the docroot is followed, so it serves its target even when the target is outside
  the docroot. Measured on the 1.0.3 build: a link at `<docroot>/assets/passwd-link` pointing at
  `/etc/passwd` returned `200` with the file's 9196 bytes, and a link at `<docroot>/etclink` pointing
  at the `/etc` **directory** exposed the whole tree beneath it (`/etclink/passwd`, `/etclink/hosts`).
  Accepted because the exposure requires someone to have placed an escaping link inside the
  developer's own project directory, and because the listener is bound to loopback (S5), so nothing
  off the machine can reach it. Implementers should know this is the known and intended boundary of
  S1: do not add link resolution to "fix" a report of it without reopening this decision, and do not
  quietly rely on the absence of links for any stronger claim.

## 8. Acceptance criteria

Set up: a docroot containing `assets/logo.png` (a valid PNG), `assets/app.css`, `assets/app.js`,
`page.zul`, `WEB-INF/web.xml`, and `.hidden/secret.txt`.

A16 is deliberately not an escape test — symbolic links are out of scope per §7 — but it is kept as
a **characterisation** row so the accepted behaviour is asserted rather than assumed. Add a symlink
`assets/escape` pointing at a file outside the docroot for it.

| # | Request | Expected |
|---|---|---|
| A1 | `GET /assets/logo.png` | `200`, `image/png`, bytes identical to the file, correct `Content-Length` |
| A2 | `GET /assets/app.css` | `200`, `text/css;charset=UTF-8` |
| A3 | `GET /assets/app.js` | `200`, `text/javascript;charset=UTF-8` |
| A4 | `GET /page.zul` | `200`, `text/html;charset=UTF-8`, rendered page — **not** file source |
| A5 | `GET /assets/missing.png` | `404`, empty body |
| A6 | `GET /assets/` | `404`, and no listing anywhere in the body |
| A7 | `HEAD /assets/logo.png` | `200`, correct `Content-Length`, empty body |
| A8 | `POST /assets/logo.png` | `405` with `Allow: GET, HEAD` |
| A9 | `GET /assets/logo.png` twice | both `200`, both carry `Cache-control: no-store, no-cache, must-revalidate`; never `304` |
| A10 | `GET /../../../../etc/passwd` (`--path-as-is`) | `404` |
| A11 | `GET /assets/../../../../etc/passwd` (`--path-as-is`) | `404` |
| A12 | `GET /%2e%2e/%2e%2e/etc/passwd` | `404` |
| A13 | `GET /WEB-INF/web.xml` | `404` |
| A14 | `GET /web-inf/web.xml` | `404` (case-insensitive) |
| A15 | `GET /.hidden/secret.txt` | `404` |
| A16 | `GET /assets/escape` (symlink out) | `200`, serving the target's bytes — **the accepted behaviour, not a defect**. Symlinks are out of scope (§7); this row exists so the boundary is asserted and a future change to it is a deliberate one |
| A17 | `GET /zkau/web/zul/less/font/ZK85Icons.woff` | `200`, `font/woff`, 10648 bytes — unchanged |
| A18 | listening socket | bound to `127.0.0.1`, not `0.0.0.0` |
| A19 | a 50 MB asset | served correctly with no `OutOfMemoryError` under the default heap |
| A20 | end to end | a page with `<image src="/assets/logo.png"/>` screenshots with the image visible |

## 9. Non-regression

Every row of the §3 measured table must hold afterwards except the five static 404s that this change
converts to 200s. Specifically unchanged: the `.zul` 200 and its body, the `X-zk-preview-controllers`
and `X-zk-preview-controller-failure` headers, the no-cache headers, `PREVIEW_PORT=<n>` on stdout,
the `--classpath` / `--webapp` / `--port` / `--isolation` / `--controller-timeout` argument surface,
and the `/zkau/web/**` behaviour including MIME typing.

## 10. Adjacent observation — also fixed in 1.0.3

On 1.0.2, `GET /nope.zul` for a `.zul` that does not exist returned **`200` with a zero-byte body**
rather than `404`, so a caller could not distinguish "page missing" from "page rendered to nothing".
This document originally asked for it to be filed separately. It was fixed in the same 1.0.3 build
and needs no further action; measured on 2026-09-01:

```
HTTP/1.1 404
Content-type: text/plain;charset=UTF-8

HTTP 404: no such page: /nope.zul
docroot: /path/to/docroot
```

Naming the docroot in the body is a good call: "no such page" and "wrong docroot" are the two causes,
and the response now separates them without a second request.

## 11. Verification of the 1.0.3 build

Run on 2026-09-01 against the **published** release asset,
`https://github.com/zkoss/zkidea/releases/download/v1.0.3/zk-preview-launcher-1.0.3.jar`,
487,521 bytes, SHA-256 `c4eb3096a59f0cbe59a71deb2ae8df86aeb82475939eaf7c1bee4e49488d2bee`,
JDK Azul Zulu 24, stock ZK 10.2.1 on the classpath, using the §8 setup.

The results were first obtained against a local pre-release build of the same version whose digest
was `cdf469c9…`, and were then re-run in full against the published artifact rather than carried
over. Same version string and same byte count, different digest — a rebuild — so the earlier run
did not automatically speak for what users download.

**A1–A15 and A17–A20 pass.** Highlights, with the numbers observed:

| Criterion | Observed |
|---|---|
| A1 | `200`, `image/png`, 67 bytes, byte-identical to the file on disk (`cmp`) |
| A2 / A3 | `text/css;charset=UTF-8` and `text/javascript;charset=UTF-8` |
| A4 | `200`, 1431 bytes of rendered HTML, not the 200-byte source |
| A8 | `405` with `Allow: GET, HEAD` |
| A9 | both responses `no-store, no-cache, must-revalidate`; no `ETag`, no `Last-Modified`, never `304` |
| A17 | `200`, `font/woff`, 10648 bytes — byte-for-byte the 1.0.2 figure |
| A18 | bound to `127.0.0.1` |
| A19 | 52,428,800 bytes served in 0.04 s, no `OutOfMemoryError`, server responsive afterwards |
| A20 | a page with a 240x120 PNG screenshots with the image visible; the same page on 1.0.2 screenshots a broken-image placeholder |

**A16 behaves as §7 now documents** — a symlink out of the docroot is followed and served.

Beyond the A-list, S2's other encodings were probed and all are rejected:
`/%2e%2e%2f%2e%2e%2fetc/passwd`, `/assets%2f..%2f..%2f..%2f..%2fetc%2fpasswd` and
`/..%252f..%252fetc/passwd` return `404`; `/WEB-INF%2fweb.xml` and `/%57EB-INF/web.xml` return `404`,
so neither slash-encoding nor case-encoding evades S3; and a backslash path returns **`400`**, which
is the reject-rather-than-normalise behaviour S2 asks for.

The consuming tool's own 29-check CLI contract suite passes end to end against 1.0.3 with no
regression.
