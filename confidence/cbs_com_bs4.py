from bs4 import BeautifulSoup
import requests
import re


week = 12
season = 2017

footballlocks_com_url = 'http://www.footballlocks.com/nfl_lines.shtml'

response = requests.get(footballlocks_com_url)
html = BeautifulSoup(response.content, 'html.parser')
games_list = []
columns = html.find_all("td")
game_data = []
begin = 0
count = 0
for col in columns:
    date_col = re.match( r'(\d+)/(\d+) \d+:\d+ ET', col.text)
    if date_col:
        begin += 1
        count = 0
        continue
    if begin > 0:
        count += 1
        hometeam = re.match(r'At (\D+)', col.text)
        if hometeam:
            game_data.append(hometeam.group(1))
        else:
            game_data.append(col.text)
        if count > 3:
            games_list.append(game_data.copy())
            game_data.clear()
            begin = 0
print(games_list)



