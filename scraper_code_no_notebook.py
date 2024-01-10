from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from collections import Counter
from itertools import count
from threading import Event
import pandas as pd
import time

from selenium.common.exceptions import ElementNotInteractableException

options = webdriver.ChromeOptions()
options.add_experimental_option("detach", True)
options.add_argument("--headless")
service_obj = Service('/Users/jabedmiah/Downloads/chromedriver')
driver = webdriver.Chrome(service=service_obj, options=options)

def player_list():
    info_container = driver.find_element(By.CLASS_NAME, 'center-container')
    container_html = info_container.get_attribute('innerHTML')
    return BeautifulSoup(container_html, 'html.parser')

def processed_player_urls(player_cards):
    players_pages = []

    for a in player_cards.find_all("a"):
        players_pages.append(a["href"])

    return players_pages

def container_extractor(table_soup):
    if table_soup == "":
        key_value_pairs = {}
    else:
        try:
            container_values, container_cols = [], []
            row = table_soup.find_all("td")
            headers = table_soup.find_all("th")

            for r in row:
                container_values.append(r.text)

            for header in headers:
                container_cols.append(header.text)

            key_value_pairs = zip(container_cols, container_values)
        except:
            key_value_pairs = {}
    
    return dict(key_value_pairs)

def table_html_extractor(soup, section_name, elem_type = "table"):
    try:
        container = soup.find("section", {"class": f"{section_name}"})
        settings = container.find(f"{elem_type}", {"class":"settings"})
    except:
        settings = ""
    return settings

def containers_with_imgs(soup, elem_id):
    try:
        container = soup.find("section", {"id":f"{elem_id}"})
        container_details = container.find_all("div", {"class":"cta-box"})

        container_cols, container_values = [], []
        for container_detail in container_details:
            container_cols.append(container_detail.find("div", {"class":"cta-box__tag--top-right"}).text)
            container_values.append(container_detail.find("h4").text)

        if len(container_cols) != len(set(container_cols)):
            c = Counter(container_cols)
            iters = {k: count(1) for k, v in c.items() if v > 1}
            new_container_cols = [x+f" {next(iters[x])}" if x in iters else x for x in container_cols]

            key_value_pairs = zip(new_container_cols, container_values)
        else:
            key_value_pairs = zip(container_cols, container_values)
    except:
        key_value_pairs = {}

    return dict(key_value_pairs)

def leftover_extractor(soup):
    player_bio_container = soup.find("section", {"class":"intro"})
    player_bio_table = player_bio_container.find("table", {"class":"data"})
    player_bio_dict = container_extractor(player_bio_table)
    player_bio_dict.update({"Country":player_bio_dict["Country"].strip()})

    try:
        social_media = player_bio_container.find("div", {"class":"social"})

        social_media_names, social_media_links = [], []

        for social in social_media.find_all("li"):
            social_media_names.append(social.text)

        for link in social_media.find_all('a'):
            social_media_links.append(link['href'])

        socials = dict(zip(social_media_names, social_media_links))
    except:
        socials = {}

    try:
        config = soup.find("section", {"id":"cs2_config"})
        a = config.find("a")
        config_dict = {"Config":a["href"]}
        player_bio_dict.update(config_dict)
    except:
        pass

    player_bio = soup.find("div", {"class":"player-bio"})
    avatar_container = player_bio.find("section", {"class":"avatar"})
    avatar_img = avatar_container.find("img")
    avatar_dict = {"Player Avatar":avatar_img["src"]}
    player_bio_dict.update(avatar_dict)

    player_name = player_bio.find("div", {"class":"name"}).find("h1").text
    player_name_dict = {"Nickname":player_name}
    player_bio_dict.update(player_name_dict)

    player_bio_ps = player_bio.find("div", {"class":"content"}).findAll("p")

    full_player_bio = ""
    for player_bio_p in player_bio_ps:
        full_player_bio += f"{player_bio_p.text}"

    player_bio_dict.update({"Background":full_player_bio})

    try: 
        launch_opts_container = soup.find("section", {"id":"cs2_launch_options"})
        launch_opts = launch_opts_container.find("pre").text
        launch_opts_dict = {"Launch Options":launch_opts}
    except:
        launch_opts_dict = {}

    try:
        for config in soup.find_all("pre", {"class":"js-csr-pre"}):
            if "CSGO" in config.text:
                crosshair_config = config.text
            if "viewmodel" in config.text:
                viewmodel_config = config.text

        config_opts_dict = {"Crosshair Config":crosshair_config, "Viewmodel Config":viewmodel_config}
    except:
        config_opts_dict = {}

    return socials, player_bio_dict, config_opts_dict, launch_opts_dict

first_page_url = "https://prosettings.net/games/cs2/"
page_n_url = first_page_url + "page/{}/"
page = 1
master_list = []

while True:
    if page == 1:
        url = first_page_url
    else:
        url = page_n_url.format(page)

    driver.get(url)
    driver.implicitly_wait(10)

    try: 
        cookies = driver.find_element(By.XPATH,'//*[@id="cmplz-cookiebanner-container"]/div[2]/div[6]/button[1]')
        cookies.click()
    except ElementNotInteractableException:
        print("Cookies have been already accepted.")

    soup = player_list()
    player_cards = soup.find("section", {"class":"players--container"})
    player_urls = processed_player_urls(player_cards)

    for player_url in player_urls:
        driver.get(player_url)
        driver.implicitly_wait(10)

        player_soup = player_list()
        socials, player_bio_dict, config_opts_dict, launch_opts_dict = leftover_extractor(player_soup)
        hud_settings = container_extractor(table_html_extractor(player_soup, "section--hud"))
        radar_settings = container_extractor(table_html_extractor(player_soup, "section--radar"))
        video_settings = container_extractor(table_html_extractor(player_soup, "section--video_settings", "div"))
        view_model_settings = container_extractor(table_html_extractor(player_soup, "section--viewmodel"))
        crosshair_settings = container_extractor(table_html_extractor(player_soup, "section--crosshair"))
        monitor_settings_table = container_extractor(table_html_extractor(player_soup, "monitor", "div"))
        graphics_card_settings = container_extractor(table_html_extractor(player_soup, "graphics_card", "div"))
        mouse_settings = container_extractor(table_html_extractor(player_soup, "section--mouse"))
        gear = containers_with_imgs(player_soup, "gear")
        pc_specs_dict = containers_with_imgs(player_soup, "pcspecs")
        setup_and_streaming = containers_with_imgs(player_soup, "setupstreaming")
        skins = containers_with_imgs(player_soup, "cs2_skins")

        merged_dict = {**player_bio_dict, 
                    **hud_settings, 
                    **radar_settings,
                    **video_settings,
                    **view_model_settings,
                    **crosshair_settings,
                    **monitor_settings_table,
                    **graphics_card_settings,
                    **mouse_settings,
                    **gear,
                    **pc_specs_dict,
                    **launch_opts_dict,
                    **setup_and_streaming,
                    **skins,
                    **socials,
                    **config_opts_dict
                    }

        master_list.append(merged_dict)
        
    if page == 46: break
    # if driver.find_element(By.CLASS_NAME, "pro-container--no-results"): break;

    page += 1
    time.sleep(5)

df = pd.DataFrame(master_list)
df.to_csv("prosettings_cs2_scrape.csv", index=False)
driver.quit()