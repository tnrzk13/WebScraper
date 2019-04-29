FROM python:3

RUN pip install beautifulsoup4
RUN pip install PyMySQL

CMD ["WebScraper.py"]