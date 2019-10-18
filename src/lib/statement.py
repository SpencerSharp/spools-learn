import os
import base64
from pathlib import Path
import requests
import sys
import pandas as pd
import numpy as np
import re
import lib.util as util
from datetime import datetime

def set_notes(new_notes):
    global notes
    notes = new_notes

def remove_statements_with_tag(tag):
    temp = notes.replace(tag, value=np.nan)
    set_notes(temp.dropna(subset=['tag']))

def add_statement(file, line):
    global tag
    tag = util.get_tag(file.name)

    if re.match('~.+?~', line):
        description = util.getline(file)
        latex = util.getline(file)
        add_equation_statement(line, description, latex)
    elif len(re.findall('<(.+?)>',line)) != 0:
        clozes = re.findall('<(.+?)>',line)
        add_cloze_statement(line, clozes)
    elif re.search('^.*?\\|.*?$', line) != None:
        definition = re.search('^.*?\\|.*?$', line)
        add_definition_statement(definition)
    else:
        answer = util.getline(file)
        add_simple_statement(line, answer)

def add_simple_statement(question, answer):
    try:
        new_id = len(notes)
    except NameError:
        new_id = 0

    question = util.sub_latex(question)
    answer = util.sub_latex(answer)

    fields = ['question','answer','tag']
    columns = [question, answer, tag]

    note = pd.Series(index=fields, data=columns, name=new_id)

    set_notes(notes.append(note))

def add_equation_statement(name, description, latex):
    clozes = re.finditer('<(.+?)>',latex)
    add_cloze_statement(latex, clozes)

    add_simple_statement(description, name)
    add_simple_statement(latex, name)

def add_cloze_statement(question, clozes):
    for cloze in clozes:
        if type(cloze) != type(''):
            prompt = question[:cloze.start()]
            prompt += '?'
            prompt += question[cloze.end():]
            cloze = question[cloze.start()+1:cloze.end()-1]
        else:
            prompt = re.sub(re.escape('<'+cloze+'>'), '[...]', question, count=1)
        add_simple_statement(prompt, cloze)

def add_definition_statement(definition):
    definition = definition.group(0)
    question = re.search('^(.*) \\|', definition)
    question = question.group(0)
    question = question[:-2]
    answer = re.search('\\| (.*)$', definition)
    answer = answer.group(0)
    answer = answer[2:]

    hint = 'Definition: '
    filename = answer + '.mp3'
    audio_str = '[sound:{}]'.format(filename)

    params = {
        'filename': filename
    }

    # is_already_saved = send_request('retrieveMediaFile', params)
    is_already_saved = True
    if not is_already_saved:
        from google.cloud import texttospeech

        client = texttospeech.TextToSpeechClient()

        synthesis_input = texttospeech.types.SynthesisInput(text=answer)

        voice = texttospeech.types.VoiceSelectionParams(
            language_code=os.getenv('TTS_LANG'),
            ssml_gender=texttospeech.enums.SsmlVoiceGender.MALE,
            name=os.getenv('TTS_VOICE'))

        audio_config = texttospeech.types.AudioConfig(
            audio_encoding=texttospeech.enums.AudioEncoding.MP3)

        response = client.synthesize_speech(synthesis_input, voice, audio_config)

        params = {
            'filename': filename,
            'data': base64.standard_b64encode(response.audio_content).decode()
        }

        send_request('storeMediaFile', params)

    add_simple_statement(hint + question, answer + audio_str)
    add_simple_statement(answer+audio_str, question)