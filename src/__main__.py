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
            add_due_date(line, util.get_tag(file))
        elif re.match('_.*?_', line):
            util.set_header(file, line[1:-1])
        elif len(line) == 0:
            util.set_header(file, None)
        else:
            statements.add_statement(file, line)
        line = util.getline(file)
    util.set_header(file, None)

def parse_dir(directory):
    subdirs = [x for x in directory.iterdir() if x.is_dir()]

    info_files = [x for x in directory.glob('*.info')]

    for anki_info_path in info_files:
        with anki_info_path.open() as anki_info_file:
            parse_info_file(anki_info_file)

    for subdir in subdirs:
        parse_dir(subdir)

#if ipc.create_process():
statements.set_notes(pd.DataFrame())
resources_directory = Path.home() / 'Documents' / 'Resources'
parse_dir(resources_directory)
statements.remove_statements_past_due(get_dates())
add_notes_to_anki(statements.notes)