from __future__ import annotations
from datetime import datetime
import platform
import socket
import threading

from HTTPServer_stubs import * # pyright: ignore[reportAssignmentType]

serverstartup = [WebServer().start]

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
	def __init__(self) -> None:
		pass
	def start(self, HOST: str="127.0.0.1", PORT: int=80, wwwpath: str="./www/", defaultcontent: str="index.html", DEBUG: bool=False):
		"""Starts the WebServer."""
		print(f"[{HOST}:{PORT}]: Starting WebServer...")
		sock = Socket().startsocket(HOST, PORT)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		print(f"[{HOST}:{PORT}]: WebServer Ready, waiting for connections...")

		while True:
			conn, addr = sock.accept()
			t = threading.Thread(target=self.handleconn, args=(HOST, PORT, conn, addr, wwwpath, defaultcontent, DEBUG), daemon=True)
			t.start()

	def handleconn(self, HOST: str, PORT: int, conn: socket.socket, addr: socket._RetAddress, wwwpath: str, defaultcontent: str, DEBUG: bool):
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
				testkey: int | None = None
				location: str = "/"

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
								htmlcont, mime, code, iserror = FileHandling().getfile(f"{wwwpath}/{defaultcontent}", addr, forcemime=True, forcemimetype="text/html")
							elif httpreq.split(" ")[1].startswith("/test"):
								print(f"[{addr[0]}:{addr[1]}]: Test URL Detected")
								testkey = int(httpreq.split(" ")[1].split("/")[2])
								print(f"[{addr[0]}:{addr[1]}]: Testing: {testkey}")
								if testkey >= 300:
									print(f"[{addr[0]}:{addr[1]}]: Testing code above 300, assuming error.")
									iserror = True
								htmlcont, mime, code = b"", "", testkey
							else:
								htmlcont, mime, code, iserror = FileHandling().getfile(f"{wwwpath}/{httpreq.split(" ")[1]}", addr)
							if mime and mime.startswith("text/") and htmlcont:
								try: node = HTMLCode(htmlcont.decode())["node:redirect"]
								except ValueError:
									iserror = True
									code = MULTIPLE_CHOICES
								except LookupError:
									pass
								else:
									iserror = True
									code = PERMANENT_REDIRECT if node.node.get("type") == "perm" else TEMPORARY_REDIRECT
									location = node.content
							print(f"[{addr[0]}:{addr[1]}]: Sending data...")
							if iserror != True:
								if mime and mime.startswith("text/"):
									htmlcontpy = PythonHandling().RunPythonInHTML(htmlcont.decode())
									if htmlcontpy:
										htmlcont = htmlcontpy.encode()
								header = (
									f"HTTP/1.1 {code} {HTTP().getstringfromcode(code)}\r\n"
									f"content-type: {mime}\r\n"
									f"content-length: {str(len(htmlcont))}\r\n"
									f"connection: close\r\n"
									f"date: {datetime.today().strftime("%a, %d %b %Y %H:%M:%S %Z")}\r\n"
									f"\r\n"
								).encode()
								conn.send(header + htmlcont)
							else:
								if code == PERMANENT_REDIRECT or code == TEMPORARY_REDIRECT or code == MOVED_PERMANENTLY or code == FOUND:
									if testkey:
										location = "/"
								htmlcode = HTMLCode()
								htmlcode.Node(htmlcode.soup).add("title", inside=htmlcode["node:head"], content=f"{code} {HTTP().getstringfromcode(code)}")
								htmlcode.Node(htmlcode.soup).add("h1", content=f"{HTTP().getstringfromcode(code)}")
								htmlcode.Node(htmlcode.soup).add("p", content=f"You tried viewing the following: {httpreq.split(" ")[1]}")
								htmlcode.Node(htmlcode.soup).add("hr")
								htmlcode.Node(htmlcode.soup).add("p", options={"style": "font-style: italic"}, content=f"WebServer/{WebServer.serverversion} at {HOST} Port {PORT}, Python {platform.python_version()}")
								htmlcont = htmlcode.soup.encode()
								mime = "text/html"
								if code == PERMANENT_REDIRECT or code == TEMPORARY_REDIRECT or code == MOVED_PERMANENTLY or code == FOUND:
									print(f"[{addr[0]}:{addr[1]}]: Redirect detected.")
									header = (
										f"HTTP/1.1 {code} {HTTP().getstringfromcode(code)}\r\n"
										f"content-type: {mime}\r\n"
										f"content-length: {str(len(htmlcont))}\r\n"
										f"connection: close\r\n"
										f"date: {datetime.today().strftime("%a, %d %b %Y %H:%M:%S %Z")}\r\n"
										f"location: {location}\r\n"
										f"\r\n"
									).encode()
								else:
									header = (
										f"HTTP/1.1 {code} {HTTP().getstringfromcode(code)}\r\n"
										f"content-type: {mime}\r\n"
										f"content-length: {str(len(htmlcont))}\r\n"
										f"connection: close\r\n"
										f"date: {datetime.today().strftime("%a, %d %b %Y %H:%M:%S %Z")}\r\n"
										f"\r\n"
									).encode()
								conn.send(header + htmlcont)
								iserror = False
								code = 200
							print(f"[{addr[0]}:{addr[1]}]: Done.")
							connectiondone = True
							break
						elif line == "" and waitforclear == True and httpreqtype == HEAD:
							print(f"[{addr[0]}:{addr[1]}]: HTTP Request: {httpreq.split(" ")}")
							if httpreq.split(" ")[1] == "/":
								htmlcont, mime, code, iserror = FileHandling().getfile(f"{wwwpath}/{defaultcontent}", addr, forcemime=True, forcemimetype="text/html")
							elif httpreq.split(" ")[1].startswith("/test"):
								print(f"[{addr[0]}:{addr[1]}]: Test URL Detected")
								testkey = int(httpreq.split(" ")[1].split("/")[2])
								print(f"[{addr[0]}:{addr[1]}]: Testing: {testkey}")
								if testkey >= 300:
									print(f"[{addr[0]}:{addr[1]}]: Testing code above 300, assuming error.")
									iserror = True
								htmlcont, mime, code = b"", "", testkey
							else:
								htmlcont, mime, code, iserror = FileHandling().getfile(f"{wwwpath}/{httpreq.split(" ")[1]}", addr)
							if mime and mime.startswith("text/") and htmlcont:
								try: node = HTMLCode(htmlcont.decode())["node:redirect"]
								except ValueError:
									iserror = True
									code = MULTIPLE_CHOICES
								except LookupError:
									pass
								else:
									iserror = True
									code = PERMANENT_REDIRECT if node.node.get("type") == "perm" else TEMPORARY_REDIRECT
									location = node.content
							print(f"[{addr[0]}:{addr[1]}]: Sending data...")
							if iserror != True:
								if mime and mime.startswith("text/"):
									htmlcontpy = PythonHandling().RunPythonInHTML(htmlcont.decode())
									if htmlcontpy:
										htmlcont = htmlcontpy.encode()
								header = (
									f"HTTP/1.1 {code} {HTTP().getstringfromcode(code)}\r\n"
									f"content-type: {mime}\r\n"
									f"content-length: {str(len(htmlcont))}\r\n"
									f"connection: close\r\n"
									f"date: {datetime.today().strftime("%a, %d %b %Y %H:%M:%S %Z")}\r\n"
									f"\r\n"
								).encode()
								conn.send(header)
							else:
								if code == PERMANENT_REDIRECT or code == TEMPORARY_REDIRECT or code == MOVED_PERMANENTLY or code == FOUND:
									if testkey:
										location = "/"
								htmlcode = HTMLCode()
								htmlcode.Node(htmlcode.soup).add("title", inside=htmlcode["node:head"], content=f"{code}: {HTTP().getstringfromcode(code)}")
								htmlcode.Node(htmlcode.soup).add("h1", options={"style": "display: flex; justify-content: center; align-items: center;"}, content=f"{code}: {HTTP().getstringfromcode(code)}")
								htmlcode.Node(htmlcode.soup).add("p", content="You tried viewing the following:")
								htmlcode.Node(htmlcode.soup).add("p", options={"style": "display: flex; justify-content: center; align-items: center;"}, content=httpreq.split(" ")[1])
								htmlcont = htmlcode.soup.encode()
								mime = "text/html"
								if code == PERMANENT_REDIRECT or code == TEMPORARY_REDIRECT or code == MOVED_PERMANENTLY or code == FOUND:
									print(f"[{addr[0]}:{addr[1]}]: Redirect detected.")
									header = (
										f"HTTP/1.1 {code} {HTTP().getstringfromcode(code)}\r\n"
										f"content-type: {mime}\r\n"
										f"content-length: {str(len(htmlcont))}\r\n"
										f"connection: close\r\n"
										f"date: {datetime.today().strftime("%a, %d %b %Y %H:%M:%S %Z")}\r\n"
										f"location: {location}\r\n"
										f"\r\n"
									).encode()
								else:
									header = (
										f"HTTP/1.1 {code} {HTTP().getstringfromcode(code)}\r\n"
										f"content-type: {mime}\r\n"
										f"content-length: {str(len(htmlcont))}\r\n"
										f"connection: close\r\n"
										f"date: {datetime.today().strftime("%a, %d %b %Y %H:%M:%S %Z")}\r\n"
										f"\r\n"
									).encode()
								conn.send(header)
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