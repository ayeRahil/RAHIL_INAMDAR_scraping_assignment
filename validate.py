import json
import csv
import os

class Validation:
    def __init__(self, product_data):
        self.product_data = product_data

    def is_mandatory_fields_present(self):
        mandatory_fields = ['title', 'product_id']
        missing_fields = [field for field in mandatory_fields if field not in self.product_data]
        if missing_fields:
            print(f"Missing mandatory fields: {missing_fields}")
            return False
        return True

    def is_description_present(self):
        if 'description' not in self.product_data or not self.product_data['description'] or not self.product_data['description'].strip():
            print("Description is missing or empty.")
            return False
        return True

    def is_sale_price_valid(self):
        if 'sale_prices' in self.product_data and 'prices' in self.product_data:
            sale_prices = [float(price.replace('$', '').replace('£', '').replace(',', '')) for price in self.product_data['sale_prices']]
            original_prices = [float(price.replace('$', '').replace('£', '').replace(',', '')) for price in self.product_data['prices']]
            for sale_price in sale_prices:
                if any(sale_price > original_price for original_price in original_prices):
                    print("Sale price is greater than original price.")
                    return False
        return True

    def has_images_and_prices(self):
        if 'models' in self.product_data:
            for model in self.product_data['models']:
                for variant in model.get('variants', []):
                    if 'image' not in variant or not variant['image']:
                        print(f"Variant {variant.get('id', 'unknown')} has no image.")
                        return False
                    if 'prices' not in variant or not variant['prices']:
                        print(f"Variant {variant.get('id', 'unknown')} has no price.")
                        return False
        return True

    def validate(self):
        validations = [
            self.is_mandatory_fields_present,
            self.is_description_present,
            self.is_sale_price_valid,
            self.has_images_and_prices
        ]
        
        for validate in validations:
            if not validate():
                return False
        return True

def read_json_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        return json.load(file)

def write_to_csv(filepath, data, headers):
    with open(filepath, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        for item in data:
            writer.writerow(item)

def main():
    # List of JSON files
    json_files = ['fortune.json', 'lechocolat.json', 'traderjoes.json']
    
    for json_file in json_files:

        products = read_json_file(json_file)

        # Headers for the CSV files
        headers = [
            'product_id', 'title', 'description', 'sale_prices', 'prices', 'images', 
            'brand', 'url', 'models'
        ]

        # Update headers based on the fields present in the product data
        for product in products:
            for key in product.keys():
                if key not in headers:
                    headers.append(key)

        valid_products = []
        invalid_products = []

        # Validate each product
        for product in products:
            validator = Validation(product)
            if validator.validate():
                valid_products.append(product)
            else:
                invalid_products.append(product)

        # Create output directory if not exists
        output_dir = 'validation_output'
        os.makedirs(output_dir, exist_ok=True)

        # Write valid and invalid products to separate CSV files
        base_filename = os.path.splitext(os.path.basename(json_file))[0]
        write_to_csv(os.path.join(output_dir, f'{base_filename}_valid_products.csv'), valid_products, headers)
        write_to_csv(os.path.join(output_dir, f'{base_filename}_invalid_products.csv'), invalid_products, headers)

if __name__ == "__main__":
    main()
