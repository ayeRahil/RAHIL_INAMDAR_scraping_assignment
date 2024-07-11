from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
import json
from time import sleep

CHROME_DRIVER_PATH = ChromeService(ChromeDriverManager().install())

class BaseScraper:
    def __init__(self, url):
        self.url = url
        self.page_source = None
        self.soup = None
        self.driver = None

    def setup_selenium(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument('log-level=3')
        options.add_argument("--disable-gpu")
        options.add_argument('--ignore-certificate-errors')
        options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"
        )
        self.driver = webdriver.Chrome(service=CHROME_DRIVER_PATH, options=options)

    def fetch_with_selenium(self):
        self.setup_selenium()
        self.driver.get(self.url)
        sleep(2)
        self.page_source = self.driver.page_source

    def fetch_with_requests(self):
        response = requests.get(self.url)
        if response.status_code == 200:
            self.page_source = response.text
        else:
            raise Exception(f"Failed to fetch page with status code: {response.status_code}")

    def parse_html(self):
        if not self.page_source:
            raise Exception("No page source available for parsing.")
        self.soup = BeautifulSoup(self.page_source, 'html.parser')

    def scrape_data(self):
        # To be implemented by subclasses
        raise NotImplementedError("Scrape data method must be implemented by subclasses.")

    def run(self, use_selenium=False):
        if use_selenium:
            self.fetch_with_selenium()
        else:
            self.fetch_with_requests()
        self.parse_html()
        self.scrape_data()

    def quit_selenium(self):
        if self.driver:
            self.driver.quit()

class Site1Scraper(BaseScraper):
    def scrape_data(self):
        # Implement Site 1 specific scraping logic
        print("Scraping Site 1")
        home_links = self.soup.select('nav > ul[class*="site-nav"] > li > a')
        pdp_links = []
        json_data = []
        for link in home_links:
            nav_link = urljoin(self.url, link.get('href'))
            for page_no in range(1, 4):
                self.url = nav_link+f"?page={page_no}"
                self.fetch_with_requests()
                self.parse_html()
                listing_page = self.soup.select('a[class*="product-card__link"]')
                for page in listing_page:
                    pdp_links.append(urljoin(self.url, page.get('href')))
        print(len(pdp_links))
        print(len(set(pdp_links)))
        
        count = 0
        for pdp in pdp_links:
            self.url = pdp
            print(self.url)
            self.fetch_with_requests()
            self.parse_html()
            data_dict = {}
            data_dict["product_id"] = self.url.split('/')[-1]
            data_dict["title"] = self.soup.select_one('h1').text
            all_img = self.soup.select('[class*="thumbnails-wrapper"] a')
            images = []
            img = ""
            for single_img in all_img:
                if not img:
                    img = urljoin(self.url,single_img.get('href'))
                images.append(urljoin(self.url,single_img.get('href')))
            data_dict["image"] = img
            description_tag = self.soup.select_one('.product-single__description.rte')
            data_dict["description"] = description_tag.get_text(strip=True) if description_tag else None
            data_dict["sale_prices"] = [self.soup.select_one('[id="ProductPrice-product-template"]').text.replace("\n","").replace(" ","")]
            data_dict["prices"] = [self.soup.select_one('[id="ProductPrice-product-template"]').text.replace("\n","").replace(" ","")]
            
            data_dict["images"] = images
            data_dict["brand"] = "Foreign Fortune Clothing"
            data_dict["url"] = self.url
            models = self.soup.select('[id="ProductSelect-product-template"] option')
            variant_links = []
            for model in models:
                variant_links.append(f"{self.url}?variant={model.get('value')}")
            colors = self.soup.select('[for*="SingleOptionSelector-"]')
            
            for col in colors:
                if 'Color' in col.text:
                    all_colors = self.soup.select(f'select[id="{col.get("for")}"] option')
            color_list = []
            for c in all_colors:
                color_list.append(c.text.replace("\n","").replace(" ",""))
            data_dict["models"] = [{"color": color_list if color_list else None, "variants": []}]
            for variant in variant_links:
                self.url = variant
                self.fetch_with_requests()
                self.parse_html()
                
                variant_dict = {}
                
                variant_dict["id"] = variant.split('=')[-1]
                img = self.soup.select_one('[class*="thumbnails-wrapper"] a')
                variant_dict["image"] = urljoin(self.url,single_img.get('href'))
                size = ""
                
                vars = self.soup.select('[for*="SingleOptionSelector-"]')
            
                for var in vars:
                    if 'Size' in var.text:
                        size = self.soup.select_one(f'select[id="{var.get("for")}"] option[selected="selected"]').text
            
                variant_dict["size"] = size.replace("\n","").replace(" ","") if size else None
                variant_dict["prices"] = self.soup.select_one('[id="ProductPrice-product-template"]').text.replace("\n","").replace(" ","")
                
                data_dict["models"][0]["variants"].append(variant_dict)
            
            
            json_data.append(data_dict)
            print(count)
            count += 1

        
        with open("fortune.json", 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=4, ensure_ascii=False)


class Site2Scraper(BaseScraper):
    def scrape_data(self):
        # Implement Site 2 specific scraping logic
        print("Scraping Site 2")
        home_links = self.soup.select('li[class="siteMenuItem"][data-depth="2"] a')
        pdp_links = []
        json_data = []
        for link in home_links:
            nav_link = urljoin(self.url, link.get('href'))
            self.url = nav_link
            self.fetch_with_requests()
            self.parse_html()
            listing_page = self.soup.select('section[class="productMiniature__data"] a')
            for page in listing_page:
                pdp_links.append(urljoin(self.url, page.get('href')))
        for pdp in pdp_links:
            self.url = pdp
            print(self.url)
            self.fetch_with_requests()
            self.parse_html()
            data_dict = {}
            data_dict["product_id"] = self.url.split('/')[-1]
            data_dict["title"] = self.soup.select_one('h1').text.replace("\n","").replace("  ","")
            all_img = self.soup.select('[class="productImages__item keen-slider__slide"] a')
            images = []
            img = ""
            for single_img in all_img:
                if not img:
                    img = urljoin(self.url,single_img.get('href'))
                images.append(urljoin(self.url,single_img.get('href')))
            data_dict["image"] = img
            description_tag = self.soup.select_one('[id="product_tab_informations"]')
            data_dict["description"] = description_tag.get_text(strip=True) if description_tag else None
            data_dict["sale_prices"] = [self.soup.select_one('button[class="productActions__addToCart button add-to-cart add"]').text.split("-")[-1].replace(" ","").replace(" ","")]
            data_dict["prices"] = [self.soup.select_one('button[class="productActions__addToCart button add-to-cart add"]').text.split("-")[-1].replace(" ","").replace(" ","")]
            
            data_dict["images"] = images
            data_dict["brand"] = "Le Chocolat - Alain Ducasse"
            data_dict["url"] = self.url
            data_dict["models"] = [{"color":"", "variants": []}]
            json_data.append(data_dict)

        
        with open("lechocolat.json", 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=4, ensure_ascii=False)

class Site3Scraper(BaseScraper):
    def scrape_data(self):
        # Implement Site 3 specific scraping logic
        print("Scraping Site 3")
        home_links = self.driver.find_elements(
                By.CSS_SELECTOR, 'li[class*="item_linkLevel_2__2W4g_"] a')
        home_urls = []
        for p  in home_links:
            home_urls.append(p.get_attribute('href'))
        pdp_links = []
        json_data = []
        for link in home_urls:
            nav_link = urljoin(self.url, link)
            self.url = nav_link
            print(self.url)
            self.driver.get(self.url)
            self.page_source = self.driver.page_source
            self.parse_html()
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[aria-label*="this is the last page"]'))
                )
                last_page = self.driver.find_element(
                    By.CSS_SELECTOR, '[aria-label*="this is the last page"]'
                ).get_attribute('aria-label').split(' ')[3].replace(',','')
            except:
                last_page = 0
            for page in range(1, int(last_page)+1):
                if 'products-2' in nav_link:
                    pdp_link = f'https://www.traderjoes.com/home/products/category/products-2?filters=%7B%22areNewProducts%22%3Atrue%2C%22page%22%3A{page}%7D'
                else:
                    pdp_link = f'{nav_link}?filters=%7B"page"%3A{page}%7D'
                self.url = pdp_link
                print(self.url)
                self.driver.get(self.url)
                self.page_source = self.driver.page_source
                self.parse_html()
                WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'h2[class*="ProductCard_card__title"] a'))
            )
                urls = self.driver.find_elements(By.CSS_SELECTOR, 'h2[class*="ProductCard_card__title"] a')
                for u in urls:
                    pdp_links.append(u.get_attribute('href'))
                
        print(pdp_links)
        print(len(pdp_links))
        count = 0
        for pdp in pdp_links:
            print(count)
            self.url = pdp
            print(self.url)
            self.driver.get(self.url)
            self.page_source = self.driver.page_source
            self.parse_html()
            data_dict = {}
            try:
                data_dict["product_id"] = self.url.split('/')[-1]
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'h1'))
                )
            except:
                data_dict["product_id"] = None

            try:
                data_dict["title"] = self.driver.find_element(
                    By.CSS_SELECTOR, 'h1'
                ).text.replace(' ', '')
            except:
                data_dict["title"] = None
            
            try:
                image = self.driver.find_element(
                        By.CSS_SELECTOR, '[class*="HeroImage_heroImage"] img'
                ).get_attribute('srcoriginal')
                img = urljoin(self.url, image)
                
                data_dict["image"] = img
            except:
                data_dict["image"] = None
            
            try:
                description_tag = self.driver.find_element(
                        By.CSS_SELECTOR, '[class*="ProductDetails_main__description"]'
                ).text.strip()
                data_dict["description"] = description_tag if description_tag else None
            except:
                data_dict["description"] = None
            
            try:
                data_dict["sale_prices"] = [self.driver.find_element(
                        By.CSS_SELECTOR, '[class*="ProductDetails_main"] [class*="ProductPrice_productPrice__price"]'
                ).text.split("-")[-1].replace(" ","").replace("\n","")]
                data_dict["prices"] = [self.driver.find_element(
                        By.CSS_SELECTOR, '[class*="ProductDetails_main"] [class*="ProductPrice_productPrice__price"]'
                ).text.split("-")[-1].replace(" ","").replace("\n","")]
            except:
                data_dict["sale_prices"] = None
                data_dict["prices"] = None
                
            data_dict["brand"] = "Trader Joe's"
            data_dict["url"] = self.url
            data_dict["models"] = [{"color":"", "variants": []}]
            json_data.append(data_dict)
            count += 1
            if count%10 == 0:
                sleep(10) 
            

        
        with open("traderjoe.json", 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=4, ensure_ascii=False)
        
        self.quit_selenium()
            
if __name__ == "__main__":
    site1_url = "https://foreignfortune.com/"
    site2_url = "https://www.lechocolat-alainducasse.com/uk/"
    site3_url = "https://www.traderjoes.com/"

    scraper1 = Site1Scraper(site1_url)
    scraper2 = Site2Scraper(site2_url)
    scraper3 = Site3Scraper(site3_url)

    # Change to False to use Requests instead of Selenium
    scraper1.run(use_selenium=False)  
    scraper2.run(use_selenium=False)  
    scraper3.run(use_selenium=True)
