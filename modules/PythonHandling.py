import contextlib
from io import StringIO
import threading
from bs4 import BeautifulSoup
from modules.HTMLCode import HTMLCode


class PythonHandling:
	_exec_lock = threading.Lock()
	def __init__(self) -> None:
		pass
	def RunPythonInHTML(self, string: str) -> str | None:
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
		else:
			return None