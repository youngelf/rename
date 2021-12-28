#!/usr/bin/env python

# New beginnings: writing convert.pl in python.  Should be fun


import argparse, os, re, sys

# Find all files in this directory
# TODO: allow changing the target directory
# TODO: dry-run mode
# TODO: recursive mode
# TODO: generate-bash mode
# TODO: safe mode (never overwrite)
# TODO: transaction mode: either all should succeed or rollback.

class dirNamer():
    def __init__(self, oldRegex, newRegex, translateNum=0):
        self.oldRegex = oldRegex
        self.newRegex = newRegex

        # Translate every occurance in the filename
        self.translateNum = translateNum
        self.rootDir = "."

        self.generate_bash = True
        self.dryrun = True
        self.modifyFiles = True
        self.modifyDirs = True

    def qq(self):
        # If we are to recurse, we should change the leaves first, otherwise
        # if we modify directory names, then the behavior of rename is shakey
        for dirName, subdirList, fileList in os.walk(self.rootDir, topdown=False):
            if (self.generate_bash):
                print(r"""# Directory "%s" """ % dirName)
            if self.modifyFiles:
                for filename in fileList:
                    newName = self.newName(filename)
                    if (self.generate_bash):
                        print(r"""mv "%s" "%s" """ % (filename, newName))
                    if not self.dryrun:
                        self.rename(filename, newName)
            if self.modifyDirs:
                for subdir in subdirList:
                    newName = self.newName(subdir)
                    if (self.generate_bash):
                        print(r"""mv "%s" "%s" """ % (subdir, newName))
                    if not self.dryrun:
                        self.rename(subdir, newName)

    def newName(self, oldName):
        return re.sub(self.oldRegex, self.newRegex, oldName, count=self.translateNum)

    def rename(self, oldName, newName, safe=True):
        """Renames file oldName to newName

        If safe=true, the rename does not modify existing files and returns.

        Returns True on success, False on failure
        """
        os.rename(oldName, newName)


def main():
    # Get the arguments here. For now, clobber spaces to underscores

# TODO use argparse here, looks darn complicated.

    oldRegex = sys.argv[1]
    newRegex = sys.argv[2]
    dryrun = sys.argv[3] == '-n'

    print(r"""Renaming with in_re="%s" and out_re="%s" """ % (oldRegex, newRegex))
    d = dirNamer(oldRegex, newRegex)
    d.qq()

if __name__ == "__main__":
    main()
