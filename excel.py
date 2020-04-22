from openpyxl.styles import NamedStyle, Font, Alignment, Side, Border
from pytz import timezone as tz
from datetime import datetime, timedelta, date, time
from django.utils import timezone
from math import floor

import json
import openpyxl
import jdatetime
import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'orm.settings'
django.setup()
from isfahan.models import Category, Location, Person, Article


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


def convert_fa_digits_to_en(date_str: str):
    result = str()
    for char in date_str:
        if ord(char) in persian_number_range:
            result += fa_to_en(char)
        else:
            result += char
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


# phone number
def validate_phone_number(number):
    if isinstance(number, int):
        return convert_int_phone_to_str(number)
    elif isinstance(number, str):
        return get_phone_number_from_str(number)
    else:
        raise ValueError("empty")


def convert_int_phone_to_str(number: int):
    if len(str(number)) < 10 or number < 0:
        raise ValueError("invalid number")

    return str(number)


def get_phone_number_from_str(number: str):
    if len(number) < 1:
        raise ValueError("empty")
    if len(number) < 10:
        raise ValueError("invalid number")

    phone = extract_int_from_str(number)
    if phone[-10:][0] != '9':
        raise ValueError("invalud number")

    return '0' + phone[-10:]


# area size
def validate_area_size(area_size):
    if isinstance(area_size, str):
        return convert_area_size_str_to_int(area_size)
    elif isinstance(area_size, int):
        return validate_area_size_int(area_size)
    else:
        raise ValueError("empty")


def convert_area_size_str_to_int(size: str):
    if len(size) < 1:
        raise ValueError("empty")
    area = ''.join(size.replace('متر', '').replace('هزار', '').strip().split('٫'))

    area_size = extract_int_from_str(area)
    return int(area_size)


def validate_area_size_int(size: int):
    area_size = size if size > 0 else -1 * size
    if area_size < 1:
        raise ValueError("size should not be lower than 1")

    return size


# price
def validate_price(price):
    if isinstance(price, str):
        return convert_price_str_to_int(price)
    elif isinstance(price, int):
        return price
    else:
        raise ValueError("empty")


def convert_price_str_to_int(price: str):
    if 'توافقی' in price:
        return None

    price_str = price.replace('میلیارد', '').replace('میلیون', '').replace('تومان', '').strip()

    if 'میلیارد' in price and 'میلیون' in price:
        billion, million = list(map(lambda x: x.strip(), price_str.split('و')))
        billion = extract_int_from_str(billion)
        million = extract_int_from_str(million)

        return int(billion) * 1000000000 + int(million) * 1000000

    else:
        price_str = extract_int_from_str(price_str)
        if 'میلیارد' in price:
            return int(price_str) * 1000000000
        elif 'میلیون' in price:
            return int(price_str) * 1000000
        else:
            return int(price_str)


# date
def validate_date(dt):
    if isinstance(dt, str):
        return convert_date_str_to_date(dt)
    elif isinstance(dt, datetime):
        return correct_false_date_datetime_to_datetime(dt)
    else:
        raise ValueError("empty")


def convert_date_str_to_date(date_str: str):
    first, month, third = list(
        map(lambda x: int(x.strip()), convert_fa_digits_to_en(date_str).strip().split('/')))
    year = max(first, third)
    day = min(first, third)

    if 1 <= year <= 17 or 21 <= year <= 31 or not 1 <= month <= 12 or not 1 <= day <= 31:
        raise ValueError("ambiguous date")

    date_obj = None
    if 1397 <= year <= 1400 or 97 <= year <= 99:
        date_obj = jdatetime.date(
            year if year > 100 else year + 1300,
            month,
            day
        ).togregorian()
    elif 2018 <= year <= 2020 or 18 <= year <= 20:
        date_obj = date(
            year if year > 100 else year + 2000,
            month,
            day
        )

    return date_obj


def correct_false_date_datetime_to_datetime(dt: datetime):
    year, month, day = dt.year, dt.month, dt.day
    if 1397 <= year <= 1400:
        return jdatetime.date(
            year, month, day
        ).togregorian()
    elif 2018 <= year <= 2021:
        return date(year, month, day)


# time
def validate_time(t, d: date):
    if isinstance(t, time):
        return correct_false_time(t, d)
    elif isinstance(t, datetime):
        return convert_time_datetime_to_time(t, d)
    elif isinstance(t, str):
        return convert_time_str_to_time(t, d)
    elif isinstance(t, int):
        return convert_time_int_to_time(t, d)
    elif t is None:
        return None


def correct_false_time(t: time, d: date):
    if t.hour == 0 and t.minute == 0:
        return None
    else:
        tehran = tz('Asia/Tehran')
        utc = tz('UTC')
        return utc.localize(tehran.localize(datetime.combine(d, t)).astimezone(utc).time())


def convert_time_datetime_to_time(dt: datetime, d: date):
    if dt.hour == 0 and dt.minute == 0:
        return None
    else:
        return correct_false_time(dt.time(), d)


def convert_time_str_to_time(t: str, d: date):
    result = convert_fa_digits_to_en(t).strip()
    if not result:
        raise ValueError("empty string")
    result = result.split(':')
    if len(result) == 1:
        if not result[0].isdecimal():
            raise ValueError("non-integer")
        return correct_false_time(time(int(result[0]), 0, 0), d)
    elif len(result) == 2:
        if not result[0].isdecimal() or not result[1].isdecimal():
            raise ValueError("non-integer")
        return correct_false_time(time(int(result[0]), int(result[1]), 0), d)
    elif len(result) == 3:
        if not all(map(lambda x: not isinstance(x, ValueError),
                       map(lambda x: x if x.isdecimal() else ValueError("non-integer"), result))):
            raise ValueError("non-integer")
        return correct_false_time(time(*list(map(int, result))), d)


def convert_time_int_to_time(t: int, d):
    if t == 0:
        return None
    else:
        return correct_false_time(time(t, 0, 0), d)


def validate_others(obj):
    if not obj or not isinstance(obj, str):
        raise ValueError("empty")
    else:
        return obj


columns = {'B': 'title', 'C': 'phone', 'D': 'category', 'E': 'area_size', 'F': 'price', 'G': 'location',
           'H': 'publisher_type', 'I': 'description', 'J': 'date_published', 'K': 'time_published'}

validations = [
    {
        'name': 'title',
        'column': 'B',
        'function': validate_others,
        'args': ['title']
    },
    {
        'name': 'phone',
        'column': 'C',
        'function': validate_phone_number,
        'args': ['phone']
    },
    {
        'name': 'category',
        'column': 'D',
        'function': validate_others,
        'args': ['category']
    },
    {
        'name': 'area_size',
        'column': 'E',
        'function': validate_area_size,
        'args': ['area_size']
    },
    {
        'name': 'price',
        'column': 'F',
        'function': validate_price,
        'args': ['price']
    },
    {
        'name': 'location',
        'column': 'G',
        'function': validate_others,
        'args': ['location']
    },
    {
        'name': 'publisher_type',
        'column': 'H',
        'function': validate_others,
        'args': ['publisher_type']
    },
    {
        'name': 'description',
        'column': 'I',
        'function': validate_others,
        'args': ['description']
    },
    {
        'name': 'date_published',
        'column': 'J',
        'function': validate_date,
        'args': ['date_published']
    },
    {
        'name': 'time_published',
        'column': 'K',
        'function': validate_time,
        'args': ['time_published', 'date_published']
    }
]


def validate(sheet, min_row: int, max_row: int):
    corrected_rows = list()
    errored_rows = list()

    for row_number in range(min_row, max_row + 1):
        row = dict()
        row['row_number'] = row_number

        for column in 'BCDEFGHIJK':
            row[columns[column]] = sheet[f'{column}{row_number}'].value

        error = False
        for validator in validations:
            args = list()
            for arg in validator['args']:
                args.append(row[arg])

            try:
                row[validator['name']] = validator['function'](*args)
            except Exception as e:
                error = True
                row[validator['name']] = {'error': e.args[0], 'value': row[validator['name']]}

        if not error:
            corrected_rows.append(row)
        else:
            errored_rows.append(row)
    return corrected_rows, errored_rows


rows = list()


def str_similiar(str_1: str, str_2: str):
    if str_1 == str_1:
        return True
    elif str_1 in str_2:
        return True
    elif str_2 in str_1:
        return True
    else:
        return False


def add(old_corrected: list, new_corrected: list):
    for new in new_corrected:
        found = False
        for old in old_corrected:
            if new['phone'] == old['phone'] and str_similiar(new['title'], old['title']):
                found = True
                break
            if new['price'] == old['price'] and new['area_size'] == old['area_size'] and \
                    new['date_published'] == old['date_published']:
                found = True
                break
        if not found:
            old_corrected.append(new)


file_dicts = dict()
file_list = os.listdir('xlsx_archive')
for file in file_list:
    file_dicts[file] = dict()
    workbook = load_excel_file(f'xlsx_archive/{file}')
    file_dicts[file]['sheet'] = workbook.active
    file_dicts[file]['max_row'] = int(file[:file.rfind('.')].split('_')[1])
    file_dicts[file]['corrected'], file_dicts[file]['errored'] = validate(file_dicts[file]['sheet'], 2,
                                                                          file_dicts[file]['max_row'])
    add(rows, file_dicts[file]['corrected'])

for i in rows:
    i['location'] = i['location'].replace('اصفهان', '').replace('محل', '').replace('،', '').strip()


def find_false_locations(rows_list: list):
    correct_locations_list = load_utf8_json_file('locations.json')
    locations = list()
    false_to_correct = dict()
    for i in rows_list:
        if i['location'].replace('(', '').replace(')', '').strip() not in locations:
            locations.append(i['location'].replace('(', '').replace(')', '').strip())

    locations.sort()
    for i in locations:
        max_match_idx = 0
        max_match_value = 0
        iword = i.replace(' ', '')
        for jdx, j in enumerate(correct_locations_list):
            jword = j.replace(' ', '')
            match_value = 0
            idx = 0
            for kdx, k in enumerate(jword):
                if idx >= len(iword) - 1:
                    break
                if jword[kdx] == iword[idx]:
                    match_value += 1
                    idx += 1
                elif kdx != len(jword) - 1:
                    if jword[kdx] == iword[idx + 1] and jword[kdx + 1] != iword[idx + 1]:
                        match_value += 1
                        idx += 2
                    elif jword[kdx] == iword[idx + 1] and jword[kdx + 1] == iword[idx + 1]:
                        idx += 1
            if match_value > max_match_value:
                max_match_value = match_value
                max_match_idx = jdx
        false_to_correct[i] = correct_locations_list[max_match_idx]
    return false_to_correct


false_to_correct_location_map = find_false_locations(rows)
false_to_correct_location_map['لبنان'] = 'لنبان'
false_to_correct_location_map['خانه'] = 'خانه اصفهان'
false_to_correct_location_map['دروازه تهران (میدان جمهوری)'] = 'دروازه تهران (میدان جمهوری)'
false_to_correct_location_map['دروازه تهران(میدان جمهوری)'] = 'دروازه تهران (میدان جمهوری)'
false_to_correct_location_map['دروازه شیراز (میدان آزادی)'] = 'دروازه شیراز (میدان آزادی)'
false_to_correct_location_map['دروازه شیراز(میدان آزادی)'] = 'دروازه شیراز (میدان آزادی)'
false_to_correct_location_map['میر'] = 'میر'
false_to_correct_location_map['پل شیری(صاپب)'] = 'پل شیری (صائب)'

del false_to_correct_location_map['گز']

correct_locations_list = load_utf8_json_file('locations.json')
for i in rows:
    if i['location'] in false_to_correct_location_map:
        i['location'] = false_to_correct_location_map[i['location']]
