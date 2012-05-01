import sys
import fnmatch #for unix-shell-style support in file matches.
import os

unparsedCmds = sys.argv[1:]

matchFiles = unparsedCmds[0] if len(unparsedCmds) else "*"
searchDir = unparsedCmds[1] if len(unparsedCmds) > 1 else "."

class Cleaner(object):
	def __init__(self, matchFiles="*", searchDir="."):
		self.matchFiles = matchFiles
		self.searchDir = searchDir
	def getMatchedFiles(self):
		allInDir = os.listdir(self.searchDir)
		matched = [p for p in allInDir if fnmatch.fnmatch(p, self.matchFiles)]
		return matched
	def getChanges(self):
		pass

class ChangeSet(object):
	pass

class Change(object):
	pass

c = Cleaner(matchFiles, searchDir)
print c.getMatchedFiles()
