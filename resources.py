import Tkinter as tk

images = {
    'trashCan' : 'images/trash_16.gif'
}

__resources = {}

def getImage(name):
    if not __resources.has_key(name):
        if images.has_key(name):
            __resources[name] = tk.PhotoImage(file=images[name])
        else:
            __resources[name] = None
    return __resources[name]
    
