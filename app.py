import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

def scrape_website(url):
    try:
        # Send an HTTP request to the provided URL
        response = requests.get(url)
        response.raise_for_status()  # Check for HTTP errors

        # Parse the content using BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract product information (You will need to modify these selectors based on the website's HTML structure)
        products = soup.find_all(class_='RfADt')
        prices = soup.find_all(class_='ooOxS')
        sold_items = soup.find_all(class_='_1cEkb')
        reviews = soup.find_all(class_='qzqFw')
        stars = soup.find_all(class_='mdmmT _32vUv')

        product_data = []

        # Loop through each product and gather details
        for product, price, sold_item, review, star in zip(products, prices, sold_items, reviews, stars):
            product_name = product.get_text().strip() if product else "N/A"

            # Convert price to integer (removing any non-numeric characters like commas or currency symbols)
            try:
                product_price = int(price.get_text().replace(",", "").replace("$", "").strip()) if price else 0
            except ValueError:
                product_price = 0

            # Convert sold count to integer
            try:
                product_sold = int(sold_item.get_text().replace(",", "").strip()) if sold_item else 0
            except ValueError:
                product_sold = 0

            # Count the number of reviews (assuming it's a numeric count)
            try:
                product_review_count = int(review.get_text().strip()) if review else 0
            except ValueError:
                product_review_count = 0

            # Count the number of full stars
            star_count = len(star.find_all(class_='_9-ogB Dy1nx')) if star else 0

            # Append the product details
            product_data.append((product_name, product_price, product_sold, product_review_count, star_count))

        # Save scraped data to a CSV file
        df = pd.DataFrame(product_data, columns=['product_name', 'product_price', 'product_sold', 'product_review_count', 'star_count'])
        csv_file = 'daraz_airpod.csv'
        df.to_csv(csv_file, index=False, encoding='utf-8')

        return csv_file
    except Exception as e:
        st.error(f"An error occurred while scraping: {e}")

# Streamlit app
st.title("Web Scraping with BeautifulSoup in Streamlit")

# Input URL from user
url_input = st.text_input("Enter the URL to scrape:")

# Scraping action upon button click
if url_input and st.button("Start Scraping"):
    with st.spinner('Scraping the website...'):
        csv_file = scrape_website(url_input)  # Pass the user input URL to scrape

# Display success message and download button if scraping was successful
    if csv_file:
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
