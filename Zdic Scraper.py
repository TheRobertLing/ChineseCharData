from bs4 import BeautifulSoup
import httpx  # Async HTTP requests
import asyncio
import pandas as pd
import json

pd.set_option('display.max_columns', None)

# Open Excel file
df = pd.read_excel('CharacterDatabase.xlsx')

# Extract Simplified Characters
char_list = df["Simplified"]

#Instead of reading from Excel, define test data
# df_test = pd.DataFrame({
#     "Simplified": ["䦃", "𪣻"]  # Add more test characters as needed
# })
# char_list = df_test["Simplified"]

# Sample data for scraping
BASE_URL = 'https://www.zdic.net/hans/'

# List for storing Data
data = []
errors = []

semaphore = asyncio.Semaphore(10)  # Limit to 10 concurrent requests at a time


async def extract_char_data(character, session):
    """Fetch character data with rate limiting."""
    async with semaphore:
        try:
            url = f"https://www.zdic.net/hans/{character.strip()}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
            }
            response = await session.get(url, headers=headers, timeout=20)
            await asyncio.sleep(0.5)  # Delay to prevent blocking

            if response.status_code != 200:
                print(f"❌ Error {response.status_code} for {character}")
                return None

            soup = BeautifulSoup(response.content, "html.parser")
            print(f"✅ Successfully fetched {character}")

            # Find the input and definition sections
            input_section = soup.find('td', {'class': 'ziif_d_l'}).find_next_sibling('td').find_all('table',
                                                                                                    {'class': 'dsk'})
            definition_section = soup.find('div', {'class': 'content definitions jnr'})


            # Initialize variables
            pinyin = zhuyin = wubi = cangjie = zhengma = four_corners = unicode = radical = ''
            stroke_count = 0
            definitions_chinese = []

            # Extract basic information
            for index, section in enumerate(input_section):
                tr_title = section.find_all('tr')[0]
                tr = section.find_all('tr')[1]
                if index == 0:
                    # Pinyin
                    pinyin_spans = tr.find('td', {'class': 'z_py'})
                    if pinyin_spans:
                        # To account for many pinyin sounds
                        pinyin = ",".join([span.text.strip() for span in pinyin_spans.find_all('span', {'class': 'z_d song'})])

                    # Zhuyin
                    zhuyin_spans = tr.find('td', {'class': 'z_zy'})
                    if zhuyin_spans:
                        zhuyin = ",".join([span.text.strip() for span in zhuyin_spans.find_all('span', {'class': 'z_d song'})])

                    # Radical
                    radical = (tr.find('td', {'class': 'z_bs2'})
                               .find('span', {'class': 'z_ts2'})
                               .find_next_sibling('a')
                               .text.strip())

                    # Stroke Count
                    stroke_count = int(tr.find('td', {'class': 'z_bs2'})
                                       .find('span', {'class': 'z_ts3'})
                                       .find_next_sibling(string=True).strip())
                elif index == 1:
                    # Unicode
                    unicode = tr.find('td', {'class': 'dsk_2_1'}).text[4:]
                else:
                    headers = [td.text.strip() for td in tr_title.find_all('td', {'class': 'dsk_2_1'})]
                    values = [td.text.strip() for td in tr.find_all('td', {'class': 'dsk_2_1'})]
                    data_map = dict(zip(headers, values))

                    wubi = data_map.get("五笔", '')
                    cangjie = data_map.get("仓颉", '')
                    zhengma = data_map.get("郑码", '')
                    four_corners = data_map.get("四角", '')

            # Extract Definitions
            dicpy_list = definition_section.select("p > span.dicpy")

            if not dicpy_list:  # Check if dicpy_list is empty
                print(f"No definitions found for {character}")
                return (character, pinyin, zhuyin, wubi, cangjie, zhengma, four_corners, unicode, radical, stroke_count,
                        definitions_chinese)

            filtered_dicpy = []

            # Get the pinyin.zhuyin for the definition
            for span in dicpy_list:
                # Ensure only the title span gets appended
                if span.find("span", class_="ptr"):
                    filtered_dicpy.append(span)


            for dicpy in filtered_dicpy:
                # Get pinyin and zhuyin for definition
                def_py = dicpy.text.strip().split()[0]
                def_zy = dicpy.text.strip().split()[1]

                #
                def_list = dicpy.find_parent('p').find_next_sibling('ol')

                if not def_list:
                    # Somtimes may not be an ordered list but just a paragraph
                    p_tag = dicpy.find_parent('p').find_next_sibling('p')
                else:
                    p_tag = def_list.find('p')

                if p_tag:
                    definitions_chinese.append(json.dumps({
                        'py': def_py,
                        'zy': def_zy,
                        'defs': [p_tag.text.strip("◎ \u3000")]
                    }))
                else:
                    li_text = [li.text.strip() for li in def_list.find_all('li')]
                    definitions_chinese.append(json.dumps({
                        'py': def_py,
                        'zy': def_zy,
                        'defs': li_text,
                    }))

            # ✅ Return extracted data as a tuple
            return (character, pinyin, zhuyin, wubi, cangjie, zhengma, four_corners, unicode, radical, stroke_count,
                    definitions_chinese)

        except Exception as e:
            print(f"❌ Error processing {character}: {e}")
            # Return everything that has been extracted
            return (character, pinyin, zhuyin, wubi, cangjie, zhengma, four_corners, unicode, radical, stroke_count,
                    definitions_chinese)


async def process_in_batches(batch_size=50):
    """Process characters in batches of 50 at a time."""
    async with httpx.AsyncClient() as session:
        for i in range(0, len(char_list), batch_size):
            batch = char_list[i:i+batch_size]  # Take 50 characters at a time
            print(f"🔄 Processing batch {i//batch_size + 1}: {len(batch)} characters...")

            tasks = [extract_char_data(char, session) for char in batch]
            results = await asyncio.gather(*tasks)

            # Filter out None values (failed requests)
            valid_results = [res for res in results if res]
            print(f"✅ Finished batch {i//batch_size + 1}: {len(valid_results)} successful requests\n")

            # Append the results
            data.extend(valid_results)
            # Optional: Delay between batches to prevent rate limiting
            await asyncio.sleep(2)

# Run the batching function
asyncio.run(process_in_batches(batch_size=50))

df_new = pd.DataFrame(data, columns=["Simplified", "Pinyin", "Zhuyin", "Wubi", "Cangjie", "Zhengma",
                                     "Four Corners", "Unicode", "Radical", "Stroke Count", "Definitions Simplified"])

# # Open the existing Excel file and append data (without overwriting)
with pd.ExcelWriter("CharacterDatabase.xlsx", mode="a", engine="openpyxl", if_sheet_exists="overlay") as writer:
    df_new.to_excel(writer, sheet_name="Sheet2", index=False, header=True, startrow=writer.sheets["Sheet2"].max_row)

print("✅ Data successfully appended to Excel!")
print(len(errors), errors)
