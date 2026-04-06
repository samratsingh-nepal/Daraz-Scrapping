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
    # Stealth mode to bypass bot detection
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
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        driver.get(url)
        
        # Give React time to 'hydrate' and fill the HTML with text
        # We scroll down to trigger the lazy-loading of products
        for i in range(2):
            driver.execute_script(f"window.scrollTo(0, {(i+1)*800});")
            time.sleep(4)
            
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        product_data = []

        # Find the main product containers based on the class 'group bg-white' from your HTML
        containers = soup.find_all('div', class_=lambda x: x and 'group bg-white' in x)

        for container in containers:
            try:
                # 1. Title: Target the <a> tag with heading-h6
                title_tag = container.select_one('a.heading-h6')
                title = title_tag.get_text(strip=True) if title_tag else "N/A"

                # 2. Description: Target the <p> tag with specific classes
                desc_tag = container.select_one('p.cursor-pointer.break-words')
                description = desc_tag.get_text(strip=True) if desc_tag else "N/A"

                # 3. Price: Target the span containing the rupee icon or specific font weight
                price_tag = container.select_one('span.text-sm.font-semibold')
                price = price_tag.get_text(strip=True) if price_tag else "N/A"

                # Safety check to avoid adding empty items
                if title != "N/A":
                    product_data.append({
                        'Title': title,
                        'Price': price,
                        'Description': description
                    })
            except Exception:
                continue

        if not product_data:
            return None

        # Create DataFrame and remove any accidental duplicates
        df = pd.DataFrame(product_data).drop_duplicates(subset=['Title'])
        csv_file = 'hamrobazaar_houses.csv'
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        return csv_file

    except Exception as e:
        st.error(f"Error during extraction: {e}")
        return None
    finally:
        if driver:
            driver.quit()

# --- Streamlit UI ---
st.set_page_config(page_title="Hamrobazaar Extractor", layout="wide")
st.title("🏘️ Hamrobazaar House Data Extractor")

url_input = st.text_input("Paste the Hamrobazaar Category URL:", "https://hamrobazaar.com/category/06B8B8E6-4CDE-4D79-AE65-38B8BAA9FF17/56C5F377-50C1-424A-B6C2-24A8B3235DC7")

if st.button("Start Scraping"):
    with st.spinner("Analyzing listing structure and downloading data..."):
        file_path = scrape_hamrobazaar(url_input)
        
        if file_path:
            df = pd.read_csv(file_path)
            st.success(f"Found {len(df)} properties!")
            st.dataframe(df, use_container_width=True)
            
            with open(file_path, "rb") as f:
                st.download_button("Download CSV", f, file_name="hamrobazaar_data.csv")
            os.remove(file_path)
        else:
            st.error("Could not find products. The page might be protected or the layout changed slightly.")
