from bs4 import BeautifulSoup
import requests


week = 12
season = 2017

cbs_com_url = 'https://www.cbssports.com/nfl/scoreboard/all/' + str(season) + '/regular/' + str(week) + "/"

response = requests.get(cbs_com_url)
html = BeautifulSoup(response.content, 'html.parser')
#
div_box_scores = html.find_all("div", attrs={'class':"single-score-card  ingame nfl"})

game_dict = {}
games_list = []
for box_score in div_box_scores:

    game_status_c = box_score.find(class_='game-status emphasis')
    print('game_status_c->', game_status_c)



