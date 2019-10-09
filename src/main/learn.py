from pathlib import Path
import pandas as pd
import re

def parse_info_file(file):
    for line in file:
        question = line[:-1]
        answer = file.readline()
        clozes = re.findall('<(.+?)>',line)
        definition = re.search('^.*?\|.*?$', line)

        add_statement(question, answer, clozes, definition)

def parse_dir(directory):
    num_subdirs = len([x for x in directory.iterdir() if x.is_dir()])

    ray = [x for x in directory.glob('info.txt')]
    if(len(ray) > 0):
        anki_info_path = ray[0]
        with anki_info_path.open() as anki_info_file:
            parse_info_file(anki_info_file)

resources_directory = Path.home() / 'Documents' / 'Resources'
parse_dir(resources_directory)
add_notes_to_anki(notes)