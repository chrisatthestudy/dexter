# Dexter
_Text-file indexer_

## Overview
Dexter indexes a directory (and optionally any sub-directories), locating
all the text-files and creating a dictionary of all the words that it finds.

The dictionary can subsequently be searched, and Dexter will return a list
of the file names and line numbers where a specified word can be found.

## Usage

Usage:
  dexter index [<path>]
  dexter find <word> [in <path>]
  dexter list [in <path>]
  dexter -h | --help
  dexter --version

Options:
  index [<path>]  Creates an index file for the specified path
  find <word> [in <path>] Searches for the specified word
  dexter list [for <path>] Lists all the words found
  -h --help     Show this screen.
  --version     Show version.
  -q --quiet    Suppress messages
  -r --recurse  Recurse into sub-directories
  -i --reindex  For 'find' and 'list' forces a reindex even if an index exists

Note that not all of the options have been fully implemented in this version.

## Dependencies

* Python 2.7+
