from __future__ import annotations
from typing import Literal
from bs4 import BeautifulSoup, Doctype, Tag

class HTMLCode:
	"""HTML Code Handler Class
	"""
	def __init__(self, html: str | None = None, /) -> None:
		"""HTML Code Handler

		Args:
		    html (str | None, optional): HTML Code. Defaults to None.
		"""		
		if html is None: html = """<html>
<head>
</head>
<body>
</body>
</html>"""
		self.soup = BeautifulSoup(html, "html.parser")

	def _parse_query(self, query: str) -> list:
		options = query.split(";")
		tag_name = None
		attr = {}
		count = None
		html_classes: list = []
		html_id = None
		for i in options:
			if i.startswith("node:"):
				tag_name = i.split(":")[1]
			if i.startswith("class:"):
				html_classes.append(i.split(":")[1])
			if i.startswith("id:"):
				html_id = i.split(":")[1]
			if i.startswith("count:"):
				count = int(i.split(":")[1])
		if html_classes:
			attr["class"] = html_classes
		if html_id:
			attr["id"] = html_id
		if count is not None and count < 1:
			raise ValueError(f"Specified count ({count}) is less than 1")
		return [tag_name, attr, count]

	def __getitem__(self, query: str, /) -> HTMLCode.TaggedNode:
		tag_name, attrs, count = self._parse_query(query)
		matches = self.soup.find_all(tag_name, attrs=attrs)
		if count is None:
			if len(matches) > 1:
				raise ValueError(f"Ambiguous query {query!r}: {len(matches)} matches, specify count")
			if not matches:
				raise LookupError(f"No node matches query {query!r}")
			return HTMLCode.TaggedNode(matches[0], self.soup)
		else:
			return HTMLCode.TaggedNode(matches[count - 1], self.soup)
	
	def __setitem__(self, query: str, value: dict):
		tag = self[query]
		name: None = None
		content: None = None
		options: dict = {}
		for i, b in value.items():
			if i == "__name__":
				name = b
			elif i == "_content":
				content = b
			else:
				options.update({i: b})
		print(f"_name: {name}, _content: {content}, _options: {options}")
		tag.modify(name=name, options=options,content=content)

	def exists(self, query: str) -> bool:
		"""Checks if query exists.

		Args:
		    query (str): Query to search

		Returns:
		    bool: Whether the query was found
		"""		
		try:
			self[query]
		except ValueError:
			return True
		except LookupError:
			return False
		else:
			return True

	class Node():
		"""HTML Code Handler Node Class
		"""
		def __init__(self, ownersoup: BeautifulSoup, /) -> None:
			"""HTML Code Handler Node Class

			Args:
			    ownersoup (BeautifulSoup): HTML Code parsed by BeautifulSoup
			"""
			self.soup = ownersoup

		def add(self, name: str, options: dict | None = None, content: str | None = None, inside: HTMLCode.TaggedNode | Literal[None, "none"] | None = None, before: HTMLCode.TaggedNode | None = None, after: HTMLCode.TaggedNode | None = None) -> HTMLCode.TaggedNode:
			"""Adds a new Node

			Args:
			    name (str): The Node name (type)
			    options (dict | None, optional): Node options. Defaults to None.
			    content (str | None, optional): Node contents. Defaults to None.
			    inside (HTMLCode.TaggedNode | Literal[None, &quot;none&quot;] | None, optional): Which Node this new Node should be inside. Defaults to None.
			    before (HTMLCode.TaggedNode | None, optional): Which Node is after this new Node. Defaults to None.
			    after (HTMLCode.TaggedNode | None, optional): Which Node if before this new Node. Defaults to None.

			Returns:
			    HTMLCode.TaggedNode: Newly created Node
			"""
			if options is None: options = dict()
			node = self.soup.new_tag(name, attrs=options, string=content)
			if isinstance(inside, HTMLCode.TaggedNode):
				inside.node.append(node)
			elif inside == "none":
				self.soup.append(node)
			else:
				self.soup.html.body.append(node) # pyright: ignore[reportOptionalMemberAccess]
			if before:
				before.node.insert_before(node)
			if after:
				after.node.insert_after(node)
			return HTMLCode.TaggedNode(node, self.soup)
		
		def add_doctype(self, name: str = "html") -> None:
			"""Adds a specific document type to the page.

			Args:
			    name (str, optional): Type of doctype. Defaults to "html".
			"""
			doctype = Doctype.for_name_and_ids(name, None, None)
			self.soup.insert(0, doctype)

	class TaggedNode():
		"""HTML Code Handler Specific Node Class
		"""
		def __init__(self, node: Tag, owner_soup: BeautifulSoup, /) -> None:
			"""HTML Code Handler Specific Node Class

			Args:
			    node (Tag): The Node this should be using/referencing.
			    owner_soup (BeautifulSoup): HTML Code parsed by BeautifulSoup
			"""
			self.node = node
			self.soup = owner_soup
			self.content = ""
			for i in self.node.contents: self.content = self.content + str(i)

		def modify(self, name: str | None = None, options: dict | None = None, content: str | None = None):
			"""Modify the node to have new values.

			Args:
			    name (str | None, optional): New name (type). Defaults to None.
			    options (dict | None, optional): New/modified options. Defaults to None.
			    content (str | None, optional): New content. Defaults to None.

			Raises:
			    SyntaxError: Raised if no modifications are specified.
			"""
			if not name and not options and not content:
				raise SyntaxError("You must at least provide one argument.")
			if name: self.node.name = name
			if content is not None: self.node.string = content
			if options:
				for i in options:
					self.node[i] = str(options[i])

		def delete(self):
			"""Deleted the specific Node.
			"""
			self.node.decompose()

def doAppend(hostname: str, port: int, workpath: str, defaultindex: str, debug: bool):
	pass