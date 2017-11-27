from bs4 import BeautifulSoup
from selenium import webdriver
import requests


week = 12
season = 2017

nfl_com_url = 'http://www.nfl.com/scores/' + str(season) + '/REG' + str(week)
browser = webdriver.Chrome()
browser.get(nfl_com_url)
response = browser.execute_script("return document.body.response")

#response = requests.get(nfl_com_url)
html = BeautifulSoup(response, 'html.parser')

div_box_scores = html.find_all("div", attrs={'class':"new-score-box-wrapper"})

game_dict = {}
games_list = []
for box_score in div_box_scores:

    final_c = box_score.find(class_='time-left')
    #print('final->', final_c.contents[0].strip())

    in_prog_c = final_c.find(class_='down-yardline')

    if not in_prog_c:
        print('game is final', final_c.contents)
        if final_c.contents[0].strip()[:5] == 'FINAL':
            is_final = True
        else:
            is_final = False
    else:
        print('game in progress', in_prog_c)
        # <span class="down-yardline">1st &amp; 10 IND 19</span>
        is_final = False

    div_away_team = box_score.find("div", attrs={'class':"away-team"})
    div_home_team = box_score.find("div", attrs={'class':"home-team"})

    home_team_name_class = div_home_team.find(class_='team-name')
    home_team_name_c = home_team_name_class.find('a')
    home_team_score_c = div_home_team.find(class_='total-score')

    away_team_name_class = div_away_team.find(class_='team-name')
    away_team_name_c = away_team_name_class.find('a')
    away_team_score_c = div_away_team.find(class_='total-score')

    home_team_name = home_team_name_c.contents[0].strip()
    away_team_name = away_team_name_c.contents[0].strip()
    home_team_score = home_team_score_c.contents[0].strip()
    away_team_score = away_team_score_c.contents[0].strip()

    game_dict['home_team'] = home_team_name
    game_dict['away_team'] = away_team_name
    game_dict['home_score'] = home_team_score
    game_dict['away_score'] = away_team_score

    games_list.append(game_dict.copy())
    game_dict.clear()

print(games_list)



    #print(div_home_team.find("p", attrs={'class':"team-name"}))
    #print(div_away_team.find("p", attrs={'class':"team-name"}))



#print('html5->', len(BeautifulSoup(html, "html5lib").find_all('div', attrs={"class":"wisbb_teams"})))
#print('html->', len(BeautifulSoup(html, "html.parser").find_all('div', attrs={"class":"wisbb_teams"})))
#print('lxml->', len(BeautifulSoup(html, "lxml").find_all('div', attrs={"class":"wisbb_teams"})))

# <div class="new-score-box-wrapper" id="scorebox-2017112302">
# 				<div class="new-score-box-heading">
# 					<p>
# 						<span class="date" title="Date Aired">Thu, Nov 23</span>
# 						<span class="network" title="Aired on Network">nbc</span>
# 						<span class="quarters-total" title="Score Key by Quarter">
# 							<span class="total-score">TOTAL</span>
# 							<span class="quarters-score">
# 								<span>1</span><span>2</span><span>3</span><span>4</span><span>OT</span>
# 							</span>
# 						</span>
# 					</p>
# 				</div>
# 				<div class="new-score-box">
# 				<div class="team-wrapper">
# 						<div class="away-team">
# 							<a href="/teams/profile?team=NYG" onclick="s_objectID=&quot;http://www.nfl.com/teams/profile?team=NYG_1&quot;;return this.s_oc?this.s_oc(e):true"><img src="http://i.nflcdn.com/static/site/7.5/img/logos/teams-matte-80x53/NYG.png" class="team-logo" alt=""></a>
# 							<div class="team-data">
# 								<div class="team-info">
# 									<p class="team-record">
#
# 											<a href="/teams/profile?team=NYG" onclick="s_objectID=&quot;http://www.nfl.com/teams/profile?team=NYG_2&quot;;return this.s_oc?this.s_oc(e):true">(2-9-0)</a>
#
# 									</p>
# 									<p class="team-name"><a href="/teams/profile?team=NYG" onclick="s_objectID=&quot;http://www.nfl.com/teams/profile?team=NYG_3&quot;;return this.s_oc?this.s_oc(e):true">Giants</a></p>
# 								</div>
# 								<p class="total-score">10</p>
# 								<p class="quarters-score"><span class="first-qt">0</span><span class="second-qt">3</span><span class="third-qt">7</span><span class="fourth-qt">0</span><span class="ot-qt"></span></p>
#
# 							</div>
# 						</div>
# 					</div>
# 					<div class="team-wrapper">
# 						<div class="home-team">
# 							<a href="/teams/profile?team=WAS" onclick="s_objectID=&quot;http://www.nfl.com/teams/profile?team=WAS_1&quot;;return this.s_oc?this.s_oc(e):true"><img src="http://i.nflcdn.com/static/site/7.5/img/logos/teams-matte-80x53/WAS.png" class="team-logo" alt=""></a>
# 							<div class="team-data">
# 								<div class="team-info">
# 									<p class="team-record">
#
# 											<a href="/teams/profile?team=WAS" onclick="s_objectID=&quot;http://www.nfl.com/teams/profile?team=WAS_2&quot;;return this.s_oc?this.s_oc(e):true">(5-6-0)</a>
#
# 									</p>
# 									<p class="team-name"><a href="/teams/profile?team=WAS" onclick="s_objectID=&quot;http://www.nfl.com/teams/profile?team=WAS_3&quot;;return this.s_oc?this.s_oc(e):true">Redskins</a></p>
# 								</div>
# 								<p class="total-score">20</p>
# 								<p class="quarters-score"><span class="first-qt">0</span><span class="second-qt">3</span><span class="third-qt">7</span><span class="fourth-qt">10</span><span class="ot-qt"></span></p>
# 							</div>
# 						</div>
# 					</div>
# 					<div class="game-center-area">
# 						<a href="/gamecenter/2017112302/2017/REG12/giants@redskins" class="game-center-link" onclick="s_objectID=&quot;http://www.nfl.com/gamecenter/2017112302/2017/REG12/giants@redskins_1&quot;;return this.s_oc?this.s_oc(e):true"><img src="http://i.nflcdn.com/static/site/7.5/img/scores/game-center-active.png" alt=""></a>
# 						<p><span class="time-left">FINAL </span></p>
# 						<div style="clear:right"></div>
# 						<div class="big-plays"><span class="title">BIG PLAYS</span><span class="big-plays-count">13</span></div>
# 						<div style="clear:both"></div>
#
# 							<div class="highlight-link">
# 								<a href="/gamecenter/2017112302/2017/REG12/giants@redskins#menu=highlights|contentId:0ap3000000882229&amp;tab=analyze" onclick="s_objectID=&quot;http://www.nfl.com/gamecenter/2017112302/2017/REG12/giants@redskins#menu=highlights|contentId:0ap_1&quot;;return this.s_oc?this.s_oc(e):true">
# 									<div class="highlight-button"><div class="highlight-arrow"></div></div>
# 									<p>Giants vs. Redskins highlights | Week 12</p>
# 								</a>
# 							</div>
#
# 					</div>
# 					<div class="products-social">
# 						<p>
# 							<span class="listen"><a href="/gamepass?icampaign=GR_Scores" onclick="s_objectID=&quot;http://www.nfl.com/gamepass?icampaign=GR_Scores_3&quot;;return this.s_oc?this.s_oc(e):true"><img src="http://i.nflcdn.com/static/site/7.5/img/scores/camera.png" alt=""> FULL GAME</a></span>
# 						</p>
# 					</div>
# 				</div>
# 			</div>