#
# Helper class to display custom modal dialogs
#
# Asuman Suenbuel
#
# (c) 2015
#

from Tkinter import *
import os

class Dialog(Toplevel):

    def __init__(self, parent, title = None, isModal = True, okText = "Ok", okInitialState=None):

        Toplevel.__init__(self, parent)
        self.transient(parent)

        if title:
            self.title(title)

        self.parent = parent

        self.result = None

        self.isModal = isModal

        self.okText = okText
        self.okInitialState = okInitialState

        body = Frame(self)
        self.initial_focus = self.body(body)
        body.pack(padx=5, pady=5)

        self.buttonbox()

        if isModal:
            self.grab_set()

        if not self.initial_focus:
            self.initial_focus = self

        self.protocol("WM_DELETE_WINDOW", self.cancel)

        self.geometry("+%d+%d" % (parent.winfo_rootx()+50,
                                  parent.winfo_rooty()+50))

        self.initial_focus.focus_set()

        if isModal:
            self.wait_window(self)

    #
    # construction hooks

    def body(self, master):
        # create dialog body.  return widget that should have
        # initial focus.  this method should be overridden

        pass

    def buttonbox(self):
        # add standard button box. override if you don't want the
        # standard buttons

        box = Frame(self)

        okText = self.okText
        okWidth = len(okText) if len(okText) > 10 else 10
        
        w = Button(box, text=okText, width=okWidth, command=self.ok, default=ACTIVE, state=self.okInitialState)
        w.pack(side=LEFT, padx=5, pady=5)
        if self.isModal:
            wcancel = Button(box, text="Cancel", width=10, command=self.cancel)
            wcancel.pack(side=LEFT, padx=5, pady=5)

        #self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        self.okButton = w

        box.pack()

    #
    # standard button semantics

    def ok(self, event=None):

        if not self.validate():
            self.initial_focus.focus_set() # put focus back
            return

        self.withdraw()
        self.update_idletasks()

        self.apply()

        self.cancel()

    def cancel(self, event=None):

        # put focus back to the parent window
        self.parent.focus_set()
        self.destroy()

    #
    # command hooks

    def validate(self):

        return 1 # override

    def apply(self):

        pass # override
