import tkinter
from tkinter import * # pyright: ignore[reportWildcardImportFromLibrary]
from tkinter import messagebox
from tkinter.ttk import * # pyright: ignore[reportWildcardImportFromLibrary]

class App(Frame):
    appname = "Some Random Python App"
    appurl = "https://example.com"
    apphelpurl = "https://help.example.com"
    appversion = "1.0.0"
    def __init__(self, master):
        super().__init__(master, padding=10)
        master.geometry("640x480")
        master.title("PCTux")
        self.grid()
        lbl1 = Label(self, text="Hello World!").grid(column=0, row=0)
        btn1 = Button(self, text="Quit", command=lambda: self.exitoutof(master)).grid(column=0, row=1)
        btn2 = Button(self, text="Show Error...", command=lambda: self.error(master=master, errormsg="A error occured. (Manual Test)", errorcode=69420)).grid(column=0, row=2)

    def exitoutof(self, master):
        messagebox.Message(icon=messagebox.INFO, type=messagebox.OK, message="Bye...").show()
        master.destroy()

    def error(self, master: Misc, errorcode: float | int = 0, errormsg: float | str = "An error occured..."):
        master.destroy()
        errorwidget = Tk()

        def lock(_=None):
            if errorwidget.winfo_geometry() != "350x255":
                errorwidget.geometry("350x255")

        errorwidget.overrideredirect(True)
        #errorwidget.bind("<Configure>", lambda event: errorwidget.after_idle(lock))
        errorwidget.geometry("350x255")
        errorwidget.resizable(False, False)
        errorwidget.pack_propagate(False)

        errorlbl1 = Label(master=errorwidget, text="An error occured and the program had to close:")
        errorlbl1.pack(anchor=N+W, side=TOP)

        errortxtscroll1 = Scrollbar(errorwidget)
        errortxtscroll1.pack(side="right", fill="y")

        errortxt1 = Text(master=errorwidget, wrap="word", height=0)
        errortxt1.pack(fill="both", expand=1)
        errortxt1.insert(tkinter.END, f"{errormsg} (Code: {errorcode})\n\nFor more information, please check {self.apphelpurl} for \"{self.appname}\" of version {self.appversion}. If any issues are to be made, use the Copy button below to copy the error content and then paste it in the specified area.")
        errortxt1.configure(state="disabled", yscrollcommand=errortxtscroll1.set)
        errortxt1.grid_columnconfigure(0, weight=1)
        errortxtscroll1.config(command=errortxt1.yview)

        errorbtn1 = Button(master=errorwidget, text="Copy...", command=lambda: [errorwidget.clipboard_clear(), errorwidget.clipboard_append(f"{errormsg} (Code: {errorcode})"), errorwidget.update(), errorwidget.focus()])
        errorbtn1.pack(anchor=N+E, padx=5, pady=5, side=LEFT)

        errorbtn2 = Button(master=errorwidget, text="Exit...", command=errorwidget.destroy)
        errorbtn2.pack(anchor=N+E, padx=5, pady=5, after=errorbtn1, side=RIGHT)
        
if __name__ == "__main__":
    App(Tk()).mainloop()
