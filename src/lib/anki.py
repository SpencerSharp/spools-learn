import json
import requests
import urllib
import pandas as pd
import numpy as np

def collapse_fields(row):
    row['fields'] = {
    'Front': row['question'],
    'Back': row['answer']
    }
    row['tags'] = [row['tag']]
    return row

def expand_fields(row):
    row['question'] = row['fields']['Front']
    row['answer'] = row['fields']['Back']

def get_params_from_dataframe(notes_frame):
    notes_frame['fields'] = None
    notes_frame['tags'] = None
    notes_frame.apply(func=collapse_fields,axis=1)
    notes_frame.drop(labels=['question','answer', 'tag'],axis=1,inplace=True)
    notes_frame['deckName'] = 'Study'
    notes_frame['modelName'] = 'Basic'
    params =  { 'notes': notes_frame.to_dict(orient='records') }

    return params

def send_request(action, params):
    data = {
    'action': action,
    'version': 6,
    "params": params
    }

    requestJson = json.dumps(data).encode('utf-8')
    response = json.load(urllib.request.urlopen(urllib.request.Request('http://localhost:8765', requestJson)))

    return response['result']

def get_current_anki_cards_as_dataframe():
    params = {
        "query": ""
    }

    response = send_request('findCards',params)

    params = {
        'cards' : response
    }

    response = send_request('cardsInfo',params)

    return pd.read_json(json.dumps(response),orient='records')

def remove_old_cards(old_frame, new_frame):
    to_remove = old_frame.merge(right=new_frame,how='outer',on='question',indicator=True)
    to_remove.replace(to_replace='right_only',value=np.nan,inplace=True)
    global expected_failures
    expected_failures = to_remove.groupby('_merge').count()['question']['both']
    to_remove.replace(to_replace='both',value=np.nan,inplace=True)
    to_remove.dropna(subset=['_merge'],inplace=True)

    if len(to_remove) > 0:
        params = {
            'cards': to_remove['cardId'].astype(dtype=np.dtype(np.int64)).to_numpy().tolist()
        }
        note_ids = send_request('cardsToNotes',params)

        params = {
            'notes': note_ids
        }

        if len(note_ids) > 0:
            print('Deleting ' + str(len(note_ids)) + ' cards')

        result = send_request('deleteNotes',params)

def add_notes_to_anki(notes_frame):
    old_frame = get_current_anki_cards_as_dataframe()

    remove_old_cards(old_frame, notes_frame)

    params = get_params_from_dataframe(notes_frame)

    response = send_request('addNotes',params)

    ind = 0
    failures = 0

    for item in response:
        row = notes_frame.loc[ind]
        if item == None:
            can_find = False
            for thing in old_frame['fields']:
                if thing['Front']['value'] == row['fields']['Front']:
                    can_find = True
            if not can_find:
                print(row['tags'])
            failures += 1
        ind += 1
    if errors > expected_failures:
        print(str(errors-expected_failures) + ' errors')