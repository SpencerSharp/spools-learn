import re
from pathlib import Path
import json
import urllib

def getline(file):
    try:
        line = file.readline()
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

def sub_latex(line):
    latex = re.search(r'(.*?)\\\[ (.+?) \\\](.*?)', line)
    if latex != None:
        line = re.sub('<','',line)
        line = re.sub('>','',line)
        latex = re.search(r'(.*?)\\\[ (.+?) \\\](.*?)', line)
        start = re.search(r'.?\\\[', latex.group(0))
        start = start.group(0)
        if len(start) < 3 or start[0] != '\\':
            before = latex.group(1)
            after = latex.group(3)
            latex = latex.group(2)

            latex_start = '[$$]'
            latex_end = '[/$$]'

            

            line = before + latex_start + latex + latex_end + after
        else:
            line = re.sub(r'\\\\\[', '\[', line)
            line = re.sub(r'\\\\\]', '\]', line)
    return line

def set_header(file, header):
    filepath = Path(file.name).as_posix()
    global tags
    try:
        if header == None:
            tags.pop(filepath,None)
        else:
            tags[filepath] = filepath + '::' + header
    except:
        tags = {}
    if header == None:
        tags.pop(filepath,None)
    else:
        tags[filepath] = filepath + '::' + header

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
    return tag