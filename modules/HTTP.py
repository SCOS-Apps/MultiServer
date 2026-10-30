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

from datetime import datetime, timezone
from typing import Literal

from MultiServer_stubs import DictWithHeader

HTTP_VERSIONS = Literal["1.1", "2.0", "3.0"]

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
	
	class HeaderResponse(DictWithHeader):
		def __init__(self, version: HTTP_VERSIONS, code: int, content: bytes | None = None, mime: str | None = "application/octet-stream") -> None:
			super().__init__()
			self[None] = f"HTTP/{version} {code} {HTTP().getstringfromcode(code)}"
			self["Date"] = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')
			if content:
				self.mime = mime
				self.content = content
				self.contentlength = len(content)
			else:
				self.mime = None
				self.content = None
				self.contentlength = 0
			if self.mime: self["Content-Type"] = self.mime
			if self.contentlength: self["Content-Length"] = self.contentlength
		def preset(self: DictWithHeader, preset: Literal["ErrorPage", "Redirect"], *values: object):
			return preset, values
		def returnHTTP(self) -> bytes:
			header = self["NoneHTTP"].encode()
			if self.content is not None: header = header + self.content
			return header

def doAppend(hostname: str, port: int, workpath: str, defaultindex: str, debug: bool, **kwargs) -> None:
	pass
