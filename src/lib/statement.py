import pandas as pd
import re
from .util import sub_latex

def add_statement(file, question, answer, clozes=None, definition=None):
    global tag
    tag = file.name

    if answer != None:
        add_simple_statement(question, answer)
    if clozes != None:
        add_cloze_statement(question, clozes)
    elif definition != None:
        add_definition_statement(definition)

def add_simple_statement(question, answer):
    global notes
    try:
        new_id = len(notes)
    except NameError:
        notes = pd.DataFrame()
        new_id = 0

    sub_latex(question)

    fields = ['question','answer','tag']
    columns = [question, answer, tag]
    note = pd.Series(index=fields, data=columns, name=new_id)

    notes = notes.append(note)

def add_cloze_statement(question, clozes):
    for cloze in clozes:
        prompt = re.sub(re.escape('<'+cloze+'>'), '[...]', question)
        add_simple_statement(prompt, cloze)

def add_definition_statement(definition):
    definition = definition.group(0)
    question = re.search('^(.*)\\|', definition)
    question = question.group(0)
    question = question[:-2]
    answer = re.search('\\|(.*)$', definition)
    answer = answer.group(0)
    answer = answer[1:]

    hint = 'Definition: '

    add_simple_statement(hint + question, answer)
    add_simple_statement(answer, question)
