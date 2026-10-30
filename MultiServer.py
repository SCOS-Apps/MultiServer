#!/bin/python3
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


from pathlib import Path
import tomllib
from importlib import import_module

MultiServerVersion = "1.0"

if __name__ == "__main__":
	config = tomllib.load(open(Path("./config.toml"), "rb"))
	server_cfg = config.get("Server", {})
	hostname = server_cfg.get("Host") # pyright: ignore[reportOptionalMemberAccess]
	port_cfg = server_cfg.get("Port") # pyright: ignore[reportOptionalMemberAccess]
	port = port_cfg[0] if isinstance(port_cfg, list) else int(port_cfg)
	workpath = server_cfg.get("WorkPath") # pyright: ignore[reportOptionalMemberAccess]
	defaultindex = server_cfg.get("DefaultIndex") # pyright: ignore[reportOptionalMemberAccess]
	debug = server_cfg.get("Debug") # pyright: ignore[reportOptionalMemberAccess]
	moduledir = config.get("Module").get("ModuleDirPy") # pyright: ignore[reportOptionalMemberAccess]
	mime_cfg = config.get("Module", {}).get("FileHandling", {}).get("MIME", {})
	mime_enable = mime_cfg.get("EnableMIME", True)
	mime_module_type = mime_cfg.get("MIMEModuleType", "auto")
	mime_default_type = mime_cfg.get("MIMEDefaultType", "application/octet-stream")
	restrict_to_workpath = config.get("Security", {}).get("RestrictToWorkPath", True)
	directory_listing = server_cfg.get("DirectoryListing", True)
	directory_listing_index_bottom = server_cfg.get("DirectoryListingIndexBottom", True)
	keep_alive = server_cfg.get("KeepAlive", True)
	keep_alive_timeout = server_cfg.get("KeepAliveTimeout", 5)
	auth_cfg = config.get("Auth", {})
	auth_enabled = auth_cfg.get("Enabled", False)
	auth_realm = auth_cfg.get("Realm", "MultiServer")
	auth_users_file = auth_cfg.get("UsersFile", "./.htpasswd")
	auth_require_methods = auth_cfg.get("RequireMethods", ["PUT", "DELETE"])
	from MultiServer_stubs import *
	for i in config.get("Module").get("Load"): # pyright: ignore[reportOptionalMemberAccess]
		print(f"[MultiServer:{MultiServerVersion}] Loading {i}...")
		module = import_module(f"{moduledir}.{i}")
		if hasattr(module, "doAppend"):
			module.doAppend(hostname, port, workpath, defaultindex, debug,
			    mime_enable=mime_enable, mime_module_type=mime_module_type,
			    mime_default_type=mime_default_type,
			    restrict_to_workpath=restrict_to_workpath,
			    directory_listing=directory_listing,
			    directory_listing_index_bottom=directory_listing_index_bottom,
			    keep_alive=keep_alive,
			    keep_alive_timeout=keep_alive_timeout,
			    auth_enabled=auth_enabled,
			    auth_realm=auth_realm,
			    auth_users_file=auth_users_file,
			    auth_require_methods=auth_require_methods)
		print(f"[MultiServer:{MultiServerVersion}] Loaded {i}.")
	handlers = []
	for handler in ConnHandling:
		handler.start()
		handlers.append(handler)
	try:
		for handler in handlers:
			handler.thread.join()
	except KeyboardInterrupt:
		print(f"[MultiServer:{MultiServerVersion}] Shutting down...")
