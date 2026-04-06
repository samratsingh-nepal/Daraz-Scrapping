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
    # These lines hide the fact that this is an automated bot
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    
    chrome_options.binary_location = "/usr/bin/chromium"
    service = Service("/usr/bin/chromedriver")

    driver = None
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # This Javascript command further hides Selenium
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        driver.get(url)
        
        # Scroll once to trigger the React "Hydration" (filling in the text)
        driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(5)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(10) 
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        product_data = []

        # Find all card containers. Hamrobazaar usually uses <a> tags for the whole card
        # or specific divs with product-related classes.
        cards = soup.find_all(['a', 'div'], recursive=True)

        for card in cards:
            text_lines = [t.strip() for t in card.get_text("|", strip=True).split("|") if len(t.strip()) > 1]
            
            # A valid card usually contains "Rs." and has at least 3 pieces of info
            # (Title, Description snippet, Price)
            has_price = any("Rs." in line or "रू" in line for line in text_lines)
            
            if has_price and len(text_lines) >= 3:
                # Based on the screenshot layout:
                # line 0 is often the Category or Tag
                # line 1 is usually the Title
                # line 2-3 is the Description
                # The line with "Rs." is the Price
                
                name = text_lines[0]
                price = next((l for l in text_lines if "Rs." in l or "रू" in l), "N/A")
                
                # Combine remaining lines for description
                description = " ".join([l for l in text_lines if l != name and l != price])
                
                # Filter out very short results or duplicates
                if len(name) > 10 and name not in [d['Product Name'] for d in product_data]:
                    product_data.append({
                        'Product Name': name,
                        'Description': description[:250], # Keep it clean
                        'Price': price
                    })

        if not product_data:
            # Final Fallback: Just grab every bold text and its nearest price
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
