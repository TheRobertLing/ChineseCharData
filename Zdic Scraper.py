from bs4 import BeautifulSoup
import requests
import pandas as pd
import json
pd.set_option('display.max_columns', None)

# Open Excel file
df = pd.read_excel('CharacterDatabase.xlsx')

# Extract Simplified Characters
char_list = df["Simplified"]

# Sample data for scraping
BASE_URL = 'https://www.zdic.net/hans/'
char = '吗'

page = requests.get(BASE_URL + char)
soup = BeautifulSoup(page.content, "html.parser")

# Find the input and definition sections
input_section = soup.find('td', {'class': 'ziif_d_l'}).find_next_sibling('td').find_all('table', {'class': 'dsk'})
definition_section = soup.find('div', {'class': 'content definitions jnr'})

pinyin = ''
zhuyin = ''
wubi = ''
cangjie = ''
zhengma = ''
four_corners = ''
unicode = ''
radical = ''
stroke_count = 0
definitions_chinese = []  # Store definitions in list of JSONS

# Extract basic information
for index, section in enumerate(input_section):
    tr = section.find_all('tr')[-1]  # only get last tr, as first one would only be for the title
    if index == 0:
        # Pinyin
        pinyin_spans = tr.find('td', {'class': 'z_py'}).find_all('span', {'class': 'z_d song'})
        pinyin_list = [span.text.strip() for span in pinyin_spans]
        pinyin = ",".join(pinyin_list)

        # Zhuyin
        zhuyin_spans = tr.find('td', {'class': 'z_zy'}).find_all('span', {'class': 'z_d song'})
        zhuyin_list = [span.text.strip() for span in zhuyin_spans]
        zhuyin = ",".join(zhuyin_list)

        # Radical
        radical = (tr
                   .find('td', {'class': 'z_bs2'})
                   .find('span', {'class': 'z_ts2'})
                   .find_next_sibling('a')
                   .text.strip())  # always first span z_ts2

        # Stroke Count
        stroke_count = int(tr.find('td', {'class': 'z_bs2'})
                           .find('span', {'class': 'z_ts3'})
                           .find_next_sibling(string=True).strip())

    elif index == 1:
        # Unicode
        unicode = tr.find('td', {'class': 'dsk_2_1'}).text[4:]
    else:
        input_spans = tr.find_all('td', {'class': 'dsk_2_1'})
        # Wubi
        wubi = input_spans[0].text.strip()
        # CangJie
        cangjie = input_spans[1].text.strip()
        # ZhengMa
        zhengma = input_spans[2].text.strip()
        # Four Corners
        four_corners = input_spans[3].text.strip()

# Find the 'dicpy' references
dicpy_list = definition_section.find_all('span', {'class': 'dicpy'})

# Extract definitions
for dicpy in dicpy_list:
    # Pinyin for def
    def_py = dicpy.text.strip().split()[0]
    # Zhuyin for def
    def_zy = dicpy.text.strip().split()[1]

    # Get ordered list right after the parent of the dicpy
    def_list = dicpy.find_parent('p').find_next_sibling('ol')

    # Check if the definition is a singular p tag or a list of definitions
    p_tag = def_list.find('p')

    # Append definitions using a JSON style format
    if p_tag:
        definitions_chinese.append(json.dumps({
            'py': def_py,
            'zy': def_zy,
            'defs': [p_tag.text.strip("◎ \u3000")]
        }))
        print(p_tag.text.strip("◎ \u3000"))
    else:
        li_text = [li.text.strip() for li in def_list.find_all('li')]
        definitions_chinese.append(json.dumps({
            'py': def_py,
            'zy': def_zy,
            'defs': li_text,
        }))














