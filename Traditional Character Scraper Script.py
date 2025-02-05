from bs4 import BeautifulSoup
import requests
import pandas as pd
pd.set_option('display.max_columns', None)
# Open Excel file
df = pd.read_excel('CharacterDatabase.xlsx')

URL = 'https://zh.wikisource.org/wiki/%E9%80%9A%E7%94%A8%E8%A7%84%E8%8C%83%E6%B1%89%E5%AD%97%E8%A1%A8'
page = requests.get(URL)
soup = BeautifulSoup(page.content, "html.parser")

# Find where the second appendix starts
appendix_two_start_title = soup.find('h2', {'id': '附件2._《通用规范汉字表》笔画检字表'})
appendix_two_start_parent = appendix_two_start_title.find_parent('div', {'class': 'mw-heading mw-heading2'})

# Get all traditional tables before the second appendix start (53 tables)
traditional_tables = appendix_two_start_parent.find_all_previous('table', {'class': 'multicol'}, limit=53)
traditional_tables.reverse()

# For every table, unpack the inner tables
inner_tables = []
for table in traditional_tables:
    inner_tables.extend(table.find_all('table', {'class': 'wikitable'}))


traditional_data = []
for table in inner_tables:
    # Ignore first row in the table as that only has the column names
    trs = table.find_all('tr')[1:]

    rowSpanCount = 0
    rowSpanData = {}
    for tr in trs:
        tds = tr.find_all('td')

        # If the count is 0, the end of the previous rowspan has been reached
        if rowSpanCount == 0:
            # First add the rowSpawnData to the traditional_data list
            if bool(rowSpanData):  # Ensure the dictionary is actually filled
                traditional_data.append((rowSpanData['position'], rowSpanData['simplified'], rowSpanData['traditional'], rowSpanData['variants']))

            # Reset rowSpanData
            rowSpanData = {}

            newCount = tds[0].get('rowspan')

            # Check if new td has rowspan property
            if newCount is not None:
                rowSpanCount = int(newCount) - 1

                # Extract the simplified and position first
                rowSpanData['position'] = int(tds[0].text)
                rowSpanData['simplified'] = tds[1].text

            else:  # New row does not have rowspan
                # Bandaid fix for case where multi-row spans across 2 tables
                if tds[0].text == "" and tds[1].text == "":
                    traditional = tds[2].find(string=True, recursive=False)
                    traditional = traditional.strip().strip("()") if traditional else ""
                    variants = tds[3].find(string=True, recursive=False)
                    variants = ','.join(variants.strip().strip("[]")) if variants else ""
                    # Get the last item in the traditional_data list and modify it
                    tpl = traditional_data.pop()
                    traditional_data.append((tpl[0], tpl[1], traditional, variants))
                    continue

                position = int(tds[0].text)
                simplified = tds[1].text
                traditional = tds[2].find(string=True, recursive=False)
                traditional = traditional.strip().strip("()") if traditional else ""
                variants = tds[3].find(string=True, recursive=False)
                variants = ','.join(variants.strip().strip("[]")) if variants else ""

                # Append data to traditional data
                traditional_data.append((position, simplified, traditional, variants))

        else:  # Guaranteed to only have 2 tds
            # Using .find() to avoid getting the superscript text
            rowSpanData['traditional'] = (
                rowSpanData.get('traditional', '') + ',' + tds[0].find(string=True, recursive=False).strip().strip("()")
                if 'traditional' in rowSpanData else tds[0].find(string=True, recursive=False).strip().strip("()")
            )

            rowSpanData['variants'] = (
                rowSpanData.get('variants', '') + ',' + tds[1].find(string=True, recursive=False).strip().strip("[]")
                if 'variants' in rowSpanData else ','.join(tds[1].find(string=True, recursive=False).strip().strip("[]"))
            )

            rowSpanCount -= 1

traditional_data_df = pd.DataFrame(traditional_data, columns=["Position", "Simplified", "Traditional", "Variants"])

# Fill up the Traditional and Variant columns with default data first
print(traditional_data_df)
left = df[["Position", "Simplified"]]
left = left.merge(traditional_data_df, how="left", on=["Position"])
left.drop(columns=["Simplified_y"], inplace=True)
left.rename(columns={'Simplified_x': 'Simplified'}, inplace=True)
left['Traditional'] = left['Traditional'].fillna('No Traditional Characters')
left['Variants'] = left['Variants'].fillna('No Variant Characters')

df['Variants'] = left['Variants']
df['Traditional'] = left['Traditional']

df.to_excel('CharacterDatabase.xlsx', index=False, engine="openpyxl")