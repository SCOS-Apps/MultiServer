from HTTPServer import WebServer, HTTP, HTMLCode

WebServer().start(PORT=8080)
#print(HTTP().getcodefromstring("permanent redirect"))

#file = open("www\\index.html").read()
#print(WebServer.PythonHandling().RunPythonInHTML(file))

#code = HTMLCode(file)
#node = code.Node(code.soup)

#print(str(code.soup))