# Utility functions and file i/o for hcp iot simulator
#
# 
# Author: Asuman Suenbuel
# (c) 2015
#

import os, sys, re
import urllib, urllib2, json
from Tkinter import *
import tkMessageBox as messageBox

sys.path.insert(0,os.getcwd())

try:
    import hcp_config as config
except ImportError:
    config = {}

defaultDataFolder = config.default_data_folder if hasattr(config,'default_data_folder') else 'simdata'

# --------------------------------------------------------------------------------
# checks whether the simulator runs on a raspberry device
# --------------------------------------------------------------------------------

def on_raspberry():
    uname_output = os.popen('uname -a').read()
    return re.match('^.*raspberrypi.*$',uname_output)

runs_on_raspberry = on_raspberry()


# --------------------------------------------------------------------------------


filePersistenceInitialized = False

# ================================================================================

def initFilePersistence():
    ensureDataFolderExists()
    filePersistenceInitialized = True

def ensureDataFolderExists(dataFolder=defaultDataFolder):
    if os.path.isdir(dataFolder):
        return
    if os.path.exists(dataFolder):
        raise Exception("File '" + dataFolder + "' exists, but is not a directory!")
    os.makedirs(dataFolder)

def saveFile(fileName,contents):
    f = open(fileName,"w")
    f.write(contents)
    f.close()

def getFileContents(fileName):
    f = open(fileName,"r")
    data = f.read()
    f.close()
    return data

def evalFileContents(fileName):
    return eval(getFileContents(fileName))

def stringEscape(string):
    return urllib.quote(string)

def stringUnescape(string):
    return urllib.unquote(string)

# ================================================================================

class FilePersistedObject(object):

    def initFilePersistence(self,typeSuffix,dataFolder=defaultDataFolder):
        self.typeSuffix = typeSuffix
        self.dataFolder = dataFolder
        if dataFolder != defaultDataFolder:
            ensureDataFolderExists(dataFolder = self.dataFolder)
        self.__loadedFromFile__ = None

    def getFileName(self):
        fname = self.dataFolder + '/'
        if hasattr(self,'name'):
            fname += self.name
        if not hasattr(self,'typeSuffix'):
            raise Exception("you have to call FilePersistedObject.initFilePersistence on this object")
        fname += '.' + self.typeSuffix
        #fname += '.py'
        return os.path.abspath(fname)
    
    def validate(self):
        pass

    # overwrite in sub-classes to generate the python string to
    # (re-)create the object
    def getPythonConstructorString(self,standalone):
        return "0"

    def saveToFile(self,fileName=None,force=False,standalone=False):
        initFilePersistence()
        self.validate()
        fname = fileName if fileName != None else self.getFileName()
        if not force:
            if self.__loadedFromFile__ != None and self.__loadedFromFile__ != fname and os.path.exists(fname):
                raise CannotOverwriteFileError("cannot overwrite existing file '" + fname + "'; please use 'force=True'")
        contents = self.getPythonConstructorString(standalone=standalone)
        saveFile(fname,contents)
        self.info(self.typeSuffix + ' saved into file "' + fname + '".')

    def setLoadFromFileName(self,fileName):
        self.__loadedFromFile__ = fileName

class CannotOverwriteFileError(Exception):
    def __init__(self,msg):
        Exception.__init__(self,msg)

# --------------------------------------------------------------------------------

# sets the background color recursively for the given widget
def tkSetBackgroundColor(widget):
    pass


# --------------------------------------------------------------------------------
# --------------------------------------------------------------------------------

def addStringVar(obj,field,label,values = None, valueType = 'string'):
    if not hasattr(obj,'stringVars'):
        obj.stringVars = {}
    stringVar = StringVar()
    value = getattr(obj,field)
    value = "" if value == None else value
    stringVar.set(value)
    infoObj = {'label' : label, 'stringVar' : stringVar, 'valueType' : valueType }
    if values != None:
        infoObj['values'] = values
    obj.stringVars[field] = infoObj
    return stringVar

def updateValueFromStringVar(obj,field):
    if not hasattr(obj,'stringVars'):
        return
    if not(field in obj.stringVars):
        return
    infoObj = obj.stringVars[field]
    sv = infoObj['stringVar']
    value = sv.get()
    if value.strip() == "":
        value = None
    else:
        if infoObj['valueType'] == 'float':
            value = float(value)
        if infoObj['valueType'] == 'int':
            value = int(value)
    setattr(obj,field,value)

def getStringVarForField(obj,field):
    if not hasattr(obj,'stringVars'):
        return None
    if not(field in obj.stringVars):
        return None
    infoObj = obj.stringVars[field]
    sv = infoObj['stringVar']
    return sv

def createStringInput(obj,field,parent,row,column=0,width=40,label=None,highlightbackground=None,bg=None,fg=None):
    infoObj = obj.stringVars[field]
    labelText = label if label != None else infoObj['label']
    labelW = Label(parent, text = labelText+":", background=highlightbackground)
    labelW.grid(row=row,column=column,sticky=W)
    tv = infoObj['stringVar']
    res = None
    if 'values' in infoObj:
        optionValues = infoObj['values'] if len(infoObj['values']) > 0 else [' ']
        options = apply(OptionMenu,(parent,tv) + tuple(optionValues))
        options.grid(row=row,column=column+1,sticky=W)
        infoObj['optionMenu'] = options
        res = options
    else:
        entry = Entry(parent, width = width, textvariable=tv, highlightbackground=highlightbackground,bg=bg,fg=fg)
        entry.grid(row=row,column=column+1,sticky=W)
        res = entry
        infoObj['entry'] = entry
    return res

def updateOptionMenuValues(obj,field,values):
    infoObj = obj.stringVars[field]
    if not infoObj.has_key('optionMenu'):
        return
    optionMenu = infoObj['optionMenu'];
    var = infoObj['stringVar']
    m = optionMenu['menu']
    m.delete(0,'end')
    for value in values:
        m.add_command(label=value, command=_setit(var,value))

def _setit(var,value):
    return lambda : var.set(value)


# --------------------------------------------------------------------------------

def saveToFileUI(obj,standalone=False):
    try:
        try:
            obj.saveToFile(standalone=standalone)
        except CannotOverwriteFileError:
            fname = obj.getFileName()
            msg = 'File "' + fname + '" already exists. Do you want to overwrite it?'
            if messageBox.askyesno('Overwrite?',msg):
                obj.saveToFile(force=True,standalone=standalone)
    except Exception as e:
        messageBox.showerror("Error saving file",str(e))

# --------------------------------------------------------------------------------

def postRequest(postUrl,dataDict={}):
    data = json.dumps(dataDict)
    print 'postUrl: ' + postUrl
    print 'data: ' + str(data)
    req = urllib2.Request(postUrl,data)
    response = urllib2.urlopen(req)
    return response.read()
