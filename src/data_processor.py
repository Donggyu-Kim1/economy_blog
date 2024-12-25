from typing import Dict, List, Any
from datetime import datetime, timedelta, timezone
import pandas as pd
from config.templates import NEWS_TEMPLATE


class DataProcessor:
    def process_us_market_data(self, data: Dict[str, Dict[str, Any]]) -> str:
        """
        미국 시장 데이터를 분석하여 요약 텍스트 생성

        Args:
            data: 미국 시장 데이터 딕셔너리
            {
                'S&P 500': {
                    'close': float,
                    'volume': int,
                    'change': float,
                    'year_high': float,
                    'year_low': float,
                    'year_high_ratio': float
                },
                'NASDAQ': {...},
                'DOW': {...}
            }

        Returns:
            str: 시장 동향 요약 문자열
        """
        if not data:
            return "미국 시장 데이터를 가져올 수 없습니다."

        # 모든 지수의 변화율 확인
        changes = {name: info["change"] for name, info in data.items()}

        # 시장 전반의 방향성 판단
        positive_changes = sum(1 for change in changes.values() if change > 0)
        negative_changes = sum(1 for change in changes.values() if change < 0)

        # 가장 큰 변화를 보인 지수 찾기
        max_change_index = max(changes.items(), key=lambda x: abs(x[1]))

        # 시장 동향 문구 생성
        if positive_changes > negative_changes:
            market_trend = "상승"
            sentiment = "긍정적인 흐름"
        elif positive_changes < negative_changes:
            market_trend = "하락"
            sentiment = "부정적인 흐름"
        else:
            market_trend = "혼조"
            sentiment = "혼조세"

        # 요약문 생성
        summary = f"미국 주요 지수는 전반적으로 {sentiment}을 보였습니다. "

        # 각 지수별 상세 정보 추가
        for index_name, info in data.items():
            change_direction = "상승" if info["change"] > 0 else "하락"
            summary += (
                f"{index_name}은 {info['close']:,.2f}로 전일 대비 {abs(info['change']):.2f}% "
                f"{change_direction}했으며, "
            )

            # 52주 최고가 대비 분석
            if abs(info["year_high_ratio"]) <= 5:
                summary += "52주 최고가에 근접한 수준이며, "
            elif info["year_high_ratio"] < -20:
                summary += "52주 최고가 대비 큰 폭의 조정을 보이고 있으며, "

            # 거래량 분석 (일반적인 거래량 수준 가정)
            volume_description = (
                "활발한"
                if info["volume"] > 1000000000
                else "평균적인" if info["volume"] > 500000000 else "다소 낮은"
            )
            summary += f"{volume_description} 거래량을 기록했습니다. "

        # 가장 큰 변화를 보인 지수에 대한 특별 언급
        summary += (
            f"\n특히 {max_change_index[0]}가 {abs(max_change_index[1]):.2f}%의 "
            f"{'상승' if max_change_index[1] > 0 else '하락'}을 기록하며 "
            f"가장 큰 변화를 보였습니다."
        )

        return summary.strip()

    def process_kr_market_data(self, data: Dict[str, Dict[str, Any]]) -> str:
        """
        한국 시장 데이터를 분석하여 요약 텍스트 생성

        Args:
            data: 한국 시장 데이터 딕셔너리
            {
                'KOSPI': {
                    'close': float,
                    'volume': int,
                    'change': float,
                    'year_high': float,
                    'year_low': float,
                    'year_high_ratio': float
                },
                'KOSDAQ': {...}
            }

        Returns:
            str: 시장 동향 요약 문자열
        """
        if not data:
            return "한국 시장 데이터를 가져올 수 없습니다."

        # 지수별 변화율 확인
        changes = {name: info["change"] for name, info in data.items()}

        # 시장 전반의 방향성 판단
        positive_changes = sum(1 for change in changes.values() if change > 0)
        negative_changes = sum(1 for change in changes.values() if change < 0)

        # 가장 큰 변화를 보인 지수 찾기
        max_change_index = max(changes.items(), key=lambda x: abs(x[1]))

        # 시장 동향 문구 생성
        if positive_changes > negative_changes:
            market_trend = "상승"
            sentiment = "강세"
        elif positive_changes < negative_changes:
            market_trend = "하락"
            sentiment = "약세"
        else:
            market_trend = "혼조"
            sentiment = "보합"

        # 요약문 생성
        summary = f"국내 증시는 전반적으로 {sentiment} 흐름을 보였습니다. "

        # 각 지수별 상세 정보 추가
        for index_name, info in data.items():
            change_direction = "상승" if info["change"] > 0 else "하락"
            points_change = abs(
                info["close"] - (info["close"] / (1 + info["change"] / 100))
            )

            summary += (
                f"{index_name}는 {info['close']:,.2f}pt로 전일 대비 {points_change:,.2f}pt"
                f"({abs(info['change']):.2f}%) {change_direction}했으며, "
            )

            # 52주 최고가 대비 분석
            high_ratio = info["year_high_ratio"]
            if abs(high_ratio) <= 5:
                summary += "52주 최고가 수준에서 거래되고 있으며, "
            elif high_ratio < -20:
                summary += f"52주 최고가 대비 {abs(high_ratio):.1f}% 하락한 수준이며, "
            else:
                summary += f"52주 최고가 대비 {abs(high_ratio):.1f}% 하락한 상태에서 거래되고 있으며, "

            # 거래량 분석 (한국 시장 기준)
            volume_description = (
                "매우 활발한"
                if info["volume"] > 1000000000
                else (
                    "활발한"
                    if info["volume"] > 500000000
                    else "평균적인" if info["volume"] > 300000000 else "다소 낮은"
                )
            )
            summary += f"{volume_description} 거래량을 보였습니다. "

        # 가장 큰 변화를 보인 지수에 대한 특별 언급
        if abs(max_change_index[1]) > 1:  # 1% 이상 변동 시에만 특별 언급
            summary += (
                f"\n특히 {max_change_index[0]}가 {abs(max_change_index[1]):.2f}%의 "
                f"{'상승' if max_change_index[1] > 0 else '하락'}을 기록하며 "
                f"큰 폭의 변동을 보였습니다."
            )

        return summary.strip()

    def process_us_treasury_data(self, data: Dict[str, Dict[str, Any]]) -> str:
        """
        미국 국채 수익률 데이터 분석 및 요약

        Args:
            data: 미국 국채 수익률 데이터 딕셔너리
            {
                '2년물': {
                    'yield_rate': float,
                    'change': float,
                    'year_high': float,
                    'year_low': float
                },
                '10년물': {...},
                '30년물': {...}
            }

        Returns:
            str: 국채 수익률 동향 요약 문자열
        """
        if not data:
            return "미국 국채 수익률 데이터를 가져올 수 없습니다."

        # 수익률 변화 방향 확인
        changes = {term: info["change"] for term, info in data.items()}

        # 가장 큰 변화를 보인 만기 찾기
        max_change_treasury = max(changes.items(), key=lambda x: abs(x[1]))

        # 수익률 곡선 분석
        try:
            curve_spread_2_10 = (
                data["10년물"]["yield_rate"] - data["2년물"]["yield_rate"]
            )
            is_inverted = curve_spread_2_10 < 0
        except KeyError:
            curve_spread_2_10 = None
            is_inverted = None

        # 요약문 생성 시작
        summary = "미국 국채 수익률은 "

        # 전반적인 방향성 판단
        positive_changes = sum(1 for change in changes.values() if change > 0)
        negative_changes = sum(1 for change in changes.values() if change < 0)

        if positive_changes > negative_changes:
            summary += "전반적으로 상승했습니다. "
        elif positive_changes < negative_changes:
            summary += "전반적으로 하락했습니다. "
        else:
            summary += "혼조세를 보였습니다. "

        # 각 만기별 상세 정보
        for term, info in data.items():
            change_direction = "상승" if info["change"] > 0 else "하락"
            summary += (
                f"{term} 수익률은 {info['yield_rate']:.3f}%로 "
                f"전일 대비 {abs(info['change']):.3f}%p {change_direction}했으며, "
            )

            # 52주 최고/최저 대비 분석
            if abs(info["yield_rate"] - info["year_high"]) <= 0.1:
                summary += "52주 최고 수준에 근접해 있습니다. "
            elif abs(info["yield_rate"] - info["year_low"]) <= 0.1:
                summary += "52주 최저 수준에 근접해 있습니다. "
            else:
                range_position = (
                    (info["yield_rate"] - info["year_low"])
                    / (info["year_high"] - info["year_low"])
                    * 100
                )
                summary += f"52주 변동범위 중 {range_position:.1f}% 수준에서 거래되고 있습니다. "

        # 수익률 곡선 분석 추가
        if curve_spread_2_10 is not None:
            summary += (
                f"\n2년물과 10년물의 스프레드는 {abs(curve_spread_2_10):.3f}%p로, "
            )
            if is_inverted:
                summary += (
                    f"수익률 곡선이 역전된 상태입니다. 이는 일반적으로 경기 침체에 대한 "
                    f"시장의 우려를 반영합니다. "
                )
            else:
                if curve_spread_2_10 < 0.5:
                    summary += "수익률 곡선이 매우 평탄화되어 있습니다. "
                else:
                    summary += "정상적인 우상향 곡선을 유지하고 있습니다. "

        # 가장 큰 변화를 보인 만기 강조
        if abs(max_change_treasury[1]) > 0.05:  # 5bp 이상 변동 시에만 언급
            summary += (
                f"\n특히 {max_change_treasury[0]} 수익률이 {abs(max_change_treasury[1]):.3f}%p의 "
                f"{'상승' if max_change_treasury[1] > 0 else '하락'}을 보이며 "
                f"가장 큰 변동을 기록했습니다."
            )

        return summary.strip()

    def process_forex_data(self, data: Dict[str, Dict[str, Any]]) -> str:
        """
        환율 데이터를 분석하여 요약 텍스트 생성

        Args:
            data: 환율 데이터 딕셔너리
            {
                'USD/KRW': {
                    'rate': float,
                    'change': float,
                    'year_high': float,
                    'year_low': float
                },
                'EUR/KRW': {...},
                'JPY/KRW': {...}
            }

        Returns:
            str: 환율 동향 요약 문자열
        """
        if not data:
            return "환율 데이터를 가져올 수 없습니다."

        # 환율 변화 방향 확인
        changes = {pair: info["change"] for pair, info in data.items()}

        # 원화 강세/약세 판단 (양수: 원화 약세, 음수: 원화 강세)
        won_weakening = sum(1 for change in changes.values() if change > 0)
        won_strengthening = sum(1 for change in changes.values() if change < 0)

        # 가장 큰 변화를 보인 통화쌍 찾기
        max_change_pair = max(changes.items(), key=lambda x: abs(x[1]))

        # 요약문 생성
        if won_weakening > won_strengthening:
            trend = "약세"
            movement = "상승"
        elif won_weakening < won_strengthening:
            trend = "강세"
            movement = "하락"
        else:
            trend = "보합"
            movement = "혼조"

        summary = f"원화는 주요 통화 대비 {trend} 흐름을 보이며, 환율은 전반적으로 {movement}했습니다. "

        # 각 통화쌍별 상세 분석
        for pair, info in data.items():
            currency = pair.split("/")[0]  # USD, EUR, JPY 추출

            # 환율 변화 방향
            change_direction = "상승" if info["change"] > 0 else "하락"

            # 통화별 단위 조정 (JPY의 경우 100엔 기준으로 표시)
            if currency == "JPY":
                rate = info["rate"] * 100
                year_high = info["year_high"] * 100
                year_low = info["year_low"] * 100
                summary += (
                    f"{currency}는 100엔당 {rate:.2f}원으로 "
                    f"전일 대비 {abs(info['change']):.2f}% {change_direction}했으며, "
                )
            else:
                summary += (
                    f"{currency}는 {info['rate']:.2f}원으로 "
                    f"전일 대비 {abs(info['change']):.2f}% {change_direction}했으며, "
                )

            # 52주 최고/최저 대비 분석
            relative_position = (
                (info["rate"] - info["year_low"])
                / (info["year_high"] - info["year_low"])
                * 100
            )

            if relative_position > 90:
                summary += "52주 최고치에 근접한 수준이며, "
            elif relative_position < 10:
                summary += "52주 최저치에 근접한 수준이며, "
            else:
                summary += f"52주 변동범위의 {relative_position:.1f}% 수준에서 거래되고 있으며, "

            # 변동성 분석
            range_percent = (
                (info["year_high"] - info["year_low"]) / info["year_low"] * 100
            )
            if range_percent > 15:
                summary += "높은 변동성을 보이고 있습니다. "
            elif range_percent > 8:
                summary += "보통 수준의 변동성을 보이고 있습니다. "
            else:
                summary += "안정적인 범위 내에서 움직이고 있습니다. "

        # 가장 큰 변화를 보인 통화에 대한 특별 언급
        if abs(max_change_pair[1]) > 0.5:  # 0.5% 이상 변동 시에만 언급
            summary += (
                f"\n특히 {max_change_pair[0].split('/')[0]}가 {abs(max_change_pair[1]):.2f}%의 "
                f"{'상승' if max_change_pair[1] > 0 else '하락'}을 기록하며 "
                f"가장 큰 변동을 보였습니다."
            )

        return summary.strip()

    def process_news_data(self, news_data: Dict[str, List[Dict[str, Any]]]) -> str:
        """
        뉴스 데이터를 처리하여 주요 뉴스 요약을 생성

        Args:
            news_data: utils/news.py에서 반환된 뉴스 데이터
        Returns:
            str: 뉴스 요약 문자열
        """
        if not news_data or all(not items for items in news_data.values()):
            return "뉴스 데이터를 가져올 수 없습니다."

        summary = []
        categories = {
            "kr_economic": "국내 경제",
            "global_economic": "글로벌 경제",
            "global_business": "글로벌 비즈니스",
        }

        for data_key, category_name in categories.items():
            news_list = news_data.get(data_key, [])
            if not news_list:
                continue

            summary.append(f"\n[{category_name}]")
            for news in news_list:
                # NEWS_TEMPLATE 형식 사용
                summary.append(
                    NEWS_TEMPLATE.format(
                        title=news.get("title_ko") or news.get("title", "N/A"),
                        source=news.get("publisher", "N/A"),
                        published_at=news.get("published_at", "N/A"),
                        summary=news.get("summary_ko") or news.get("summary", "N/A"),
                    )
                )

        return "\n".join(summary) if summary else "뉴스 데이터를 가져올 수 없습니다."

    def process_economic_calendar(self, calendar_data: List[Dict[str, Any]]) -> str:
        """
        경제 지표 일정을 처리하여 주요 지표 요약을 생성

        Args:
            calendar_data: 경제 지표 데이터 리스트
            [{'time': str, 'date': str, 'country': str, 'event': str,
              'importance': str, 'actual': str, 'forecast': str, 'previous': str}, ...]

        Returns:
            str: 경제 지표 요약 문자열
        """
        if not calendar_data:
            return "예정된 주요 경제 지표가 없습니다."

        # 현재 한국 시간
        now_kst = datetime.now(timezone(timedelta(hours=9)))
        target_date = now_kst.strftime("%Y-%m-%d")
        next_date = (now_kst + timedelta(days=1)).strftime("%Y-%m-%d")

        # 헤더 추가
        formatted = [f"{target_date} ~ {next_date} 경제 지표 일정\n"]

        # 중요 이벤트 필터링 (⭐⭐ 이상)
        important_events = [
            event for event in calendar_data if event["importance"].count("⭐") >= 2
        ]

        if not important_events:
            return "예정된 주요 경제 지표가 없습니다."

        # 날짜별로 이벤트 그룹화
        events_by_date = {}
        for event in important_events:
            date = event["date"]
            # 타겟 날짜의 데이터만 포함
            if date in [target_date, next_date]:
                if date not in events_by_date:
                    events_by_date[date] = []
                events_by_date[date].append(event)

        # 날짜별로 정렬된 이벤트 포맷팅
        for date in sorted(events_by_date.keys()):
            formatted.append(f"\n[{date}]")

            # 해당 날짜의 이벤트를 시간순으로 정렬
            day_events = sorted(events_by_date[date], key=lambda x: x["time"])

            for event in day_events:
                formatted.append(
                    f"{event['time']} [{event['country']}] {event['importance']} {event['event']}"
                )
                if event["actual"] != "N/A":
                    formatted.append(f"  발표: {event['actual']}")
                if event["forecast"] != "N/A":
                    formatted.append(f"  예상: {event['forecast']}")
                if event["previous"] != "N/A":
                    formatted.append(f"  이전: {event['previous']}")
                formatted.append("")

        return "\n".join(formatted).strip()
