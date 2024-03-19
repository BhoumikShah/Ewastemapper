import asyncio
from dataclasses import dataclass, asdict, field
import pandas as pd
import argparse
from playwright.async_api import async_playwright

@dataclass
class Business:
    name: str = None
    address: str = None
    website: str = None
    phone_number: str = None
    amount_of_reviews: int = None
    rating: float = None

@dataclass
class BusinessList:
    business_list: list[Business] = field(default_factory=list)

    def dataframe(self):
        return pd.json_normalize((asdict(business) for business in self.business_list), sep="_")

    def save_to_csv(self, filename):
        self.dataframe().to_csv(f'{filename}.csv', index=False)

async def get_business_async(page, listing):
    business = Business()

    xpath_mapping = {
        'name': '//h1[contains(@class, "DUwDvf") and contains(@class, "lfPIob")]',
        'address': '//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]',
        'website': '//a[@data-item-id="authority"]//div[contains(@class, "fontBodyMedium")]',
        'phone_number': '//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]',
        'rating': '//div[@class="F7nice "]/span/span[@aria-hidden="true"]',
        'amount_of_reviews': '//div[@class="F7nice "]/span/span/span[@aria-label]'
    }

    for key, xpath in xpath_mapping.items():
        if await page.locator(xpath).count() > 0:
            text = await page.locator(xpath).inner_text()
            if key == 'rating':
                business.rating = float(text.replace(',', '.'))
            elif key == 'amount_of_reviews':
                business.amount_of_reviews = int(text.replace('(', '').replace(')', ''))
            else:
                setattr(business, key, text)

    return business

async def main_async(search_for):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        await page.goto('https://www.google.com/maps', timeout=60000)
        await page.wait_for_timeout(5000)

        await page.locator('//input[@id="searchboxinput"]').fill(search_for)
        await page.wait_for_timeout(3000)

        await page.keyboard.press('Enter')
        await page.wait_for_timeout(5000)

        listings = await page.locator('//a[@class="hfpxzc"]').all()

        business_list = BusinessList()

        tasks = [get_business_async(page, listing) for listing in listings]
        business_list.business_list.extend(await asyncio.gather(*tasks))

        business_list.save_to_csv('google_maps_data')

        await browser.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--search", type=str)
    parser.add_argument("-l", "--location", type=str)

    args = parser.parse_args()

    if args.location and args.search:
        search_for = f'{args.search} {args.location}'
    else:
        search_for = 'dentist new york'

    asyncio.run(main_async(search_for))