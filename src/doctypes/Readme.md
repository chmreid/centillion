# Overview

## Submodule Files and Organization

Doctype class submodule organization, organized in logical order:

- registry.py contains the DoctypeRegistry metaclass
    - used by all doctypes
    - lookup table from doctype to class reference

- doctype.py contains the Doctype base class
    - defines the common schema
    - defines common functionality among all doctypes
    - implements virtual methods

- github.py contains Github Doctype classes
    - utility functions related to Github
    - Github base doctype for common Github functionality
    - Github issue/PR doctype
    - Github file doctype
    - Github markdown doctype

- gdrive.py contains Google Drive Doctype classes
    - utility funtions related to Google Drive
    - Google Drive base doctype for common functionality
    - Google Drive file
    - Google Drive docx

- content.py contains helper methods for parsing content
    - intended to be used by all doctypes
    - used when there is a content field in markdown
    - implements parsers, markdown to html translators


## Doctype Classes

### Required Functionality

All doctype classes must implement the following functionality:

- a constructor (parses credentials section of config file to get credentials info as needed)
- a way to validate credentials
- a way to get a list of "remote" documents of the form (last modified date, document id)
- a way to get details of a document given its document ID
- a function to translate search results from whoosh into search results that can be rendered
  as HTML using Jinja templates
- a function to return a Jinja template to use to render a search result of the given doctype

This seems like a lot of work, but the doctype class is central to centillion and interfaces with
every other submodule.

### Lifecycle of a Doctype

Let's look at the lifecycle of a Doctype instance to see how the Doctype classes interface
with the rest of centillion.

- The search submodule parses the configuration file's credentials section and creates Doctype classes
  based on the information found.

- The constructor and validate credentials method are called by the search submodule, and ensure the
  credentials provided in the config file work.

- The search submodule uses the get remote list method (to get a list of remote documents and their
  last modified date) when updating the search index, specifically when determining what documents
  to update in the index.

- The search submodule uses the get by ID method, which returns details of a document given its document
  ID, when updating the search index, specifically when it determines a particular document needs
  to be updated in the search index.

- The webapp submodule uses the method to translate from whoosh search results to search results that
  are ready to be used in Jinja HTML templates. The webapp submodule calls the `search()` method of
  `whoosh.search`, but this returns "raw" document fields. The translation method turns
  markdown into HTML, formats datetime stamps, fixes links, etc.

- The webapp submodule uses the Jinja template to display each search result. Once the method to translate
  whoosh search results to Jinja-ready search results, the webapp submodule combines this search result with
  the doctype Jinja template to render each search result.


## Tests

Two test suites for doctypes:

- standalone tests - test static functionality that does not require the use of any API
- integration tests - test integrated class behavior using real API keys and calls


