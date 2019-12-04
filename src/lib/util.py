import re
from pathlib import Path
import json
import urllib

def getline(file):
    try:
        line = file.readline()
        if len(line) == 1:
            return ''
        while re.match('\\s',line[0]):
            line = line[1:]
        while re.match('\\s',line[-1]):
            line = line[:-1]
        return line
    except:
        return None

def send_request(action, params):
    data = {
    'action': action,
    'version': 6,
    "params": params
    }

    requestJson = json.dumps(data).encode('utf-8')
    response = json.load(urllib.request.urlopen(urllib.request.Request('http://localhost:8765', requestJson)))

    result = response['result']

    return result

def sub_question(line, tag, raw_tag):
    line = sub_latex(line)
    if tag != raw_tag:
        header = tag.split("::")[-1]
        header = re.sub("-"," ",header)
        line = header + ": " + line
    return line

def sub_answer(line, tag, raw_tag):
    line = sub_latex(line)
    return line

def get_raw_question(question):
    raw_question = re.sub('^(\w[ ]?)+?: ', '', question)
    return raw_question

def sub_latex(line):
    if line == None:
        return None
    latex = re.search(r"(.*?)\\\[(.+?)\\\](.*?)", line)
    if latex != None:
        before = latex.group(1)
        after = latex.group(3)
        latex = latex.group(2)
        latex = re.sub("[...]","?",latex)

        latex_start = '[$$]'
        latex_end = '[/$$]'

        line = before + latex_start + latex + latex_end + after
    return line

def set_header(file, header):
    global tags
    filepath = Path(file.name).as_posix()
    try:
        temp = tags.keys()
    except:
        tags = {}
    if header == None:
        if filepath in tags.keys():
            del tags[filepath]
    else:
        tags[filepath] = re.sub(" ","-",get_raw_tag(file) + '::' + header)

def get_tag(file):
    filepath = Path(file.name).as_posix()
    try:
        return tags[filepath]
    except:
        return get_raw_tag(file)

def get_raw_tag(file):
    resources_directory = Path.home() / 'Documents' / 'Resources'
    relative_tag = Path(file.name).relative_to(resources_directory)
    tag = '::'.join(relative_tag.parts[:-1])
    tag = re.sub(' ','-',tag)
    return tag

