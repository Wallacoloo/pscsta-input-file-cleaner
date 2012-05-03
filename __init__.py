#replace unix line endings ("\n") with Windows line endings ("\r\n")
#replace utf-quotes with ansi quotes
#replace word hyphen with -
#warn for any non-ansi character.

import sys
import fnmatch #for unix-shell-style support in file matches.
import os

unparsedCmds = sys.argv[1:]
print unparsedCmds

#rawFileMatcher = unparsedCmds[0] if len(unparsedCmds) else "*"

#searchDir = os.path.dirname(rawFileMatcher)
#matchFiles = os.path.split(rawFileMatcher)[1]
files = unparsedCmds

class Cleaner(object):
	def __init__(self, files):
		self.files = files
	#def __init__(self, matchFiles="*", searchDir="."):
	#	self.matchFiles = matchFiles
	#	self.searchDir = searchDir
	#def getMatchedFiles(self):
	#	allInDir = os.listdir(self.searchDir)
	#	print allInDir, self.matchFiles
	#	matched = [os.path.join(self.searchDir, p) for p in allInDir if fnmatch.fnmatch(p, self.matchFiles)]
	#	return matched
	def getChanges(self):
		return DirChangeSet.fromFiles(self.files)

class DirChangeSet(object):
	@classmethod
	def fromFiles(cls, files):
		return cls([FileChangeSet(i) for i in files])

	def __init__(self, fileChanges):
		self.fileChanges = fileChanges
	def __repr__(self):
		return repr(self.fileChanges)

class FileChangeSet(object):
	def __init__(self, fName):
		self.fName, self.content = fName, open(fName).read()
		self.changes = []
		self.findChanges()
	def __repr__(self):
		return repr(self.changes)

	def addChange(self, change):
		self.changes.append(change)

	def findChanges(self):
		for i, c in enumerate(self.content):
			if self.content[i:i+2] in ["\x20\x1C", "\x20\x1D"]: #double quotes
				self.addChange(UnicodeDoubleQuote(i))
			elif self.content[i:i+2] in ["\x20\x18", "\x20\x19"]: #single quotes
				self.addChange(UnicodeSingleQuote(i))
			elif ord(c) > 127: #non-ansi character
				self.addChange(NonAnsiCharacter(i))
			elif c == "\n" and (i == 0 or self.content[i-1] != "\r"): #unix line endings - change to windows.
				self.addChange(ChangeLineEnding(i))

class Change(object):
	def __init__(self, idx, do=True):
		self.idx = idx
		self.do = do
	def __repr__(self):
		return "Change(%s) at %i" %("Y" if self.do else "N", self.idx)

class UnicodeDoubleQuote(Change):
	pass
class UnicodeSingleQuote(Change):
	pass
class NonAnsiCharacter(Change):
	pass
class ChangeLineEnding(Change):
	pass

c = Cleaner(files)

print c.getChanges()
