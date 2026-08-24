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
	def __init__(self) -> None:
		pass
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
	def writefile(self, filename: str, addr: Any, wrtype: Literal["append", "fromstart", "specific"] | None = "append", wrfrom: int | None = 0) -> bool:
		return True

def doAppend(hostname: str, port: int, workpath: str, defaultindex: str, debug: bool):
	pass

GetFileHandling.append(FileHandling) # pyright: ignore[reportArgumentType]