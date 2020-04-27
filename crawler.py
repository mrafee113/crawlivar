from selenium.webdriver.chrome.webdriver import Options
from datetime import datetime, timedelta, date, time
from openpyxl.styles import NamedStyle, Font, Alignment, Side, Border
from time import sleep
from django.utils import timezone
from django import setup as django_setup
from pytz import timezone as tz

import pickle
import helium
import jdatetime
import openpyxl
import json
import os


def ls_items(driver):
    return driver.execute_script(
        "var ls = window.localStorage, items = {}; "
        "for (var i = 0, k; i < ls.length; ++i) "
        "  items[k = ls.key(i)] = ls.getItem(k); "
        "return items; ")


def ls_setitem(driver, key, value):
    driver.execute_script("window.localStorage.setItem(arguments[0], arguments[1]);", key, value)


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


def convert_naive_utc_to_aware(naive_datetime: datetime):
    utc = tz('UTC')
    if naive_datetime.tzinfo:
        raise ValueError("datetime is not naive")
    return utc.localize(naive_datetime)


def convert_utc_to_tehran(utc_datetime: datetime):
    utc = tz('UTC')
    tehran = tz('Asia/Tehran')
    if not utc_datetime.tzinfo:
        raise ValueError("naive datetime given")
    if utc_datetime.tzinfo != utc:
        raise ValueError("tzinfo of utc datetime is not utc")

    return utc_datetime.astimezone(tehran)


def convert_tehran_to_utc(tehran_datetime: datetime):
    utc = tz('UTC')
    tehran = tz('Asia/Tehran')
    if not tehran_datetime.tzinfo:
        raise ValueError("naive datetime given")
    if tehran_datetime.tzinfo != tehran:
        raise ValueError("tzinfo of utc datetime is not utc")

    return tehran_datetime.astimezone(utc)


def get_article_detailed_page(article_link="https://divar.ir/v/gX4JbAzd"):
    data = dict()

    driver.get(article_link)

    with open("article-page/page-cookies.pickle", 'rb') as file:
        for ck in pickle.load(file):
            driver.add_cookie(ck)

    with open("article-page/page-localStorage.pickle", 'rb') as file:
        for k, v in pickle.load(file).items():
            ls_setitem(driver, k, v)

    driver.refresh()
    helium.click('دریافت اطلاعات تماس')
    sleep(3)
    # TODO: add wait until element visible

    info_node = driver.find_element_by_xpath('//*[@class="post-page__info"]')

    data['title'] = info_node.find_element_by_xpath('//*[@class="post-header__title"]').text
    data['date_published'] = info_node.find_element_by_xpath('//span[@class="post-header__publish-time"]').text

    post_fields_node = info_node.find_element_by_xpath('//*[@class="post-fields"]')
    post_fields_span_texts_dict = load_utf8_json_file("article-page/post-fields-span-texts-dict.json")
    post_fields_span_texts = [i for i in post_fields_span_texts_dict.keys()]
    for post_field_item in post_fields_node.find_elements_by_xpath('//*[@class="post-fields-item"]'):
        span_text = post_field_item.text.split('\n')[0]
        if span_text in post_fields_span_texts:
            data[post_fields_span_texts_dict[span_text]['db_column']] = post_field_item.text[len(span_text) + 1:]

            if span_text == 'تلفن':
                data['phone'] = data['phone'].replace('کپی', '')

            if span_text == "محل":
                location_node = post_fields_node.find_element_by_xpath(
                    '//a[@class="post-fields-item__value" and contains(@href, "/s/")]')
                try:
                    href = location_node.get_attribute('href')
                except Exception as a:
                    print(a)
                    continue
                data['location_href'] = href

    data['description'] = info_node.find_element_by_xpath('//*[@class="post-page__description"]').text
    data['uri'] = driver.find_element_by_xpath('//span[@class="share-link__link"]').text

    data['datetime_crawled'] = timezone.now()

    return data


english_number_range = range(ord('0'), ord('9') + 1)
persian_number_range = range(ord('۰'), ord('۹') + 1)


def fa_to_en(num: str):
    result = str()
    for digit in num:
        if ord(digit) in persian_number_range:
            result += chr(ord(digit) - 1728)
    return result


def en_to_fa(num: str):
    result = str()
    for digit in num:
        if ord(digit) in english_number_range:
            result += chr(ord(digit) + 1728)
    return result


def extract_int_from_str(number: str):
    result = str()
    for digit in number:
        if ord(digit) in persian_number_range:
            result += chr(ord(digit) - 1728)
        elif ord(digit) in english_number_range:
            result += digit
    return result


def convert_crawl_data_for_excel(data):
    result = {k: v for k, v in data.items()}
    del result['datetime_crawled']

    now = timezone.now
    diff_times = load_utf8_json_file("article-page/diff-time.json")
    date_published = now() - timedelta(**diff_times[data['date_published']])
    date_published = convert_utc_to_tehran(date_published)
    jalali_date = jdatetime.datetime.fromgregorian(datetime=date_published)
    date_str = jalali_date.strftime('%d/%m/%Y')
    if 'روز' not in data['date_published'] and 'هفته' not in data['date_published']:
        time_str = jalali_date.strftime('%H:%M')
    else:
        time_str = '00:00'

    result['date_published'] = '/'.join(list(map(en_to_fa, date_str.split('/'))))
    result['time_published'] = ':'.join(list(map(en_to_fa, time_str.split(':'))))

    result['location'] = data['location'][7:].strip()

    return result


def create_template_excel_file():
    workbook = openpyxl.Workbook()
    workbook.encoding = 'utf-8'

    sheet = workbook.active
    sheet.title = 'دیوار'
    sheet.sheet_view.rightToLeft = True
    sheet.sheet_view.zoomToFit = True
    sheet.page_setup.fitToWidth = True

    global_style = NamedStyle(name="global")
    global_style.font = Font(name="B Nazanin", size=13, charset=1, family=0.0)
    global_style.alignment = Alignment(horizontal='center', vertical='center', readingOrder=2.0)
    global_style.border = Border(
        **{i: Side(border_style='thin') for i in ['top', 'bottom', 'left', 'right']}
    )
    workbook.add_named_style(global_style)

    column_info_dict = load_utf8_json_file('article-page/pyxl-column-info.json')
    for k, v in column_info_dict.items():
        sheet[f"{v['column_letter']}1"] = v['header_text']
        sheet[f"{v['column_letter']}1"].style = global_style
        sheet[f"{v['column_letter']}1"].font = Font(name="B Nazanin", size=13, bold=True)
        sheet.column_dimensions[v['column_letter']].width = v["column_width"]

    workbook.save('data/template.xlsx')


def load_excel_file(path):
    workbook = openpyxl.load_workbook(path)
    return workbook


def save_excel_file(workbook, path):
    workbook.save(path)


def append_data_to_excel(sheet, data):
    last_row = int(sheet.dimensions.split(":")[1][1])
    if last_row == 1:
        data['id'] = en_to_fa('1')
    else:
        data['id'] = en_to_fa(f'{int(sheet[f"A{last_row}"].value) + 1}')

    column_info_dict = load_utf8_json_file('article-page/pyxl-column-info.json')
    for k, v in column_info_dict.items():
        cell = sheet[f"{v['column_letter']}{last_row + 1}"]
        cell.style = 'global'
        cell.data_type = 's'
        cell.number_format = '@'
        cell.value = data[k]


def convert_crawl_data_for_db(data):
    result = {k: v for k, v in data.items()}

    now = timezone.now
    diff_times = load_utf8_json_file("article-page/diff-time.json")
    date_published = now() - timedelta(**diff_times[data['date_published']])
    result['date_published'] = date_published.date()
    if 'روز' not in data['date_published'] or 'هفته' not in data['date_published']:
        result['time_published'] = date_published.time()
    else:
        result['time_published'] = None

    result['phone'] = '0' + fa_to_en(data['phone'][-10:])
    result['area_size'] = int(fa_to_en(''.join(data['area_size'].replace('متر ', '').split('٫'))))
    result['price'] = int(fa_to_en(''.join(data['price'].replace(' تومان', '').split('٫'))))
    result['datetime_crawled'] = data['datetime_crawled']

    lfs = last_forward_slash = data['location_href'].rfind('/')
    slfs = second_to_last_forward_slash = data['location_href'].rfind('/', 0, lfs - 1)
    result['location_en'] = data['location_href'][lfs + 1:]
    result['category_en'] = data['location_href'][slfs + 1: lfs]

    result['location'] = data['location'][7:].strip()

    return result


os.environ['DJANGO_SETTINGS_MODULE'] = 'orm.settings'
django_setup()
from isfahan.models import Category, Location, Person, Article


def save_data_to_db(data):
    mapper = load_utf8_json_file('db/crawler_to_db_mapper.json')

    for table_name, fields in mapper.items():
        dict_name = table_name.lower() + '_kwargs'
        locals()[dict_name] = dict()
        for db_column, data_column in fields.items():
            locals()[dict_name][db_column] = data[data_column]

    category, category_created = Category.objects.get_or_create(
        name=locals()['category_kwargs']['name'],
        name_english=locals()['category_kwargs']['name_english']
    )

    location, location_created = Location.objects.get_or_create(
        name=locals()['location_kwargs']['name'],
        name_english=locals()['location_kwargs']['name_english'],
        defaults={'href': locals()['location_kwargs']['href']}
    )

    person, person_created = Person.objects.get_or_create(number=locals()['person_kwargs']['number'])

    article = Article(
        person=person,
        location=location,
        category=category,
        **locals()['article_kwargs']
    )
    article.save()


# test
driver = init_driver()
a = get_article_detailed_page()
pickle.dump(a, open('crawler_data.pickle', 'wb'))
b = convert_crawl_data_for_db(a)
pickle.dump(b, open('db_data.pickle', 'wb'))
save_data_to_db(b)
