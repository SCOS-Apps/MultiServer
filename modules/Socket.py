import socket

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