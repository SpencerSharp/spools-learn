import numpy as np
from .util import send_request

def set_to_repair(rep):
    global to_repair
    to_repair = rep

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
            if(len(note['tags']) > 1):
                tags_to_remove = note['tags']
                tags_to_remove.remove(local_tag)
                params = {
                    'notes': [note['noteId']],
                    'tags': " ".join(note['tags'])
                }
                send_request('removeTags',params)
        else:
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

def fix_ease():
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

def get_leech_cards():
    card_intervals = get_card_intervals()
    leech_cards = []
    ind = 0
    for card in get_card_ids():
        intervals = card_intervals[ind]
        ind += 1
        if type(intervals) == type([]) and len(intervals) >= 2:
            if intervals[-1] == 1 and intervals[-2] == 1:
                leech_cards.append(card)
    return leech_cards

def reset_cards():
    leech_cards = get_leech_cards()
    params = {
        'cards': leech_cards
    }
    print("resetting " + str(len(leech_cards)) + " cards")
    send_request('forgetCards',params)

def unsuspend_cards():
    cardIds = get_card_ids()
    params = {
        'cards': cardIds
    }
    print("unsuspending " + str(len(cardIds)) + " cards")
    send_request('unsuspendCards',params)

def repair(to_repair, max_new):
    set_to_repair(to_repair)
    print("\nrepairing " + str(len(to_repair)) + " cards")
    
    reset_cards()
    unsuspend_cards()
    fix_ease()
    fix_tags()
