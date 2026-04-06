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
    # Stealth User-Agent to avoid bot detection
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
    
    # Paths for Streamlit Cloud
    chrome_options.binary_location = "/usr/bin/chromium"
    service = Service("/usr/bin/chromedriver")

    driver = None
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(url)
        
        # 1. Scroll to trigger content loading (important for more than 3 products)
        driver.execute_script("window.scrollTo(0, 1000);")
        time.sleep(5)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(10) # Total wait 15s for the API to fill the text
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        product_data = []

        # 2. Find all 'Product Card' containers
        # These are usually <a> tags that wrap the entire ad
        cards = soup.find_all('a', href=True)

        for card in cards:
            # We extract all text chunks inside the card
            chunks = [c.strip() for c in card.get_text("|", strip=True).split("|") if len(c.strip()) > 1]
            
            # A valid real estate card has a Price (Rs. or रू) and several lines of text
            has_price = any("Rs." in chunk or "रू" in chunk for chunk in chunks)
            
            if has_price and len(chunks) >= 3:
                try:
                    # Based on Hamrobazaar's current UI:
                    # chunk[0] is usually the label (e.g., 'House for Sale')
                    # chunk[1] is the PRODUCT TITLE
                    # chunk[2] is the DESCRIPTION / DETAIL TEXT
                    # The chunk containing 'Rs.' is the PRICE
                    
                    title = chunks[1]
                    # Sometimes the title is chunk[0] if there's no label
                    if len(title) < 5: 
                        title = chunks[0]

                    price = next((c for c in chunks if "Rs." in c or "रू" in c), "N/A")
                    
                    # Description is typically the longest text block that isn't the title or price
                    description = "N/A"
                    for chunk in chunks:
                        if chunk != title and chunk != price and len(chunk) > 20:
                            description = chunk
                            break

                    # Only add if it's a real product (Title longer than 10 chars)
                    if len(title) > 10 and title not in [d['Title'] for d in product_data]:
                        product_data.append({
                            'Title': title,
                            'Price': price,
                            'Description': description
                        })
                except Exception:
                    continue

        if not product_data:
            return None

        # Create DataFrame and Save
        df = pd.DataFrame(product_data)
        csv_file = 'hamrobazaar_listings.csv'
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        return csv_file

    except Exception as e:
        st.error(f"Scraping Error: {e}")
        return None
    finally:
        if driver:
            driver.quit()

# --- Streamlit UI ---
st.set_page_config(page_title="Hamrobazaar Scraper", layout="wide")
st.title("🏠 Hamrobazaar Real Estate Extractor")

target_url = st.text_input("Category URL:", "https://hamrobazaar.com/category/06B8B8E6-4CDE-4D79-AE65-38B8BAA9FF17/56C5F377-50C1-424A-B6C2-24A8B3235DC7")

if st.button("Scrape Listings"):
    with st.spinner("Scrolling and extracting Titles, Prices, and Descriptions..."):
        file_path = scrape_hamrobazaar(target_url)
        
        if file_path:
            df_result = pd.read_csv(file_path)
            st.success(f"Successfully found {len(df_result)} properties!")
            st.dataframe(df_result, use_container_width=True)
            
            with open(file_path, "rb") as f:
                st.download_button("Download CSV File", f, file_name="hamrobazaar_houses.csv")
            os.remove(file_path)
        else:
            st.error("No products found. Try running the app again or check if the URL is correct.")
