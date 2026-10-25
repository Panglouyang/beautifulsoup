"""Rename b to blockquote during parsing and save the result."""
from _common import main
from bs4 import SoupReplacer

if __name__ == "__main__":
    main("Replace b with blockquote during parsing", replacer=SoupReplacer("b", "blockquote"), save=True)
