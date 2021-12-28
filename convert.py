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
    def __init__(self, oldRegex, newRegex,
                 dryrun=True,
                 generate_bash=True,
                 modifyDirs=True,
                 modifyFiles=True,
                 translateNum=0):

        self.oldRegex = oldRegex
        self.newRegex = newRegex

        # Translate every occurance in the filename
        self.translateNum = translateNum
        self.rootDir = "."

        self.generate_bash = generate_bash
        self.dryrun = dryrun
        self.modifyFiles = modifyFiles
        self.modifyDirs = modifyDirs

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

    desc=""" Utility to bulk rename files, recursively
 This utility applies a regular expression rename to all files and directories.
It will rename leaf files before renaming higher-level directories.

It can wreck your filesystem, so try running with dry-run turned on first.

Calling it with --in-re='' --out-re='_' will rewrite all space characters to
underscores.

Examples:
    # Replace every _-_ by _
    rename.py --in-re='_-_' --out-re='-'

    # Replace at max 3 _ by -
    rename.py --in-re='_' --out-re='-' --count=3

    # Only look at toplevel
    rename.py --in-re='_' --out-re='-' --recursive=False

    # Don't modify files, just show what it would do
    rename.py --in-re='_' --out-re='-' --dry-run


"""
    # TODO use argparse here, looks darn complicated.
    desc=""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-i', '--in-regex', type=ascii, required=True,
                        help="Regular expression applied to existing filename")
    parser.add_argument('-o', '--out-regex', type=ascii, required=True,
                        help="Expression to write in new filename")
    parser.add_argument('-n', '--dry-run',
                        help="If true, do not modify files")
    parser.add_argument('-r', '--recursive',
                        help="If true, recursively traverse filesystem")

    args = parser.parse_args()

    print(args)
    oldRegex = args.in_regex
    newRegex = args.out_regex
    dryrun = args.dry_run == None

    print(r"""Renaming with in_re="%s" and out_re="%s", dryrun=%s """ % (oldRegex, newRegex, dryrun))
    d = dirNamer(oldRegex, newRegex, dryrun)
    d.qq()

if __name__ == "__main__":
    main()
