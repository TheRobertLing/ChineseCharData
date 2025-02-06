from bs4 import BeautifulSoup
import requests
import pandas as pd

# Open Excel file
df = pd.read_excel('CharacterDatabase.xlsx')

# Get the page HTML
URL = 'https://zh.wikisource.org/wiki/%E9%80%9A%E7%94%A8%E8%A7%84%E8%8C%83%E6%B1%89%E5%AD%97%E8%A1%A8'
page = requests.get(URL)
soup = BeautifulSoup(page.content, "html.parser")

# Find where the appendix starts
appendix_start_title = soup.find('h2', {'id': '附件1._规范字与繁体字、异体字对照表'})
appendix_start_parent = appendix_start_title.find_parent('div', {'class': 'mw-heading mw-heading2'})

# Get all simplified Chinese tables before the appendix start
character_tables = appendix_start_parent.find_all_previous('table', {'class': 'multicol'})
character_tables.reverse()

# Extract character data
character_data = []
for table in character_tables:
    for dd in table.find_all('dd'):
        # Get text and strip whitespaces
        string = dd.text.strip()
        character_data.append((int(string[:4]), string[4:6]))

# Write the character data into a data frame and concatenate it to the existing data frame
character_data_df = pd.DataFrame(character_data, columns=["Position", "Simplified"])
df["Position"] = character_data_df["Position"]
df["Simplified"] = character_data_df["Simplified"]

# Write back to the same sheet, overwriting the data
with pd.ExcelWriter('CharacterDatabase.xlsx', engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
    df.to_excel(writer, sheet_name='Sheet1', index=False)
