from dataclasses import dataclass, asdict, field
import pandas as pd
import argparse
from playwright.sync_api import sync_playwright


@dataclass
class Business:
    name: str = None
    address: str = None
    phone: str = None
    website: str = None


@dataclass
class BusinessList:
    businesses: list[Business] = field(default_factory=list)

    def dataframe(self):
        return pd.json_normalize([asdict(business) for business in self.businesses], sep=".")

    def save_to_excel(self, filename):
        self.dataframe().to_excel(f"{filename}.xlsx", index=False)

    def save_to_csv(self, filename):
        self.dataframe().to_csv(f"{filename}.csv", index=False)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.google.com/maps", timeout=50000)
        page.wait_for_timeout(5000)
        page.locator('//input[@id="searchboxinput"]').fill(search)
        page.wait_for_timeout(3000)

        page.keyboard.press("Enter")
        page.wait_for_timeout(5000)

        listings = page.locator('//div[@role="article"]').all()
        print(len(listings))

        business_list = BusinessList()

        # Currently, the first 20 listings on the first page of the search results:
        for listing in listings[:20]:
            listing.click()
            page.wait_for_timeout(5000)

            name_xpath = '//h1[contains(@class,"fontHeadlineLarge")]/span[2]'
            address_xpath = '//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]'
            website_xpath = '//a[@data-item-id="authority"]//div[contains(@class, "fontBodyMedium")]'
            phone_xpath = '//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]'

            business = Business()
            try:
                business.name = page.locator(name_xpath).inner_text()
            except:
                pass
            try:
                business.address = page.locator(address_xpath).inner_text()
            except:
                pass
            try:
                business.website = page.locator(website_xpath).inner_text()
            except:
                pass
            try:
                business.phone = page.locator(phone_xpath).inner_text()
            except:
                pass

            business_list.businesses.append(business)

        business_list.save_to_csv("map_data")
        business_list.save_to_excel("map_data")

        context.close()
        browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape Google Maps for businesses")
    parser.add_argument("search", type=str, help="Search term")
    parser.add_argument("location", type=str, help="Location")
    args = parser.parse_args()

    if args.location and args.search:
        search = f"{args.search} {args.location.strip()}"
    else:
        search = "restaurants in Guwahati"

    main()
