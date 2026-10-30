from datetime import datetime
from urllib.parse import urlparse, parse_qs
import base64
import hashlib
import hmac
import os
import platform
import secrets
import threading
from bs4 import BeautifulSoup

from MultiServer_stubs import * # pyright: ignore[reportAssignmentType]
from modules.FileHandling import *
from modules.HTMLCode import *
from modules.HTTP import *
from modules.PythonHandling import *
from modules.Socket import *


class WebServer:
    """
    Simple web server
    """
    serverversion = "1.0"
    ALLOWED_METHODS = "GET, HEAD, POST, OPTIONS, PUT, DELETE"

    # Auth config (set by doAppend)
    auth_enabled: bool = False
    auth_realm: str = "MultiServer"
    auth_users_file: str = "./.htpasswd"
    auth_require_methods: list = ["PUT", "DELETE"]
    auth_algorithm: str = "SHA-256"
    auth_qop: str = "auth"

    def __init__(self) -> None:
        pass

    def start(self, HOST: str = "127.0.0.1", PORT: int = 80, wwwpath: str = "./www/",
              defaultcontent: str = "index.html", DEBUG: bool = False,
              keep_alive: bool = True, keep_alive_timeout: int = 5,
              directory_listing: bool = True, directory_listing_index_bottom: bool = True,
              auth_enabled: bool = False, auth_realm: str = "MultiServer",
              auth_users_file: str = "./.htpasswd", auth_require_methods: list | None = None,
              auth_algorithm: str = "SHA-256", auth_qop: str = "auth"):
        """Start the HTTP WebServer Manually (Not Recommended)

        Args:
            HOST (str, optional): Specific host to listen on. Defaults to "127.0.0.1".
            PORT (int, optional): Specific port to listen on. Defaults to 80.
            wwwpath (str, optional): Website page data directory. Defaults to "./www/".
            defaultcontent (str, optional): Default index. Defaults to "index.html".
            DEBUG (bool, optional): Debug mode. Defaults to False.
            keep_alive (bool, optional): Enable HTTP keep-alive. Defaults to True.
            keep_alive_timeout (int, optional): Keep-alive timeout in seconds. Defaults to 5.
            directory_listing (bool, optional): Enable directory listings. Defaults to True.
            directory_listing_index_bottom (bool, optional): Put index at bottom of listings. Defaults to True.
            auth_enabled (bool, optional): Enable HTTP Digest authentication. Defaults to False.
            auth_realm (str, optional): Authentication realm. Defaults to "MultiServer".
            auth_users_file (str, optional): Path to .htpasswd file. Defaults to "./.htpasswd".
            auth_require_methods (list, optional): Methods requiring auth. Defaults to ["PUT", "DELETE"].
            auth_algorithm (str, optional): Digest algorithm. Defaults to "SHA-256".
            auth_qop (str, optional): Quality of protection. Defaults to "auth".
        """
        if auth_require_methods is None:
            auth_require_methods = ["PUT", "DELETE"]
        WebServer.auth_enabled = auth_enabled
        WebServer.auth_realm = auth_realm
        WebServer.auth_users_file = auth_users_file
        WebServer.auth_require_methods = auth_require_methods
        WebServer.auth_algorithm = auth_algorithm
        WebServer.auth_qop = auth_qop
        print(f"[{HOST}:{PORT}]: Starting WebServer...")
        sock = Socket().startsocket(HOST, PORT)
        print(f"[{HOST}:{PORT}]: WebServer Ready, waiting for connections...")
        while True:
            conn, addr = sock.accept()
            t = threading.Thread(target=self.handleconn, args=(HOST, PORT, conn, addr, wwwpath, defaultcontent, DEBUG,
                keep_alive, keep_alive_timeout, directory_listing, directory_listing_index_bottom,
                WebServer.auth_enabled, WebServer.auth_realm, WebServer.auth_users_file,
                WebServer.auth_require_methods, WebServer.auth_algorithm, WebServer.auth_qop), daemon=True)
            t.start()

    def _build_header(self, code: int, mime: str, length: int, location: str | None = None,
                      keep_alive: bool = True, extra_headers: dict | None = None) -> bytes:
        reason = HTTP().getstringfromcode(code)
        connection = "keep-alive" if keep_alive else "close"
        header = (
            f"HTTP/1.1 {code} {reason}\r\n"
            f"content-type: {mime}\r\n"
            f"content-length: {str(length)}\r\n"
            f"connection: {connection}\r\n"
            f"date: {datetime.today().strftime('%a, %d %b %Y %H:%M:%S %Z')}\r\n"
        )
        if location:
            header += f"location: {location}\r\n"
        if extra_headers:
            for key, val in extra_headers.items():
                header += f"{key}: {val}\r\n"
        header += "\r\n"
        return header.encode()

    def _auth_challenge(self, realm: str, algorithm: str = "SHA-256", qop: str = "auth") -> dict:
        """Return WWW-Authenticate Digest challenge header per RFC 7616.

        Generates a nonce and opaque value for the challenge.
        """
        nonce = secrets.token_hex(16)
        opaque = secrets.token_hex(16)
        challenge = (
            f'Digest realm="{realm}", '
            f'nonce="{nonce}", '
            f'opaque="{opaque}", '
            f'algorithm={algorithm}, '
            f'qop="{qop}"'
        )
        # Store nonce/opaque for verification (simple in-memory, per-server)
        if not hasattr(WebServer, "_nonce_store"):
            WebServer._nonce_store = {}
        WebServer._nonce_store[nonce] = {"opaque": opaque, "realm": realm}
        return {"WWW-Authenticate": challenge}

    def _parse_digest_auth(self, auth_header: str) -> dict | None:
        """Parse a Digest Authorization header into a dict of parameters."""
        if not auth_header.lower().startswith("digest "):
            return None
        params_str = auth_header[7:].strip()
        params = {}
        # Parse key="value" pairs, handling quoted values with commas inside
        i = 0
        while i < len(params_str):
            # Skip whitespace and commas
            while i < len(params_str) and params_str[i] in " ,":
                i += 1
            if i >= len(params_str):
                break
            # Read key
            key_start = i
            while i < len(params_str) and params_str[i] not in "=,":
                i += 1
            key = params_str[key_start:i].strip()
            if i >= len(params_str) or params_str[i] != "=":
                continue
            i += 1  # skip '='
            # Read value
            if i < len(params_str) and params_str[i] == '"':
                i += 1  # skip opening quote
                val_start = i
                while i < len(params_str) and params_str[i] != '"':
                    i += 1
                val = params_str[val_start:i]
                if i < len(params_str):
                    i += 1  # skip closing quote
            else:
                val_start = i
                while i < len(params_str) and params_str[i] != ",":
                    i += 1
                val = params_str[val_start:i].strip()
            params[key] = val
        return params

    def _error_page(self, code: int, path: str, HOST: str, PORT: int) -> tuple[bytes, str]:
        """Generate an error page HTML body.

        Returns (html_bytes, mime_type).
        """
        htmlcode = HTMLCode()
        reason = HTTP().getstringfromcode(code)
        htmlcode.Node(htmlcode.soup).add("title", inside=htmlcode["node:head"],
            content=f"{code} {reason}")
        is_redirect = code in (PERMANENT_REDIRECT, TEMPORARY_REDIRECT,
                               MOVED_PERMANENTLY, FOUND)
        if is_redirect:
            htmlcode.Node(htmlcode.soup).add("h1", content=f"{reason}")
            htmlcode.Node(htmlcode.soup).add("p",
                content=f"You tried viewing the following: {path}")
            htmlcode.Node(htmlcode.soup).add("hr")
            htmlcode.Node(htmlcode.soup).add("p",
                options={"style": "font-style: italic"},
                content=f"WebServer/{WebServer.serverversion} at {HOST} "
                f"Port {PORT}, Python {platform.python_version()}")
        else:
            htmlcode.Node(htmlcode.soup).add("h1",
                options={"style": "display: flex; justify-content: center; "
                "align-items: center;"}, content=f"{code}: {reason}")
            htmlcode.Node(htmlcode.soup).add("p",
                content="You tried viewing the following:")
            htmlcode.Node(htmlcode.soup).add("p",
                options={"style": "display: flex; justify-content: center; "
                "align-items: center;"}, content=path)
        htmlcont = htmlcode.soup.encode()
        return htmlcont, "text/html"

    def _multiple_choices_page(self, matches: list, www_dir: Path, path: str,
                               HOST: str, PORT: int) -> bytes:
        """Generate a 300 Multiple Choices page listing matching files."""
        htmlcode = HTMLCode()
        reason = HTTP().getstringfromcode(MULTIPLE_CHOICES)
        htmlcode.Node(htmlcode.soup).add("title", inside=htmlcode["node:head"],
            content=f"{MULTIPLE_CHOICES} {reason}")
        htmlcode.Node(htmlcode.soup).add("h1",
            options={"style": "display: flex; justify-content: center; "
            "align-items: center;"}, content=f"{MULTIPLE_CHOICES}: {reason}")
        htmlcode.Node(htmlcode.soup).add("p",
            content=f"Multiple files match '{path}':")
        ul_node = htmlcode.Node(htmlcode.soup).add("ul")
        for match in matches:
            rel = match.relative_to(www_dir)
            href = f"/{rel}"
            link_tag = BeautifulSoup(
                f'<li><a href="{href}">{href}</a></li>',
                "html.parser").find("li")
            ul_node.node.append(link_tag)
        htmlcode.Node(htmlcode.soup).add("hr")
        htmlcode.Node(htmlcode.soup).add("p",
            options={"style": "font-style: italic"},
            content=f"WebServer/{WebServer.serverversion} at {HOST} "
            f"Port {PORT}, Python {platform.python_version()}")
        return htmlcode.soup.encode()

    def _directory_listing(self, dir_path: Path, www_dir: Path,
                           requested_path: str, HOST: str, PORT: int,
                           index_bottom: bool,
                           defaultindex: str) -> tuple[bytes, str, int, bool]:
        """Generate a directory listing HTML page Apache-style.

        Returns (html_bytes, mime, code, skip_html_mod).
        """
        htmlcode = HTMLCode()
        reason = HTTP().getstringfromcode(OK)
        htmlcode.Node(htmlcode.soup).add("title", inside=htmlcode["node:head"],
            content=f"Index of {requested_path}")
        htmlcode.Node(htmlcode.soup).add("h1",
            options={"style": "display: flex; justify-content: center; "
            "align-items: center;"}, content=f"Index of {requested_path}")
        htmlcode.Node(htmlcode.soup).add("hr")

        entries = sorted(dir_path.iterdir(),
            key=lambda p: (not p.is_dir(), p.name.lower()))
        ul_node = htmlcode.Node(htmlcode.soup).add("ul")

        index_file = None
        other_entries = []

        for entry in entries:
            rel = entry.relative_to(www_dir)
            href = f"/{rel}"
            display = entry.name + ("/" if entry.is_dir() else "")
            if entry.name == defaultindex:
                index_file = (entry, href, display)
            else:
                other_entries.append((entry, href, display))

        # Other entries first
        for entry, href, display in other_entries:
            li = BeautifulSoup(
                f'<li><a href="{href}">{display}</a></li>',
                "html.parser").find("li")
            ul_node.node.append(li)

        # Index at bottom if configured
        if index_bottom and index_file:
            entry, href, display = index_file
            li = BeautifulSoup(
                f'<li><a href="{href}">{display}</a> (index)</li>',
                "html.parser").find("li")
            ul_node.node.append(li)

        htmlcode.Node(htmlcode.soup).add("hr")
        htmlcode.Node(htmlcode.soup).add("p",
            options={"style": "font-style: italic"},
            content=f"WebServer/{WebServer.serverversion} at {HOST} "
            f"Port {PORT}, Python {platform.python_version()}")

        return htmlcode.soup.encode(), "text/html", OK, True

    def _check_auth(self, headers: dict, realm: str, users_file: str,
                    algorithm: str = "SHA-256", qop: str = "auth") -> bool:
        """Check Digest authentication credentials per RFC 7616.

        Returns True if authenticated, False otherwise.
        """
        auth_header = headers.get("authorization", "")
        if not auth_header:
            return False

        params = self._parse_digest_auth(auth_header)
        if params is None:
            return False

        username = params.get("username", "")
        realm_val = params.get("realm", "")
        nonce = params.get("nonce", "")
        uri = params.get("uri", "")
        response = params.get("response", "")
        algorithm_val = params.get("algorithm", algorithm)
        qop_val = params.get("qop", "")
        nc = params.get("nc", "")
        cnonce = params.get("cnonce", "")
        opaque = params.get("opaque", "")

        if realm_val != realm:
            return False

        # Verify nonce is valid (server-generated)
        if not hasattr(WebServer, "_nonce_store"):
            WebServer._nonce_store = {}
        if nonce not in WebServer._nonce_store:
            return False
        nonce_info = WebServer._nonce_store[nonce]
        if nonce_info.get("opaque") != opaque:
            return False

        # Look up user's HA1 hash from .htpasswd
        ha1 = None
        try:
            with open(users_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if ":" not in line:
                        continue
                    stored_user, stored_hash = line.split(":", 1)
                    if stored_user == username:
                        ha1 = stored_hash.strip()
                        break
        except FileNotFoundError:
            return False

        if ha1 is None:
            return False

        # Compute HA2 = SHA-256(method:uri)
        method = headers.get("_method", "GET")  # Will be set by caller
        ha2_input = f"{method}:{uri}"
        ha2 = hashlib.sha256(ha2_input.encode("utf-8")).hexdigest()

        # Compute response digest
        if qop_val == "auth":
            # response = SHA-256(HA1:nonce:nc:cnonce:qop:HA2)
            resp_input = f"{ha1}:{nonce}:{nc}:{cnonce}:{qop_val}:{ha2}"
        else:
            # response = SHA-256(HA1:nonce:HA2)
            resp_input = f"{ha1}:{nonce}:{ha2}"
        expected_response = hashlib.sha256(resp_input.encode("utf-8")).hexdigest()

        return hmac.compare_digest(response, expected_response)

    def _load_users(self, users_file: str) -> dict:
        """Load users from .htpasswd file. Returns dict of username -> HA1 hash."""
        users = {}
        try:
            with open(users_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if ":" not in line:
                        continue
                    stored_user, stored_hash = line.split(":", 1)
                    users[stored_user.strip()] = stored_hash.strip()
        except FileNotFoundError:
            pass
        return users

    def _handle_options(self, path: str, headers: dict) -> tuple[bytes, str, int, bool, dict | None]:
        """Handle OPTIONS request per RFC 9110.

        Supports both asterisk form (* for whole server) and request-target form.
        Returns CORS preflight headers when appropriate.
        """
        allow = self.ALLOWED_METHODS
        body = f"Allowed methods: {allow}".encode()
        extra_headers = {"Allow": allow}

        # CORS preflight support
        origin = headers.get("origin", "")
        if origin:
            extra_headers["Access-Control-Allow-Origin"] = origin
            extra_headers["Access-Control-Allow-Methods"] = allow
            req_headers = headers.get("access-control-request-headers", "")
            if req_headers:
                extra_headers["Access-Control-Allow-Headers"] = req_headers
            max_age = headers.get("access-control-max-age", "86400")
            extra_headers["Access-Control-Max-Age"] = max_age

        if path == "*":
            body = f"OPTIONS for whole server. Allowed methods: {allow}".encode()
        return body, "text/plain", OK, False, extra_headers

    def _handle_delete(self, full_path: str, addr: Any) -> tuple[bytes, str, int, bool]:
        """Handle DELETE request - remove a file."""
        success = FileHandling().deletefile(full_path, addr)
        if success:
            return b"", "text/plain", NO_CONTENT, False
        return b"", "text/plain", NOT_FOUND, True

    def _process_request(self, path: str, httpreqtype: str, addr: Any, wwwpath: str,
                         defaultcontent: str, DEBUG: bool, HOST: str, PORT: int,
                         form_data: dict | None = None, query_params: dict | None = None,
                         directory_listing: bool = True, directory_listing_index_bottom: bool = True,
                         keep_alive: bool = True,
                         auth_enabled: bool = False, auth_realm: str = "MultiServer",
                         auth_users_file: str = "./.htpasswd",
                         auth_require_methods: list | None = None,
                         auth_algorithm: str = "SHA-256", auth_qop: str = "auth",
                         headers: dict | None = None) -> tuple[bytes, bytes, dict | None]:
        """Process an HTTP request and return (header, body, extra_headers) bytes."""
        if auth_require_methods is None:
            auth_require_methods = ["PUT", "DELETE"]
        if headers is None:
            headers = {}

        iserror: bool = False
        htmlcont: bytes = b""
        testkey: int | None = None
        location: str = "/"
        mime: str | None = None
        code: int = OK
        skip_html_mod: bool = False
        extra_headers: dict | None = None

        # --- Authentication check for protected methods ---
        if auth_enabled and httpreqtype in auth_require_methods:
            if not self._check_auth(headers, auth_realm, auth_users_file,
                                    auth_algorithm, auth_qop):
                extra_headers = self._auth_challenge(auth_realm, auth_algorithm, auth_qop)
                err_body = b"Unauthorized"
                header = self._build_header(UN_AUTHORIZED, "text/plain", len(err_body),
                    extra_headers=extra_headers, keep_alive=keep_alive)
                return header, err_body, extra_headers

        if httpreqtype == OPTIONS:
            body, mime, code, iserror, extra_headers = self._handle_options(path, headers)
            header = self._build_header(code, mime, len(body), extra_headers=extra_headers,
                keep_alive=keep_alive)
            body = b"" if httpreqtype == HEAD else body
            return header, body, extra_headers

        if httpreqtype == PUT:
            full_put_path = f"{wwwpath}/{path}"
            # Body is already read by handleconn; write it directly
            success = FileHandling().writefile(full_put_path, addr, b"")
            if not success:
                code = INTERNAL_SERVER_ERROR
                iserror = True
            else:
                code = CREATED
            header = self._build_header(code, "text/plain", 0, keep_alive=keep_alive)
            return header, b"", extra_headers

        if httpreqtype == DELETE:
            full_delete_path = f"{wwwpath}/{path}"
            success = FileHandling().deletefile(full_delete_path, addr)
            if success:
                code = NO_CONTENT
                iserror = False
            else:
                code = NOT_FOUND
                iserror = True
            header = self._build_header(code, "text/plain", 0, keep_alive=keep_alive)
            return header, b"", extra_headers

        if httpreqtype == GET and path == "/":
            htmlcont, mime, code, iserror = FileHandling().getfile(
                f"{wwwpath}/{defaultcontent}", addr, forcemime=True, forcemimetype="text/html")
        elif httpreqtype == GET and path.startswith("/test/") and len(path.split("/")) == 3:
            print(f"[{addr[0]}:{addr[1]}]: Test URL Detected")
            testkey = int(path.split("/")[2])
            print(f"[{addr[0]}:{addr[1]}]: Testing: {testkey}")
            if testkey >= 300:
                print(f"[{addr[0]}:{addr[1]}]: Testing code above 300, assuming error.")
                iserror = True
            htmlcont, mime, code = b"", "", testkey
        elif path.endswith(".pyhtml"):
            """AJAX endpoint: execute Python code and return stdout as data."""
            print(f"[{addr[0]}:{addr[1]}]: PythonHTML endpoint detected: {path}")
            try:
                with open(Path(f"{wwwpath}/{path}"), "r") as f:
                    pycode = f.read()
                executed = PythonHandling().execute(pycode, form_data=form_data,
                    query_params=query_params)
                htmlcont = executed.encode()
                mime = "text/plain"
                code = OK
                iserror = False
                skip_html_mod = True
            except FileNotFoundError:
                print(f"[{addr[0]}:{addr[1]}]: PythonHTML not found: {path}")
                htmlcont, mime, code, iserror = b"", "text/plain", NOT_FOUND, True
            except Exception as e:
                print(f"[{addr[0]}:{addr[1]}]: PythonHTML execution error: {e}")
                htmlcont, mime, code, iserror = str(e).encode(), "text/plain", INTERNAL_SERVER_ERROR, True
        else:
            # Check if it's a directory first (getfile would return FORBIDDEN for IsADirectoryError)
            safe_path = FileHandling()._resolve_path(f"{wwwpath}/{path}")
            if safe_path and Path(safe_path).is_dir() and directory_listing:
                dir_path = Path(safe_path)
                listing, mime, code, skip = self._directory_listing(
                    dir_path, Path(wwwpath).resolve(), path, HOST, PORT,
                    directory_listing_index_bottom, defaultcontent)
                htmlcont = listing
                iserror = False
                skip_html_mod = skip
            else:
                htmlcont, mime, code, iserror = FileHandling().getfile(f"{wwwpath}/{path}", addr)

                # No-extension handling: try exact file first, then glob for path.*
                if iserror and code == NOT_FOUND:
                    clean_path = path.lstrip("/")
                    if ".." not in Path(clean_path).parts:
                        www_dir = Path(wwwpath).resolve()
                        matches = []
                        for match in www_dir.glob(f"{clean_path}.*"):
                            if match.is_file() and www_dir in match.resolve().parents:
                                matches.append(match)
                        matches.sort()
                        if len(matches) > 1:
                            iserror = False
                            code = MULTIPLE_CHOICES
                            htmlcont = self._multiple_choices_page(matches, www_dir, path,
                                HOST, PORT)
                            mime = "text/html"
                            skip_html_mod = True
                        elif len(matches) == 1:
                            htmlcont, mime, code, iserror = FileHandling().getfile(
                                str(matches[0]), addr)

                # Directory handling: path without trailing slash that resolves to a directory
                if iserror and code == FORBIDDEN:
                    safe = FileHandling()._resolve_path(f"{wwwpath}/{path}")
                    if safe and Path(safe).is_dir():
                        if directory_listing:
                            dir_path = Path(safe)
                            listing, mime, code, skip = self._directory_listing(
                                dir_path, Path(wwwpath).resolve(), path, HOST, PORT,
                                directory_listing_index_bottom, defaultcontent)
                            htmlcont = listing
                            iserror = False
                            skip_html_mod = skip
                        else:
                            code = FORBIDDEN
                            iserror = True

        if mime and mime.startswith("text/") and htmlcont:
            try:
                node = HTMLCode(htmlcont.decode())["node:redirect"]
            except ValueError:
                iserror = True
                code = MULTIPLE_CHOICES
            except LookupError:
                pass
            else:
                iserror = True
                code = PERMANENT_REDIRECT if node.node.get("type") == "perm" else TEMPORARY_REDIRECT
                location = node.content

        if code in (PERMANENT_REDIRECT, TEMPORARY_REDIRECT, MOVED_PERMANENTLY, FOUND):
            if testkey:
                location = "/"

        print(f"[{addr[0]}:{addr[1]}]: Sending data...")
        if not iserror:
            if not skip_html_mod and mime and mime.startswith("text/"):
                htmlcontpy = PythonHandling().modify(
                    htmlcont.decode(), form_data=form_data, query_params=query_params)
                if htmlcontpy:
                    htmlcont = htmlcontpy.encode()
            mime = mime or "application/octet-stream"
            header = self._build_header(code, mime, len(htmlcont),
                location if code in (PERMANENT_REDIRECT, TEMPORARY_REDIRECT,
                                     MOVED_PERMANENTLY, FOUND) else None,
                keep_alive, extra_headers)
            body = b"" if httpreqtype == HEAD else htmlcont
        else:
            if code in (PERMANENT_REDIRECT, TEMPORARY_REDIRECT, MOVED_PERMANENTLY, FOUND):
                print(f"[{addr[0]}:{addr[1]}]: Redirect detected.")
                htmlcont, mime = self._error_page(code, path, HOST, PORT)
                header = self._build_header(code, mime, len(htmlcont), location,
                    keep_alive, extra_headers)
            else:
                htmlcont, mime = self._error_page(code, path, HOST, PORT)
                header = self._build_header(code, mime, len(htmlcont),
                    keep_alive=keep_alive, extra_headers=extra_headers)
            body = b"" if httpreqtype == HEAD else htmlcont

        return header, body, extra_headers

    def handleconn(self, conn: socket.socket, addr: Any, HOST: str, PORT: int,
                   wwwpath: str, defaultcontent: str, DEBUG: bool,
                   keep_alive: bool = True, keep_alive_timeout: int = 5,
                   directory_listing: bool = True,
                   directory_listing_index_bottom: bool = True,
                   auth_enabled: bool | None = None, auth_realm: str | None = None,
                   auth_users_file: str | None = None,
                   auth_require_methods: list | None = None,
                   auth_algorithm: str | None = None, auth_qop: str | None = None):
        """Connection Handler with keep-alive and auth support.

        Args:
            conn (socket.socket): Connection Socket
            addr (socket._RetAddress): Connection Socket Return Address
            HOST (str): Specific host to listen on
            PORT (int): Specific port to listen on
            wwwpath (str): Website page data directory
            defaultcontent (str): Default index
            DEBUG (bool): Debug Mode
            keep_alive (bool): Enable HTTP keep-alive
            keep_alive_timeout (int): Keep-alive timeout in seconds
            directory_listing (bool): Enable directory listings
            directory_listing_index_bottom (bool): Put index at bottom of listings
            auth_enabled (bool): Enable HTTP Digest authentication (None = use class default)
            auth_realm (str): Authentication realm (None = use class default)
            auth_users_file (str): Path to .htpasswd file (None = use class default)
            auth_require_methods (list): Methods requiring auth (None = use class default)
            auth_algorithm (str): Digest algorithm (None = use class default)
            auth_qop (str): Quality of protection (None = use class default)
        """
        # Resolve auth config from class attributes if not explicitly provided
        if auth_enabled is None:
            auth_enabled = WebServer.auth_enabled
        if auth_realm is None:
            auth_realm = WebServer.auth_realm
        if auth_users_file is None:
            auth_users_file = WebServer.auth_users_file
        if auth_require_methods is None:
            auth_require_methods = WebServer.auth_require_methods
        if auth_algorithm is None:
            auth_algorithm = WebServer.auth_algorithm
        if auth_qop is None:
            auth_qop = WebServer.auth_qop

        connectiondone: bool = False
        buffer: str = ""
        with conn:
            if keep_alive:
                conn.settimeout(keep_alive_timeout)
            print(f"[{addr[0]}:{addr[1]}]: Connected by {addr[0]}:{addr[1]}")
            while True:
                try:
                    sockdata = conn.recv(4096)
                except socket.timeout:
                    print(f"[{addr[0]}:{addr[1]}]: Keep-alive timeout")
                    break
                if not sockdata:
                    break
                buffer += sockdata.decode(errors="replace")

                # Process complete HTTP requests from buffer
                while "\r\n\r\n" in buffer and not connectiondone:
                    header_end = buffer.find("\r\n\r\n")
                    header_section = buffer[:header_end]
                    body_start = header_end + 4
                    remaining = buffer[body_start:]

                    # Parse the request line
                    lines = header_section.split("\r\n")
                    request_line = lines[0] if lines else ""
                    parts = request_line.split(" ")
                    if len(parts) < 2:
                        conn.send(f"HTTP/1.1 {BAD_REQUEST} {HTTP().getstringfromcode(BAD_REQUEST)}\r\n\r\n".encode())
                        connectiondone = True
                        break

                    httpreqtype = parts[0]
                    raw_path = parts[1] if len(parts) > 1 else "/"

                    # Parse headers
                    headers = {}
                    for line in lines[1:]:
                        if ":" in line:
                            key, val = line.split(":", 1)
                            headers[key.strip().lower()] = val.strip()

                    # Store method for Digest HA2 computation
                    headers["_method"] = httpreqtype

                    query_params: dict | None = None
                    if "?" in raw_path:
                        path, query_string = raw_path.split("?", 1)
                        parsed_qs = parse_qs(query_string)
                        query_params = {k: v[0] if v else "" for k, v in parsed_qs.items()}
                    else:
                        path = raw_path

                    print(f"[{addr[0]}:{addr[1]}]: HTTP Request: {request_line}")

                    form_data: dict | None = None
                    if httpreqtype == POST:
                        content_length = int(headers.get("content-length", "0"))
                        body = remaining
                        while len(body.encode()) < content_length:
                            try:
                                more = conn.recv(4096)
                            except socket.timeout:
                                break
                            if not more:
                                break
                            body += more.decode(errors="replace")
                        form_data = parse_form_data(body)

                    # Handle PUT with raw body + auth
                    if httpreqtype == PUT:
                        content_length = int(headers.get("content-length", "0"))
                        body = remaining
                        while len(body.encode()) < content_length:
                            try:
                                more = conn.recv(4096)
                            except socket.timeout:
                                break
                            if not more:
                                break
                            body += more.decode(errors="replace")

                        # Auth check
                        if (auth_enabled and
                                "PUT" in (auth_require_methods or ["PUT", "DELETE"])):
                            if not self._check_auth(headers, auth_realm, auth_users_file,
                                                    auth_algorithm, auth_qop):
                                extra_headers = self._auth_challenge(
                                    auth_realm, auth_algorithm, auth_qop)
                                err_body = b"Unauthorized"
                                header = self._build_header(
                                    UN_AUTHORIZED, "text/plain", len(err_body),
                                    extra_headers=extra_headers, keep_alive=keep_alive)
                                conn.send(header + err_body)
                                print(f"[{addr[0]}:{addr[1]}]: Auth required for PUT.")
                                if headers.get("connection", "").lower() == "close":
                                    connectiondone = True
                                    break
                                buffer = remaining
                                if not buffer:
                                    break
                                continue

                        success = FileHandling().writefile(
                            f"{wwwpath}/{path}", addr, body.encode(errors="replace"))
                        if success:
                            code = CREATED
                        else:
                            code = INTERNAL_SERVER_ERROR
                        header = self._build_header(code, "text/plain", 0,
                            keep_alive=keep_alive)
                        response_body = b""

                    elif httpreqtype == DELETE:
                        # Auth check
                        if (auth_enabled and
                                "DELETE" in (auth_require_methods or ["PUT", "DELETE"])):
                            if not self._check_auth(headers, auth_realm, auth_users_file,
                                                    auth_algorithm, auth_qop):
                                extra_headers = self._auth_challenge(
                                    auth_realm, auth_algorithm, auth_qop)
                                err_body = b"Unauthorized"
                                header = self._build_header(
                                    UN_AUTHORIZED, "text/plain", len(err_body),
                                    extra_headers=extra_headers, keep_alive=keep_alive)
                                conn.send(header + err_body)
                                print(f"[{addr[0]}:{addr[1]}]: Auth required for DELETE.")
                                if headers.get("connection", "").lower() == "close":
                                    connectiondone = True
                                    break
                                buffer = remaining
                                if not buffer:
                                    break
                                continue

                        header, response_body, extra_headers = self._process_request(
                            path, httpreqtype, addr, wwwpath, defaultcontent, DEBUG,
                            HOST, PORT, form_data=None, query_params=query_params,
                            directory_listing=directory_listing,
                            directory_listing_index_bottom=directory_listing_index_bottom,
                            keep_alive=keep_alive,
                            auth_enabled=auth_enabled, auth_realm=auth_realm,
                            auth_users_file=auth_users_file,
                            auth_require_methods=auth_require_methods,
                            auth_algorithm=auth_algorithm, auth_qop=auth_qop,
                            headers=headers)

                    else:
                        header, response_body, extra_headers = self._process_request(
                            path, httpreqtype, addr, wwwpath, defaultcontent, DEBUG,
                            HOST, PORT, form_data=form_data, query_params=query_params,
                            directory_listing=directory_listing,
                            directory_listing_index_bottom=directory_listing_index_bottom,
                            keep_alive=keep_alive,
                            auth_enabled=auth_enabled, auth_realm=auth_realm,
                            auth_users_file=auth_users_file,
                            auth_require_methods=auth_require_methods,
                            auth_algorithm=auth_algorithm, auth_qop=auth_qop,
                            headers=headers)

                    conn.send(header + response_body)
                    print(f"[{addr[0]}:{addr[1]}]: Done.")

                    # Check if client wants to close
                    if headers.get("connection", "").lower() == "close":
                        connectiondone = True
                        break

                    # Keep remaining data in buffer for next request
                    buffer = remaining
                    if not buffer:
                        break

                if connectiondone:
                    break


def doAppend(hostname: str, port: int, workpath: str, defaultindex: str, debug: bool,
             mime_enable: bool = True, mime_module_type: str = "auto",
             mime_default_type: str = "application/octet-stream",
             restrict_to_workpath: bool = True,
             directory_listing: bool = True,
             directory_listing_index_bottom: bool = True,
             keep_alive: bool = True,
             keep_alive_timeout: int = 5,
             auth_enabled: bool = False,
             auth_realm: str = "MultiServer",
             auth_users_file: str = "./.htpasswd",
             auth_require_methods: list | None = None,
             auth_algorithm: str = "SHA-256",
             auth_qop: str = "auth",
             **kwargs) -> None:
    if auth_require_methods is None:
        auth_require_methods = ["PUT", "DELETE"]
    WebServer.auth_enabled = auth_enabled
    WebServer.auth_realm = auth_realm
    WebServer.auth_users_file = auth_users_file
    WebServer.auth_require_methods = auth_require_methods
    WebServer.auth_algorithm = auth_algorithm
    WebServer.auth_qop = auth_qop


ServerStartup.append(WebServer)
ServerHandling.append(WebServer().handleconn)
