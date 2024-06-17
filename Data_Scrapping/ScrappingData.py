# !pip install selenium

import pandas as pd
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import re

driver = webdriver.Chrome()

driver.maximize_window()

driver.get("https://www.1mg.com/categories/homeopathy-57?filter=true&page=1")

# Upon opening the website a popup window is coming so to close that we are using this cose snippet
driver.find_element(By.CLASS_NAME, 'UpdateCityModal__update-btn___2qmN1.UpdateCityModal__btn___oMW5n').click()

# If you don't want to start from the starting page then can skip pages using this code snippet'
# skip_pages = 10
# for i in range(skip_pages):
#     time.sleep(3)
#     driver.find_element(By.CLASS_NAME, 'button-text.link-next').click()

parent_list = []
pages_to_scrape = 20
for i in range(pages_to_scrape):
    parent_list += driver.find_elements(By.CLASS_NAME, 'col-md-3.col-sm-4.col-xs-6.style__container___1TL2R')
    time.sleep(3)
    driver.find_element(By.CLASS_NAME, 'button-text.link-next').click()
    time.sleep(3)

reference_dict = {
    "Name": "style__pro-title___2QwJy",
    "Size": "style__pack-size___2JQG7",
    "MRP": "style__discount-price___25Bya",
    "Price": "style__price-tag___cOxYc",
    "1mg URL": ["style__product-link___UB_67", "href"],
    "Ratings": "CardRatingDetail__weight-700___27w9q",
    "No. of Ratings": "CardRatingDetail__ratings-header___2yyQW",
}

values_dict = {
    "Name": [],
    "Size": [],
    "MRP": [],
    "Price": [],
    "1mg URL": [],
    "Ratings": [],
    "No. of Ratings": [],
}


def extract_values(total_records, class_name, att=0):
    values = []
    if att == 0:
        for i in total_records:
            try:
                values.append(i.find_element(By.CLASS_NAME, class_name).text)
            except:
                values.append("NA")
    else:
        for i in total_records:
            try:
                values.append(i.find_element(By.CLASS_NAME, class_name).get_attribute(att))
            except:
                values.append("NA")
    return values


for key, value in values_dict.items():
    if len(reference_dict[key]) != 2:
        value.extend(extract_values(parent_list, reference_dict[key]))
    else:
        value.extend(extract_values(parent_list, reference_dict[key][0], reference_dict[key][1]))

product_df = pd.DataFrame.from_dict(values_dict)

remain_values = {
    "Name": [],
    "Brand Name": [],
    "Key Benefits": [],
    "Key Ingredients": [],
}


def get_element_text(by, value):
    try:
        return driver.find_element(by, value).text
    except NoSuchElementException:
        return " "


for url in values_dict['1mg URL']:
    driver.get(url)

    key_ingredients = []
    key_benefits = []
    name_brand_added = False

    try:
        WebDriverWait(driver, 4).until(EC.presence_of_element_located((By.CLASS_NAME, 'ProductTitle__product-title___3QMYH')))
        product_name = get_element_text(By.CLASS_NAME, 'ProductTitle__product-title___3QMYH')
        brand_name = get_element_text(By.CLASS_NAME, 'ProductTitle__marketer___7Wsj9')

        remain_values["Name"].append(product_name)
        remain_values["Brand Name"].append(brand_name)
        name_brand_added = True

        WebDriverWait(driver, 4).until(
            EC.presence_of_element_located((By.XPATH, "//b[following-sibling::ul] | //strong[following-sibling::ul]"))
        )
        headings_and_lists = driver.find_elements(By.XPATH, "//b[following-sibling::ul] | //strong[following-sibling::ul]")

        for heading in headings_and_lists:
            heading_text = heading.text.lower()
            following_siblings = heading.find_elements(By.XPATH, "following-sibling::*")

            for sibling in following_siblings:
                if sibling.tag_name in ("b", "strong"):
                    break
                if sibling.tag_name == "ul":
                    if "ingredients" in heading_text:
                        key_ingredients.extend([child.text for child in sibling.find_elements(By.XPATH, ".//*")])
                    elif "benefits" in heading_text:
                        key_benefits.extend([child.text for child in sibling.find_elements(By.XPATH, ".//*")])

    except TimeoutException:
        print(f"Timed out waiting for elements on page: {url}")
        if not name_brand_added:
            remain_values["Name"].append("")
            remain_values["Brand Name"].append("")

    except NoSuchElementException as e:
        print(f"Element not found: {str(e)}")
        if not name_brand_added:
            remain_values["Name"].append("")
            remain_values["Brand Name"].append("")

    if not key_ingredients:
        prod_des = driver.find_element(By.CLASS_NAME, 'ProductDescription__description-content___A_qCZ').text
        pattern = re.compile(r'Key Ingredients?:\s*((?:.+\n?)+)(?=\n\n|Key Benefits:|Directions For Use:|Safety Information:|Indications:)')
        match = pattern.search(prod_des)
        if match:
            key_ingredients = match.group(1).strip().splitlines()
            remain_values["Key Ingredients"].append(key_ingredients)
        else:
            remain_values["Key Ingredients"].append([])
    else:
        remain_values["Key Ingredients"].append(key_ingredients)

    if not key_benefits:
        remain_values["Key Benefits"].append([])
    else:
        remain_values["Key Benefits"].append(key_benefits)

    time.sleep(2)

driver.quit()


for i in remain_values.values():
    print(len(i))

remaining_data = pd.DataFrame.from_dict(remain_values)

combined_data = pd.concat([product_df, remaining_data], axis=1)

# I created this as a backup copy of the original
data_copy = combined_data.copy()
print(data_copy)

print(data_copy.head())
print(data_copy.info())

print(data_copy.isnull().sum())

data_copy.columns = ["name", "size_of_the_bottle", "MRP_of_the_bottle", "price_of_the_bottle", "1mg_url", "rating", "number_of_rating", "again_name", "brand_name", "key_benefits", "key_ingredients"]
data_copy.drop(["again_name"], axis=1)
data_copy = data_copy[["name", "size_of_the_bottle", "MRP_of_the_bottle", "price_of_the_bottle", "1mg_url", "brand_name", "key_benefits", "key_ingredients", "rating", "number_of_rating"]]
data_copy.head(5)

# I created this as a second backup copy of the original and modifying this each time I'm doing something to the fist backup copy so that I can reterive after any step if it goes wrong
data_copy_backup = data_copy.copy()


data_copy.drop_duplicates(subset=["name", "size_of_the_bottle", "MRP_of_the_bottle", "price_of_the_bottle", "1mg_url", "brand_name", "rating", "number_of_rating"])
data_copy['size_of_the_bottle'] = data_copy['size_of_the_bottle'].str.extract(r'(\d+\s*\w+)', expand=False)
data_copy['price_of_the_bottle'] = data_copy['price_of_the_bottle'].str.extract(r'(\d+)').astype(float)
data_copy['MRP_of_the_bottle'] = data_copy['MRP_of_the_bottle'].str.extract(r'(\d+)').astype(float)
data_copy['MRP_of_the_bottle'].fillna(data_copy['price_of_the_bottle'], inplace=True)
data_copy['rating'] = data_copy['rating'].replace("NA", 0)
data_copy['number_of_rating'] = data_copy['number_of_rating'].str.extract(r'(\d+)')
data_copy['number_of_rating'].fillna(0, inplace=True)
data_copy.to_csv("Table2_scrapingData4.csv", index=False)
data_copy["name"].to_csv("Table1_scrapingData4.csv", index=False)
