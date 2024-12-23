import os
import sys
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from config.settings import NEWSAPI_KEY, DATE_FORMAT

BASE_URL = "https://api-v2.deepsearch.com/v1"


def get_formatted_date() -> str:
    """오늘 날짜를 YYYY-MM-DD 형식으로 반환"""
    return datetime.now().strftime(DATE_FORMAT)


def fetch_kr_economic_news() -> Optional[List[Dict[str, Any]]]:
    """
    한국 경제 뉴스를 가져옵니다.

    Returns:
        List[Dict[str, Any]]: 뉴스 기사 리스트 또는 에러 시 None
    """
    try:
        url = f"{BASE_URL}/articles/economy"
        params = {
            "date_from": get_formatted_date(),
            "date_to": get_formatted_date(),
            "page_size": 5,
            "api_key": NEWSAPI_KEY,
        }

        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        return data.get("data", [])

    except Exception as e:
        print(f"Error fetching Korean economic news: {str(e)}")
        return None


def fetch_global_news(section: str) -> Optional[List[Dict[str, Any]]]:
    """
    글로벌 뉴스를 가져옵니다.

    Args:
        section (str): 뉴스 섹션 (economy 또는 business)

    Returns:
        List[Dict[str, Any]]: 뉴스 기사 리스트 또는 에러 시 None
    """
    try:
        url = f"{BASE_URL}/global-articles/{section}"
        params = {
            "date_from": get_formatted_date(),
            "date_to": get_formatted_date(),
            "page_size": 5,
            "api_key": NEWSAPI_KEY,
        }

        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        return data.get("data", [])

    except Exception as e:
        print(f"Error fetching global {section} news: {str(e)}")
        return None


def get_all_news() -> Dict[str, List[Dict[str, Any]]]:
    """
    모든 뉴스를 수집합니다.

    Returns:
        Dict[str, List[Dict[str, Any]]]: 카테고리별 뉴스 데이터
    """
    news_data = {
        "kr_economic": fetch_kr_economic_news() or [],
        "global_economic": fetch_global_news("economy") or [],
        "global_business": fetch_global_news("business") or [],
    }

    return news_data


def format_news_data(news: Dict[str, Any]) -> str:
    """
    뉴스 데이터를 보기 좋은 문자열로 포맷팅합니다.

    Args:
        news (Dict[str, Any]): 뉴스 데이터

    Returns:
        str: 포맷팅된 문자열
    """
    # 국문 제목이 있는 경우 함께 표시
    title = f"{news.get('title', 'N/A')}"
    if news.get("title_ko"):
        title += f"\n({news.get('title_ko')})"

    # 국문 요약이 있는 경우 국문 요약을 사용, 없는 경우 영문 요약 사용
    summary = news.get("summary_ko", news.get("summary", "N/A"))

    return f"""
제목: {title}
시간: {news.get('published_at', 'N/A')}
출처: {news.get('publisher', 'N/A')}
요약: {summary}
"""


if __name__ == "__main__":
    # 모듈 테스트
    print("Testing news data collection...")
    try:
        news_data = get_all_news()

        # 수집된 뉴스 출력
        for category, news_list in news_data.items():
            print(f"\n=== {category} ===")
            for news in news_list:
                print(format_news_data(news))

    except Exception as e:
        print(f"Test failed with error: {str(e)}")
