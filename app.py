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
    chrome_options.add_argument("--disable-gpu")
    
    # This line is crucial for Streamlit Cloud to find the browser
    chrome_options.binary_location = "/usr/bin/chromium-browser"

    driver = None
    try:
        # On Streamlit Cloud, we don't always need ChromeDriverManager 
        # because we installed chromium-chromedriver via packages.txt
        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        driver.get(url)
        
        # Wait for JavaScript to render (important for Daraz!)
        time.sleep(5) 
        
        # 4. Pass the rendered HTML to BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Updated selectors based on Daraz's current structure
        # Note: These can change, so we look for common patterns
        product_cards = soup.find_all('div', {'class': 'gridItem--YdSTg'})
        
        product_data = []

        for card in product_cards:
            try:
                name = card.find('div', {'class': 'title--w9198'}).text.strip()
                # Price is often inside a span
                price_text = card.find('span', {'class': 'currency--GVKO0'}).find_next_sibling(text=True)
                price = int(price_text.replace(',', '').strip())
                
                # Rating and Sold counts are sometimes deeply nested or missing
                rating_count = card.find('span', {'class': 'rating__review--yg3n5'})
                reviews = rating_count.text.strip('()') if rating_count else "0"

                product_data.append({
                    'product_name': name,
                    'product_price': price,
                    'product_review_count': reviews
                })
            except Exception:
                continue # Skip items that don't match the format

        if not product_data:
            st.warning("No products found. Daraz might be blocking the automated request or the layout has changed.")
            return None

        # 5. Save to CSV
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
