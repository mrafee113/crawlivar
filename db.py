import os
import django
import pickle

# os.environ['DJANGO_SETTINGS_MODULE'] = 'orm.settings'
# django.setup()
#
# data = pickle.load(open('d.pickle', 'rb'))
#
# print(data['time_published'])
# from test_models.models import TestModel
# from django.utils import timezone
#
# TestModel(datetime=timezone.now()).save()
from selenium.webdriver.chrome.webdriver import Options
import helium
import json

link = r'https://divar.ir/s/isfahan/real-estate/atashgah?districts=400%2C380%2C382%2C376%2C407%2C649%2C651%2C402%2C394%2C391%2C645%2C408%2C415%2C381%2C387%2C650%2C396%2C395%2C410%2C414%2C646%2C409%2C385%2C393%2C388%2C386%2C379%2C411%2C417%2C390%2C389%2C377%2C384%2C875%2C378%2C413%2C398%2C647%2C648%2C392%2C383%2C401%2C397%2C406%2C404%2C403'


def init_driver():
    profile_path = "/home/mehdi/.config/google-chrome/Default"
    options = Options()
    options.headless = False
    options.add_argument(f"user-data-dir={profile_path}")

    driver = helium.get_driver()
    if not driver:
        driver = helium.start_chrome(options=options)

    driver.set_window_rect(311, 142, 1550, 797)

    return driver


def load_utf8_json_file(file_name):
    with open(file_name, 'r', encoding='utf-8') as file:
        return json.load(file)


def dump_utf8_json_file(obj, file_name):
    with open(file_name, 'w', encoding='utf-8') as file:
        json.dump(obj, file, ensure_ascii=False)
