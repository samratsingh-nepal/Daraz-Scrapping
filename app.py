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
    
    # Cloud Config
    chrome_options.binary_location = "/usr/bin/chromium"
    service = Service("/usr/bin/chromedriver")

    driver = None
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(url)
        
        # 1. SCROLL: Essential to trigger React to 'paint' the text
        driver.execute_script("window.scrollTo(0, 800);")
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(12) 
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        product_data = []

        # 2. FIND ALL DIVS: We look for containers that have 'Rs.' or 'रू'
        # This is the most reliable footprint of a product card.
        all_divs = soup.find_all('div')

        for div in all_divs:
            # We only want 'leaf' divs that are product cards (not the whole page)
            # A product card usually has 'Rs.' and is between 100-1000 characters
            text = div.get_text(" ", strip=True)
            if ("Rs." in text or "रू" in text) and 50 < len(text) < 600:
                
                # Check if this div has already been processed (avoid nested duplicates)
                if any(text[:30] in d['Product Name'] for d in product_data):
                    continue

                try:
                    # Logic: The first line is usually the title
                    lines = [l.strip() for l in text.split("  ") if len(l.strip()) > 2]
                    
                    if len(lines) >= 2:
                        name = lines[0]
                        # Price is the one with Rs.
                        price = next((l for l in lines if "Rs." in l or "रू" in l), "N/A")
                        # Description is usually the line that isn't the name or price
                        desc = next((l for l in lines if l != name and l != price and len(l) > 15), "N/A")

                        product_data.append({
                            'Product Name': name,
                            'Description': desc,
                            'Price': price
                        })
                except:
                    continue

        if not product_data:
            # FALLBACK: If the above fails, search for common React classes
            st.info("Attempting fallback search...")
            cards = soup.select('div[class*="product"], div[class*="card"]')
            for card in cards:
                # Basic text extraction
                info = card.get_text("|", strip=True).split("|")
                if len(info) >= 2:
                    product_data.append({'Product Name': info[0], 'Description': info[1] if len(info)>2 else "N/A", 'Price': info[-1]})

        if not product_data:
            return None

        df = pd.DataFrame(product_data).drop_duplicates(subset=['Product Name'])
        csv_file = 'hamrobazaar_data.csv'
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        return csv_file

    except Exception as e:
        st.error(f"Error: {e}")
        return None
    finally:
        if driver:
            driver.quit()
# --- Streamlit Interface ---
st.set_page_config(page_title="Hamrobazaar Scraper", layout="wide")

st.title("🏘️ Hamrobazaar Product Scraper")
st.markdown("""
Extract product names, descriptions, and prices from Hamrobazaar categories. 
Paste the URL of the category page you want to scrape below.
""")

# Default URL based on your screenshot
default_url = "https://hamrobazaar.com/category/06B8B8E6-4CDE-4D79-AE65-38B8BAA9FF17/56C5F377-50C1-424A-B6C2-24A8B3235DC7"
url_input = st.text_input("Hamrobazaar Category URL:", value=default_url)

if st.button("Start Scraping"):
    if url_input:
        with st.spinner('Connecting to Hamrobazaar and rendering page...'):
            result_file = scrape_hamrobazaar(url_input)
            
            if result_file:
                df_final = pd.read_csv(result_file)
                st.success(f"Found {len(df_final)} unique products!")
                
                # Display preview
                st.dataframe(df_final, use_container_width=True)
                
                # Download button
                with open(result_file, "rb") as f:
                    st.download_button(
                        label="Download Data as CSV",
                        data=f,
                        file_name=result_file,
                        mime="text/csv"
                    )
                # Cleanup
                os.remove(result_file)
            else:
                st.warning("No products were found. Try increasing the sleep timer or checking the URL.")
    else:
        st.error("Please enter a valid URL.")
