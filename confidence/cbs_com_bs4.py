from bs4 import BeautifulSoup
import requests
import re


week = 12
season = 2017

nfl_scores_xml = 'http://www.nfl.com/liveupdate/scorestrip/ss.xml'

response = requests.get(nfl_scores_xml)
xml = BeautifulSoup(response.content, 'xml')
games_list = []
games = xml.find_all("g")
game_results = {}
game_list = []
for game in games:
    fields = str(game).split()
    for field in fields:
        if field.find("=") > 0:
            key, value = field.split("=")
            if value[-2:] == "/>":
                value = value[:len(value)-2]
            game_results[key] = value.strip('\"')
    games_list.append(game_results.copy())
    print(game_results)
    game_results.clear()

#print(games_list)


    #
    # mo = re.match(r'<g d=\"(\w+)\" eid=\"(\w+)\" ga=\"\" gsis=\"(\w+)\" gt=\"(\w+)\" h=\"(\w+)\" hnn=\"(\w+)\" hs=\"(\w+)\" q=\"(\w+)\" rz=\"(\w+)\" t=\"(\S+)\" v=\"(\w+)\" vnn=\"(\w+)\" vs=\"(\w+)\"/>', str(game), re.M|re.I)
    # game_results['game_d'] = mo.group(1)
    # game_results['game_eid'] = mo.group(2)
    # game_results['game_gsis'] = mo.group(3)
    # game_results['game_gt'] = mo.group(4)
    # game_results['game_h'] = mo.group(5)
    # game_results['game_hnn'] = mo.group(6)
    # game_results['game_hs'] = mo.group(7)
    # game_results['game_q'] = mo.group(8)
    # game_results['game_rz'] = mo.group(9)
    # game_results['game_t'] = mo.group(10)
    # game_results['game_v'] = mo.group(11)
    # game_results['game_vnn'] = mo.group(12)
    # game_results['game_vs'] = mo.group(13)

