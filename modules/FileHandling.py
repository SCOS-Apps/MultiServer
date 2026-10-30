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

import mimetypes
import socket
from typing import Any, Literal
import magic
from pathlib import Path

from MultiServer_stubs import FileLike, GetFileHandling
from modules.HTTP import *

class FileHandling(FileLike):
	"""File Handling Class
	"""
	filecont = bytes
	mimetype = str | None
	returncode = int
	iserror = bool

	workpath: str = "./www"
	mime_enable: bool = True
	mime_module_type: str = "auto"
	mime_default_type: str = "application/octet-stream"
	restrict_to_workpath: bool = True
	directory_listing: bool = True
	directory_listing_index_bottom: bool = True

	def __init__(self) -> None:
		pass

	def _sanitize_filename(self, filename: str) -> str | None:
		"""Strip workpath prefix if present, then ensure path stays within workpath."""
		clean = filename
		if self.workpath and clean.startswith(self.workpath):
			clean = clean[len(self.workpath):].lstrip("/")
		if not clean:
			clean = "index.html"
		if ".." in Path(clean).parts:
			return None
		base = Path(self.workpath).resolve()
		target = (base / clean).resolve()
		try:
			target.relative_to(base)
		except ValueError:
			return None
		return str(target)

	def _resolve_path(self, filename: str) -> str | None:
		"""Resolve and sanitize a path, returning the absolute path or None if invalid."""
		if self.restrict_to_workpath:
			return self._sanitize_filename(filename)
		return filename

	def getfile(self, filename: str, addr: Any, forcemime: bool = False, forcemimetype: str = "") -> tuple[filecont, mimetype, returncode, iserror]:
		"""Gets a specific file.

		Args:
		    filename (str): Name of the file to be opened.
		    addr (socket._RetAddress): Socket Return Address.
		    forcemime (bool, optional): Force a specific MIME Type. Defaults to False.
		    forcemimetype (str, optional): Forced MIME Type. Defaults to "".

		Returns:
		    tuple[filecont, mimetype, returncode, iserror]: Tuple containing the file content, MIME Type, the HTTP return code and iserror bool.
		"""
		safe = self._resolve_path(filename)
		if safe is None:
			print(f"[{addr[0]}:{addr[1]}]: Path traversal blocked: {filename}")
			return (b"", "", FORBIDDEN, True)
		filename = safe

		filemime: str = ""
		mime: str | None = self.mime_default_type
		try:
			with open(Path(f"{filename}"), "rb") as f:
				filecont = f.read()
		except FileNotFoundError:
			print(f"[{addr[0]}:{addr[1]}]: File not found: {filename}")
			return (b"", "", NOT_FOUND, True)
		except OSError:
			print(f"[{addr[0]}:{addr[1]}]: Could not open file: {filename}")
			return (b"", "", FORBIDDEN, True)
		except Exception:
			print(f"[{addr[0]}:{addr[1]}]: Unknown error trying to open file: {filename}")
			return (b"", "", INTERNAL_SERVER_ERROR, True)
		else:
			if not forcemime and self.mime_enable:
				if self.mime_module_type in ("mime", "auto"):
					guess = mimetypes.guess_type(filename)
					if guess and guess[0]:
						mime = guess[0]
				if self.mime_module_type in ("mimetype", "auto") and (mime == self.mime_default_type or mime is None):
					try:
						filemagic = magic.from_file(filename, mime=True)
						if filemagic:
							mime = filemagic
					except Exception:
						pass
			else:
				mime = forcemimetype or self.mime_default_type
		return (filecont, mime or self.mime_default_type, OK, False)

	def writefile(self, filename: str, addr: Any, content: bytes, wrtype: Literal["append", "fromstart", "specific"] | None = "append", wrfrom: int | None = 0) -> bool:
		"""Write content to a file.

		Args:
		    filename (str): Name of the file to write to.
		    addr (socket._RetAddress): Socket Return Address.
		    content (bytes): Content to write.
		    wrtype (str, optional): Write mode. Defaults to "append".
		    wrfrom (int, optional): Start position for "specific" mode. Defaults to 0.

		Returns:
		    bool: True on success.
		"""
		safe = self._resolve_path(filename)
		if safe is None:
			print(f"[{addr[0]}:{addr[1]}]: Path traversal blocked on write: {filename}")
			return False
		filename = safe

		try:
			Path(filename).parent.mkdir(parents=True, exist_ok=True)
			mode = "ab" if wrtype == "append" else "wb"
			with open(Path(filename), mode) as f:
				if wrtype == "specific" and wrfrom is not None:
					f.seek(wrfrom)
				f.write(content)
			return True
		except Exception as e:
			print(f"[{addr[0]}:{addr[1]}]: Write error for {filename}: {e}")
			return False

	def deletefile(self, filename: str, addr: Any) -> bool:
		"""Delete a file.

		Args:
		    filename (str): Name of the file to delete.
		    addr (socket._RetAddress): Socket Return Address.

		Returns:
		    bool: True on success.
		"""
		safe = self._resolve_path(filename)
		if safe is None:
			print(f"[{addr[0]}:{addr[1]}]: Path traversal blocked on delete: {filename}")
			return False
		filename = safe

		try:
			Path(filename).unlink()
			return True
		except FileNotFoundError:
			print(f"[{addr[0]}:{addr[1]}]: Delete error: file not found: {filename}")
			return False
		except Exception as e:
			print(f"[{addr[0]}:{addr[1]}]: Delete error for {filename}: {e}")
			return False

	def isdir(self, filename: str, addr: Any) -> bool:
		"""Check if a path is a directory."""
		safe = self._resolve_path(filename)
		if safe is None:
			return False
		return Path(safe).is_dir()

	def listdir(self, filename: str, addr: Any) -> list:
		"""List contents of a directory."""
		safe = self._resolve_path(filename)
		if safe is None:
			return []
		try:
			return sorted(Path(safe).iterdir())
		except Exception:
			return []


def doAppend(hostname: str, port: int, workpath: str, defaultindex: str, debug: bool,
             mime_enable: bool = True, mime_module_type: str = "auto",
             mime_default_type: str = "application/octet-stream",
             restrict_to_workpath: bool = True,
             directory_listing: bool = True,
             directory_listing_index_bottom: bool = True,
             keep_alive: bool = True,
             keep_alive_timeout: int = 5,
             **kwargs) -> None:
	FileHandling.workpath = workpath
	FileHandling.mime_enable = mime_enable
	FileHandling.mime_module_type = mime_module_type
	FileHandling.mime_default_type = mime_default_type
	FileHandling.restrict_to_workpath = restrict_to_workpath
	FileHandling.directory_listing = directory_listing
	FileHandling.directory_listing_index_bottom = directory_listing_index_bottom

GetFileHandling.append(FileHandling) # pyright: ignore[reportArgumentType]
