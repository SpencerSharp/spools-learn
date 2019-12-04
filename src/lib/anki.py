import re, random
import sys
import json
import requests
import urllib
import pandas as pd
import numpy as np
from .util import send_request, get_raw_question
import lib.statement as statements

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

    return df

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
    # to_remove.replace(to_replace='right_only',value=np.nan,inplace=True)
    # to_remove.replace(to_replace='both',value=np.nan,inplace=True)
    # to_remove.dropna(subset=['_merge'],inplace=True)
    if len(to_remove) > 0:
        print("\nsuspending " + str(len(to_remove)) + " cards")
        params = {
            'cards': to_remove['cardId'].astype(dtype=np.dtype(np.int64)).to_numpy().tolist()
        }
        note_ids = send_request('suspend',params)
        # result = send_request('deleteNotes',params)
        # params = {
        #     'notes': to_remove['note'].astype(dtype=np.dtype(np.int64)).to_numpy().tolist()
        # }
        # notes = send_request('notesInfo',params)
        # ind = -1
        # cards_to_suspend = []
        # for card in to_remove.iterrows():
        #     card_front = card['question']
        #     card_front = re.sub(heading_regex,'',card_front)
        #     for local_card in new_frame.iterrows():
        #         note_front = note['question']
        #         note_front = re.sub(heading_regex,'',card_front)
        #         if card_front == note_front:
        #             if card_back == note_back:
        #                 send_request('removeTags')
        #     ind += 1
        #     pos_question = to_remove.iloc[ind]['question']

    
    # to_unsuspend = new_frame.merge(right=old_frame,how='left',on='question',indicator=True, validate='one_to_one', suffixes=(True, False))

    # to_unsuspend = to_unsuspend[['question','cardId','note','tag']]
    # to_unsuspend.dropna(axis=0,inplace=True)

    if len(to_repair) > 0:
        print("\nrepairing " + str(len(to_repair)) + " cards")
        cardIds = to_repair['cardId'].astype(dtype=np.dtype(np.int64)).to_numpy().tolist()
        params = {
            'cards': cardIds,
            'complete': True
        }
        # for ind,thing in to_unsuspend.iterrows():
        #     print(thing['question'])
        card_intervals = send_request('getIntervals',params)
        leech_cards = []
        ind = 0
        for card in cardIds:
            intervals = card_intervals[ind]
            ind += 1
            if type(intervals) == type([]) and len(intervals) >= 2:
                if intervals[-1] == 1 and intervals[-2] == 1:
                    leech_cards.append(card)
        params = {
            'cards': leech_cards
        }
        print("resetting " + str(len(leech_cards)) + " cards")
        send_request('forgetCards',params)
        params = {
            'cards': cardIds
        }
        print("unsuspending " + str(len(cardIds)) + " cards")
        send_request('unsuspendCards',params)
        ind = 0
        while ind < len(to_repair):
            card = to_repair.iloc[ind]
            if card['queue'] == 0:
                for pos_tag in max_new.keys():
                    if pos_tag in card['tag']:
                        max_new[pos_tag] -= 1
            elif card['factor'] > 3000 or card['factor'] < 2000:
                ease = int(random.uniform(2.0,3.0)*1000.0)
                params = {
                    'card': int(card['cardId']),
                    'ease': ease
                }
                print('{} - Old ease: {} New ease: {}'.format(card['question_x'],card['factor'],ease))
                send_request('setEase',params)
            ind += 1
        params = {
            'notes': to_repair['note'].astype(dtype=np.dtype(np.int64)).to_numpy().tolist()
        }
        notes = send_request('notesInfo',params)
        ind = -1
        for note in notes:
            ind += 1
            local_tag = to_repair.iloc[ind]['tag']
            if local_tag in note['tags']:
                if(len(note['tags']) > 1):
                    tags_to_remove = note['tags']
                    tags_to_remove.remove(local_tag)
                    params = {
                        'notes': [note['noteId']],
                        'tags': " ".join(note['tags'])
                    }
                    send_request('removeTags',params)
            else:
                # print(note['noteId'])
                # print(note['tags'])
                # print(len(note['tags']))
                # print(local_tag)
                
                if(len(note['tags']) > 0):
                    tags_to_remove = note['tags']
                    params = {
                        'notes': [note['noteId']],
                        'tags': " ".join(note['tags'])
                    }
                    send_request('removeTags',params)
                params = {
                    'notes': [note['noteId']],
                    'tags': local_tag
                }
                send_request('addTags',params)

    # to_add = old_frame.merge(right=new_frame,how='outer',on='question',indicator=True)
    # to_add.replace(to_replace='left_only',value=np.nan,inplace=True)
    # to_add.replace(to_replace='both',value=np.nan,inplace=True)
    # to_add.dropna(subset=['_merge'],inplace=True)
    return to_create

def add_notes_to_anki(notes_frame, max_new):
    

    old_frame = get_current_anki_cards_as_dataframe()

    

    notes_frame = remove_old_cards(old_frame, notes_frame, max_new)

    print(max_new)

    statements.set_notes(notes_frame.copy())
    
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