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
    
    # --- STEALTH SETTINGS ---
    # These prevent the site from detecting Selenium
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")

    # Path configuration for Streamlit Cloud
    chrome_options.binary_location = "/usr/bin/chromium"
    service = Service("/usr/bin/chromedriver")

    driver = None
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Additional stealth: Remove the 'webdriver' flag
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        driver.get(url)
        
        # 1. Wait for the page to load initial assets
        time.sleep(5)
        
        # 2. Scroll to trigger "Hydration" (the process where React fills in the data)
        driver.execute_script("window.scrollTo(0, 600);")
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(7) # Total wait ~15s
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        product_data = []

        # 3. ROBUST EXTRACTION: 
        # Hamrobazaar uses specific 'data-testid' or nested <a> tags for cards.
        # We target all <a> tags that look like they contain a product.
        cards = soup.find_all('a', href=True)

        for card in cards:
            text_content = card.get_text("|", strip=True).split("|")
            
            # A valid product card usually has 3-5 lines of text
            # e.g., ['HOUSE FOR SALE', 'Beautiful House in Lalitpur', 'Description snippet...', 'Rs. 2,50,00,000', '2 days ago']
            if len(text_content) >= 3 and any("Rs." in line or "रू" in line for line in text_content):
                try:
                    # Logic based on current Hamrobazaar structure:
                    # Usually: [0]Category, [1]Title, [2]Description, [Next]Price
                    name = text_content[1]
                    details = text_content[2]
                    
                    # Find the price line
                    price = next((l for l in text_content if "Rs." in l or "रू" in l), "N/A")
                    
                    # Basic cleaning
                    if len(name) > 5 and name not in [d['Product Name'] for d in product_data]:
                        product_data.append({
                            'Product Name': name,
                            'Description': details,
                            'Price': price
                        })
                except Exception:
                    continue

        if not product_data:
            return None

        df = pd.DataFrame(product_data)
        csv_file = 'hamrobazaar_results.csv'
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        return csv_file

    except Exception as e:
        st.error(f"Error during scraping: {e}")
        return None
    finally:
        if driver:
            driver.quit()

# --- Streamlit UI ---
st.set_page_config(page_title="Hamrobazaar Scraper", page_icon="🏠")
st.title("🏠 Hamrobazaar Real Estate Scraper")

url_input = st.text_input("Category URL:", "https://hamrobazaar.com/category/06B8B8E6-4CDE-4D79-AE65-38B8BAA9FF17/56C5F377-50C1-424A-B6C2-24A8B3235DC7")

if st.button("Start Scraping"):
    with st.spinner("Bypassing security and loading listings..."):
        file_path = scrape_hamrobazaar(url_input)
        
        if file_path:
            df = pd.read_csv(file_path)
            st.success(f"Extracted {len(df)} listings successfully!")
            st.dataframe(df, use_container_width=True)
            
            with open(file_path, "rb") as f:
                st.download_button("Download CSV", f, file_name="hamrobazaar_houses.csv")
            os.remove(file_path)
        else:
            st.error("No products found. Hamrobazaar might be blocking the request or the page is taking too long to load.")
