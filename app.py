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
        
        # 1. SCROLL DOWN: Hamrobazaar often lazy-loads data. 
        # This scrolls the page to trigger the content to appear.
        driver.execute_script("window.scrollTo(0, 1000);")
        time.sleep(5)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(10) # Total 15s wait
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        product_data = []

        # 2. TARGET THE GRID: Most Hamrobazaar items are inside <a> tags or <div> cards
        # We search for elements that look like a product card.
        potential_cards = soup.find_all(['div', 'a'], recursive=True)

        for card in potential_cards:
            card_text = card.get_text()
            
            # Check if this div contains a price (Rs. or रू)
            if ("Rs." in card_text or "रू" in card_text) and len(card_text) < 500:
                try:
                    # The Title is usually the first heading or bold text
                    title_el = card.find(['h2', 'h3', 'h4', 'strong'])
                    if not title_el:
                        continue
                        
                    name = title_el.get_text(strip=True)
                    if len(name) < 5: continue

                    # The Price is the part containing 'Rs.'
                    price = "N/A"
                    price_tags = card.find_all(string=lambda t: "Rs." in t or "रू" in t)
                    if price_tags:
                        price = price_tags[0].strip()

                    # The Details/Description is usually the text between the title and price
                    # We clean the text by removing the name and price from the string
                    full_text = card.get_text(" | ", strip=True)
                    details = full_text.replace(name, "").replace(price, "").strip(" | ")
                    
                    # Clean up the detail text if it's too long or contains garbage
                    if len(details) > 200:
                        details = details[:197] + "..."

                    if name not in [d['Product Name'] for d in product_data]:
                        product_data.append({
                            'Product Name': name,
                            'Description': details if details else "N/A",
                            'Price': price
                        })
                except:
                    continue

        if not product_data:
            # DEBUG: Let's see what the robot actually saw
            st.error(f"Debug Info: Found {len(potential_cards)} potential containers, but none matched.")
            return None

        df = pd.DataFrame(product_data)
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
