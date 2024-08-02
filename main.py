
from enum import Enum
from logging import basicConfig, critical, CRITICAL
from requests import get
from time import sleep
from random import choice, randint

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from models import Base, AdultGarment, ChildGarment, Photo
from request_headers import USER_AGENTS as UA

basicConfig(filename='log.log', filemode='a', level=CRITICAL)


class Categories(Enum):
    ADULT = 'odezhda_obuv_aksessuary'
    CHILD = 'detskaya_odezhda_i_obuv'
    TOYS = 'tovary_dlya_detey_i_igrushki'
    BEAUTY = 'krasota_i_zdorove'
    FURNISHING = 'mebel_i_interer'


FILE = 'all_active_29_07_2024.html'
DISCLAIMER = '1.Все вещи в профиле'
MAX_PHOTOS = 20


def parse_item(link, item_type, sel, session):
    '''Parsing attributes, which are not class-specific.'''

    def tranctuate_description(description):
        return description.split(
            DISCLAIMER
        )[0] if DISCLAIMER in description else description

    sel.get(link)
    avito_id = int(link.split('_')[-1])
    name = sel.find_element(By.XPATH, "//h1[@itemprop='name']").text
    if sel.find_element(
        By.XPATH,
        "//*[@itemprop='priceCurrency']"
    ).get_attribute('content') != 'RUB':
        print('NON RUBLE PRICING')
        raise Exception("NON RUBLE PRICING")
    price = sel.find_element(
        By.XPATH,
        "//*[@itemprop='price']"
    ).get_attribute('content')
    description = tranctuate_description(
        sel.find_element(By.XPATH, "//*[@itemprop='description']").text
    )
    photos = []
    # open a gallery:
    sel.find_element(
        By.XPATH,
        "//*[@data-marker='image-frame/image-wrapper']"
    ).click()
    previous_image_number = -1
    for i in range(MAX_PHOTOS):
        image = sel.find_element(
            By.XPATH,
            "//*[@data-marker='extended-gallery/frame-img']"
        )
        avito_url = image.get_attribute('src')
        image_number = int(image.get_attribute("data-image-id"))
        if image_number <= previous_image_number:
            break
        photo_id = int(f'{avito_id}{image_number:>03}')
        # sel.send_keys(Keys.CONTROL + 't')
        # sel.get(avito_url)
        response = get(avito_url, headers={'User-Agent': choice(UA)})
        if response.status_code != 200:
            critical('COULD NOT DOWNLOAD IMAGE', image_number)
            downloaded = False
        else:
            with open(f'photos/{photo_id}.png', 'wb') as file:
                file.write(response.content)
                downloaded = True
        photo = Photo(
            id=photo_id,
            avito_url=avito_url,
            downloaded=downloaded
        )
        session.add(photo)
        session.commit()
        photos.append(photo)
        previous_image_number = image_number
        # next photo:
        sel.find_element(
            By.XPATH,
            "//*[@data-marker='extended-gallery-frame/control-right']"
        ).click()
        sleep(randint(2, 4))

    return item_type(
        name=name,
        price=price,
        description=description,
        id=avito_id,
        photos=photos
    )


def parse_garment(link, sel, session):
    if Categories.ADULT.value in link:
        garment_type = AdultGarment
    elif Categories.CHILD.value in link:
        garment_type = ChildGarment
    else:
        raise Exception('unknown category')
    item = parse_item(link, garment_type, sel, session)
    # Next add garment-specific fields:
    item.sex = 'Муж' if sel.find_element(
        By.PARTIAL_LINK_TEXT,
        'Мужская'
    ) else 'Жен'
    item.tag = BeautifulSoup(
        sel.find_element(
            By.XPATH,
            "//*[@itemscope]"
        ).get_attribute('innerHTML'),
        'lxml'
    ).find_all('span')[-4].text
    specs = BeautifulSoup(sel.page_source, 'lxml').find_all(
        'li',
        class_='params-paramsList__item-_2Y2O'
    )
    for li in specs:
        keyword = li.find('span').text
        if 'Тип' in keyword or 'Предмет' in keyword:
            item.tag = li.text
        elif 'Размер' in keyword:
            item.size = li.text.split(': ')[1]
        elif 'Цвет' in keyword:
            item.color = li.text.split(': ')[1]
        elif 'Бренд' in keyword:
            item.brand = li.text.split(': ')[1]
        elif 'Цвет' in keyword:
            item.color = li.text
        elif 'Состояние' in keyword:
            item.condition = li.text[len('Cостояние'):]
        elif 'Материал' in keyword:
            item.composition = li.text.split(': ')[1]
    print(f'{item.name} {item.price} {item.tag} {item.size} {item.color} {item.brand} {item.condition} {item.composition} {item.sex}')
    session.add(item)
    session.commit()


item_links = [link['href'].split('?')[0] for link in BeautifulSoup(
    open(FILE, 'r', encoding='utf-8'),
    features='lxml'
).find_all(attrs={
    'data-marker': 'item-title',
})]
print('item links', len(item_links))

engine = create_engine('sqlite:///sqlite.db')  # echo=True
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
session = Session(engine)

driver = webdriver.Chrome()
driver.implicitly_wait(11)

parse_garment(item_links[0], driver, session)
# for l in tqdm(item_links):
#    parse_item(l)
#    sleep(randint(5, 20))
