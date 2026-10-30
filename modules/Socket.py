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
		s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		s.bind((HOST, PORT))
		s.listen(5)
		print(f"[{HOST}:{PORT}]: Socket opened.")
		return s
	def recv(self, sock: socket.socket, bufsize: int) -> bytes:
		return socket.socket.recv(sock, bufsize)
	def send(self, sock: socket.socket, data: bytes) -> int:
		return socket.socket.send(sock, data)

def doAppend(hostname: str, port: int, workpath: str, defaultindex: str, debug: bool, **kwargs) -> None:
	ConnHandling.append(TransportHandler(Socket().startsocket, hostname, port, ServerHandling, (hostname, port, workpath, defaultindex, debug)))
