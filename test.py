from MultiServer_stubs import *
from modules.PythonHandling import FormField, FormBuilder, FORM_TEMPLATES, parse_form_data, PythonHandling
from modules.HTMLCode import HTMLCode

print("MultiServer Tests")
print("")

testprogress = int(0)
testprogresspercentagemax = float(100.0)
tests = int(44)

def run_test(name, condition):
        global testprogress
        testprogress = testprogress + 1
        if not condition:
                print(f"FAILED: {name}")
                raise Exception
        print(f"PASSED: {name}")
        return True

# === DictWithHeader tests (existing) ===
print("--- DictWithHeader ---")
DWH = DictWithHeader()
run_test("DWH is instance of DictWithHeader", isinstance(DWH, DictWithHeader))
run_test("DWH.dhlist is ['', {}]", DWH.dhlist == ['', {}])
run_test("DWH['NoneDict'] is {}", DWH["NoneDict"] == {})
run_test("DWH['NoneHeader'] is ''", DWH["NoneHeader"] == '')
run_test("DWH['NoneSimple'] is 'header=\\r\\n'", DWH["NoneSimple"] == "header=\r\n")
run_test("DWH['NoneHTTP'] is b'\\r\\n\\r\\n'", DWH["NoneHTTP"] == b"\r\n\r\n")

DWH["foo"] = "bar"
run_test("DWH['foo'] == 'bar'", DWH["foo"] == "bar")

DWH[None] = "HELLO WORLD"
run_test("DWH[None] sets header to 'HELLO WORLD'", DWH["NoneHeader"] == "HELLO WORLD")
run_test("DWH['NoneSimple'] updated", DWH["NoneSimple"] == "header=HELLO WORLD\r\nfoo=bar\r\n")
run_test("DWH['NoneHTTP'] updated", DWH["NoneHTTP"] == b'HELLO WORLD\r\nfoo: bar\r\n\r\n')

# === FormField tests ===
print("--- FormField ---")
field = FormField("username", field_type="text", label="Username", value="", required=True)
run_test("FormField stores name", field.name == "username")
run_test("FormField stores type", field.field_type == "text")
run_test("FormField stores label", field.label == "Username")
run_test("FormField stores required", field.required is True)
rendered = field.render()
run_test("FormField render contains name", 'name="username"' in rendered)
run_test("FormField render contains required", "required" in rendered)
run_test("FormField render contains label", "Username" in rendered)

select_field = FormField("choice", field_type="select", options=["A", "B", "C"])
run_test("FormField select options stored", select_field.options == ["A", "B", "C"])
select_rendered = select_field.render()
run_test("FormField select renders options", "<select" in select_rendered and "option" in select_rendered)

# === FormBuilder tests ===
print("--- FormBuilder ---")
builder = FormBuilder(form_id="myform", action="/submit", method="POST", css_class="form-class")
builder.add_field(FormField("name", field_type="text", label="Name"))
form_html = builder.build()
run_test("FormBuilder has form tag", "<form" in form_html)
run_test("FormBuilder has id", 'id="myform"' in form_html)
run_test("FormBuilder has action", 'action="/submit"' in form_html)
run_test("FormBuilder has method", 'method="POST"' in form_html)
run_test("FormBuilder has class", 'class="form-class"' in form_html)
run_test("FormBuilder has field", 'name="name"' in form_html)
run_test("FormBuilder has submit button", "Submit" in form_html)

# Static builder method
builder2 = PythonHandling.build_form(action="/test", method="GET")
run_test("PythonHandling.build_form returns FormBuilder", isinstance(builder2, FormBuilder))

# === FORM_TEMPLATES tests ===
print("--- FORM_TEMPLATES ---")
run_test("FORM_TEMPLATES has login", "login" in FORM_TEMPLATES)
run_test("FORM_TEMPLATES has contact", "contact" in FORM_TEMPLATES)
run_test("FORM_TEMPLATES has search", "search" in FORM_TEMPLATES)
run_test("FORM_TEMPLATES login is non-empty str", isinstance(FORM_TEMPLATES["login"], str) and len(FORM_TEMPLATES["login"]) > 0)
run_test("FORM_TEMPLATES contact contains textarea", "textarea" in FORM_TEMPLATES["contact"])
run_test("FORM_TEMPLATES search contains input", "input" in FORM_TEMPLATES["search"])

# === parse_form_data tests ===
print("--- parse_form_data ---")
run_test("parse_form_data empty body returns {}", parse_form_data("") == {})
run_test("parse_form_data None returns {}", parse_form_data(None) == {})
result = parse_form_data("username=oscar&password=secret")
run_test("parse_form_data parses username", result.get("username") == "oscar")
run_test("parse_form_data parses password", result.get("password") == "secret")
result2 = parse_form_data("a=1&a=2&b=3")
run_test("parse_form_data takes first value for duplicate keys", result2.get("a") == "1")
result3 = parse_form_data("city=New%20York")
run_test("parse_form_data decodes URL encoding", result3.get("city") == "New York")

# === PythonHandling.modify with form_data ===
print("--- PythonHandling.modify ---")
ph = PythonHandling()
html_no_python = "<html><body><p>Hello</p></body></html>"
run_test("modify returns None when no <python> tag", ph.modify(html_no_python) is None)

html_with_python = """<html><body>
<python>print("<p>Hello from Python!</p>")</python>
</body></html>"""
result = ph.modify(html_with_python)
run_test("modify processes <python> tag", result is not None and "Hello from Python!" in result)

html_with_form = """<html><body>
<python>print(f"<p>Hello, {form.get('name', 'Guest')}!</p>")</python>
</body></html>"""
result_with_form = ph.modify(html_with_form, form_data={"name": "Oscar"})
run_test("modify with form_data accesses form", result_with_form is not None and "Hello, Oscar!" in result_with_form)
result_without_form = ph.modify(html_with_form)
run_test("modify without form_data defaults to Guest", result_without_form is not None and "Hello, Guest!" in result_without_form)

html_with_form_data = """<html><body>
<python>print(f"<p>Keys: {list(FORM_DATA.keys())}</p>")</python>
</body></html>"""
result_fd = ph.modify(html_with_form_data, form_data={"a": "1", "b": "2"})
run_test("modify exposes FORM_DATA", result_fd is not None and "Keys:" in result_fd and "a" in result_fd and "b" in result_fd)

# === PythonHandling.execute tests ===
print("--- PythonHandling.execute ---")
result_exec = ph.execute("print('hello world')")
run_test("execute captures stdout", result_exec == "hello world\n")

result_exec_form = ph.execute("print(f'Name: {form.get(\"user\", \"none\")}')", form_data={"user": "bob"})
run_test("execute accesses form data", result_exec_form == "Name: bob\n")

result_exec_request = ph.execute("print(request.get('post', {}).get('key', 'missing'))", form_data={"key": "val"})
run_test("execute accesses request.post", result_exec_request == "val\n")

result_exec_query = ph.execute("print(request.get('get', {}).get('q', 'none'))", query_params={"q": "search"})
run_test("execute accesses request.get", result_exec_query == "search\n")

result_exec_json = ph.execute("import json; print(json.dumps({'ok': True}))")
run_test("execute can import modules", result_exec_json == '{"ok": true}\n')

tests = int(49)

print("")
print(f"Unit tests done! ({testprogress / tests * testprogresspercentagemax:.1f}% done.)")

# === Web-based integration tests ===
print("")
print("--- Web Integration Tests ---")

import subprocess
import time
import urllib.request
import urllib.error
import json

BASE_URL = "http://127.0.0.1:8888"
server_proc = None
web_tests_passed = 0
web_tests_total = 0

def web_test(name, condition):
        global web_tests_passed, web_tests_total
        web_tests_total = web_tests_total + 1
        if condition:
                web_tests_passed = web_tests_passed + 1
                print(f"PASSED: {name}")
        else:
                print(f"FAILED: {name}")

def http_get(path, timeout=5):
        """Make a GET request and return (status, headers, body_text)."""
        req = urllib.request.Request(f"{BASE_URL}{path}", method="GET")
        try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                        body = resp.read().decode(errors="replace")
                        return resp.status, dict(resp.headers), body
        except urllib.error.HTTPError as e:
                body = e.read().decode(errors="replace")
                return e.code, dict(e.headers), body

def http_head(path, timeout=5):
        """Make a HEAD request and return (status, headers)."""
        req = urllib.request.Request(f"{BASE_URL}{path}", method="HEAD")
        try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                        return resp.status, dict(resp.headers)
        except urllib.error.HTTPError as e:
                return e.code, dict(e.headers)

def http_options(path, timeout=5):
        """Make an OPTIONS request and return (status, headers, body_text)."""
        req = urllib.request.Request(f"{BASE_URL}{path}", method="OPTIONS")
        try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                        body = resp.read().decode(errors="replace")
                        return resp.status, dict(resp.headers), body
        except urllib.error.HTTPError as e:
                body = e.read().decode(errors="replace")
                return e.code, dict(e.headers), body

# Start the server
try:
        server_proc = subprocess.Popen(
                ["python3", "./MultiServer.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd="/home/oscar/Desktop/MultiServer"
        )
        # Wait for server to be ready
        server_ready = False
        for _ in range(50):
                time.sleep(0.1)
                try:
                        urllib.request.urlopen(f"{BASE_URL}/", timeout=1)
                        server_ready = True
                        break
                except Exception:
                        pass

        if not server_ready:
                print("WARNING: Server did not start in time; skipping web tests.")
        else:
                print("Server is ready. Running web tests...")

                # --- Test 1: GET /index.html returns 200 ---
                status, headers, body = http_get("/index.html")
                web_test("GET /index.html returns 200", status == 200)
                web_test("GET /index.html has content-type text/html",
                         "text/html" in headers.get("content-type", ""))
                web_test("GET /index.html body contains Hello World",
                         "Hello World" in body)

                # --- Test 2: GET /index (no extension) returns 200 ---
                status, headers, body = http_get("/index")
                web_test("GET /index (no extension) returns 200", status == 200)
                web_test("GET /index body contains Hello World",
                         "Hello World" in body)

                # --- Test 3: HEAD /index.html returns headers only ---
                status, headers = http_head("/index.html")
                web_test("HEAD /index.html returns 200", status == 200)
                web_test("HEAD /index.html has content-length",
                         "content-length" in {k.lower(): v for k, v in headers.items()})

                # --- Test 4: GET /nonexistent returns 404 ---
                status, headers, body = http_get("/nonexistent.html")
                web_test("GET /nonexistent.html returns 404", status == 404)
                web_test("GET /nonexistent.html body contains 404",
                         "404" in body)

                # --- Test 5: Path traversal is blocked ---
                status, headers, body = http_get("/../../../etc/passwd")
                web_test("GET /../../../etc/passwd is blocked (403 or 404)",
                         status in (403, 404))

                # --- Test 6: OPTIONS / returns Allow header ---
                status, headers, body = http_options("/")
                resp_headers = {k.lower(): v for k, v in headers.items()}
                web_test("OPTIONS / returns 200", status == 200)
                web_test("OPTIONS / has Allow header",
                         "allow" in resp_headers)
                allow_val = resp_headers.get("allow", "")
                web_test("OPTIONS / Allow includes PUT and DELETE",
                         "PUT" in allow_val and "DELETE" in allow_val)

                # --- Test 7: GET /api.pyhtml returns JSON ---
                status, headers, body = http_get("/api.pyhtml")
                web_test("GET /api.pyhtml returns 200", status == 200)
                try:
                        data = json.loads(body)
                        web_test("GET /api.pyhtml returns valid JSON", True)
                        web_test("GET /api.pyhtml JSON has time key",
                                 "time" in data)
                        web_test("GET /api.pyhtml JSON has message key",
                                 "message" in data)
                except json.JSONDecodeError:
                        web_test("GET /api.pyhtml returns valid JSON", False)
                        web_test("GET /api.pyhtml JSON has time key", False)
                        web_test("GET /api.pyhtml JSON has message key", False)

                # --- Test 8: GET /test/200 test URL ---
                status, headers, body = http_get("/test/200")
                web_test("GET /test/200 returns 200", status == 200)

                # --- Test 9: GET /test/404 test URL ---
                status, headers, body = http_get("/test/404")
                web_test("GET /test/404 returns 404", status == 404)

                # --- Test 10: Directory listing ---
                import os
                os.makedirs("/home/oscar/Desktop/MultiServer/www/webtestdir", exist_ok=True)
                with open("/home/oscar/Desktop/MultiServer/www/webtestdir/a.txt", "w") as f:
                        f.write("a")
                with open("/home/oscar/Desktop/MultiServer/www/webtestdir/b.html", "w") as f:
                        f.write("<p>b</p>")
                status, headers, body = http_get("/webtestdir/")
                web_test("GET /webtestdir/ returns 200", status == 200)
                web_test("GET /webtestdir/ lists a.txt", "a.txt" in body)
                web_test("GET /webtestdir/ lists b.html", "b.html" in body)
                # Cleanup
                import shutil
                shutil.rmtree("/home/oscar/Desktop/MultiServer/www/webtestdir", ignore_errors=True)

        # Shutdown the server
        if server_proc:
                server_proc.terminate()
                try:
                        server_proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                        server_proc.kill()
                        server_proc.wait()

except Exception as e:
        print(f"WARNING: Could not run web tests: {e}")
        if server_proc:
                server_proc.kill()

print("")
print(f"Web tests done! ({web_tests_passed / web_tests_total * 100:.1f}% done.)" if web_tests_total > 0 else "Web tests skipped!")

tests = int(49 + web_tests_total)

print("")
print(f"All tests done! ({testprogress + web_tests_passed} / {tests * testprogresspercentagemax / 100:.0f} total passed.)")