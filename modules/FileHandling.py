import mimetypes
from pathlib import Path
import socket
import magic
from modules.HTTP import *

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