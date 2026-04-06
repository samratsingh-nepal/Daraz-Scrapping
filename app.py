def scrape_hamrobazaar(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    
    chrome_options.binary_location = "/usr/bin/chromium"
    service = Service("/usr/bin/chromedriver")

    driver = None
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(url)
        
        # Give the page plenty of time to load the React grid
        time.sleep(12) 
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        product_data = []

        # Hamrobazaar usually wraps the title in an <h2> or a <span> with a specific font size
        # We look for the titles first
        all_titles = soup.find_all(['h2', 'h3'])

        for title_el in all_titles:
            name = title_el.get_text(strip=True)
            
            # Skip noise like "Filters" or "Quality"
            if len(name) < 5 or "results" in name.lower():
                continue

            # Navigate to find the details and price
            # In their current layout, the description and price are usually 
            # in the same parent container as the title.
            parent = title_el.find_parent('div')
            if not parent:
                continue

            # 1. Extract Detail Text 
            # It's usually the next paragraph or div with a smaller font
            detail_text = "N/A"
            description_el = title_el.find_next_sibling(['p', 'div', 'span'])
            if description_el:
                detail_text = description_el.get_text(strip=True)

            # 2. Extract Price
            # We look specifically for the currency symbol inside this product card
            price = "N/A"
            price_search = parent.find_all(text=lambda t: "Rs." in t or "रू" in t)
            if price_search:
                price = price_search[0].strip()

            # Only add if we found a valid price or description
            if price != "N/A" or detail_text != "N/A":
                product_data.append({
                    'product_name': name,
                    'product_details': detail_text,
                    'product_price': price
                })

        # Remove duplicates based on name
        df = pd.DataFrame(product_data).drop_duplicates(subset=['product_name'])

        if df.empty:
            st.warning("No products found. The selectors might need adjusting or the page didn't load.")
            return None

        csv_file = 'hamrobazaar_results.csv'
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        return csv_file

    except Exception as e:
        st.error(f"Scraping Error: {e}")
        return None
    finally:
        if driver:
            driver.quit()
