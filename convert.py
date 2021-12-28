#!/usr/bin/env python

# New beginnings: writing convert.pl in python.  Should be fun

import argparse, os, re, sys

# TODO: safe mode (never overwrite)
# TODO: transaction mode: either all should succeed or rollback.

class bulkRename():
    def __init__(self, oldRegex, newRegex,
                 rootDir=".",
                 dryrun=True,
                 generate_bash=True,
                 modifyDirs=True,
                 modifyFiles=True,
                 recursive=True,
                 translateNum=0):

        self.oldRegex = oldRegex
        self.newRegex = newRegex

        # Translate every occurance in the filename
        self.translateNum = translateNum
        self.rootDir = rootDir

        self.generate_bash = generate_bash
        self.dryrun = dryrun
        self.modifyFiles = modifyFiles
        self.modifyDirs = modifyDirs
        self.recursive = recursive

    def run(self):
        # If we are to recurse, we should change the leaves first, otherwise
        # if we modify directory names, then the behavior of rename is shakey
        if not self.recursive:
            # Only look at one level and quit
            dirName = self.rootDir
            if (self.generate_bash):
                print(r"""# Directory "%s" """ % dirName)
            if self.modifyFiles:
                for filename in os.listdir(dirName):
                    if os.path.isfile(dirName + "/" + filename):
                        self.rename(dirName, filename)
            return

        # The inner code. This uses Python's os.walk, and goes to the
        # leaves first (topdown=False) so that we modify the leaves,
        # and then the inner nodes. If we modify the inner nodes, then
        # the leaf renames become difficult as the path has shifted
        # during the loop.
        #
        # We only modify files if asked, similarly for directories.
        for dirName, subdirList, fileList in os.walk(self.rootDir, topdown=False):
            if (self.generate_bash):
                print(r"""# Examining: "%s" """ % dirName)

            if self.modifyFiles:
                for filename in fileList:
                    self.rename(dirName, filename)

            if self.modifyDirs:
                for subdir in subdirList:
                    self.rename(dirName, subdir)


    def rename(self, dirName, oldName):
        """Renames file oldName to newName.
        Prints out the shell code for Unix if generate_bash is True.
        Only prints out and doesn't do anything if dryrun is True.
        """
        newName = re.sub(self.oldRegex, self.newRegex, oldName, count=self.translateNum)

        # Only do something if newName and oldName differ
        if newName == oldName:
            return

        if self.generate_bash:
            print(r"""mv "%s" "%s" """ %
                  (dirName + "/" + oldName, dirName + "/" + newName))
        if not self.dryrun:
            os.rename(dirName + "/" + oldName, dirName + "/" + newName)


def main():
    usage=""" Utility to bulk rename files, recursively
 This utility applies a regular expression rename to all files and directories.
It will rename leaf files before renaming higher-level directories.

It can wreck your filesystem, so try running with dry-run turned on first.

Calling it with --in-re='' --out-re='_' will rewrite all space characters to
underscores.

Examples:
    # Replace every _-_ by _
    rename.py --in-regex='_-_' --out-regex='-'

    # Only look at toplevel
    rename.py --in-regex='_' --out-regex='-' --recursive=false

    # Don't modify files, just show what it would do
    rename.py --in-regex='_' --out-regex='-' --dry-run true

    # Rename "yy__<number>__xx" to "yy_<number>.xx"
    rename.py -i '__(\d+)__' -o "_\g<1>."

    # Rename "yy_._xx" to "yy.xx" (Notice the \. rather than . which
    # matches any one character!)
    rename.py -i '__\.__' -o "."

    It uses Python re.sub(...) syntax, so read up on that for
    positional rewrites, etc.

"""
    parser = argparse.ArgumentParser(usage=usage, description="Bulk rename files and directories" )
    binaryChoices = ['true', 't', 'false', 'f']

    parser.add_argument('-i', '--in-regex', type=ascii, required=True,
                        help="Regular expression applied to existing filename")
    parser.add_argument('-o', '--out-regex', type=ascii, required=True,
                        help="Expression to write in new filename")

    parser.add_argument('-d', '--dir', type=ascii, default=".",
                        help="If provided, the directory to modify. Otherwise, current directory")

    parser.add_argument('-md', '--modify-dirs', choices=binaryChoices,
                        help="If true, modify directories")
    parser.add_argument('-mf', '--modify-files', choices=binaryChoices,
                        help="If true, modify files")
    parser.add_argument('-n', '--dry-run', choices=binaryChoices,
                        help="If true, do not modify files")
    parser.add_argument('-r', '--recursive', choices=binaryChoices,
                        help="If true, recursively traverse filesystem")

    args = parser.parse_args()

    print("#", args)

    # At the commandline, we have to pass spaces in quotes. So remove
    # these, if they exist.  How does a user pass a quote
    oldRegex = removeDoubleQuotes(args.in_regex).replace('\\\\', '\\')
    newRegex = removeDoubleQuotes(args.out_regex).replace('\\\\', '\\')

    rootDir = removeDoubleQuotes(args.dir)

    modifyDirs = parseOptionalBool(args.modify_dirs, True)
    modifyFiles = parseOptionalBool(args.modify_files, True)
    dryrun = parseOptionalBool(args.dry_run, True)

    recursive = parseOptionalBool(args.recursive, True)

    print(r"""# Renaming with in_re="%s" and out_re="%s", dryrun=%s """ % (oldRegex, newRegex, dryrun))
    print(r"""# Renaming with modifyDirs="%s" and modifyFiles="%s" """ % (modifyDirs, modifyFiles))
    print(r"""# Renaming rootDir="%s" """ % rootDir)

    bulk = bulkRename(oldRegex, newRegex,
                      rootDir=rootDir,
                      dryrun=dryrun,
                      modifyFiles=modifyFiles,
                      modifyDirs=modifyDirs,
                      recursive=recursive)
    bulk.run()

def parseOptionalBool(inString, default=False):
    """Take an optional string representing a commandline argument.

    If it matches 't' return True,
    If it matches 'f' or 'false' return False,

    If it isn't a string, or none of the options, return the default
    value provided.
    """

    # I need to learn argparse, I'm sure this is doable from inside it.
    if inString == None or len(inString) == 0:
        return default

    if inString[0].lower() == 'f':
        return False
    if inString[0].lower() == 't':
        return True

    return default


def removeDoubleQuotes(inString):
    """Removes quotes, only if they exist both in the beginning and end of
    the string.  This is safer than string.strip("\"'") because that
    will remove from the front and end, but won't care if it is
    quoting the string, or just happens to exist somewhere in the string
    """
    # argparse adds extra ' at the beginning and end always, so remove
    # these.
    if (inString[0] == inString[-1] and inString[0] == "'"):
        inString = inString.strip("'")

    # Check if there's additional quoting added by the user, and
    # remove it.
    if (inString[0] == inString[-1]):
        q = inString[0]
        if (q in "\"'"):
            return inString.strip(q)

    # Safest to send the string back
    return inString


if __name__ == "__main__":
    main()
