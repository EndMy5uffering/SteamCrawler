import HTMLParser
from HTMLParser import HTMLTag, HTMLPage, HTMLData
import ConsoleController as CC
import Parser
import Plexer
import pymongo


STEAM_PROFILE = 'https://steamcommunity.com/profiles/'
REQUEST_PAUSE = 0

class SteamProfile:
    def __init__(self, name, lvl, num_friends, profile_page):
        self.name = name
        self.lvl = lvl
        self.num_friends = num_friends
        self.profile_page = profile_page
        self.user_id = '-'
        self.nationality = '-'
        self.private = True
        self.faulty = False
        self.friends_list = []
        self._faulty_data = []
    
    def add_freind(self, friend):
        self.friends_list.append(friend)
    
    @staticmethod
    def FROM_DATA(data):
        profile = SteamProfile(data['user_name'], data['lvl'], data['num_friends'], data['profile_page'])
        profile.friends_list = data['friends']
        profile.private = data['private']
        profile.user_id = data['user_id']
        profile.nationality = data['nationality']
        profile._faulty_data = data['faulty_data']
        
        return profile 
    
    def get_data(self):
        return {'user_name': self.name,
        'lvl': self.lvl,
        'num_friends': self.num_friends,
        'user_id': self.user_id,
        'profile_page': self.profile_page,
        'nationality': self.nationality,
        'private': self.private,
        'friends': self.friends_list,
        'faulty_data:': self._faulty_data}


def create_profile_for(url, steamID):

    DataList = lambda tagList, data_name, data_value: [s for s in tagList if s.has_tag_data(data_name) and s.get_tag_data(data_name) == data_value and s.html_data]

    html = HTMLParser.HTMLParser()
    html.parser.status_callback = update_bottom_info
    html.plexer.status_callback = update_bottom_info

    htmlPage = html.html_parse(url, REQUEST_PAUSE)
    htmlPage_friends = html.html_parse(url+'/friends', REQUEST_PAUSE)

    divFriends = htmlPage_friends.get_tags_with_type('div')
    
    friends_list = [s for s in divFriends if s.has_tag_data('class') and 'selectable friend_block_v2 persona' in s.tag_data['class']]
    

    spans = htmlPage.get_tags_with_type('span')     
    spans_Name = DataList(spans, 'class', 'actual_persona_name')
    span_LVL = DataList(spans, 'class', 'friendPlayerLevelNum')
    num_games = DataList(spans, 'class', 'profile_count_link_total')
    
    images:list[HTMLTag] = htmlPage.get_tags_with_type('img')
    images = DataList(images, 'class', 'profile_flag')

    body_tags = htmlPage.get_tags_with_type('body')
    body_tags = [t for t in body_tags if 'class' in t.tag_data and 'private_profile' in t.tag_data['class']]


    name = '-'
    lvl = '-1'
    num_friends = str(len(friends_list))
    nationality = '-'
    private = len(body_tags) > 0
    
    if len(spans_Name) > 0 and spans_Name[0]:
        name = spans_Name[0].html_data[0].raw
    if len(span_LVL) > 0 and span_LVL[0]:
        lvl = span_LVL[0].html_data[0].raw
    if images:
        if images[0].html_data:
            nationality = images[0].html_data[0].raw.strip()

    
    profile = SteamProfile(name, lvl, num_friends, url)
    profile.nationality = nationality
    profile.private = private
    profile.user_id = steamID

    try:
        for friend in friends_list:
            tdata = friend.tag_data
            if 'class' in tdata and 'data-steamid' in tdata and 'data-search' in tdata:
                profile.add_freind({'steamid':tdata['data-steamid'], 'name':tdata['data-search'].split(';')[0].strip()})
            elif 'class' in tdata and 'unavailable' in tdata['class']:
                profile.faulty = True
                profile._faulty_data.append({'steam_id:':tdata['data-steamid'], 'raw': friend.raw, 'url':STEAM_PROFILE+tdata['data-steamid']})
    except:
        CC.cls_line()
        print('-'*50)
        print('GOT AN ERROR FOR PROFILE', url)
        print('-'*50)
    return profile

def print_profile(profile:SteamProfile):
    public_setting = '🔴' if profile.private else '🟢'
    if profile.faulty:
        public_setting = '🟡'
    CC.cls_line()
    print(public_setting,'Name:', profile.name, '; ID:(', profile.user_id,')')
    print('| 💎 LVL:    ', profile.lvl)
    print('| 🌍 From:   ', profile.nationality)
    print('| 🦑 Friends:', profile.num_friends)
    print('| 📃 Page:   ', profile.profile_page)
    if profile.faulty:
        for entry in profile._faulty_data:
            print('| ☣️ Faulty:', entry)

def update_bottom_info(who, current, max):
    max = max if max > 0 else 1
    origin = '📝Parser' if isinstance(who, Parser.Parser) else '⏳Plexer'
    ratio = current/max
    x, y = CC.win_size()
    bar_len = int(x*0.25)
    output = f'{origin}: ({str(int(ratio*100))}%)' + '|' + '█'*int((ratio)*bar_len) + ' '*int((1-ratio)*bar_len) + '|'
    CC.save_cur_pos()
    print(output + ' '*(x-len(output)-1), end='')
    CC.reset_cur_pos()

if __name__=='__main__':
    print('Connecting to database...')
    dbclient = pymongo.MongoClient('mongodb://localhost:27017/')
    print('Getting database...')
    mydb = dbclient['steam_user_data']
    print('Getting collection...')
    mycol = mydb['user_data']
    print('Getting colleciton for faulty data...')
    faultydb = mydb['faulty_users']

    REQUEST_PAUSE = 10
    url = 'https://steamcommunity.com/profiles/76561198071620611/'

    print('Processing allready collected data...')
    _DATA = {}
    nextup = []

    for data in mycol.find({}):
        if not data['user_id'] in _DATA:
            _DATA[data['user_id']] = data
    print('Getting freinds from (', len(_DATA) ,') profiles')
    for data in _DATA:
        for friend in _DATA[data]['friends']:
            if not friend['steamid'] in _DATA:
                nextup.append(friend)
    del _DATA

    print('Reading entry point...')
    st = create_profile_for(url, '76561198071620611')
    if not st.faulty:
        if not mycol.count_documents({'user_id':st.user_id}, limit = 1):
            mycol.insert_one(st.get_data())
            for friend in st.friends_list:
                nextup.append(friend)
            print(CC.CLS_LINE + 'Starting with:')
            print_profile(st)
            print('_'*CC.win_size()[0])
        else:
            print(CC.CLS_LINE + 'Entry is allready in the collection processing next data...')
    else:
        print(CC.CLS_LINE + 'Faulty profile')
  
    print(CC.CLS_LINE + 'Next up:', len(nextup), 'profiles')

    depth = 2
    while depth > 0 and nextup:
        friends_of_friends = []
        for f_data in nextup:
            if not mycol.count_documents({'user_id': f_data['steamid']}, limit = 1):
                fprofile = create_profile_for(STEAM_PROFILE + f_data['steamid'], f_data['steamid'])
                if not fprofile.faulty:
                    mycol.insert_one(fprofile.get_data())
                    for friend in fprofile.friends_list:
                        friends_of_friends.append(friend)
                elif not faultydb.count_documents({'user_id': f_data['steamid']}, limit = 1):
                    faultydb.insert_one(fprofile.get_data())
                print_profile(fprofile)
        CC.cls_line()
        print()
        print('Done reading list(' ,len(nextup), ')', 'new list(', len(friends_of_friends) ,')', 'remaining steps:', depth-1)
        print()
        nextup = friends_of_friends
        depth -= 1

