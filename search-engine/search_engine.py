#!/usr/bin/env python3
"""
search_engine.py -- Manages the tutorial search engine
    author: Lucas Vitalos
    date: 2019-05-04
"""
from pathlib import Path

from bs4 import BeautifulSoup
from bs4.element import Comment

from whoosh.fields import Schema, TEXT, ID
from whoosh.index import create_in, open_dir
from whoosh.qparser import MultifieldParser

DEFAULT_INDEX_DIRECTORY = Path.cwd() / 'search_index'
DEFAULT_SITES_DIRECTORY = Path.cwd() / 'sites'
DEFAULT_SCHEMA = Schema(title=TEXT(stored=True), content=TEXT(stored=True), path=ID(stored=True))
DEFAULT_QUERY_PARSER = MultifieldParser(('title', 'content'), schema=DEFAULT_SCHEMA)
DEFAULT_RESULT_LIMIT = 10


def tag_visible(element):
    """Filter predicate for tags that produce visible text on a 
    webpage.

    credit: jbochi on StackOverflow (https://stackoverflow.com/a/1983219/11354490)
    """
    if element.parent.name in {'style', 'script', 'head', 'title', 'meta', '[document]'}:
        return False
    if isinstance(element, Comment):
        return False
    return True


def text_from_html(html):
    """Function for retrieving the visible text from an html document.

    credit: jbochi on StackOverflow (https://stackoverflow.com/a/1983219/11354490)
    """
    texts = html.findAll(text=True)
    visible_texts = filter(tag_visible, texts)
    return ' '.join(t.strip() for t in visible_texts)


def recurse(directory):
    """List all files below the given directory. Does not the list the
    directory itself or any subdirectories.
    """
    if not directory.is_dir():
        raise ValueError('ERROR: tried to recurse() a path that is not a directory')
    directories_to_explore = [directory.iterdir()]
    while directories_to_explore:
        try:
            next_path = next(directories_to_explore[-1])
            if next_path.is_dir():
                directories_to_explore.append(next_path.iterdir())
            else:
                yield next_path
        except StopIteration:
            directories_to_explore.pop()


class SearchEngine:
    """The interface to the search index for our tutorial search
    engine. Creates the index on instantiation if it doesn't exist yet.
    """
    def __init__(self, index_directory=DEFAULT_INDEX_DIRECTORY, sites_directory=DEFAULT_SITES_DIRECTORY,
                 schema=DEFAULT_SCHEMA, query_parser = DEFAULT_QUERY_PARSER):
        if not sites_directory.is_dir():
            raise ValueError(f'ERROR: Given sites path {sites_directory} is not a directory')
        
        if not index_directory.exists():
            index_directory.mkdir()
            self.index = create_in(str(index_directory), schema)
            writer = self.index.writer()
            for document in recurse(sites_directory):
                with document.open() as doc_stream:
                    html = BeautifulSoup(doc_stream, 'lxml')
                    writer.add_document(title=str(html.title), content=text_from_html(html), path=str(document))
            writer.commit()
        elif not index_directory.is_dir():
            raise ValueError(f'ERROR: Given index path {index_directory} is not a directory')
        else:
            self.index = open_dir(index_directory)
        
        self.query_parser = query_parser


    def search(self, query_string, result_limit=DEFAULT_RESULT_LIMIT):
        with self.index.searcher() as searcher:
            query = self.query_parser.parse(query_string)
            results = searcher.search(query, limit=result_limit)
            return [result.fields() for result in results]
