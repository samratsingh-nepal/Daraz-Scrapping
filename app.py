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
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    
    # Path for Streamlit Cloud
    chrome_options.binary_location = "/usr/bin/chromium"
    service = Service("/usr/bin/chromedriver")

    driver = None
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(url)
        
        # Wait for React to render the cards
        time.sleep(10) 
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # In the new Hamrobazaar layout, each ad is usually wrapped in a specific 
        # container. We target the sections that contain both a title and a price.
        product_data = []

        # Find all card-like structures
        # Strategy: Find the titles first, then navigate to their parent containers
        titles = soup.find_all(['h2', 'h3', 'span'], style=lambda s: s and 'font-weight' in s.lower() or 'bold' in s.lower())
        
        for title_el in titles:
            name = title_el.get_text(strip=True)
            
            # Filter out short strings that aren't product names
            if len(name) < 10:
                continue
                
            # Find the parent container that holds the whole "row" or "card"
            # We move up the tree to find the box containing all info
            parent = title_el.parent
            for _ in range(3): # Look up up to 3 levels
                if parent:
                    parent_text = parent.get_text()
                    if "Rs." in parent_text or "रू" in parent_text:
                        break
                    parent = parent.parent

            if parent:
                # 1. EXTRACT PRICE
                # Look for currency markers
                price_el = parent.find(text=lambda t: "Rs." in t or "रू" in t)
                price = price_el.strip() if price_el else "N/A"

                # 2. EXTRACT DETAIL TEXT
                # In Hamrobazaar, the description is usually the p or span 
                # immediately following the title element
                details = "N/A"
                # Search for any long text block within the same parent that isn't the title
                all_texts = parent.find_all(['p', 'span', 'div'], recursive=True)
                for t in all_texts:
                    txt = t.get_text(strip=True)
                    # The description is usually longer than the title but shorter than the whole card
                    if len(txt) > 20 and txt != name and "Rs." not in txt and "रू" not in txt:
                        details = txt
                        break

                # Avoid duplicates and "Noise" like "For Sale - House"
                if name not in [d['product_name'] for d in product_data] and "results" not in name.lower():
                    product_data.append({
                        'product_name': name,
                        'product_details': details,
                        'product_price': price
                    })

        if not product_data:
            st.warning("No products found. Please check if the URL is correct or try a longer wait time.")
            return None

        df = pd.DataFrame(product_data)
        csv_file = 'hamrobazaar_results.csv'
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        return csv_file

    except Exception as e:
        st.error(f"Scraping Error: {e}")
        return None
    finally:
        if driver:
            driver.quit()

# --- Streamlit UI ---
st.title("Hamrobazaar Search Scraper")

# Default to your House for Sale link
default_url = "https://hamrobazaar.com/category/06B8B8E6-4CDE-4D79-AE65-38B8BAA9FF17/56C5F377-50C1-424A-B6C2-24A8B3235DC7"
url_input = st.text_input("Enter Hamrobazaar URL:", value=default_url)

if st.button("Start Extraction"):
    with st.spinner('Reading product cards...'):
        csv_path = scrape_hamrobazaar(url_input)
        if csv_path:
            df_display = pd.read_csv(csv_path)
            st.success(f"Successfully scraped {len(df_display)} products!")
            st.dataframe(df_display) # Show a preview in the app
            
            with open(csv_path, "rb") as f:
                st.download_button("Download Full CSV", f, file_name=csv_path)
