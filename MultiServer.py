from pathlib import Path
import tomllib

MultiServerVersion = "1.0"

if __name__ == "__main__":
	config = tomllib.load(open(Path("./config.toml"), "rb"))
	hostname = config.get("Server").get("Host") # pyright: ignore[reportOptionalMemberAccess]
	port = config.get("Server").get("Port")[0] # pyright: ignore[reportOptionalMemberAccess]
	workpath = config.get("Server").get("WorkPath") # pyright: ignore[reportOptionalMemberAccess]
	defaultindex = config.get("Server").get("DefaultIndex") # pyright: ignore[reportOptionalMemberAccess]
	debug = config.get("Server").get("Debug") # pyright: ignore[reportOptionalMemberAccess]
	moduledir = config.get("Module").get("ModuleDirPy") # pyright: ignore[reportOptionalMemberAccess]
	from MultiServer_stubs import *
	for i in config.get("Module").get("Load"): # pyright: ignore[reportOptionalMemberAccess]
		print(f"[MultiServer:{MultiServerVersion}] Loading {i}...")
		exec(f"""from {moduledir}.{i} import *
doAppend('{hostname}', {port}, '{workpath}', '{defaultindex}', {debug})
del(doAppend)""")
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