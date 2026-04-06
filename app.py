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
        time.sleep(5) # Initial load

        product_data = []
        last_height = 0
        # Increase this range to scrape more pages (e.g., 20 or 30 for the whole category)
        max_scroll_attempts = 15 

        for attempt in range(max_scroll_attempts):
            # 1. Scroll down by a fixed amount
            driver.execute_script(f"window.scrollTo(0, {attempt * 1200});")
            time.sleep(3) # Wait for React to render the new batch

            # 2. Parse the current snapshot of the page
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            listings = soup.find_all('div', attrs={'data-index': True})

            new_items_found = 0
            for item in listings:
                try:
                    # Target Title
                    title_tag = item.select_one('a.heading-h6')
                    if not title_tag:
                        continue # This skips advertisements automatically
                    
                    title = title_tag.get_text(strip=True)

                    # Skip if we already scraped this specific title
                    if any(d['Title'] == title for d in product_data):
                        continue

                    # Target Description
                    desc_tag = item.select_one('p.cursor-pointer')
                    description = desc_tag.get_text(separator="\n", strip=True) if desc_tag else "N/A"

                    # Target Price
                    price_tag = item.select_one('span.font-semibold')
                    price = price_tag.get_text(strip=True) if price_tag else "N/A"

                    product_data.append({
                        'Title': title,
                        'Price': price,
                        'Description': description
                    })
                    new_items_found += 1
                except Exception:
                    continue
            
            # Optional: if no new items are found for 2 scrolls, we might be at the end
            # if new_items_found == 0 and attempt > 5: break

        if not product_data:
            return None

        df = pd.DataFrame(product_data)
        csv_file = 'hamrobazaar_full_data.csv'
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        return csv_file

    except Exception as e:
        st.error(f"Error: {e}")
        return None
    finally:
        if driver:
            driver.quit()

# --- Streamlit UI stays the same ---
st.title("🏘️ Hamrobazaar Full Category Extractor")

url_input = st.text_input("Category URL:", "https://hamrobazaar.com/category/06B8B8E6-4CDE-4D79-AE65-38B8BAA9FF17/56C5F377-50C1-424A-B6C2-24A8B3235DC7")

if st.button("Extract All Products"):
    with st.spinner("Scrolling through listings and skipping ads..."):
        file = scrape_hamrobazaar(url_input)
        if file:
            df = pd.read_csv(file)
            st.success(f"Successfully extracted {len(df)} listings!")
            st.dataframe(df, use_container_width=True)
            with open(file, "rb") as f:
                st.download_button("Download CSV", f, file_name="hamrobazaar_all_data.csv")
            os.remove(file)
        else:
            st.error("No items found.")
