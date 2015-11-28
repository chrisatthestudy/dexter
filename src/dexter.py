#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Dexter
Text-file indexer

Usage:
  dexter [-vr] index [<path>]
  dexter [-vri] find <word> [in <path>]
  dexter [-vria] list [in <path>] [max <count>]
  dexter -h | --help
  dexter --version

Options:
  index [<path>]  Creates an index file for the specified path
  find <word> [in <path>] Searches for the specified word
  list [in <path>] [max <count>] Lists all the words found
  -h --help     Show this screen
  --version     Show version
  -v --verbose  Show messages
  -r --recurse  Recurse into sub-directories
  -i --reindex  For 'find' and 'list' forces a reindex even if an index exists
  -a --abbrev   Show abbreviated list (word, line, and filename only, no path)
"""

# Standard library imports
import os
import glob
import collections
import re

# Third party imports
from docopt import docopt

# Application specific imports

class Dexter():

    """
    Main processor class, with Dexter.execute() as the entry-point.
    """

    # ----------------------------------------------------------------------
    # Main entry point and command functions
    # ----------------------------------------------------------------------
    
    def execute(self, params):
        """
        Main entry point. 

        params - a fully-populated docopt params object
        """
        self.params = params

        self.dictionary = {}

        self.ignore_words = [
            "all",
            "any",
            "and",
            "are",
            "but",
            "for",
            "from",
            "have",
            "its",
            "it's",
            "not",
            "the",
            "their",
            "there",
            "they",
            "that",
            "this",
            "too",
            "was",
            "were"
            ]
        
        # Retrieve the command-line options
        self.verbose = self.params["--verbose"]
        self.recurse = self.params["--recurse"]
        self.abbreviate = self.params["--abbrev"]
        self.path = self.params["<path>"]
        self.word = self.params["<word>"]
        self.reindex = self.params["--reindex"]
        self.count = self.params["<count>"]
        if not self.count:
            self.count = -1
        else:
            self.count = int(self.count)

        self.read_ignore_file()

        # Ensure we have valid options
        if self.verify_path():
            
            # Call the requested command
            if self.params["index"]:
                self.make_index()
            elif self.params["find"]:
                self.find_word()
            elif self.params["list"]:
                self.list_words()
                
        return True

    def make_index(self):
        """
        Creates an index file in the target path, populating it from
        the contents of the text-files found in the path.
        """
        self.report("Building index for %s" % self.path)
        files = self.get_files(self.path)
        self.index_files(files)
        self.save_index()

    def index_files(self, file_list):
        """
        Scans the text-files found in the supplied list, recursively
        scanning any sub-folders found, provided the recurse option
        has been set.
        """
        for filespec in file_list:
            if os.path.isdir(filespec):
                self.report("Building index for %s" % filespec)
                self.index_files(self.get_files(filespec))
            else:
                self.scan_file(filespec)
            
    def find_word(self):
        """
        Searches for the specified word in the directory. Creates a new
        index file if one does not already exist, or if the --reindex
        parameter is specified.
        """
        self.report("Searching for %s" % self.word)

        if self.reindex or not self.index_exists():
            self.make_index()
        else:
            self.read_index()
        
        try:
            # Retrieve the tuple of all the locations where this word was
            # found, if any. This will raise a KeyError if the word was
            # not found.
            print "Searching for %s" % self.word.lower()
            locations = self.dictionary[self.word.lower()]
            
            # List all the line numbers from each location
            current_location = ""
            lines = ""
            print "Found at:"
            for location in locations:
                if current_location != location[0]:
                    if lines != "":
                        print "", "", lines
                        lines = ""
                    current_location = location[0]
                    print "", current_location
                lines += "%d " % location[1]
            if lines != "":
                print "", "", lines
            
        except KeyError:
            print "'%s' not found" % self.word

    def list_words(self):
        """
        Lists all the words in the index of the directory. Creates a new
        index file if one does not already exist, or if the --reindex
        parameter is specified.
        """
        self.report("Listing all words in %s" % self.path)

        if self.reindex or not self.index_exists():
            self.make_index()
        else:
            self.read_index()
            
        # Temporary version: just list the contents of the dictionary
        sorted_words = collections.OrderedDict(sorted(self.dictionary.items()))
        count = 0
        if self.count == -1:
            self.count = len(sorted_words)

        for word, locations in sorted_words.iteritems():
            count += 1
            if count <= self.count:
                if self.abbreviate:
                    print "%s %s" % (word.strip(), self.book_index_entry(locations))
                else:
                    for location in locations:
                        print "{:20}|{:06d}|{}".format(word, location[1], location[0])
            else:
                break        

    def book_index_entry(self, locations):
        """
        Scans the supplied list of filenames and numbers and builds a book-style
        index out of them.
        """
        current_filename = ""
        entries = {}
        numbers = []
        # locations is the list of filenames and line numbers for a specific word
        for location in locations:
            # Extract the filename and number
            filename = os.path.basename(location[0])
            number = location[1]
            
            # If this is a new filename, begin a new list of numbers, against
            # this filename
            if filename != current_filename:
                current_filename = filename
                entries[current_filename] = []
                
            # Add the number to the list of numbers against the filename
            entries[current_filename].append(number)

        # Build the final list so that each entry consists of the filename
        # followed by the list of line numbers in that file
        result = []
        for filename, numbers in entries.iteritems():
            result.append("\n\t%s, %s" % (filename, ", ".join(map(str, numbers))))
        return "; ".join(result)
        
    
    # ----------------------------------------------------------------------
    # Main processing functions
    # ----------------------------------------------------------------------

    def scan_file(self, filespec):
        """
        Scans the specified file, extracting all the words it can find,
        and returning a list of them.
        """
        words = []

        self.report("Scanning %s" % filespec)

        with open(filespec, 'r') as f:
            line_number = 1
            for line in f:
                words = self.scan_line(line)
                for word in words:
                    if len(word) > 2 and not word in self.ignore_words:
                        self.add_to_dictionary(word, filespec, line_number)
                line_number += 1

    def scan_line(self, line):
        """
        Scans the supplied line for words, returning a list of all the
        words found.
        """
        words = []
        word = ""
        alpha = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        for char in line:
            if char in alpha:
                word += char
            else:
                if word.strip() != "":
                    words.append(word.strip().lower())
                word = ""

        return words

    def add_to_dictionary(self, word, filespec, line_number):
        """
        Adds the supplied word to the dictionary, or updates an existing
        word with the additional details.
        """
        if not word in self.dictionary:
            self.dictionary[word] = [(filespec, line_number)]
        else:
            self.dictionary[word].append((filespec, line_number))

    def read_ignore_file(self):
        """
        Reads the list of 'ignore' words from file.
        """
        filespec = os.path.join(os.path.expanduser("~"), ".dexter", "dexter.ignore")
        if os.path.exists(filespec):
            with open(os.path.join(os.path.expanduser("~"), ".dexter", "dexter.ignore"), "r") as f:
                self.ignore_words = f.read().splitlines()
        else:
            self.write_ignore_file()

    def write_ignore_file(self):
        """
        Writes the current list of 'ignore' files as the default list
        """
        filespec = os.path.join(os.path.expanduser("~"), ".dexter")
        if not os.path.exists(filespec):
            os.makedirs(filespec)
        with open(os.path.join(filespec, "dexter.ignore"), "w") as f:
            for word in self.ignore_words:
                f.write("%s\n" % word)
            
    def read_index(self):
        """
        Reads the dexter.index file and imports the contents. Assumes that the
        file has already been confirmed to exist.
        """
        self.dictionary = {}
        with open(os.path.join(self.path, "dexter.index"), "r") as f:
            for line in f:
                line = line.strip()
                (word, line_number, filespec) = line.split("|")
                self.add_to_dictionary(word.strip(), filespec, int(line_number))
                
    def save_index(self):
        """
        Saves the dexter.index file into the path given on the command-line,
        or to the current working directory by default.
        """
        sorted_words = collections.OrderedDict(sorted(self.dictionary.items()))
        with open(os.path.join(self.path, "dexter.index"), "w") as f:
            for word, locations in sorted_words.iteritems():
                for location in locations:
                    f.write("{:20}|{:06d}|{}\n".format(word, location[1], location[0]))
    
    # ----------------------------------------------------------------------
    # Support functions
    # ----------------------------------------------------------------------
    
    def verify_path(self):
        """
        If no path is supplied, the current working directory is
        used instead.
        
        Checks that the path is valid. If it is not, an error message is
        printed, and the function returns False, otherwise it returns True.
        """
        if not self.path:
            self.path = os.getcwd()

        if not os.path.exists(self.path):
            print "Path not found: %s" % self.path
            return False
        else:
            return True

    def index_exists(self):
        """
        Returns True if an index file (dexter.index) exists in the
        specified path.
        """
        filespec = os.path.join(self.path, "dexter.index")
        return os.path.exists(filespec)
    
    def report(self, message):
        """
        Prints the supplied message, provided that  the --verbose option has
        been specified.
        """
        if self.verbose:
            print message

    def get_files(self, path):
        """
        Returns a list of the textfiles in the specified path.
        """
        base_list = glob.glob(os.path.join(path, "*"))
        files = [filespec for filespec in base_list if self.is_textfile(filespec) or (os.path.isdir(filespec) and self.recurse)]
        return files

    def is_textfile(self, filespec):
        """
        Returns True if the supplied filespec appears to be a text file. If
        the file has an extension which usually indicates a text file, this
        test automatically returns True, otherwise it returns False.

        TODO: implement a decent check
        """
        filename, ext = os.path.splitext(filespec)
        return (ext in [".txt", ".py", ".cpp", ".c", ".h", ".hpp", ".pas", ".sql"])
    
if (__name__ == "__main__"):
    params = docopt(__doc__, version='Dexter, v0.0.7')

    # print params
    
    api = Dexter()
    api.execute(params)

