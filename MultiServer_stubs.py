from __future__ import annotations
from abc import ABC
import socket

import threading
from types import MethodType
from typing import Any, Iterable, Literal, Protocol, SupportsIndex, overload, override, runtime_checkable
from typing_extensions import disjoint_base
from bs4 import BeautifulSoup, Tag

class HandlerBase(ABC):
	def __init__(self, *args, **kwargs) -> None:
		self.args = args
		self.kwargs = kwargs
class ThreadedHandlerBase(HandlerBase):
	def __init__(self, *args, **kwargs) -> None:
		super().__init__(*args, **kwargs)
		self.thread: threading.Thread | None = None
	def run(self) -> None:
		raise NotImplementedError
	def start(self) -> threading.Thread:
		self.thread = threading.Thread(target=self.run, daemon=True)
		self.thread.start()
		return self.thread
class TransportHandler(ThreadedHandlerBase):
	def __init__(self, opener: MethodType, HOST: str, PORT: int, on_connection: MethodType | list[Any], extraargs: tuple | None = None):
		super().__init__()
		self.opener = opener
		self.HOST, self.PORT = HOST, PORT
		self.on_connection = on_connection
		self.extraargs = extraargs
	def run(self) -> None:
		sock = self.opener(self.HOST, self.PORT)
		print(f"[{self.HOST}:{self.PORT}]: Listening...")
		services = []
		if isinstance(self.on_connection, list):
			for i in self.on_connection:
				service = threading.Thread(target=self.runsub, args=(sock, i), daemon=True)
				service.start()
				services.append(service)
			try:
				for i in services:
					i.join()
			except KeyboardInterrupt:
				print("Shutting Down...")
		else:
			service = threading.Thread(target=self.runsub, args=(sock, self.on_connection), daemon=True)
			service.start()
			services.append(service)
			try:
				for i in services:
					i.join()
			except KeyboardInterrupt:
				print("Shutting Down...")
	def runsub(self, sock, service):
		while True:
			conn, addr = sock.accept()
			print(f"{conn}, {addr}")
			if self.extraargs:
				args = (conn, addr) + self.extraargs
			else:
				args = (conn, addr)
			threading.Thread(target=service, args=args, daemon=True).start()

class DictWithHeader:
	"""
	List-based dict with a bytes header.
	Setting an item sets the dict key (if key not is none), otherwise set the header.
	Getting an item gets the dict key (if key is str), otherwise it chooses based on the Literal:
	 * `NoneDict`: gets the whole Dictionary object;
	 * `NoneHeader`: gets the whole Bytes object;
	 * `NoneSimple`: returns both objects in a simple format as str;
	 * `NoneHTTP`: returns both objects in the HTTP format as bytes.

	Self is not defined as list, so you can't use this as a normal list unless you specify `DictWithHeader().dhlist`
	"""
	def __init__(self) -> None:
		self.dhlist = list()
		self.dhlist.append(str())
		self.dhlist.append(dict())
	def __getitem__(self, key: str | Literal["NoneDict", "NoneHeader", "NoneSimple", "NoneHTTP"]) -> Any:
		"""
		Returns `self.dhlist[key]` if `key` is `str`, otherwise return based on the Literal:
		```
		Literal["NoneDict", "NoneHeader", "NoneSimple", "NoneHTTP"]
		```
		"""
		whole: str | bytes
		if key == "NoneHeader":
			return self.dhlist[0]
		elif key == "NoneDict":
			return self.dhlist[1]
		elif key == "NoneSimple":
			whole = f"header={self.dhlist[0]}\r\n"
			for i, b in self.dhlist[1].items():
				whole += f"{i}={b}\r\n"
			return whole
		elif key == "NoneHTTP":
			whole = f"{self.dhlist[0]}\r\n"
			for i, b in self.dhlist[1].items():
				whole += f"{i}: {b}\r\n"
			whole += "\r\n"
			return whole.encode()
		return self.dhlist[1][key]
	def __setitem__(self, key: str | None, value: str | Any) -> None:
		if key is None:
			if not isinstance(value, str):
				raise TypeError(f"Header status line must be str, got {type(value).__name__}")
			self.dhlist[0] = value
		elif isinstance(key, str):
			self.dhlist[1][key] = value

# Reserved for future use. (TODO)
ServerStartup: list[MethodType | type] = []
ServerHandling: list[MethodType] = []
ConnHandling: list[TransportHandler] = []
GetFileHandling: list[MethodType] = []
FileModHandling: list[MethodType] = []
HeaderHandling: list[MethodType] = []
ErrorHandling: list[MethodType] = []
ErrorPageHandling: list[MethodType] = []

@runtime_checkable
class ConnectionLike(Protocol):
	def recv(self, sock: Any, bufsize: int) -> bytes: ...
	def send(self, sock: socket.socket, data: bytes) -> int: ...
@runtime_checkable
class FileLike(Protocol):
	def getfile(self, filename: str, addr: Any) -> tuple[Any, ...]: ...
	def writefile(self, filename: str, addr: Any) -> bool: ...
@runtime_checkable
class PageModLike(Protocol):
	def modify(self, string: str) -> str | None: ...

@disjoint_base
class WebServer:
	def __init__(self) -> None: ...
	def start(self, HOST: str="127.0.0.1", PORT: int=80, wwwpath: str="./www/", defaultcontent: str="index.html", DEBUG: bool=False): ...
	def handleconn(self, HOST: str, PORT: int, conn: socket.socket, addr: Any, wwwpath: str, defaultcontent: str, DEBUG: bool): ...
@disjoint_base
class FileHandling:
	filecont = bytes
	mimetype = str | None
	returncode = int
	iserror = bool
	def __init__(self) -> None: ...
	def getfile(self, filename: str, addr: Any, forcemime: bool = False, forcemimetype: str = "") -> tuple[filecont, mimetype, returncode, iserror]: ...
@disjoint_base
class HTMLCode:
	def __init__(self, html: str | None = None, /) -> None:
		self.soup = BeautifulSoup()
		...
	def _parse_query(self, query: str) -> list: ...
	def __getitem__(self, query: str, /) -> HTMLCode.TaggedNode: ...
	def __setitem__(self, query: str, value: dict): ...
	def exists(self, query: str) -> bool: ...
	class Node():
		def __init__(self, ownersoup: BeautifulSoup, /) -> None: ...
		def add(self, name: str, options: dict | None = None, content: str | None = None, inside: HTMLCode.TaggedNode | Literal[None, "none"] | None = None, before: HTMLCode.TaggedNode | None = None, after: HTMLCode.TaggedNode | None = None) -> HTMLCode.TaggedNode: ...
		def add_doctype(self, name: str = "html") -> None: ...
	class TaggedNode():
		def __init__(self, node: Tag, owner_soup: BeautifulSoup, /) -> None:
			self.node = node
			self.soup = owner_soup
			self.content = ""
			...
		def modify(self, name: str | None = None, options: dict | None = None, content: str | None = None): ...
		def delete(self): ...
@disjoint_base
class HTTP:
	REASON = {...}
	def getstringfromcode(self, code: int) -> str: ...
	def getcodefromstring(self, string: str) -> None | int: ...
@disjoint_base
class PythonHandling:
	def __init__(self) -> None: ...
	def RunPythonInHTML(self, string: str) -> str | None: ...
@disjoint_base
class Socket:
	def __init__(self) -> None: ...
	def startsocket(self, HOST: str="", PORT: int=80) -> socket.socket: ...