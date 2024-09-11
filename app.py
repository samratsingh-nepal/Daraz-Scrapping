import streamlit as st
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
import pandas as pd
import os
from selenium.webdriver import Remote

def configure_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver= webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    return driver

# Web scraping function
def scrape_website(url):
    driver = configure_driver()
    driver.get(url)

    # Wait for products to load
    WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'RfADt')))

    # Find product elements
    products = driver.find_elements(By.CLASS_NAME, 'RfADt')
    prices = driver.find_elements(By.CLASS_NAME, 'ooOxS')
    sold = driver.find_elements(By.CLASS_NAME, '_1cEkb')
    reviews = driver.find_elements(By.CLASS_NAME, 'qzqFw')

    # Wait for star ratings to load
    WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.mdmmT._32vUv'))
    )
    stars = driver.find_elements(By.CSS_SELECTOR, '.mdmmT._32vUv')

    product_data = []

    # Loop through each product and gather details
    for product, price, sold_item, review, star_element in zip(products, prices, sold, reviews, stars):
        try:
            # Extract product details
            product_name = product.text if product else "N/A"
            product_price = price.text if price else "N/A"
            product_sold = sold_item.text if sold_item else "N/A"
            product_review = review.text if review else "N/A"
            
            # Find full star elements inside star container
            full_star_elements = star_element.find_elements(By.CSS_SELECTOR, '._9-ogB.Dy1nx')
            full_star_count = len(full_star_elements)

            # Append the product details to the list
            product_data.append((product_name, product_price, product_sold, product_review, full_star_count))
        except Exception as e:
            st.write(f"Error processing product: {e}")

    driver.quit()
    
    # Save to CSV
    df = pd.DataFrame(product_data, columns=['Product Name', 'Price', 'Sold', 'Reviews', 'Stars'])
    csv_file = 'daraz_airpod.csv'
    df.to_csv(csv_file, index=False, encoding='utf-8')

    return csv_file

# Streamlit app
st.title("Web Scraping with Selenium in Streamlit")
url_input = st.text_input("Enter the URL to scrape:")
if url_input:
    with st.spinner('Scraping the website...'):
        csv_file = scrape_website(url_input)
    
    st.success("Scraping completed!")
    
    # Provide download button for the CSV file
    with open(csv_file, "rb") as file:
        st.download_button(
            label="Download CSV",
            data=file,
            file_name=csv_file,
            mime="text/csv"
        )

    # Clean up the generated CSV file after download option is provided
    if os.path.exists(csv_file):
        os.remove(csv_file)
