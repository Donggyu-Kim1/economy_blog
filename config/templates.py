# 마크다운 리포트 템플릿
REPORT_TEMPLATE = """
# {date} 시장 동향 리포트

## 1. 한국 시장 동향
{kr_market_summary}

## 2. 미국 시장 동향
{us_market_summary}

## 3. 미국 국채 수익률
{us_treasury_summary}

## 4. 주요 환율
{forex_summary}

## 5. 주요 뉴스
{news_summary}

## 6. 주요 경제 지표
{economic_calendar}
"""

# 시장 데이터 섹션 템플릿
MARKET_SECTION_TEMPLATE = """
### {market_name}
- 종가: {close:,.2f} ({change:+.2f}%)
- 거래량: {volume:,}
- 52주 최고가 대비: {year_high_ratio:.1f}%

![{market_name} Price Movement]({image_path})
"""

# 국채 수익률 섹션 템플릿
TREASURY_SECTION_TEMPLATE = """
### {treasury_name}
- 수익률: {yield_rate:.3f}%
- 전일대비: {change:+.3f}%p
- 52주 최고: {year_high:.3f}%
- 52주 최저: {year_low:.3f}%
"""

# 뉴스 섹션 템플릿
NEWS_TEMPLATE = """
### {title}
- 출처: {source}
- 시간: {published_at}
- 요약: {summary}
"""

# 경제 지표 템플릿
CALENDAR_TEMPLATE = """
### {date}
- {time} {event}
- 예상: {forecast}
- 이전: {previous}
"""
