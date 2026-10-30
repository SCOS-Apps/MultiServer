# MultiServer

A simple, modular Python HTTP web server with support for keep-alive connections, directory listings, form building, inline Python execution, `.pyhtml` AJAX endpoints, and HTTP Digest authentication.

## Features

- **HTTP/1.1** server with GET, HEAD, POST, OPTIONS, PUT, DELETE methods
- **Keep-alive / persistent connections** with configurable timeout
- **Directory listings** (Apache-style, configurable index position)
- **No-extension URL handling** (`/index` serves `index.html`; ambiguous matches return 300 Multiple Choices)
- **Path traversal protection** (all file access confined to `WorkPath`)
- **MIME type detection** (via `mimetypes` and `python-magic` fallback)
- **Inline Python execution** in HTML via `<python>` tags
- **`.pyhtml` AJAX endpoints** — execute Python code and return stdout as raw data
- **Form building** (`FormField`, `FormBuilder`, `FORM_TEMPLATES`)
- **HTTP Digest authentication** (SHA-256, RFC 7616) for PUT/DELETE
- **CORS preflight** support on OPTIONS requests
- **Modular architecture** — separate modules for FileHandling, HTMLCode, HTTP, PythonHandling, Socket, WebServer

## Requirements

- Python 3.11+
- `bs4`
- `python-magic`

Install dependencies:

```bash
pip install bs4 python-magic
```

## Quick Start

```bash
git clone https://github.com/SCOS-Apps/MultiServer
cd MultiServer
mkdir www # default directory for web content
cp demos/index.html www/
python3 MultiServer.py
```

The server will start on `http://127.0.0.1:8888` by default. Open your browser and navigate there.

## Configuration (`config.toml`)

All server settings are in `config.toml`:

```toml
[Server]
Host = "127.0.0.1"
Port = [8888]
MaxConnections = 50
WorkPath = "./www"
DefaultIndex = "index.html"
Debug = false
DirectoryListing = true
DirectoryListingIndexBottom = true
KeepAlive = true
KeepAliveTimeout = 5

[Module]
ModuleDirPy = "modules"
Load = ["FileHandling", "HTMLCode", "HTTP", "PythonHandling", "Socket", "WebServer"]

[Module.FileHandling.MIME]
EnableMIME = true
MIMEModuleType = "auto"
MIMEDefaultType = "application/octet-stream"

[Security]
RestrictToWorkPath = true

[Auth]
Enabled = true
Realm = "MultiServer"
UsersFile = "./.htpasswd"
RequireMethods = ["PUT", "DELETE"]
```

### `[Server]`
- `Host` — Bind address
- `Port` — Port as a list (e.g. `[8888]`) or bare int
- `WorkPath` — Website root directory
- `DefaultIndex` — Default filename served for `/`
- `DirectoryListing` — Enable directory listings
- `DirectoryListingIndexBottom` — Put `index.html` at the bottom of listings (Apache-style)
- `KeepAlive` — Enable persistent connections
- `KeepAliveTimeout` — Idle timeout in seconds

### `[Security]`
- `RestrictToWorkPath` — Block path traversal outside `WorkPath` (default: `true`)

### `[Auth]`
- `Enabled` — Turn on HTTP Digest authentication
- `Realm` — Authentication realm shown to clients
- `UsersFile` — Path to `.htpasswd` file
- `RequireMethods` — HTTP methods that require authentication (default: `["PUT", "DELETE"]`)

## Authentication

MultiServer uses **HTTP Digest Authentication** (RFC 7616) with SHA-256. Passwords are never stored in plaintext — `.htpasswd` contains `username:sha256_hex` hashes:

```
# Format: username:sha256_hex(SHA-256(username:realm:password))
testuser:cb44f4d07169e5f14bb4d9a80480d789d53e0a206ece4d156f6631f6f0bf2577
```

Generate a hash:

```bash
python3 -c "
import hashlib
print(hashlib.sha256(f'testuser:MultiServer:test'.encode()).hexdigest())
"
```

Protected methods (PUT, DELETE by default) return `401 Unauthorized` with a `WWW-Authenticate: Digest` challenge until valid credentials are supplied.

## `.pyhtml` AJAX Endpoints

Any file ending in `.pyhtml` is executed as a Python script and its stdout is returned as `text/plain`. This is ideal for AJAX endpoints that return dynamic data.

Example (`demos/api.pyhtml`):

```python
import datetime, json
data = {
    "time": datetime.datetime.now().isoformat(),
    "message": "Hello from PythonHTML!",
    "form": form,           # POST form data (dict)
    "query": request.get("get", {}),  # URL query parameters (dict)
}
print(json.dumps(data))
```

Available in `<python>` blocks and `.pyhtml` files:
- `form` / `FORM_DATA` — POST form data dict
- `request` — `{"post": {...}, "get": {...}}`

## Form Building

Programmatically build HTML forms:

```python
from modules.PythonHandling import FormBuilder, FormField, FORM_TEMPLATES

builder = FormBuilder(form_id="myform", action="/submit", method="POST")
builder.add_field(FormField("name", field_type="text", label="Name", required=True))
builder.add_field(FormField("choice", field_type="select", options=["A", "B", "C"]))
html = builder.build()
```

Predefined templates: `login`, `contact`, `search`.

Inline Python in HTML:

```html
<python>
name = form.get("name", "Guest")
print(f"<p>Hello, {name}!</p>")
</python>
```

## Project Structure

```
MultiServer/
├── MultiServer.py          # Entry point — loads config, starts modules
├── MultiServer_stubs.py    # Type stubs, protocols, base classes
├── config.toml             # Server configuration
├── test.py                 # Unit + web integration tests (71 tests)
├── LICENSE                 # GNU GPL v3
├── modules/
│   ├── FileHandling.py     # File read/write/delete, MIME detection, path sanitization
│   ├── HTMLCode.py         # BeautifulSoup-based HTML manipulation
│   ├── HTTP.py             # HTTP status codes, reason phrases, HeaderResponse
│   ├── PythonHandling.py   # Inline Python execution, FormBuilder, .pyhtml execution
│   ├── Socket.py           # TCP socket wrapper (ConnectionLike)
│   └── WebServer.py        # HTTP request handling, keep-alive, auth, directory listings
└── demos/                  # demos for different things.
    ├── index.html
    ├── ajax.html           # AJAX demo page
    ├── api.pyhtml          # JSON AJAX endpoint demo
    ├── echo.html           # Form echo demo
    ├── formtest.html
    ├── redirect.html
    └── paltest.webp
```

## Running Tests

```bash
python3 test.py
```

Runs 49 unit tests + 22 web integration tests (starts the server, makes real HTTP requests via `urllib`, then shuts it down).

## Security Notes

- **Path traversal**: All file access is confined to `WorkPath`. `../` sequences are rejected.
- **Basic auth is NOT used**: Digest authentication sends hashed challenges, never raw passwords.
- **Inline Python execution**: `<python>` tags and `.pyhtml` files execute arbitrary code with `exec()`. Only enable on trusted networks or behind authentication.
- **No HTTPS**: This server does not implement TLS. Use behind a reverse proxy (e.g., nginx, Caddy) for production HTTPS.

## License

This project is licensed under the GNU General Public License v3.0. See the [`LICENSE`](LICENSE) file for details.
