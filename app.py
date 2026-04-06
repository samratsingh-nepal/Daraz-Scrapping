import streamlit as st
import pandas as pd
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

def scrape_hamrobazaar(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
    
    # Cloud Config
    chrome_options.binary_location = "/usr/bin/chromium"
    service = Service("/usr/bin/chromedriver")

    driver = None
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(url)
        
        # Scroll to load more than 3 products
        driver.execute_script("window.scrollTo(0, 1000);")
        time.sleep(5)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(8) 
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        product_data = []

        # 1. Target the titles using the class you provided
        # We use a partial match 'heading-h6' because the rest can be dynamic
        titles = soup.select('a[class*="heading-h6"]')

        for title_el in titles:
            title_text = title_el.get_text(strip=True)
            
            # 2. Find the Card Container
            # We go up to the main div that holds the image, title, and price
            card = title_el.find_parent('div')
            # Move up a few more levels if necessary to get the full card info
            for _ in range(3):
                if card and ("Rs." in card.get_text() or "रू" in card.get_text()):
                    break
                card = card.parent if card else None

            if card:
                # 3. Extract Price
                price_el = card.find(string=lambda t: "Rs." in t or "रू" in t)
                price = price_el.strip() if price_el else "N/A"

                # 4. Extract Description
                # Usually a span or p tag inside the same card that isn't the title
                description = "N/A"
                all_texts = card.find_all(['span', 'p', 'div'], recursive=True)
                for t in all_texts:
                    txt = t.get_text(strip=True)
                    # The description is usually the 'middle' length text
                    if 20 < len(txt) < 200 and txt != title_text and "Rs." not in txt:
                        description = txt
                        break

                if title_text not in [d['Title'] for d in product_data]:
                    product_data.append({
                        'Title': title_text,
                        'Price': price,
                        'Description': description
                    })

        if not product_data:
            return None

        df = pd.DataFrame(product_data)
        csv_file = 'hamrobazaar_houses.csv'
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        return csv_file

    except Exception as e:
        st.error(f"Error: {e}")
        return None
    finally:
        if driver:
            driver.quit()

# --- Streamlit UI ---
st.set_page_config(page_title="Hamrobazaar House Scraper", layout="wide")
st.title("🏘️ Hamrobazaar House Listings Scraper")

default_url = "https://hamrobazaar.com/category/06B8B8E6-4CDE-4D79-AE65-38B8BAA9FF17/56C5F377-50C1-424A-B6C2-24A8B3235DC7"
url_input = st.text_input("Category URL:", value=default_url)

if st.button("Start Extraction"):
    with st.spinner("Processing listings... this takes a moment."):
        path = scrape_hamrobazaar(url_input)
        if path:
            df = pd.read_csv(path)
            st.success(f"Found {len(df)} listings!")
            st.dataframe(df, use_container_width=True)
            with open(path, "rb") as f:
                st.download_button("Download CSV", f, file_name="houses.csv")
            os.remove(path)
        else:
            st.error("No data found. Try refreshing or checking the URL.")
