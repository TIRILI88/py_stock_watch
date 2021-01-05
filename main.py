import requests
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

ALPHA_VANTAGE_KEY = ""
NEWS_API_KEY = ""
date_today = ""

STOCKS_TO_WATCH = {
    "TSLA": "Tesla Inc",
    "ZM": "Zoom Video Communications Inc.",
    "MRNA": "Moderna Inc.",
    "ENPH": "Enphase Energy Inc.",
    "FSLY": "Fastly Inc."
}


def get_stock_data(stock):
    global date_today

    url = "https://www.alphavantage.co/query"
    parameters = {
        "function": "TIME_SERIES_DAILY",
        "symbol": stock,
        "outputsize": "compact",
        "apikey": ALPHA_VANTAGE_KEY
    }

    response = requests.get(url=url, params=parameters)
    response.raise_for_status()
    data = response.json()
    df = pd.DataFrame(data["Time Series (Daily)"]).T
    stock_dict = df.to_dict()

    # opening price
    date_today = list(stock_dict["1. open"].keys())[0]
    open_price_today = stock_dict["1. open"][date_today]

    # closing price
    stock_dict_keys_close = list(stock_dict["4. close"].keys())[1]
    close_price_yesterday = stock_dict["4. close"][stock_dict_keys_close]

    return float(open_price_today), float(close_price_yesterday)


def get_change(opening, closing):
    if opening == closing:
        return 0
    try:
        delta = (abs(opening - closing) / closing) * 100.0
        return delta
    except ZeroDivisionError:
        return 0


def get_news(company_name):
    url = ("http://newsapi.org/v2/everything")

    parameters ={
        "q": company_name,
        "from": date_today,
        "sortBy": "popularity",
        "apiKey": NEWS_API_KEY
    }

    response = requests.get(url, params=parameters)
    response.raise_for_status()
    data = response.json()["articles"]
    three_articles = data[:3]

    if len(three_articles) > 0:
        plain_message_list = []
        html_message_list = []
        for headline in three_articles:
            plain_message = headline["title"]
            url = headline["url"]
            html_message = f"<a href={url}>{plain_message}</a><br>"
            plain_message_list.append(plain_message)
            html_message_list.append(html_message)
        return plain_message_list, html_message_list
    else:
        no_news = [f"No news for {company_name}"]
        return no_news


def send_mail(subject, plain_message, html_message):
    from_mail = ""
    password = ""
    to_address = ""
    # smtp.mail.yahoo.com

    with smtplib.SMTP("smtp.gmail.com", port=587) as connection:
        connection.starttls()
        connection.login(user=from_mail, password=password)
        send_message = MIMEMultipart("alternative")
        send_message["Subject"] = subject
        send_message["From"] = from_mail
        send_message["To"] = to_address
        send_message.attach(MIMEText(plain_message, "plain"))
        send_message.attach(MIMEText(html_message, "html"))

        connection.sendmail(
            from_mail, to_address, send_message.as_string()
            )


def main():
    for stock in STOCKS_TO_WATCH:
        company_name = STOCKS_TO_WATCH[stock]
        opening_price, closing_price = get_stock_data(stock)
        delta = get_change(opening_price, closing_price)
        print(f"Delta: {stock}:{delta}")
        if delta > 0.5:
            plain_message_list, html_message_list = get_news(company_name)
            plain_message = "\n".join(str(msg) for msg in plain_message_list)
            html_message = "\n".join(str(msg) for msg in html_message_list)
            delta = str(round(delta, 2))
            if opening_price > closing_price:
                subject = f"{stock} 🔺{delta}%"
                send_mail(subject, plain_message, html_message)
            elif opening_price < closing_price:
                subject = f"{stock} 🔻{delta}%"
                send_mail(subject, plain_message, html_message)


main()

