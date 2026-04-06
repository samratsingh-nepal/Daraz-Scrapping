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
        
        # --- THE VIRTUAL LIST FIX ---
        # We must scroll slowly to trigger the dynamic loading of items.
        # This loop scrolls down 5 times to uncover hidden products.
        for i in range(5):
            driver.execute_script(f"window.scrollTo(0, {i * 800});")
            time.sleep(3) 
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        product_data = []

        # Find all product containers based on the 'group' class in your snippet
        cards = soup.find_all('div', class_='group')

        for card in cards:
            try:
                # 1. Title: Target the heading-h6 anchor
                title_el = card.select_one('a.heading-h6')
                title = title_el.get_text(strip=True) if title_el else None

                # 2. Description: Target the specific paragraph class
                desc_el = card.select_one('p.text-on-surface-dim-1')
                description = desc_el.get_text(strip=True) if desc_el else "No description"

                # 3. Price: Look for the span that contains the currency icon
                # Based on your HTML, it's a span with specific text classes near the SVG
                price = "N/A"
                price_container = card.find('span', class_='font-semibold')
                if price_container:
                    price = price_container.get_text(strip=True)

                if title and title not in [d['Title'] for d in product_data]:
                    product_data.append({
                        'Title': title,
                        'Price': price,
                        'Description': description
                    })
            except Exception:
                continue

        if not product_data:
            return None

        df = pd.DataFrame(product_data)
        csv_file = 'hamrobazaar_data.csv'
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        return csv_file

    except Exception as e:
        st.error(f"Error: {e}")
        return None
    finally:
        if driver:
            driver.quit()

# --- Streamlit UI ---
st.set_page_config(page_title="Hamrobazaar Scraper", layout="wide")
st.title("🏘️ Hamrobazaar Listing Scraper")

url_input = st.text_input("Category URL:", "https://hamrobazaar.com/category/06B8B8E6-4CDE-4D79-AE65-38B8BAA9FF17/56C5F377-50C1-424A-B6C2-24A8B3235DC7")

if st.button("Start Scraping"):
    with st.spinner("Scrolling through virtual list and extracting data..."):
        file_path = scrape_hamrobazaar(url_input)
        if file_path:
            df = pd.read_csv(file_path)
            st.success(f"Extracted {len(df)} listings!")
            st.dataframe(df)
            with open(file_path, "rb") as f:
                st.download_button("Download CSV", f, file_name="hamrobazaar_houses.csv")
        else:
            st.error("No data extracted. Try running it again.")
