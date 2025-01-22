import os
from datetime import datetime
from typing import Dict, Any, Optional
import sys

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from config.templates import (
    REPORT_TEMPLATE,
    MARKET_SECTION_TEMPLATE,
    TREASURY_SECTION_TEMPLATE,
    NEWS_TEMPLATE,
    CALENDAR_TEMPLATE,
    BUFFETT_INDICATOR_TEMPLATE,
)
from config.settings import get_report_filepath, get_image_filepath, DATE_FORMAT


class MarkdownBuilder:
    """마크다운 형식의 리포트를 생성하는 클래스"""

    def __init__(self, date: Optional[str] = None):
        """
        Args:
            date: 리포트 날짜 (기본값: 오늘)
        """
        self.date = date or datetime.now().strftime(DATE_FORMAT)

    def build_us_market_section(
        self, data: Dict[str, Dict[str, Any]], summary: str
    ) -> str:
        """미국 시장 섹션 생성"""
        sections = []
        for market_name, market_data in data.items():
            image_path = get_image_filepath(market_name, self.date)
            section = MARKET_SECTION_TEMPLATE.format(
                market_name=market_name,
                close=market_data["close"],
                change=market_data["change"],
                volume=market_data["volume"],
                year_high_ratio=market_data["year_high_ratio"],
                image_path=image_path,
            )
            sections.append(section)

        # 전체 요약을 먼저 추가하고 각 지수별 상세 정보 포함
        return summary + "\n\n" + "\n".join(sections)

    def build_kr_market_section(
        self, data: Dict[str, Dict[str, Any]], summary: str
    ) -> str:
        """한국 시장 섹션 생성"""
        sections = []
        for market_name, market_data in data.items():
            image_path = get_image_filepath(market_name, self.date)
            section = MARKET_SECTION_TEMPLATE.format(
                market_name=market_name,
                close=market_data["close"],
                change=market_data["change"],
                volume=market_data["volume"],
                year_high_ratio=market_data["year_high_ratio"],
                image_path=image_path,
            )
            sections.append(section)

        return summary + "\n\n" + "\n".join(sections)

    def build_us_treasury_section(
        self, data: Dict[str, Dict[str, Any]], summary: str
    ) -> str:
        """미국 국채 섹션 생성"""
        sections = []
        for treasury_name, treasury_data in data.items():
            section = TREASURY_SECTION_TEMPLATE.format(
                treasury_name=treasury_name,
                yield_rate=treasury_data["yield_rate"],
                change=treasury_data["change"],
                year_high=treasury_data["year_high"],
                year_low=treasury_data["year_low"],
            )
            sections.append(section)

        return summary + "\n\n" + "\n".join(sections)

    def build_forex_section(self, data: Dict[str, Dict[str, Any]], summary: str) -> str:
        """환율 섹션 생성"""
        formatted_data = []
        for pair, forex_data in data.items():
            currency = pair.split("/")[0]
            if currency == "JPY":
                # JPY는 100엔 단위로 표시
                rate = forex_data["rate"] * 100
                formatted = (
                    f"### {pair}\n"
                    f"- 환율: {rate:.2f}원/100엔 ({forex_data['change']:+.2f}%)\n"
                    f"- 52주 변동폭: {forex_data['year_low']*100:.2f}원 ~ {forex_data['year_high']*100:.2f}원"
                )
            else:
                formatted = (
                    f"### {pair}\n"
                    f"- 환율: {forex_data['rate']:.2f}원 ({forex_data['change']:+.2f}%)\n"
                    f"- 52주 변동폭: {forex_data['year_low']:.2f}원 ~ {forex_data['year_high']:.2f}원"
                )
            formatted_data.append(formatted)

        return summary + "\n\n" + "\n\n".join(formatted_data)

    def build_buffett_indicator_section(
        self, data: Dict[str, Any], summary: str
    ) -> str:
        """버핏 지표 섹션 생성"""
        section = BUFFETT_INDICATOR_TEMPLATE.format(
            current_ratio=data.get("current_ratio", 0),
            historical_mean=data.get("historical_mean", 0),
            market_status=data.get("market_status", "정보 없음"),
            deviation_from_trend=data.get("deviation_from_trend", 0),
            zscore=data.get("zscore", 0),
            lower_2std=data.get("lower_2std", 0),
            upper_2std=data.get("upper_2std", 0),
        )

        return summary + "\n\n" + section

    def build_news_section(self, news_data: Dict[str, Any], summary: str) -> str:
        """뉴스 섹션 생성"""
        return summary  # 이미 DataProcessor에서 포맷팅된 요약문을 사용

    def build_calendar_section(
        self, calendar_data: Dict[str, Any], summary: str
    ) -> str:
        """경제 지표 섹션 생성"""
        return summary  # 이미 DataProcessor에서 포맷팅된 요약문을 사용

    def build_options_section(
        self, data: Dict[str, Dict[str, Any]], summary: str
    ) -> str:
        """옵션 시장 섹션 생성"""
        # DataProcessor에서 이미 포맷팅된 요약문을 사용
        return summary  # 다른 섹션들과 동일한 방식으로 처리

    def build_report(
        self,
        us_market_data: Dict[str, Dict[str, Any]],
        us_market_summary: str,
        us_treasury_data: Dict[str, Dict[str, Any]],
        us_treasury_summary: str,
        kr_market_data: Dict[str, Dict[str, Any]],
        kr_market_summary: str,
        forex_data: Dict[str, Dict[str, Any]],
        forex_summary: str,
        buffett_indicator_data: Dict[str, Any],
        buffett_indicator_summary: str,
        news_summary: str,
        calendar_summary: str,
        options_data: Optional[Dict[str, Dict[str, Any]]] = None,
        options_summary: Optional[str] = None,
    ) -> str:
        """전체 리포트 생성"""
        report = REPORT_TEMPLATE.format(
            date=self.date,
            us_market_summary=self.build_us_market_section(
                us_market_data, us_market_summary
            ),
            options_summary=self.build_options_section(
                options_data or {},
                options_summary or "옵션 시장 데이터를 가져올 수 없습니다.",
            ),
            us_treasury_summary=self.build_us_treasury_section(
                us_treasury_data, us_treasury_summary
            ),
            kr_market_summary=self.build_kr_market_section(
                kr_market_data, kr_market_summary
            ),
            forex_summary=self.build_forex_section(forex_data, forex_summary),
            buffett_indicator_summary=self.build_buffett_indicator_section(
                buffett_indicator_data, buffett_indicator_summary
            ),
            news_summary=news_summary,
            economic_calendar=calendar_summary,
        )

        return report

    def save_report(self, report_content: str) -> str:
        """생성된 리포트를 파일로 저장"""
        report_path = get_report_filepath(self.date)

        # 디렉토리가 없으면 생성
        os.makedirs(os.path.dirname(report_path), exist_ok=True)

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        return report_path


def create_report(
    date: Optional[str] = None,
    us_market_data: Optional[Dict[str, Dict[str, Any]]] = None,
    us_market_summary: Optional[str] = None,
    us_treasury_data: Optional[Dict[str, Dict[str, Any]]] = None,
    us_treasury_summary: Optional[str] = None,
    kr_market_data: Optional[Dict[str, Dict[str, Any]]] = None,
    kr_market_summary: Optional[str] = None,
    forex_data: Optional[Dict[str, Dict[str, Any]]] = None,
    forex_summary: Optional[str] = None,
    buffett_indicator_data: Optional[Dict[str, Any]] = None,
    buffett_indicator_summary: Optional[str] = None,
    news_summary: Optional[str] = None,
    calendar_summary: Optional[str] = None,
    options_data: Optional[Dict[str, Dict[str, Any]]] = None,
    options_summary: Optional[str] = None,
) -> str:
    """
    리포트 생성 헬퍼 함수

    Args:
        date: 리포트 날짜
        us_market_data: 미국 시장 데이터
        us_market_summary: 미국 시장 요약
        us_treasury_data: 미국 국채 데이터
        us_treasury_summary: 미국 국채 요약
        kr_market_data: 한국 시장 데이터
        kr_market_summary: 한국 시장 요약
        forex_data: 환율 데이터
        forex_summary: 환율 요약
        buffett_indicator_data: 버핏 지표 데이터
        buffett_indicator_summary: 버핏 지표 요약
        news_summary: 뉴스 요약
        calendar_summary: 경제 지표 요약
        options_data: 옵션 시장 데이터
        options_summary: 옵션 시장 요약

    Returns:
        str: 저장된 리포트 파일 경로
    """
    builder = MarkdownBuilder(date)
    report_content = builder.build_report(
        us_market_data or {},
        us_market_summary or "미국 시장 데이터를 가져올 수 없습니다.",
        us_treasury_data or {},
        us_treasury_summary or "미국 국채 데이터를 가져올 수 없습니다.",
        kr_market_data or {},
        kr_market_summary or "한국 시장 데이터를 가져올 수 없습니다.",
        forex_data or {},
        forex_summary or "환율 데이터를 가져올 수 없습니다.",
        buffett_indicator_data or {},
        buffett_indicator_summary or "버핏 지표 데이터를 가져올 수 없습니다.",
        news_summary or "뉴스 데이터를 가져올 수 없습니다.",
        calendar_summary or "경제 지표 데이터를 가져올 수 없습니다.",
        options_data or {},
        options_summary or "옵션 시장 데이터를 가져올 수 없습니다.",
    )
    return builder.save_report(report_content)


if __name__ == "__main__":
    # 테스트 데이터로 리포트 생성 테스트
    test_data = {
        "us_market_data": {
            "S&P 500": {
                "close": 4500.21,
                "change": 1.2,
                "volume": 2500000000,
                "year_high_ratio": -2.17,
            }
        },
        "us_market_summary": "미국 시장은 상승세를 보였습니다.",
        "buffett_indicator_data": {
            "current_ratio": 180.5,
            "historical_mean": 165.2,
            "market_status": "고평가됨",
            "deviation_from_trend": 15.3,
            "zscore": 1.5,
            "lower_2std": 140.0,
            "upper_2std": 190.0,
        },
        "buffett_indicator_summary": "현재 버핏 지표는 장기 평균을 상회하고 있습니다.",
        "options_data": {
            "SPX": {
                "ratios": {
                    "volume_ratio": 1.2,
                    "oi_ratio": 1.1,
                    "final_signal": "BEARISH",
                    "strength": 0.7,
                },
                "skew": {"atm_iv": 0.15, "trend": "LEFT_SKEWED"},
            }
        },
        "options_summary": "옵션 시장은 하방 리스크에 대한 우려가 높은 상태입니다.",
    }

    builder = MarkdownBuilder()
    print("Testing markdown builder...")
    try:
        # 테스트 루틴에 옵션 섹션 추가
        report = builder.build_report(
            test_data.get("us_market_data"),
            test_data.get("us_market_summary"),
            {},  # us_treasury_data
            "국채 데이터 없음",  # us_treasury_summary
            {},  # kr_market_data
            "한국 시장 데이터 없음",  # kr_market_summary
            {},  # forex_data
            "환율 데이터 없음",  # forex_summary
            test_data.get("buffett_indicator_data"),
            test_data.get("buffett_indicator_summary"),
            "뉴스 데이터 없음",  # news_summary
            "경제 지표 데이터 없음",  # calendar_summary
            test_data.get("options_data"),
            test_data.get("options_summary"),
        )
        print("Sample report:")
        print(report)
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
