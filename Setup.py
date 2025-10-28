import requests
import time
import json
import logging
from threading import Timer
from bs4 import BeautifulSoup
import os
from emailalert import alert_system

# Configuration
CONFIG = {
    'check_interval': 300,  # 5 minutes
    'products_file': 'products.json',
    'log_file': 'price_tracker.log'
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(CONFIG['log_file']),
        logging.StreamHandler()
    ]
)

class PriceTracker:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        self.load_products()

    def load_products(self):
        try:
            with open(CONFIG['products_file'], 'r') as f:
                self.products = json.load(f)
        except FileNotFoundError:
            self.products = []
            self.save_products()

    def save_products(self):
        with open(CONFIG['products_file'], 'w') as f:
            json.dump(self.products, f, indent=2)

    def add_product(self, url, target_price, name=None):
        product = {
            'url': url,
            'target_price': target_price,
            'name': name,
            'last_checked': None,
            'last_price': None
        }
        self.products.append(product)
        self.save_products()

    def get_price(self, url):
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Multiple price selectors for better compatibility
            price_selectors = [
                '#priceblock_ourprice',
                '#priceblock_dealprice',
                '.a-price-whole',
                '.a-price .a-offscreen'
            ]
            
            price = None
            for selector in price_selectors:
                price_element = soup.select_one(selector)
                if price_element:
                    price_text = price_element.get_text().strip()
                    # Extract numeric price
                    price_str = ''.join(c for c in price_text if c.isdigit() or c == '.')
                    if price_str:
                        price = float(price_str)
                        break
            
            # Get product title
            title_element = soup.find('span', {'id': 'productTitle'})
            title = title_element.get_text().strip() if title_element else "Unknown Product"
            
            return price, title
            
        except Exception as e:
            logging.error(f"Error fetching price for {url}: {str(e)}")
            return None, None

    def check_prices(self):
        for product in self.products:
            try:
                current_price, product_name = self.get_price(product['url'])
                
                if current_price is None:
                    continue
                
                # Update product info
                if not product.get('name'):
                    product['name'] = product_name
                
                product['last_checked'] = time.time()
                previous_price = product.get('last_price')
                product['last_price'] = current_price
                
                logging.info(f"{product['name']}: ₹{current_price}")
                
                # Check if price dropped below target
                if current_price <= product['target_price']:
                    if previous_price is None or current_price < previous_price:
                        alert_system(product['name'], product['url'], current_price)
                        logging.info(f"Alert sent for {product['name']} at ₹{current_price}")
                
            except Exception as e:
                logging.error(f"Error processing {product.get('name', 'Unknown')}: {str(e)}")
        
        self.save_products()
        # Schedule next check
        Timer(CONFIG['check_interval'], self.check_prices).start()

    def run(self):
        logging.info("Starting price tracker...")
        self.check_prices()

if __name__ == "__main__":
    tracker = PriceTracker()
    
    # Add products (you can make this interactive)
    if not tracker.products:
        tracker.add_product(
            "https://www.amazon.in/dp/B082VS5H3Y",
            1000,
            "Boat Rockerz 255 Pro"
        )
    
    tracker.run()  
