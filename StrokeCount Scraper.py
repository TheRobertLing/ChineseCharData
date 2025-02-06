from bs4 import BeautifulSoup
import requests
import pandas as pd


# Get the page HTML
URL = 'https://zh.wikisource.org/wiki/%E9%80%9A%E7%94%A8%E8%A7%84%E8%8C%83%E6%B1%89%E5%AD%97%E8%A1%A8'
page = requests.get(URL)
soup = BeautifulSoup(page.content, "html.parser")

stroke_dict = {
    "一画": 1, "二画": 2, "三画": 3, "四画": 4, "五画": 5, "六画": 6, "七画": 7, "八画": 8, "九画": 9, "十画": 10,
    "十一画": 11, "十二画": 12, "十三画": 13, "十四画": 14, "十五画": 15, "十六画": 16, "十七画": 17, "十八画": 18, "十九画": 19,
    "二十画": 20, "二十一画": 21, "二十二画": 22, "二十三画": 23, "二十四画": 24, "二十五画": 25, "二十六画": 26, "二十七画": 27,
    "二十八画": 28, "二十九画": 29, "三十画": 30, "三十一画": 31, "三十二画": 32, "三十三画": 33, "三十四画": 34, "三十五画": 35,
    "三十六画": 36
}

# Find reference
stroke_order_title = soup.find('h2', {'id': '附件2._《通用规范汉字表》笔画检字表'})

# Find all tables containing the character data
tds = stroke_order_title.find_parent('div').find_all_next('td')

# Keep track of current strokeCount
stroke_count = 0
data = []
for td in tds:
    for tag in td.find_all(["p", "dl"], recursive=False):
        if tag.name == "p":
            # Get the stroke count
            if tag.find('b'):
                stroke_count = stroke_dict[tag.text.strip()]

        elif tag.name == "dl":
            # Get a list of all dds
            for dd in tag.find_all('dd'):
                # Add the character and stroke count
                data.append((dd.text.strip()[-1], stroke_count))

stroke_counter_data = pd.DataFrame(data, columns=["Simplified", "Stroke Count"])

with pd.ExcelWriter("CharacterDatabase.xlsx", engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
    stroke_counter_data.to_excel(writer, sheet_name="Sheet3", index=False)
