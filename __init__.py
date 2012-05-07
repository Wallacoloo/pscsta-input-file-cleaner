#replace unix line endings ("\n") with Windows line endings ("\r\n")
#replace utf-quotes with ansi quotes
#replace word hyphen with -
#warn for any non-ansi character.

import sys
import fnmatch #for unix-shell-style support in file matches.
import os
from Tkinter import *

unparsedCmds = sys.argv[1:]
print unparsedCmds

files = unparsedCmds
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
        raise TclError, "cannot use pack with this widget"
    def place(self, **kw):
        raise TclError, "cannot use place with this widget"


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

	#root.mainloop()
	return root, frame, canvas

#getRootFrame()[0].mainloop()

class Cleaner(object):
	def __init__(self, files, outdir):
		self.files = files
		self.outdir = outdir
	def getChanges(self):
		return DirChangeSet.fromFiles(self.files, self.outdir)
	def showUi(self):
		global row
		changes = self.getChanges()
		#import Tkinter as Tk
		#root = Tk.Tk()
		#scrollbar = AutoScrollbar(root)#Tk.Scrollbar(root)
		#scrollbar.grid(row=0, column=1, stick=Tk.N+Tk.S)
		#canvas = Tk.Canvas(root, yscrollcommand=scrollbar.set)
		#canvas.grid(row=0, column=0, sticky=Tk.N+Tk.S+Tk.E+Tk.W)
		#frame = Tk.Frame(canvas)
		#frame.pack(side=Tk.LEFT)


		#frame.rowconfigure(1, weight=1)
		#frame.columnconfigure(1, weight=1)
		#canvas.create_window(0, 0, anchor=Tk.NW, window=frame)

		#frame.update_idletasks()
		#scrollbar.config(command=canvas.yview)
		#root.grid_rowconfigure(0, weight=1)
		#root.grid_columnconfigure(0, weight=1)
		#canvas.config(scrollregion=canvas.bbox("all"))
		root, frame, canvas = getRootFrame()
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
						print var.get()
						change.setApply(var.get())
					check = Checkbutton(cFrame, command=onChange, variable=var)
					if change.doApply():
						check.select()
					check.grid(row=0, column=0, sticky=W, padx=16)
					txt = change.detailDesc()
					underlineIdx = txt.rfind("_")
					if underlineIdx != -1:
						txt = txt[:underlineIdx] + txt[underlineIdx+1:]
					lbl = Label(cFrame, text=txt, underline=underlineIdx)
					lbl.grid(row=0, column=1, sticky=W)
				mkCheck(change)
			#fFrame.pack()
			fFrame.grid(row=row, column=0, sticky=W)
			row += 1

		applyBtn = Button(root, text="Apply", fg="black", command=changes.applyChanges)
		applyBtn.grid(row=row, column=0, sticky=W, padx=100)
		cancelBtn = Button(root, text="Cancel", fg="black", command=lambda:None)
		cancelBtn.grid(row=row, column=0, sticky=E, padx=100)
		frame.update_idletasks()
		canvas.config(scrollregion=canvas.bbox("all"))
		root.mainloop()
		#root.destroy()

class DirChangeSet(object):
	@classmethod
	def fromFiles(cls, files, outdir):
		return cls([FileChangeSet(i) for i in files], outdir)
	def __init__(self, fileChanges, outdir):
		self.fileChanges = fileChanges
		self.outdir = outdir
	def __repr__(self):
		return repr(self.fileChanges)
	def getFileChangeSets(self):
		return self.fileChanges
	def applyChanges(self):
		os.mkdir(self.outdir)

class FileChangeSet(object):
	def __init__(self, fName):
		self.fName, self.content = fName, open(fName).read()
		self.changes = []
		self.findChanges()
	def __repr__(self):
		return repr(self.changes)
	def getFileName(self):
		return self.fName
	def getChanges(self):
		return self.changes
	def getStr(self): return self.content

	def addChange(self, change):
		self.changes.append(change)

	def findChanges(self):
		for i, c in enumerate(self.content):
			if self.content[i:i+2] in ["\x20\x1C", "\x20\x1D"]: #double quotes
				self.addChange(UnicodeDoubleQuote(self, i))
			elif self.content[i:i+2] in ["\x20\x18", "\x20\x19"]: #single quotes
				self.addChange(UnicodeSingleQuote(self, i))
			elif ord(c) > 127: #non-ansi character
				self.addChange(NonAnsiCharacter(self, i))
			elif c == "\n" and (i == 0 or self.content[i-1] != "\r"): #unix line endings - change to windows.
				self.addChange(ChangeLineEnding(self, i))

class Change(object):
	def __init__(self, fChangeSet, idx, do=True):
		self.fChangeSet = fChangeSet
		self.idx = idx
		self.do = do
	def doApply(self): return self.do
	def setApply(self, a=True): self.do = a
	def getChar(self): return self.fChangeSet.getStr()[self.idx]
	def lineNo(self):
	    return sum(i == "\n" for i in self.fChangeSet.getStr()[:self.idx])
	def lineOffset(self):
		return len(self.fChangeSet.getStr()[:self.idx].split("\n")[-1])
	def lineValue(self):
		return self.fChangeSet.getStr().split("\n")[self.lineNo()]
	def __repr__(self):
		return "Change(%s) at %i" %("Y" if self.do else "N", self.idx)
	def desc(self):
		return "Unknown change"
	def context(self):
		return self.lineValue() #self.fChangeSet.getStr()[max(0, self.idx-10): self.idx+10].split("\n")[0]
	def detailDesc(self):
		return "%i:%i %s (%s)" %(self.lineNo()+1, self.lineOffset()+1, self.desc(), self.context())

class UnicodeDoubleQuote(Change):
	def desc(self):
		return "Unicode double quote"
class UnicodeSingleQuote(Change):
	def desc(self):
		return "Unicode quote"
class NonAnsiCharacter(Change):
	def desc(self):
		return "Non-ansi character (%s)" %self.getChar()
class ChangeLineEnding(Change):
	def desc(self):
		return "Unix line-ending"

c = Cleaner(files, outdir)

#print c.getChanges()

c.showUi()
