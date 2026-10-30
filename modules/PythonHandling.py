#    MultiServer - A modular Python3 server
#    Copyright (C) 2026  Oscar Allegro
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

import contextlib
from io import StringIO
import threading
from urllib.parse import parse_qs, unquote
from bs4 import BeautifulSoup
from MultiServer_stubs import FileModHandling, PageModLike
from modules.HTMLCode import HTMLCode


class FormField:
	"""Represents a single HTML form input field."""
	def __init__(self, name, field_type="text", label="", value="",
	             options=None, required=False, css_class=""):
		self.name = name
		self.field_type = field_type
		self.label = label
		self.value = value
		self.options = options or []
		self.required = required
		self.css_class = css_class

	def render(self):
		cls = f' class="{self.css_class}"' if self.css_class else ""
		req = " required" if self.required else ""
		val = f' value="{self.value}"' if self.value else ""

		if self.field_type == "select":
			opts = "".join(
				f'<option value="{o}">{o}</option>' for o in self.options
			)
			return (f'<label for="{self.name}">{self.label}</label>'
					f'<select name="{self.name}"{cls}{req}>{opts}</select>')
		if self.field_type == "textarea":
			return (f'<label for="{self.name}">{self.label}</label>'
					f'<textarea name="{self.name}"{cls}{req}>{self.value}</textarea>')
		if self.field_type in ("radio", "checkbox"):
			items = "".join(
				f'<label><input type="{self.field_type}" name="{self.name}"'
				f' value="{o}"{cls}{req}> {o}</label>' for o in self.options
			)
			return f'<label>{self.label}</label>{items}'
		return (f'<label for="{self.name}">{self.label}</label>'
				f'<input type="{self.field_type}" name="{self.name}"'
				f'{cls}{req}{val}>')


class FormBuilder:
	"""Programmatically builds HTML <form> elements."""
	def __init__(self, form_id="", action="", method="POST", css_class=""):
		self.form_id = form_id
		self.action = action
		self.method = method
		self.css_class = css_class
		self.fields = []

	def add_field(self, field):
		self.fields.append(field)
		return self

	def build(self):
		fid = f' id="{self.form_id}"' if self.form_id else ""
		cls = f' class="{self.css_class}"' if self.css_class else ""
		fields_html = "".join(f.render() for f in self.fields)
		return (
			f'<form action="{self.action}" method="{self.method}"{fid}{cls}>'
			f'{fields_html}'
			f'<button type="submit">Submit</button>'
			f'</form>'
		)


# Predefined form templates
FORM_TEMPLATES = {
	"login": """<form action="/login" method="POST">
  <label for="username">Username</label>
  <input type="text" name="username" required>
  <label for="password">Password</label>
  <input type="password" name="password" required>
  <button type="submit">Login</button>
</form>""",
	"contact": """<form action="/contact" method="POST">
  <label for="name">Name</label>
  <input type="text" name="name" required>
  <label for="email">Email</label>
  <input type="email" name="email" required>
  <label for="message">Message</label>
  <textarea name="message" required></textarea>
  <button type="submit">Send</button>
</form>""",
	"search": """<form action="/search" method="GET">
  <label for="q">Search</label>
  <input type="text" name="q" required>
  <button type="submit">Search</button>
</form>""",
}


def parse_form_data(body):
	"""Parse an application/x-www-form-urlencoded body into a dict."""
	if not body:
		return {}
	parsed = parse_qs(body)
	return {k: v[0] if v else "" for k, v in parsed.items()}


class PythonHandling(PageModLike):
	_exec_lock = threading.Lock()
	def __init__(self) -> None:
		pass
	def modify(self, string: str, form_data: dict | None = None, query_params: dict | None = None) -> str | None:
		html = HTMLCode(string)
		if html.exists("node:python"):
			exec_globals = {"form": {}, "request": {"post": {}, "get": {}}}
			if form_data:
				exec_globals["form"] = form_data
				exec_globals["FORM_DATA"] = form_data
				exec_globals["request"]["post"] = form_data
			if query_params:
				exec_globals["request"]["get"] = query_params
			for i in html.soup.find_all("python"):
				tag = html.TaggedNode(i, html.soup)
				with self._exec_lock:
					PyHTMLOut = StringIO()
					with contextlib.redirect_stdout(PyHTMLOut):
						exec(tag.content, exec_globals)
					final = PyHTMLOut.getvalue()
					PyHTMLOut.close()
				replacement = BeautifulSoup(final, "html.parser")
				tag.node.replace_with(replacement)
			return str(html.soup)
		else:
			return None

	def execute(self, code: str, form_data: dict | None = None, query_params: dict | None = None) -> str:
		"""Execute a full Python script and return its stdout as a string.

		Args:
		    code (str): Python source code to execute.
		    form_data (dict | None): POST form data.
		    query_params (dict | None): GET query string parameters.

		Returns:
		    str: The captured stdout of the executed code.
		"""
		exec_globals = {"form": {}, "request": {"post": {}, "get": {}}}
		if form_data:
			exec_globals["form"] = form_data
			exec_globals["FORM_DATA"] = form_data
			exec_globals["request"]["post"] = form_data
		if query_params:
			exec_globals["request"]["get"] = query_params
		with self._exec_lock:
			PyHTMLOut = StringIO()
			with contextlib.redirect_stdout(PyHTMLOut):
				exec(code, exec_globals)
			final = PyHTMLOut.getvalue()
			PyHTMLOut.close()
		return final

	@staticmethod
	def build_form(form_id="", action="", method="POST", css_class=""):
		return FormBuilder(form_id, action, method, css_class)


def doAppend(hostname: str, port: int, workpath: str, defaultindex: str, debug: bool, **kwargs) -> None:
	pass

FileModHandling.append(PythonHandling) # pyright: ignore[reportArgumentType]
