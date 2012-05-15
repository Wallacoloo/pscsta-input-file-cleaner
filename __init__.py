#usage: python __init__.py file1 [file2 [...]]
#X replace unix line endings ("\n") with Windows line endings ("\r\n")
#X replace utf-quotes with ansi quotes
#X replace word hyphen with -
#X warn for any non-ansi character.
#X Remove trailing lines from input files
#  Note: Might override warning for non-windows line endings when the last line is empty.
#X remove trailing spaces at end of lines
#Make it possible to specify an output directory
#X Make *.dat argument possible on Windows (just expand *all* file arguments using fnmatch. Should work on Unix still)
#X Set the window title

import sys
import glob #for windows argument expanding.
import os
try:
    from Tkinter import *
except ImportError: #python 3
    from tkinter import *

unparsedCmds = sys.argv[1:]
print(unparsedCmds)
files = []
for a in unparsedCmds:
    files.extend(glob.glob(a))
print(files)

outdir = "output"

#AutoScrollbar from http://effbot.org/zone/tkinter-autoscrollbar.htm
class AutoScrollbar(Scrollbar):
    # a scrollbar that hides itself if it's not needed.  only
    # works if you use the grid geometry manager.
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            # grid_remove is currently missing from Tkinter!
            self.tk.call("grid", "remove", self)
        else:
            self.grid()
        Scrollbar.set(self, lo, hi)
    def pack(self, **kw):
        raise TclError("cannot use pack with this widget")
    def place(self, **kw):
        raise TclError("cannot use place with this widget")


def getRootFrame():
    root = Tk()

    vscrollbar = AutoScrollbar(root)
    vscrollbar.grid(row=0, column=100, sticky=N+S)
    hscrollbar = AutoScrollbar(root, orient=HORIZONTAL)
    hscrollbar.grid(row=1, column=0, sticky=E+W)

    canvas = Canvas(root, width=500, height=600,
                    yscrollcommand=vscrollbar.set,
                    xscrollcommand=hscrollbar.set)
    canvas.grid(row=0, column=0, sticky=N+S+E+W)

    vscrollbar.config(command=canvas.yview)
    hscrollbar.config(command=canvas.xview)

    # make the canvas expandable
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    #
    # create canvas contents

    frame = Frame(canvas)
    frame.rowconfigure(1, weight=1)
    frame.columnconfigure(1, weight=1)

    canvas.create_window(0, 0, anchor=NW, window=frame)

    frame.update_idletasks()

    canvas.config(scrollregion=canvas.bbox("all"))

    return root, frame, canvas


class Cleaner(object):
    def __init__(self, files, outdir):
        self.files = files
        self.outdir = outdir
    def getChanges(self):
        return DirChangeSet.fromFiles(self.files, self.outdir)
    def showUi(self):
        global row
        changes = self.getChanges()

        root, frame, canvas = getRootFrame()
        root.wm_title("PSCSTA Input File Cleaner")
        row = 0
        for fChangeSet in changes.getFileChangeSets():
            fFrame = Frame(frame)
            fLbl = Label(fFrame, text=fChangeSet.getFileName())
            fLbl.grid(row=0, column=0, sticky=W)
            row += 1
            for change in fChangeSet.getChanges():
                def mkCheck(change):
                    global row
                    cFrame = Frame(fFrame)
                    cFrame.grid(row=row, column=0, sticky=W)
                    row += 1
                    var = IntVar()
                    def onChange(*args):
                        print(var.get())
                        change.setApply(var.get())
                    check = Checkbutton(cFrame, command=onChange, variable=var)
                    if change.doApply():
                        check.select()
                    check.grid(row=0, column=0, sticky=W, padx=16)
                    txt = change.detailDesc()
                    underlineIdx = -1
                    #underlineIdx = txt.rfind("_")
                    #if underlineIdx != -1:
                    #    txt = txt[:underlineIdx] + txt[underlineIdx+1:]
                    lbl = Label(cFrame, text=txt, underline=underlineIdx)
                    lbl.grid(row=0, column=1, sticky=W)
                mkCheck(change)
            fFrame.grid(row=row, column=0, sticky=W)
            row += 1

        def applyChangesAndQuit():
            changes.applyChanges()
            root.destroy()
        applyBtn = Button(root, text="Apply", fg="black", command=applyChangesAndQuit)
        applyBtn.grid(row=row, column=0, sticky=W, padx=100)
        cancelBtn = Button(root, text="Cancel", fg="black", command=root.destroy)
        cancelBtn.grid(row=row, column=0, sticky=E, padx=100)
        frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))
        root.mainloop()

class DirChangeSet(object):
    @classmethod
    def fromFiles(cls, files, outdir):
        return cls([FileChangeSet(i, os.path.join(outdir, os.path.split(i)[1])) for i in files], outdir)
    def __init__(self, fileChanges, outdir):
        self.fileChanges = fileChanges
        self.outdir = outdir
    def __repr__(self):
        return repr(self.fileChanges)
    def getFileChangeSets(self):
        return self.fileChanges
    def applyChanges(self):
        try:
            os.mkdir(self.outdir)
        except OSError:
            pass #directory already exists.
        for fSet in self.getFileChangeSets():
            fSet.applyChanges()

class FileChangeSet(object):
    def __init__(self, fName, outName, matchers=None):
        self.matchers = matchers if matchers is not None else Change.all
        self.fName, self.content = fName, open(fName, "rb").read().decode("cp437")
        self.outName = outName
        self.changes = []
        self.findChanges()
        
    def __repr__(self):
        return repr(self.changes)
    def getFileName(self):
        return self.fName
    def getChanges(self):
        return self.changes
    def getStr(self): return self.content
    def setStr(self, s): self.context=s
    def applyChanges(self):
        offset = 0
        for c in self.changes:
            addOffset, self.content = c.applyChanges(offset, self.content)
            offset += addOffset
        open(self.outName, "wb").write(self.content.encode())

    def nextLineEnding(self, idx):
        n = self.content[idx:].find("\n")
        r = self.content[idx:].find("\r")
        if n >= 0 and r >= 0: return idx+min(n, r)
        elif r >= 0:
            return idx+r
        elif n >= 0:
            return idx+n
        else:
            return -1
        
    def addChange(self, change):
        self.changes.append(change)

    def findChanges(self):
        i = 0
        while i < len(self.content):
            for m in self.matchers:
                mLen = m.doesMatch(self, i)
                if mLen:
                    self.addChange(m(self, i))
                    i += mLen
                    break
            else:
                i += 1

class Change(object):
    all = []
    def __init__(self, fChangeSet, idx, do=True):
        self.fChangeSet = fChangeSet
        self.idx = idx
        self.do = do
    def doApply(self): return self.do
    def setApply(self, a=True): self.do = a
    def applyChanges(self, offset, inp):
        if self.doApply():
            self.idx += offset
            try:
                ret = self.derivedApply(inp)
                self.idx -= offset
                return ret
            except:
                self.idx -= offset #must do this to prevent potential errors later.
                raise
        return 0, inp
    def getChar(self): return self.fChangeSet.getStr()[self.idx]
    def lineNo(self):
        return sum(i == "\n" for i in self.fChangeSet.getStr()[:self.idx])
    def lineOffset(self):
        return len(self.fChangeSet.getStr()[:self.idx].split("\n")[-1])
    def lineValue(self):
        return self.fChangeSet.getStr().split("\n")[self.lineNo()].replace("\r", "")
    def __repr__(self):
        return "Change(%s) at %i" %("Y" if self.do else "N", self.idx)
    def desc(self):
        return "Unknown change"
    def context(self):
        return self.lineValue() #self.fChangeSet.getStr()[max(0, self.idx-10): self.idx+10].split("\n")[0]
    def detailDesc(self):
        return "%i:%i %s (%s)" %(self.lineNo()+1, self.lineOffset()+1, self.desc(), self.context())

def RawSequenceMatch(sMatch, replaceWith, description=None):
    class Matcher(Change):
        @staticmethod
        def doesMatch(cSet, idx):
            return cSet.getStr()[idx:idx+len(sMatch)] == sMatch and len(sMatch)
        def desc(self):
            if description: return description
            else:
                return "Illegal sequence: %s" % sMatch
        def derivedApply(self, inp):
            return len(replaceWith)-len(sMatch), inp[:self.idx] + replaceWith + inp[self.idx+len(sMatch):]
    Change.all.append(Matcher)
    return Matcher

RawSequenceMatch("\x20\x1C", '"', "Unicode double quote")
RawSequenceMatch("\x20\x1D", '"', "Unicode double quote")

RawSequenceMatch("\x20\x18", '"', "Unicode quotation mark")
RawSequenceMatch("\x20\x19", '"', "Unicode quotation mark")
RawSequenceMatch("\x20\x14", '-', "Unicode hyphen")

class NonAnsiCharacter(Change):
    @staticmethod
    def doesMatch(cSet, idx):
        return ord(cSet.getStr()[idx]) > 127
    def desc(self):
        return "Non-ansi character (%s)" %self.getChar()
    def derivedApply(self, inp):
        return -1, inp[:self.idx] + inp[self.idx+1:]
        
Change.all.append(NonAnsiCharacter)

class TrailingWS(Change):
    @staticmethod
    def getMatch(cSet, idx):
        eIdx = cSet.nextLineEnding(idx)
        if eIdx == -1: eIdx = len(cSet.getStr())
        betweenChars = cSet.getStr()[idx:eIdx]
        return betweenChars
    @classmethod
    def doesMatch(cls, cSet, idx):
        betweenChars = cls.getMatch(cSet, idx)
        return all(c in " \t" for c in betweenChars) and len(betweenChars)
    def desc(self):
        return "Trailing whitespace at end of line"
    def derivedApply(self, inp):
        match = self.getMatch(self.fChangeSet, self.idx)
        return -len(match), inp[:self.idx] + inp[self.idx + len(match):]
        
Change.all.append(TrailingWS)

class TrailingLine(TrailingWS):
    @staticmethod
    def doesMatch(cSet, idx):
        mLen = cSet.getStr()[idx:idx+2] == "\r\n" or cSet.getStr()[idx] == "\n"
        mLen += TrailingWS.doesMatch(cSet, idx+mLen)
        return mLen if idx+mLen == len(cSet.getStr()) else 0
    def desc(self):
        return "Empty line at end of file"
    def derivedApply(self, inp):
        mLen = self.doesMatch(self.fChangeSet, self.idx)
        return -mLen, inp[:self.idx]
        
Change.all.append(TrailingLine)

class ChangeLineEnding(Change):
    @staticmethod
    def doesMatch(cSet, idx):
        return cSet.getStr()[idx] == "\n" and (idx == 0 or cSet.getStr()[idx-1] != "\r")
    def desc(self):
        return "Unix line-ending"
    def derivedApply(self, inp):
        return 1, inp[:self.idx] + "\r\n" + inp[self.idx+1:]
       
Change.all.append(ChangeLineEnding)

c = Cleaner(files, outdir)

c.showUi()
