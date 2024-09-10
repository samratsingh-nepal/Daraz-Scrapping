import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import csv
import time
import os

# Configure Selenium to run headless Chrome
def configure_driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")  # Ensure headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Set up ChromeDriver
    driver = webdriver.Chrome(service=Service("/usr/bin/chromedriver"), options=chrome_options)
    return driver

# Define a function to scrape the website
def scrape_website(url):
    driver = configure_driver()  # Use the headless driver
    driver.get(url)

    # Wait for products to load
    WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'RfADt')))

    # Find product elements
    products = driver.find_elements(By.CLASS_NAME, 'RfADt')
    prices = driver.find_elements(By.CLASS_NAME, 'ooOxS')
    sold = driver.find_elements(By.CLASS_NAME, '_1cEkb')
    reviews = driver.find_elements(By.CLASS_NAME, 'qzqFw')

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
            full_star_elements = star_element.find_elements(By.CSS_SELECTOR, '._9-ogB.Dy1nx')  # Find full star elements inside star container
            full_star_count = len(full_star_elements)

            # Append the product details to the list
            product_data.append((product_name, product_price, product_sold, product_review, full_star_count))
        except Exception as e:
            print(f"Error processing product: {e}")
    
    driver.quit()

    # Write the data to a CSV file
    file_path = 'daraz_airpod.csv'
    with open(file_path, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # Write the header
        writer.writerow(['Product Name', 'Price', "Sold", "Reviews", "Stars"])
        # Write the product data
        writer.writerows(product_data)

    return file_path

# Streamlit UI
st.title("Product Scraper App")
url_input = st.text_input("Enter the product URL:")

if st.button('Scrape'):
    if url_input:
        result = scrape_website(url_input)
        st.write(f"Data successfully written to {result}")
        with open(result, "rb") as file:
            st.download_button(label="Download CSV", data=file, file_name='daraz_airpod.csv')
    else:
        st.write("Please enter a valid URL.")
