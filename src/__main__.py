import os
from pathlib import Path
import pandas as pd
import re

from lib.anki import add_notes_to_anki
import lib.statement as statements
import lib.ipc as ipc

def parse_info_file(file):
    for line in file:
        question = line[:-1]
        if len(question) == 0:
            continue
        answer = None
        clozes = re.findall('<(.+?)>',line)
        definition = re.search('^.*?\\|.*?$', line)

        if len(clozes) == 0:
            clozes = None

        if clozes == None and definition == None:
            answer = file.readline()
            answer = answer[:-1]

        statements.add_statement(file, question, answer, clozes, definition)

def parse_dir(directory):
    subdirs = [x for x in directory.iterdir() if x.is_dir()]

    ray = [x for x in directory.glob('*.info')]
    if(len(ray) > 0):
        anki_info_path = ray[0]
        with anki_info_path.open() as anki_info_file:
            parse_info_file(anki_info_file)

    for subdir in subdirs:
        parse_dir(subdir)

if ipc.create_process():
    print('Background starting')
    resources_directory = Path.home() / 'Documents' / 'Resources'
    parse_dir(resources_directory)
    add_notes_to_anki(statements.notes)