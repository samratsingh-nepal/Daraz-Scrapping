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
    
    # Path configuration for Streamlit Cloud
    # If running locally on Windows, you can comment out the binary_location line
    chrome_options.binary_location = "/usr/bin/chromium"
    service = Service("/usr/bin/chromedriver")

    driver = None
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(url)
        
        # Give React time to render the content
        time.sleep(12) 
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        product_data = []

        # Find potential title elements
        all_titles = soup.find_all(['h2', 'h3'])

        for title_el in all_titles:
            name = title_el.get_text(strip=True)
            
            # Filter out UI elements and noise
            if len(name) < 5 or "results" in name.lower() or "filter" in name.lower():
                continue

            # Find the common parent container for this specific product
            parent = title_el.find_parent('div')
            if not parent:
                continue

            # 1. Extract Detail Text (Description snippet)
            detail_text = "N/A"
            # Look for the immediate next sibling or a paragraph within the same block
            description_el = title_el.find_next_sibling(['p', 'div', 'span'])
            if description_el:
                detail_text = description_el.get_text(strip=True)

            # 2. Extract Price
            price = "N/A"
            # Search for currency markers within the parent block
            price_search = parent.find_all(string=lambda t: "Rs." in t or "रू" in t)
            if price_search:
                price = price_search[0].strip()

            # Logic to handle if the price is nested slightly differently
            if price == "N/A":
                all_text_in_parent = parent.get_text()
                if "Rs." in all_text_in_parent:
                    # Simple extraction if it exists anywhere in the card
                    parts = all_text_in_parent.split("Rs.")
                    if len(parts) > 1:
                        price = "Rs. " + parts[1].split()[0]

            # Only append if we actually found usable data
            if name and (price != "N/A" or detail_text != "N/A"):
                product_data.append({
                    'Product Name': name,
                    'Description': detail_text,
                    'Price': price
                })

        if not product_data:
            return None

        # Clean up data
        df = pd.DataFrame(product_data).drop_duplicates(subset=['Product Name'])
        csv_file = 'hamrobazaar_data.csv'
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        return csv_file

    except Exception as e:
        st.error(f"Scraping Error: {e}")
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
