import streamlit as st
import pandas as pd
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

def scrape_website(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # CRITICAL: Adding a real User-Agent helps bypass the "No products found" block
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    
    chrome_options.binary_location = "/usr/bin/chromium"
    service = Service("/usr/bin/chromedriver")

    driver = None
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(url)
        
        # Increased wait time for slow cloud rendering
        time.sleep(10) 
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # 1. NEW SELECTOR: Look for any div that contains the product data-qa-locator
        # This is much safer than using class names like 'gridItem--YdSTg'
        product_cards = soup.select('div[data-qa-locator="product-item"]')
        
        product_data = []

        for card in product_cards:
            try:
                # 2. NEW LOGIC: Use 'select_one' with partial class matches
                # We look for the "title" and "price" based on common prefixes
                name_el = card.select_one('div[class*="title"]')
                price_el = card.select_one('span[class*="currency"]')
                review_el = card.select_one('span[class*="rating__review"]')

                if name_el and price_el:
                    name = name_el.text.strip()
                    # The price value is usually the next text node after the currency symbol
                    price_text = price_el.find_next_sibling(text=True)
                    price = price_text.replace(',', '').strip() if price_text else "0"
                    reviews = review_el.text.strip('() ') if review_el else "0"

                    product_data.append({
                        'product_name': name,
                        'product_price': price,
                        'product_review_count': reviews
                    })
            except Exception as e:
                continue 

        if not product_data:
            # DEBUG: If it fails, we show what the page title was to see if we were blocked
            st.warning(f"No products found. Page title seen by robot: {driver.title}")
            return None

        df = pd.DataFrame(product_data)
        csv_file = 'daraz_products.csv'
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        return csv_file

    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None
    finally:
        if driver:
            driver.quit()
# --- Streamlit UI ---
st.title("Daraz Scraper (Selenium Version)")
st.info("Note: This uses Selenium to handle Daraz's dynamic JavaScript content.")

url_input = st.text_input("Enter Daraz Search URL:", placeholder="https://www.daraz.com.np/catalog/?q=earpods")

if st.button("Start Scraping"):
    if url_input:
        with st.spinner('Opening browser and loading data... this takes a few seconds.'):
            csv_file = scrape_website(url_input)
            
            if csv_file:
                st.success("Scraping completed!")
                with open(csv_file, "rb") as file:
                    st.download_button(
                        label="Download CSV",
                        data=file,
                        file_name=csv_file,
                        mime="text/csv"
                    )
                os.remove(csv_file)
    else:
        st.warning("Please enter a URL first.")
