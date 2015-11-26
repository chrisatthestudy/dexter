# Dexter
_Text-file indexer_

## Overview
Dexter indexes a directory (and optionally any sub-directories), locating
all the text-files and creating a dictionary of all the words that it finds.

The dictionary can subsequently be searched, and Dexter will return a list
of the file names and line numbers where a specified word can be found.

## Usage

    dexter [-vr] index [<path>]
    dexter [-vri] find <word> [in <path>]
    dexter [-vria] list [in <path>] [max <count>]
    dexter -h | --help
    dexter --version

    Options:
      index [<path>]  Creates an index file for the specified path
      find <word> [in <path>] Searches for the specified word
      dexter list [in <path>] [max <count>] Lists all the words found
      -h --help     Show this screen
      --version     Show version
      -v --verbose  Show messages
      -r --recurse  Recurse into sub-directories
      -i --reindex  For 'find' and 'list' forces a reindex even if an index exists
      -a --abbrev   Show abbreviate list (word, line, and filename only, no path)

Note that not all of the options have been fully implemented in this version.

## Dependencies

* Python 2.7+
