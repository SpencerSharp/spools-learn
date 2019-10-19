import re
import sys
import json
import requests
import urllib
import pandas as pd
import numpy as np
from .util import send_request

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
    return df

def remove_old_cards(old_frame, new_frame):
    old_frame['question'] = old_frame['fields'].apply(lambda x: x['Front']['value'])

    to_remove = old_frame.merge(right=new_frame,how='outer',on='question',indicator=True)
    expected_failures = to_remove.groupby('_merge').count()['question']['both']
    to_remove.replace(to_replace='right_only',value=np.nan,inplace=True)
    to_remove.replace(to_replace='both',value=np.nan,inplace=True)
    to_remove.dropna(subset=['_merge'],inplace=True)

    if len(to_remove) > 0:
        print("\nsuspending " + str(len(to_remove)) + " cards")
        params = {
            'cards': to_remove['cardId'].astype(dtype=np.dtype(np.int64)).to_numpy().tolist()
        }
        for ind,thing in to_remove.iterrows():
            print(thing)
        # print('-----------------------')
        # print(params)
        # print('-----------------------')
        # note_ids = send_request('areSuspended',params)
        # print('-----------------------')
        # print(note_ids)
        # print('-----------------------')
        
        note_ids = send_request('suspend',params)
        # print('-----------------------')
        # print(note_ids)
        # print('-----------------------')
        # note_ids = send_request('areSuspended',params)
        # print('-----------------------')
        # print(note_ids)
        # print('-----------------------')

        # params = {
        #     'notes': note_ids
        # }

        # result = send_request('deleteNotes',params)
    to_unsuspend = new_frame.merge(right=old_frame,how='left',on='question',indicator=True, validate='one_to_one', suffixes=(True, False))
    to_unsuspend = to_unsuspend[['question','cardId']]
    to_unsuspend.dropna(axis=0,inplace=True)

    if len(to_unsuspend) > 0:
        print("\nunsuspending " + str(len(to_unsuspend)) + " cards")
        params = {
            'cards': to_unsuspend['cardId'].astype(dtype=np.dtype(np.int64)).to_numpy().tolist()
        }
        for ind,thing in to_unsuspend.iterrows():
            print(thing['question'])
        note_ids = send_request('unsuspend',params)

    to_add = old_frame.merge(right=new_frame,how='outer',on='question',indicator=True)
    to_add.replace(to_replace='left_only',value=np.nan,inplace=True)
    to_add.replace(to_replace='both',value=np.nan,inplace=True)
    to_add.dropna(subset=['_merge'],inplace=True)
    return to_add

def add_notes_to_anki(notes_frame):
    old_frame = get_current_anki_cards_as_dataframe()

    notes_frame = remove_old_cards(old_frame, notes_frame)

    if len(notes_frame) > 0:
        print("\nadding " + str(len(notes_frame)) + " cards")
        listable_notes = get_params_from_dataframe(notes_frame)

        responses = []
        for note in listable_notes:
            params = {
                'note': note
            }
            print(note)
            print()
            response = send_request('addNote',params)
            responses.append(response)
        print(responses)