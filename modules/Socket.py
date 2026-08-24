import socket

from MultiServer_stubs import ConnHandling, ConnectionLike, ServerHandling, TransportHandler

class Socket(ConnectionLike):
	"""TCP Socket Class"""
	def __init__(self) -> None:
		pass
	def startsocket(self, HOST: str="", PORT: int=80) -> socket.socket:
		"""Starts the TCP Socket.

		Args:
		    HOST (str, optional): Specific host to listen on. Defaults to "".
		    PORT (int, optional): Specific port to listen on. Defaults to 80.

		Returns:
		    socket.socket: Started socket.
		"""		
		print(f"[{HOST}:{PORT}]: Opening socket...")
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.bind((HOST, PORT))
		s.listen(5)
		print(f"[{HOST}:{PORT}]: Socket opened.")
		return s
	def recv(self, sock: socket.socket, bufsize: int) -> bytes:
		return socket.socket.recv(sock, bufsize)
	def send(self, sock: socket.socket, data: bytes) -> int:
		return socket.socket.send(sock, data)

def doAppend(hostname: str, port: int, workpath: str, defaultindex: str, debug: bool):
	ConnHandling.append(TransportHandler(Socket().startsocket, hostname, port, ServerHandling, (hostname, port, workpath, defaultindex, debug)))