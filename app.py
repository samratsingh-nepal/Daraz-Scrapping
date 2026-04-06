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
    
    chrome_options.binary_location = "/usr/bin/chromium"
    service = Service("/usr/bin/chromedriver")

    driver = None
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(url)
        
        product_data = []
        
        # --- THE FIX: MULTI-STAGE SCROLLING ---
        # We scroll multiple times to trigger the lazy-loading of all items
        for scroll_step in range(5):  # Increase range for more data
            driver.execute_script(f"window.scrollTo(0, {scroll_step * 1500});")
            time.sleep(4)  # Wait for the 'Next' batch to load
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Find all listings current in the DOM
            listings = soup.find_all('div', attrs={'data-index': True})
            
            for item in listings:
                try:
                    # Search for the Title
                    title_tag = item.select_one('a.heading-h6')
                    
                    # If there's no title_tag, this is likely an ADVERTISEMENT or empty slot.
                    # We just skip it and move to the next 'data-index'
                    if not title_el := title_tag:
                        continue
                        
                    title = title_el.get_text(strip=True)

                    # Skip if we already captured this product in a previous scroll step
                    if any(d['Title'] == title for d in product_data):
                        continue

                    # Extract Description
                    desc_tag = item.select_one('p.cursor-pointer')
                    description = desc_tag.get_text(separator="\n", strip=True) if desc_tag else "N/A"

                    # Extract Price
                    price_tag = item.select_one('span.font-semibold')
                    price = price_tag.get_text(strip=True) if price_tag else "N/A"

                    product_data.append({
                        'Title': title,
                        'Price': price,
                        'Description': description
                    })
                except Exception:
                    continue  # Keep moving even if one item fails

        if not product_data:
            return None

        df = pd.DataFrame(product_data)
        csv_file = 'hamrobazaar_extracted.csv'
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        return csv_file

    except Exception as e:
        st.error(f"Error: {e}")
        return None
    finally:
        if driver:
            driver.quit()

# --- Streamlit UI stays the same ---
# --- Streamlit UI ---
st.title("🏘️ Hamrobazaar Listing Extractor")

url_input = st.text_input("Category URL:", "https://hamrobazaar.com/category/06B8B8E6-4CDE-4D79-AE65-38B8BAA9FF17/56C5F377-50C1-424A-B6C2-24A8B3235DC7")

if st.button("Extract Titles, Prices & Details"):
    with st.spinner("Parsing HTML structure..."):
        file = scrape_hamrobazaar(url_input)
        if file:
            df = pd.read_csv(file)
            st.success(f"Successfully extracted {len(df)} listings!")
            st.dataframe(df, use_container_width=True)
            with open(file, "rb") as f:
                st.download_button("Download CSV", f, file_name="hamrobazaar_data.csv")
            os.remove(file)
        else:
            st.error("No items found. Make sure the page is fully loaded.")
