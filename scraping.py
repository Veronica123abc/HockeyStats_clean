import numpy as numpy
import pandas as pd
#data = pd.read_csv('https://example.com/passkey=wedsmdjsjmdd')
import urllib
import csv
import requests
import os
import re
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.select import Select

from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

import copy
import time
import numpy as np
from urllib.request import urlopen
from utils.read_write import string_to_file
import shutil
import json
import uuid




def download_gamefiles(game_ids, src_dir):
    tmp_dir = '/home/veronica/hockeystats/tmp'# +  str(uuid.uuid4())

    if not isinstance(game_ids, list):
        game_ids=[game_ids]

    driver=get_web_driver()
    # login(driver)
    ctr = 1
    for game in game_ids:
        print(f"Downloading gamefile for game number {game} ({ctr} of {len(game_ids)})")
        url = f'https://hockey.sportlogiq.com/games/league/{game}/video'
        driver.get(url)
        element_xpath = "//*[@id='main-content']/app-games/div/app-games-for-league/game-video/div/div[1]/div[1]/div[2]/button"
        driver = wait_for_element(driver, element_xpath)
        element = driver.find_element(By.XPATH, element_xpath)
        #print(element)

        # time.sleep(20)
        files = []
        while (len(files) == 0):
            try:
                element.click()
            except:
                pass

            time.sleep(1)
            files = os.listdir(tmp_dir)
            files = [f for f in files if re.match('playsequence', f)]
            files = [f for f in files if os.path.splitext(f)[1] == '.csv']


        for file in files: # Should be only one
            new_file_name = str(game) + '_' + file
            shutil.move(os.path.join(tmp_dir, file), os.path.join(src_dir, new_file_name))
        ctr += 1




def login(driver):
    # driver = webdriver.Chrome('./chromedriver')
    driver.get('https://hockey.sportlogiq.com/login')
    driver.implicitly_wait(10)
    login = driver.find_element(By.XPATH, "//input[@id='mat-input-0']")  # .send_keys('eriksson@kth.se')
    login.send_keys('veronica.eriksson580@gmail.com')
    pwd = driver.find_element(By.XPATH, "//input[@id='mat-input-1']")
    pwd.send_keys('B1llyfjant.1')
    submit = driver.find_element(By.XPATH, "//button[@type='submit']")
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable(submit))
    submit.click()
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "league-selector")))

def get_web_driver():
    # DRIVER_PATH = '/home/veronica/Downloads/chromedriver_linux64_117/chromedriver'
    #DRIVER_PATH = '/home/veronica/Downloads/chromedriver_117_unzipped/chromedriver-linux64/chromedriver'


    #options.add_argument('/home/veronica/.config/google-chrome/Default')
    with open('./config/webdriver/options.json') as f:
        webdriver_options = json.load(f)
    options = webdriver.ChromeOptions()
    options.add_argument(f"user-data-dir={webdriver_options['user-data-dir']}")
    options.page_load_strategy = 'normal'
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def wait_and_click(driver, xpath):
    WebDriverWait(driver, 50).until(EC.presence_of_element_located(
        (By.XPATH, xpath)))
    select_element = driver.find_element(By.XPATH, xpath)
    select_element.click()
    return driver

def wait_for_element(driver, xpath):
    WebDriverWait(driver, 50).until(EC.presence_of_element_located(
        (By.XPATH, xpath)))
    # select_element = driver.find_element(By.XPATH, xpath)
    return driver

def select_category(driver, regular_season=True):
    select_xpath = "/html/body/app-root/div/ng-component/div/div[2]/div/main-navigator/div/button"
    driver = wait_and_click(driver, select_xpath)
    if regular_season:
        el = "//*[@id='mat-button-toggle-1']"
    else:
        el = "//*[@id='mat-button-toggle-2']"
    driver = wait_and_click(driver, el)
    cancel_xpath = "/html/body/div[3]/div[2]/div/mat-dialog-container/team-selector/div/action-button-bar/div/button[1]"
    apply_xpath = "/html/body/div[3]/div[2]/div/mat-dialog-container/team-selector/div/action-button-bar/div/button[2]"
    driver = wait_for_element(driver, cancel_xpath)
    driver = wait_for_element(driver, apply_xpath)
    cancel_element = driver.find_element(By.XPATH, cancel_xpath)
    apply_element = driver.find_element(By.XPATH, apply_xpath)


    time.sleep(2)
    if apply_element.is_enabled():
        print("Clicking APPLY")
        apply_element.click()
        return driver
    else:
        return False
        # print("Clicking CANCEL")
        # cancel_element.click()

    return driver

def select_team(driver, team_order, regular_season=True):
    select_xpath = "/html/body/app-root/div/ng-component/div/div[2]/div/main-navigator/div/button"
    driver = wait_and_click(driver, select_xpath)
    element_xpath = f"/html/body/div[3]/div[2]/div/mat-dialog-container/team-selector/div/mat-selection-list/mat-list-option[{team_order}]"
    driver = wait_and_click(driver, element_xpath)

    if regular_season:
        el = "//*[@id='mat-button-toggle-1']"
    else:
        el = "//*[@id='mat-button-toggle-2']"
    driver = wait_and_click(driver, el)


    cancel_xpath = "/html/body/div[3]/div[2]/div/mat-dialog-container/team-selector/div/action-button-bar/div/button[1]"
    apply_xpath = "/html/body/div[3]/div[2]/div/mat-dialog-container/team-selector/div/action-button-bar/div/button[2]"
    cancel_element = driver.find_element(By.XPATH, cancel_xpath)
    apply_element = driver.find_element(By.XPATH, apply_xpath)

    time.sleep(2)
    if apply_element.is_enabled():
        print("Clicking APPLY")
        apply_element.click()
        return driver
    else:
        return False
        # print("Clicking CANCEL")
        # cancel_element.click()

    return driver

def extract_teams_from_league(filename):
    f = open(filename)
    html = f.read()
    team_segments = html.split('data-cy-teamid-value')
    teams=[]
    for team_segment in team_segments[1:]:
        team_id = int(team_segment.split('\"')[1])
        team_name =  team_segment.split('title=\"')[1].split('\"')[0]
        teams.append({'sl_id': team_id, 'sl_name': team_name})
    return teams

def download_all_schedules(league_file=None, sl_team_ids=None, target_dir='./', regular_season=True):
    # For  now, season must be selected MANUALLY on the first go ...

    if (league_file is None) and (sl_team_ids is None):
        return None
    if sl_team_ids is None:
        extracted_teams = extract_teams_from_league(league_file)
        sl_team_ids = [team['sl_id'] for team in extracted_teams]
    for sl_team_id in sl_team_ids: # team in teams:
        print(sl_team_id)
        url = f'https://hockey.sportlogiq.com/teams/{sl_team_id}/schedule/all'
        download_schedule(url, target_dir, regular_season=regular_season)


def download_schedule(url, path, regular_season=True):
    # For  now, eason must be selected MANUALLY on the first go ...

    driver = get_web_driver()
    #login(driver)

    with open("./config/schedule_elements.json") as f:
        elements = json.load(f)
    driver.get(url)
    # driver = select_category(driver, regular_season=regular_season)
    # Wait for "season reports" to load since that means all games are read into the page.

    driver = wait_for_element(driver, elements['team_selector_dropdown'])
    team_selector_dropdown_element = driver.find_element(By.XPATH, elements['team_selector_dropdown'])
    is_regular_season = 'REG' in team_selector_dropdown_element.text
    team_name = team_selector_dropdown_element.text.split('\n')[0]

    #driver.implicitly_wait(10)
    # Test clicking the left scroller button in header. Just for fun ...
    # wait_and_click(driver, elements['header_scroller_left'])

    if (is_regular_season ^ regular_season):
        driver = select_category(driver, regular_season=regular_season)

    if driver:
        #Wait for all games to load
        driver = wait_for_element(driver, elements['first_game_summary_button'])

        # Grab the body of the page and get the innerHTML
        body_element = driver.find_element(By.XPATH, elements['page_body'])
        inner_html = body_element.get_attribute("innerHTML")
        if regular_season:
            filename = team_name + '_regular_season.txt'
        else:
            filename = team_name + '_playoffs.txt'
        string_to_file(inner_html, path, filename)





def get_all_game_numbers(root_dir):
    """Returns a list of game-numbers given a directory of the html-files
    for each team's schedule"""
    # root_dir = '/home/veronica/hockeystats/SHL/2022-23/regular-season/schedules'
    files = [os.path.join(root_dir, f) for f in os.listdir(root_dir)]
    games = []
    tag = r"\/\d+\/summary"
    for file in files:
        str = open(file,'r').read()
        game_numbers = [int(n.split('/')[1]) for n in re.findall(tag, str)]
        #game_numbers = [int(n.split('/')[0]) for n in re.findall(r'\d+/video', str)]
        new_game_numbers = [n for n in game_numbers if n not in games]
        games = games + new_game_numbers
    return games

def get_teams(league):
    url='https://hockey.sportlogiq.com/league'
    driver = get_web_driver()
    driver.get(url)
    wait_and_click(driver, '/html/body/app-root/div/ng-component/div/app-header/header/div/league-selector')
    url=f'https://hockey.sportlogiq.com/teams/{league}/schedule'

def teams_from_gamefile_names(root_dir):
    files = os.listdir(root_dir)
    games=[]
    for file in files:
        teams=file.split('-')[3]
        games.append(tuple(teams.split('vs')))
    print(games)


def extract_game_info_from_schedule_html(filename):
    html = open(filename,'r').read()
    months=["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    year_adds = [1,1,1,1,1,1,1,0,0,0,0,0]
    year = 2022
    months_start_pos = []
    for (idx, month) in enumerate(months):
        res = re.search(f"\"month-label\">{month}", html)
        if res:
            months_start_pos.append((idx, res.start()))


    months_start_pos = sorted(months_start_pos, key=lambda x:(x[1]))
    months_end_pos = months_start_pos[1:]+[tuple(np.array(months_start_pos[-1]) + ((0,len(html))))]
    parts = []
    for i in range(0, len(months_start_pos)):
        parts.append(months_start_pos[i] + (months_end_pos[i][1],))
    games = []
    for (month, start, end) in parts:
        crop = html[start:end]
        rows = crop.split('season-schedule-row')[1:]
        for row in rows:
            home_team = row.split('matchup-content\">')[2].split('<')[0].replace(' ','')
            away_team = row.split('matchup-content\">')[1].split('<')[0].replace(' ','')
            date = str(year + year_adds[month]) + str(month + 1).zfill(2)  +\
                   re.findall('\d+', row.split('date-container')[1])[0].zfill(2)
            sl_game_id = row.split('/games/league/')[1].split('/')[0]
            games.append((home_team, away_team, date, sl_game_id))
            print(date + ' ' + home_team + ' ' + away_team)


    return games
