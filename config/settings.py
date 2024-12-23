from datetime import datetime
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 기본 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
IMAGES_DIR = os.path.join(REPORTS_DIR, "images")

# 날짜 형식
DATE_FORMAT = "%Y-%m-%d"
TODAY = datetime.now().strftime(DATE_FORMAT)

# 파일 포맷
REPORT_FILENAME_FORMAT = "{date}_market_report.md"
IMAGE_FILENAME_FORMAT = "{market_name}_price.png"

# 데이터 수집 설정
LOOKBACK_DAYS = 30
NEWS_LIMIT = 5
NEWS_LANGUAGES = ["ko", "en"]

# 시장 데이터 설정
US_INDICES = {"S&P 500": "^GSPC", "NASDAQ": "^IXIC", "DOW": "^DJI"}
KR_INDICES = {"KOSPI": "KS11", "KOSDAQ": "KQ11"}

# 환율 설정
CURRENCIES = ["USD/KRW", "EUR/KRW", "JPY/KRW", "CNY/KRW"]

# API 키 설정
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")


def get_daily_image_path():
    return os.path.join(IMAGES_DIR, TODAY)


def get_report_filepath(date=TODAY):
    """리포트 파일의 전체 경로를 반환"""
    return os.path.join(REPORTS_DIR, REPORT_FILENAME_FORMAT.format(date=date))


def get_image_filepath(market_name, date=TODAY):
    """이미지 파일의 전체 경로를 반환"""
    daily_path = os.path.join(IMAGES_DIR, date)
    return os.path.join(
        daily_path, IMAGE_FILENAME_FORMAT.format(market_name=market_name)
    )
