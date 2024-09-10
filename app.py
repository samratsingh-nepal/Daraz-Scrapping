import selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
import time
import streamlit as st
from io import StringIO

# Define a function to perform web scraping
def scrape_daraz_data(url):
    # Setup Selenium driver (you will need to set your chromedriver path)
    service = Service(executable_path='path_to_chromedriver')
    driver2 = webdriver.Chrome(service=service)

    # Open the URL provided by the user
    driver2.get(url)

    # Wait for the product elements to load
    WebDriverWait(driver2, 20).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'RfADt')))

    # Find product elements
    products = driver2.find_elements(By.CLASS_NAME, 'RfADt')
    prices = driver2.find_elements(By.CLASS_NAME, 'ooOxS')
    sold = driver2.find_elements(By.CLASS_NAME, '_1cEkb')
    reviews = driver2.find_elements(By.CLASS_NAME, 'qzqFw')

    WebDriverWait(driver2, 20).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.mdmmT._32vUv'))
    )
    stars = driver2.find_elements(By.CSS_SELECTOR, '.mdmmT._32vUv')

    # Store product data
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
            st.write(f"Error processing product: {e}")

    # Close the browser
    driver2.quit()

    return product_data

# Streamlit app
def main():
    st.title('Daraz Web Scraper')

    # Input field for URL
    url = st.text_input('Enter the Daraz URL:', '')

    # Button to trigger scraping
    if st.button('Scrape Data'):
        if url:
            # Scrape the data
            product_data = scrape_daraz_data(url)

            if product_data:
                # Display data in Streamlit
                st.write('Scraped Data:')
                st.table(product_data)

                # Create CSV
                csv_data = StringIO()
                writer = csv.writer(csv_data)
                writer.writerow(['Product Name', 'Price', "Sold", "Reviews", "Stars"])
                writer.writerows(product_data)

                # Download link
                st.download_button(label="Download CSV", data=csv_data.getvalue(), file_name="daraz_airpod.csv", mime="text/csv")
            else:
                st.write("No data found or failed to scrape.")
        else:
            st.write("Please enter a valid URL.")

if __name__ == '__main__':
    main()
