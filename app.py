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
    # Using a modern User-Agent to avoid the "Bot Detection" screen
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    
    # Path for Streamlit Cloud
    chrome_options.binary_location = "/usr/bin/chromium"
    service = Service("/usr/bin/chromedriver")

    driver = None
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(url)
        
        # Hamrobazaar needs time to fetch data from their API
        time.sleep(10) 
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Hamrobazaar products are usually inside 'card' or 'product' styled containers
        # We look for all 'div' elements that contain the product info
        product_cards = soup.find_all('div', recursive=True)
        
        product_data = []

        for card in product_cards:
            # We filter for divs that look like they contain a price (Rs. or रू.)
            # This is a 'Broad Search' strategy
            card_text = card.get_text()
            if "Rs." in card_text or "रू" in card_text:
                try:
                    # Look for the title (usually the first bold or large text)
                    title_el = card.find(['h2', 'h3', 'span'], recursive=True)
                    # Look for price specifically
                    price_el = card.find(text=lambda t: "Rs." in t or "रू" in t)
                    
                    if title_el and price_el and len(title_el.text) > 5:
                        name = title_el.text.strip()
                        price = price_el.strip()
                        
                        # Avoid duplicates
                        if not any(d['product_name'] == name for d in product_data):
                            product_data.append({
                                'product_name': name,
                                'product_price': price
                            })
                except:
                    continue

        if not product_data:
            st.warning(f"No products found. The page might still be loading or structure changed. Page title: {driver.title}")
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
st.title("Hamrobazaar Category Scraper")

# Your specific category URL as default
target_url = "https://hamrobazaar.com/category/06B8B8E6-4CDE-4D79-AE65-38B8BAA9FF17/237B5864-5C80-46A3-AC73-ACAFCF2E8E5C"
url_input = st.text_input("Target URL:", value=target_url)

if st.button("Scrape Hamrobazaar"):
    with st.spinner('Accessing Hamrobazaar... please wait.'):
        csv_path = scrape_hamrobazaar(url_input)
        if csv_path:
            st.success(f"Found {len(pd.read_csv(csv_path))} items!")
            with open(csv_path, "rb") as f:
                st.download_button("Download Data as CSV", f, file_name=csv_path)
