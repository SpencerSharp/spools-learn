import numpy as np
import random
from .util import send_request

def set_to_repair(rep):
    global to_repair
    to_repair = rep

def remove_tags(note):
    if(len(note['tags']) > 1):
        tags_to_remove = note['tags']
        tags_to_remove.remove(local_tag)
        params = {
            'notes': [note['noteId']],
            'tags': " ".join(note['tags'])
        }
        send_request('removeTags',params)

def add_tags(note):
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

def fix_tags():
    params = {
        'notes': to_repair['note'].astype(dtype=np.dtype(np.int64)).to_numpy().tolist()
    }
    notes = send_request('notesInfo',params)
    ind = -1
    for note in notes:
        ind += 1
        local_tag = to_repair.iloc[ind]['tag']
        if local_tag in note['tags']:
            remove_tags(note)
        else:
            add_tags(note)
'''
What is the point of this?
    I think to be able to generate datapoints? idk
Why in the range of 1500 to 3000?
    dunno
Shouldnt this factor into leeches more?
Or into lapses?

setEaseFactors is a custom function in ankiconnect that i wrote
I tried to merge it into master, no status update on that yet


'''
def fix_ease(max_new):
    ind = 0
    while ind < len(to_repair):
        card = to_repair.iloc[ind]
        if 'queue' in card.keys():
            if card['queue'] == 0:
                for pos_tag in max_new.keys():
                    if pos_tag in card['tag']:
                        max_new[pos_tag] -= 1
        elif card['factor'] > 3000 or card['factor'] < 1500:
            base = card['factor']
            if base > 3000:
                diff = base - 3000
                ease = 2500 + int(random.uniform(0,diff))
            else:
                diff = 1500 - base
                ease = 2000 - int(random.uniform(0,diff))
            params = {
                'cards': [int(card['cardId'])],
                'easeFactors': [ease]
            }
            print('{} - Old ease: {} New ease: {}'.format(card['question_x'],card['factor'],ease))
            send_request('setEaseFactors',params)
        ind += 1

def get_card_ids():
    cardIds = to_repair['cardId'].astype(dtype=np.dtype(np.int64)).to_numpy().tolist()
    return cardIds

def get_card_intervals():
    params = {
        'cards': get_card_ids(),
        'complete': True
    }
    card_intervals = send_request('getIntervals',params)
    return card_intervals

def get_are_due():
    params = {
        'cards': get_card_ids()
    }
    are_due = send_request('areDue',params)
    print('done asking')
    return are_due

def get_leech_cards():
    card_intervals = get_card_intervals()
    leech_cards = []
    ind = 0
    for card in get_card_ids():
        intervals = card_intervals[ind]
        ind += 1
        if type(intervals) == type([]) and len(intervals) >= 3:
            if intervals[-1] == 1 and intervals[-2] == 1 and intervals[-3] > 0:
                leech_cards.append(card)
    return leech_cards

def reset_cards():
    leech_cards = get_leech_cards()
    params = {
        'cards': leech_cards
    }
    print("resetting " + str(len(leech_cards)) + " leech cards")
    # Also custom AnkiConnect function, have not tried to merge into master yet
    send_request('forgetCards',params)

def unsuspend_cards():
    cardIds = get_card_ids()
    toKeep = []
    areDue = []
    arentDue = []
    toTempSuspend = []
    are_due = get_are_due()
    index = 0
    for card in cardIds:
        if are_due[index]:
            areDue.append(card)
        else:
            arentDue.append(card)
        index += 1
    areDue.sort()
    index = 0
    for card in areDue:
        if index > 100:
            toTempSuspend.append(card)
        else:
            toKeep.append(card)
        index += 1
    for card in arentDue:
        toKeep.append(card)
    params = {
        'cards': toKeep
    }
    print("unsuspending " + str(len(toKeep)) + " cards")
    send_request('unsuspend',params)
    params = {
        'cards': toTempSuspend
    }
    print("temp suspending " + str(len(toTempSuspend)) + " cards")
    send_request('suspend',params)

def repair(to_repair, max_new):
    set_to_repair(to_repair)
    print("\nrepairing " + str(len(to_repair)) + " cards")
    
    reset_cards()
    unsuspend_cards()
    fix_ease(max_new)
    fix_tags()
