import re, random
import sys
import json
import requests
import urllib
import pandas as pd
import numpy as np
from .util import send_request, get_raw_question
import lib.statement as statements
from .repair import repair

def collapse_fields(row):
    row['fields'] = {
        'Front': row['question'],
        'Back': row['answer']
    }
    row['tags'] = [row['tag']]
    row = row[['fields','tags']]
    return row

def expand_fields(row):
    row['question'] = row['fields']['Front']
    row['answer'] = row['fields']['Back']

def get_params_from_dataframe(notes_frame):
    notes_frame['fields'] = None
    notes_frame['tags'] = None
    if 'answer_y' in notes_frame.columns:
        notes_frame['answer'] = notes_frame['answer_y']
    if 'question_y' in notes_frame.columns:
        notes_frame['question'] = notes_frame['question_y']
    result = []
    for ind, row in notes_frame.iterrows():
        row = collapse_fields(row)
        result.append(row)
    notes_frame = pd.DataFrame(result)

    notes_frame['deckName'] = 'Study'
    notes_frame['modelName'] = 'Basic (type in the answer)'

    listable_notes = [row.to_dict() for index,row in notes_frame.iterrows()]
    notes = json.dumps(listable_notes)
    params =  { 'notes': notes }

    return listable_notes

def get_current_anki_cards_as_dataframe():
    params = {
        "query": ""
    }

    response = send_request('findCards',params)

    params = {
        'cards' : response
    }

    response = send_request('cardsInfo',params)

    res = json.dumps(response)
    df = pd.read_json(res,orient='records')

    df['question'] = df['fields'].apply(lambda x: x['Front']['value'])
    df['raw_question'] = df['fields'].apply(lambda x: get_raw_question(x['Front']['value']))
    df['answer'] = df['fields'].apply(lambda x: x['Back']['value'])

    statements.set_old_frame(df)

# this code is such a mess, please fix
def remove_old_cards(old_frame, new_frame, max_new):
    if old_frame.empty:
        return new_frame

    new_frame['raw_question'] = new_frame['question'].apply(lambda x: get_raw_question(x))
    old_frame['question'] = old_frame['fields'].apply(lambda x: x['Front']['value'])
    old_frame['raw_question'] = old_frame['fields'].apply(lambda x: get_raw_question(x['Front']['value']))
    old_frame['answer'] = old_frame['fields'].apply(lambda x: x['Back']['value'])
    should_quit = False
    try:
        temp = pd.concat(g for _, g in new_frame.groupby(["raw_question","answer"]) if len(g) > 1)
        should_quit = True
    except:
        try:
            temp = pd.concat(g for _, g in old_frame.groupby(["raw_question","answer"]) if len(g) > 1)
            should_quit = True
        except:
            pass
    
    if should_quit:
        print(temp)
        print("Nonunique keys, see table above")
        sys.exit()
    
    to_remove = old_frame.merge(right=new_frame,how='outer',on=['raw_question','answer'],indicator=True,validate='one_to_one')
    to_remove = to_remove.loc[to_remove['_merge'] == 'left_only']
    to_repair = old_frame.merge(right=new_frame,how='inner',on=['raw_question','answer'],validate='one_to_one')
    to_create = old_frame.merge(right=new_frame,how='outer',on=['raw_question','answer'],indicator=True,validate='one_to_one')
    to_create = to_create.loc[to_create['_merge'] == 'right_only']

    if len(to_remove) > 0:
        print("\nsuspending " + str(len(to_remove)) + " cards")
        # print(to_remove.tail(10))
        params = {
            'cards': to_remove['cardId'].astype(dtype=np.dtype(np.int64)).to_numpy().tolist()
        }
        note_ids = send_request('suspend',params)

    if len(to_repair) > 0:
        repair(to_repair, max_new)

    return to_create

def add_notes_to_anki(notes_frame, max_new):
    old_frame = statements.get_old_frame()

    notes_frame = remove_old_cards(old_frame, notes_frame, max_new)

    # print(max_new)

    print(notes_frame)
    print('koooooooooooooooooooooooooooooooofers')

    statements.set_notes(notes_frame.copy())

    # print(notes_frame)
    
    statements.limit_new(max_new)

    notes_frame = statements.notes

    if len(notes_frame) > 0:
        print("\nadding " + str(len(notes_frame)) + " cards")
        listable_notes = get_params_from_dataframe(notes_frame)

        responses = []
        for note in listable_notes:
            params = {
                'note': note
            }
            response = send_request('addNote',params)
            if(response == None):
                print("Below note failed to add")
                print(note)
                print()
            responses.append(response)
        print(responses)
    else:
        print('No cards to add')