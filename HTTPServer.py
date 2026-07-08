from __future__ import annotations
import contextlib
from io import StringIO
import socket
from pathlib import Path
import threading
from typing import Literal
from bs4 import BeautifulSoup, Doctype, Tag
import magic
import mimetypes

# HTTP Methods
CONNECT="CONNECT"
DELETE="DELETE"
GET="GET"
HEAD="HEAD"
OPTIONS="OPTIONS"
POST="POST"
PUT="PUT"

# Info Responses
CONTINUE=100
SWITCH_PROTOCOL=101
EARLY_HINTS=103

# Successful Responses
OK=200
CREATED=201
ACCEPTED=202
NON_AUTHORITATIVE_INFO=203
NO_CONTENT=204
RESET_CONTENT=205
PARTIAL_CONTENT=206
IM_USED=226

# Redirect Responses
MULTIPLE_CHOICES=300
MOVED_PERMANENTLY=301
FOUND=302
SEE_OTHER=303
NOT_MODIFIED=304
TEMPORARY_REDIRECT=307
PERMANENT_REDIRECT=308

# Client Error Responses
BAD_REQUEST=400
UN_AUTHORIZED=401
PAYMENT_REQUIRED=402
FORBIDDEN=403
NOT_FOUND=404
METHOD_NOT_ALLOWED=405
NOT_ACCEPTABLE=406
PROXY_AUTHENTICATION_REQUIRED=407
REQUEST_TIMEOUT=408
CONFLICT=409
GONE=410
LENGTH_REQUIRED=411
PRECONDITION_FAILED=412
CONTENT_TOO_LARGE=413
URI_TOO_LONG=414
UNSUPPORTED_MEDIA_TYPE=415
RANGE_NOT_SATISFIABLE=416
EXPECTATION_FAILED=417
TEAPOT=418
MISDIRECTED_REQUEST=421
UPGRADE_REQUIRED=426
PRECONDITION_REQUIRED=428
TOO_MANY_REQUESTS=429
REQUEST_HEADER_FIELDS_TOO_LARGE=431

# Server Error Responses
INTERNAL_SERVER_ERROR=500
NOT_IMPLEMENTED=501
BAD_GATEWAY=502
SERVICE_UNAVAILABLE=503
GATEWAY_TIMEOUT=504
HTTP_VERSION_NOT_SUPPORTED=505
VARIANT_ALSO_NEGOTIATES=506
NOT_EXTENDED=510
NETWORK_AUTHENTICATION_REQUIRED=511

class HTTP:
	REASON = {
		# Info Responses
		100: "Continue",
		101: "Switch Protocol",
		102: "Processing",
		103: "Early Hints",
		# Successful Responses
		200: "OK",
		201: "Created",
		202: "Accepted",
		203: "Non-Authoritative Information",
		204: "No Content",
		205: "Reset Content",
		206: "Partial Content",
		207: "Multi-Status",
		208: "Already Reported",
		226: "IM Used",
		# Redirect Responses
		300: "Multiple Choices",
		301: "Moved Permanently",
		302: "Found",
		303: "See Other",
		304: "Not Modified",
		305: "Use Proxy",
		306: "",
		307: "Temporary Redirect",
		308: "Permanent Redirect",
		# Client Error Responses
		400: "Bad Request",
		401: "Unauthorized",
		402: "Payment Required",
		403: "Forbidden",
		404: "Not Found",
		405: "Method Not Allowed",
		406: "Not Acceptable",
		407: "Proxy Authentication Required",
		408: "Request Timeout",
		409: "Conflict",
		410: "Gone",
		411: "Length Required",
		412: "Precondition Failed",
		413: "Content Too Large",
		414: "URI Too Long",
		416: "Range Not Satisfiable",
		417: "Expectation Failed",
		418: "I'm a teapot",
		421: "Misdirected Request",
		422: "Unprocessable Content",
		423: "Locked",
		424: "Failed Dependency",
		425: "Too Early",
		426: "Upgrade Required",
		428: "Precondition Required",
		429: "Too Many Requests",
		431: "Request Header Fields Too Large",
		451: "Unavailable For Legal Reasons",
		# Server Error Responses
		500: "Internal Server Error",
		501: "Not Implemented",
		502: "Bad Gateway",
		503: "Service Unavailable",
		504: "Gateway Timeout",
		505: "HTTP Version Not Supported",
		506: "Variants Also Negotiates",
		507: "Insufficient Storage",
		508: "Loop Detected",
		510: "Not Extended", 
		511: "Network Authentication Required"
	}

	def getstringfromcode(self, code: int) -> str:
		return self.REASON[code]
	def getcodefromstring(self, string: str) -> None | int:
		for code, reason in self.REASON.items():
			if reason.lower() == string.lower():
				return code
		return None

class HTMLCode:
	"""
	HTMLCode Type
	"""
	def __init__(self, html: str | None = None, /) -> None:
		if html is None: html = """<html>
<head>
</head>
<body>
</body>
</html>"""
		self.soup = BeautifulSoup(html, "html.parser")

	def _parse_query(self, query: str) -> list:
		options = query.split(";")
		tag_name = None
		attr = {}
		count = None
		html_classes: list = []
		html_id = None
		for i in options:
			if i.startswith("node:"):
				tag_name = i.split(":")[1]
			if i.startswith("class:"):
				html_classes.append(i.split(":")[1])
			if i.startswith("id:"):
				html_id = i.split(":")[1]
			if i.startswith("count:"):
				count = int(i.split(":")[1])
		if html_classes:
			attr["class"] = html_classes
		if html_id:
			attr["id"] = html_id
		if count is not None and count < 1:
			raise ValueError(f"Specified count ({count}) is less than 1")
		return [tag_name, attr, count]

	def __getitem__(self, query: str, /) -> HTMLCode.TaggedNode:
		tag_name, attrs, count = self._parse_query(query)
		matches = self.soup.find_all(tag_name, attrs=attrs)
		if count is None:
			if len(matches) > 1:
				raise ValueError(f"Ambiguous query {query!r}: {len(matches)} matches, specify count")
			if not matches:
				raise LookupError(f"No node matches query {query!r}")
			return HTMLCode.TaggedNode(matches[0], self.soup)
		else:
			return HTMLCode.TaggedNode(matches[count - 1], self.soup)
	
	def __setitem__(self, query: str, value: dict):
		tag = self[query]
		name: None = None
		content: None = None
		options: dict = {}
		for i, b in value.items():
			if i == "__name__":
				name = b
			elif i == "_content":
				content = b
			else:
				options.update({i: b})
		print(f"_name: {name}, _content: {content}, _options: {options}")
		tag.modify(name=name, options=options,content=content)

	def exists(self, query: str) -> bool:
		try:
			self[query]
		except ValueError:
			return True
		except LookupError:
			return False
		else:
			return True

	class Node():
		def __init__(self, ownersoup: BeautifulSoup, /) -> None:
			self.soup = ownersoup

		def add(self, name: str, options: dict | None = None, content: str | None = None, inside: HTMLCode.TaggedNode | Literal[None, "none"] | None = None, before: HTMLCode.TaggedNode | None = None, after: HTMLCode.TaggedNode | None = None) -> HTMLCode.TaggedNode:
			if options is None: options = dict()
			node = self.soup.new_tag(name, attrs=options, string=content)
			if isinstance(inside, HTMLCode.TaggedNode):
				inside.node.append(node)
			elif inside == "none":
				self.soup.append(node)
			else:
				self.soup.html.body.append(node) # pyright: ignore[reportOptionalMemberAccess]
			if before:
				before.node.insert_before(node)
			if after:
				after.node.insert_after(node)
			return HTMLCode.TaggedNode(node, self.soup)
		
		def add_doctype(self, name: str = "html") -> None:
			doctype = Doctype.for_name_and_ids(name, None, None)
			self.soup.insert(0, doctype)

	class TaggedNode():
		def __init__(self, node: Tag, owner_soup: BeautifulSoup, /) -> None:
			self.node = node
			self.soup = owner_soup
			self.content = ""
			for i in self.node.contents: self.content = self.content + str(i)

		def modify(self, name: str | None = None, options: dict | None = None, content: str | None = None):
			"""Modify the node to have new values."""
			if not name and not options and not content:
				raise SyntaxError("You must at least provide one argument.")
			if name: self.node.name = name
			if content is not None: self.node.string = content
			if options:
				for i in options:
					self.node[i] = str(options[i])

		def delete(self):
			self.node.decompose()

class WebServer:
	"""
	Simple web server
	"""
	def __init__(self) -> None:
		pass
	def start(self, HOST: str="127.0.0.1", PORT: int=80, wwwpath: str="./www/", defaultcontent: str="index.html", DEBUG: bool=False):
		"""Starts the WebServer."""
		print(f"[{HOST}:{PORT}]: Starting WebServer...")
		sock = self.Socket().startsocket(HOST, PORT)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		print(f"[{HOST}:{PORT}]: WebServer Ready, waiting for connections...")

		while True:
			conn, addr = sock.accept()
			t = threading.Thread(target=self.handleconn, args=(conn, addr, wwwpath, defaultcontent, DEBUG), daemon=True)
			t.start()

	def handleconn(self, conn: socket.socket, addr: socket._RetAddress, wwwpath: str, defaultcontent: str, DEBUG: bool):
		connectiondone: bool = False
		with conn:
			print(f"[{addr[0]}:{addr[1]}]: Connected by {addr[0]}:{addr[1]}")
			while True:
				sockdata = conn.recv(4096)
				if not sockdata: break

				waitforclear: bool = False
				httpreq: str = ""
				httpreqtype: str = ""
				iserror: bool = False
				htmlcont: bytes = b""

				try: sockdata.decode()
				except:
					print(f"[{addr[0]}:{addr[1]}]: Error in header!!!")
					connectiondone = True
				if connectiondone != True:
					for line in sockdata.decode().splitlines():
						if DEBUG: print(f"[DEBUG]: {line}")
						if line.startswith(GET):
							httpreq = line
							waitforclear = True
							httpreqtype = GET
						elif line.startswith(HEAD):
							httpreq = line
							waitforclear = True
							httpreqtype = HEAD
						if line == "" and waitforclear == True and httpreqtype == GET:
							print(f"[{addr[0]}:{addr[1]}]: HTTP Request: {httpreq.split(" ")}")
							if httpreq.split(" ")[1] == "/":
								htmlcont, mime, code, iserror = self.FileHandling().getfile(f"{wwwpath}/{defaultcontent}", addr, forcemime=True, forcemimetype="text/html")
							else:
								htmlcont, mime, code, iserror = self.FileHandling().getfile(f"{wwwpath}/{httpreq.split(" ")[1]}", addr)
							print(f"[{addr[0]}:{addr[1]}]: Sending data...")
							if iserror != True:
								header = (
									f"HTTP/1.1 {code} {HTTP().getstringfromcode(code)}\r\n"
									f"content-type: {mime}\r\n"
									f"content-length: {str(len(htmlcont))}\r\n"
									f"\r\n"
								).encode()
								if mime and mime.startswith("text/"):
									htmlcontpy = self.PythonHandling().RunPythonInHTML(htmlcont.decode())
									if htmlcontpy:
										htmlcont = htmlcontpy.encode()
								conn.send(header + htmlcont)
							else:
								conn.send(f"HTTP/1.1 {code} {HTTP().getstringfromcode(code)}".encode())
								iserror = False
								code = 200
							print(f"[{addr[0]}:{addr[1]}]: Done.")
							connectiondone = True
							break
						elif line == "" and waitforclear == False and httpreqtype == "":
							print(f"[{addr[0]}:{addr[1]}]: ERROR!!! Invalid HTTP Request!!!")
							conn.send(f"HTTP/1.1 {NOT_IMPLEMENTED} {HTTP().getstringfromcode(NOT_IMPLEMENTED)}".encode())
							connectiondone = True
				if connectiondone == True: break

	class PythonHandling:
		_exec_lock = threading.Lock()
		def __init__(self) -> None:
			pass
		def RunPythonInHTML(self, string: str) -> str:
			html = HTMLCode(string)
			if html.exists("node:python"):
				for i in html.soup.find_all("python"):
					tag = html.TaggedNode(i, html.soup)
					with self._exec_lock:
						PyHTMLOut = StringIO()
						with contextlib.redirect_stdout(PyHTMLOut):
							exec(tag.content)
						final = PyHTMLOut.getvalue()
						PyHTMLOut.close()
					replacement = BeautifulSoup(final, "html.parser")
					tag.node.replace_with(replacement)
			return str(html.soup)
	class FileHandling:
		filecont = bytes
		mimetype = str | None
		returncode = int
		iserror = bool
		def __init__(self) -> None:
			pass
		def getfile(self, filename: str, addr: socket._RetAddress, forcemime: bool = False, forcemimetype: str = "") -> tuple[filecont, mimetype, returncode, iserror]:
			filemime: str = ""
			mime: None | str = "application/octet-stream"
			try: filecont = open(Path(f"{filename}"), "rb").read()
			except FileNotFoundError:
				print(f"[{addr[0]}:{addr[1]}]: File not found: {filename}")
				return (b"", "", NOT_FOUND, True)
			except OSError:
				print(f"[{addr[0]}:{addr[1]}]: Could not open file: {filename}")
				return (b"", "", FORBIDDEN, True)
			except:
				print(f"[{addr[0]}:{addr[1]}]: Unknown error trying to open file: {filename}")
				return (b"", "", INTERNAL_SERVER_ERROR, True)
			else:
				if not forcemime:
					filemimesec = mimetypes.guess_file_type(Path(f"{filename}"))
					try: filemime = magic.from_file(Path(f"{filename}"), mime=True)
					except Exception: pass
	
					if filemimesec: mime = filemimesec[0]
					elif filemime: mime = filemime
				else:
					mime = forcemimetype
			return (filecont, mime, OK, False)
	class Socket:
		"""WebServer Socket Class"""
		def __init__(self) -> None:
			pass
		def startsocket(self, HOST: str="", PORT: int=80) -> socket.socket:
			"""
			Starts a socket for streaming data with.
			"""
			print(f"[{HOST}:{PORT}]: Opening socket...")
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.bind((HOST, PORT))
			s.listen(5)
			print(f"[{HOST}:{PORT}]: Socket opened.")
			return s