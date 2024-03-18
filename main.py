import requests
from bs4 import BeautifulSoup
import pandas as pd
import json

def extract_product_info(product_url):
    response = requests.get(product_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    data = {}

    # Breadcrumb Category
    breadcrumb = soup.select(".breadcrumb_wrap .breadcrumbList .breadcrumbListItem:not(:first-child)")
    data['Bread crumb category'] = '/'.join([item.get_text(strip=True) for item in breadcrumb])

    # Side Image URLs
    data['Side image urls'] = '\n'.join([item.find("img").get("src") for item in soup.select(".slider-frame .slider-list .slider-slide")])

    # Category
    article_header = soup.select(".articlePurchaseBox .articleInformation .articleNameHeader")[0]
    category = article_header.select(".articleOtherLabel")[0].get_text(strip=True) + " " + article_header.select(".groupName")[0].get_text(strip=True)
    data['Category'] = category

    # Product Name
    data['Product Name'] = article_header.select("h1.itemTitle")[0].get_text(strip=True)

    # Pricing
    data['Pricing'] = soup.select("div.articlePurchaseBox .articleInformation div.articlePrice")[0].get_text(strip=True)

    # Available Size
    sizes = [size_li.get_text(strip=True) for size_li in soup.select(".addToCartForm ul li") if size_li.get_text(strip=True)]
    data['Available Size'] = ' | '.join(sizes)

    # Sense of the Size
    sense_of_the_size = ' | '.join([sense_item.get_text(strip=True) for sense_item in soup.select(".addToCartForm .sizeFitBar .label span")])
    data['Sense of the size'] = sense_of_the_size

    # Coordinated Products
    script_data = soup.find(id="__NEXT_DATA__").get_text(strip=True)
    product_data = json.loads(script_data)["props"]["pageProps"]["apis"]["pdpInitialProps"]["detailApi"]["product"]
    coordinated_products = [f"{article['name']}\n{article['price']['current']['withTax']}\n{article['articleCode']}\n{article.get('image')}\nhttps://shop.adidas.jp/products/{article['articleCode']}\n" for article in product_data["article"]["coordinates"]["articles"]]
    data['Coordinated Products'] = '\n'.join(coordinated_products)

    # Article Promotion
    article_promotion = soup.select(".pdpContainer .articlePromotion")
    if article_promotion:
        article_promotion = article_promotion[0]
        data['Title of description'] = article_promotion.select("h4.heading")[0].get_text(strip=True)
        data['General description of product'] = article_promotion.select("div .description .details .commentItem-mainText")[0].get_text(strip=True)
        data['General description itemization'] = '\n'.join([item.get_text(strip=True) for item in article_promotion.select("div .description .articleFeatures li")])

    # Size Chart
    model_code = soup.find(id="vs-product-id").get("value")
    size_chart_response = requests.get(f"https://shop.adidas.jp/f/v1/pub/size_chart/{model_code}")
    size_chart_data = size_chart_response.json().get("size_chart", {})
    header_data = size_chart_data.get("header", {}).get("0", {}).get("value", [])
    body_data = size_chart_data.get("body", {})

    table_size_information = ""
    for i in range(len(header_data)):
        header_val = header_data[i]
        record = header_val + "|"
        body_val = body_data.get(str(i), {})
        for j in range(len(body_val)):
            body_value = body_val.get(str(j), {}).get("value", "")
            record += body_value + "|"
        record += "\n"
        table_size_information += record

    data['Table size information'] = table_size_information

    # Review and Rating
    review = product_data["model"]["review"]
    reviewSeoLd = review["reviewSeoLd"]
    rating = review["fitbarScore"]
    number_of_reviews = review["reviewCount"]
    recommended_rate = f"{review['ratingAvg']}%"
    review_rating_rate = f"{rating}\n{number_of_reviews}\n{recommended_rate}\n"
    data['Review/rating/Rate'] = review_rating_rate

    review_info = '\n'.join([f"{review['datePublished']}\n{review['reviewRating']['ratingValue']}\n{review['name']}\n{review['reviewBody']}\n" for review in reviewSeoLd])
    data['Review information'] = review_info

    return data



def main():
    product_url = 'https://shop.adidas.jp/products/II5763/'
    product_info = extract_product_info(product_url)

    df = pd.DataFrame([product_info])
    df.to_excel('output_file.xlsx', index=False)

if __name__ == "__main__":
    main()

