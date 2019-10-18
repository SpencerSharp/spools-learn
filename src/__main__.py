import subprocess
import os
from pathlib import Path
import pandas as pd
import re
import urllib
import json
from datetime import datetime, timedelta

from lib.anki import add_notes_to_anki
import lib.statement as statements
import lib.ipc as ipc
import lib.util as util

def get_dates():
    try:
        return dates
    except:
        return {}

def add_due_date(line, tag):
    line = line[4:]
    while line[0] == ' ':
        line = line[1:]
    global dates
    try:
        dates[tag] = datetime.strptime(line, '%Y-%m-%d')
    except:
        dates = {}
    dates[tag] = datetime.strptime(line, '%Y-%m-%d')

def parse_info_file(file):
    line = util.getline(file)
    while line != None:
        if re.match('Due.*', line):
            add_due_date(line, util.get_tag(file.name))
        elif re.match('_.*?_', line):
            set_header(file.name, line[1:-1])
        elif len(line) == 0:
            set_header(file.name, None)
        else:
            statements.add_statement(file, line)
        line = util.getline(file)

def parse_dir(directory):
    subdirs = [x for x in directory.iterdir() if x.is_dir()]

    ray = [x for x in directory.glob('*.info')]
    if(len(ray) > 0):
        anki_info_path = ray[0]
        with anki_info_path.open() as anki_info_file:
            parse_info_file(anki_info_file)
            tag = util.get_tag(anki_info_file.name)
            try:
                if tag in get_dates().keys():
                    due_date = get_dates()[tag]
                    if datetime.now() > (due_date + timedelta(days=1)):
                        statements.remove_statements_with_tag(tag)
            except:
                raise

    for subdir in subdirs:
        parse_dir(subdir)

#if ipc.create_process():
statements.set_notes(pd.DataFrame())
resources_directory = Path.home() / 'Documents' / 'Resources'
parse_dir(resources_directory)
add_notes_to_anki(statements.notes)