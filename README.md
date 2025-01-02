# Market Report Generator

자동화된 경제 시황 리포트 생성 시스템입니다. 매일 주요 시장 지표, 환율, 경제 뉴스를 수집하여 마크다운 형식의 종합 리포트를 생성합니다.

정리 결과는 [금융경제이야기](https://storyofeconomy.tistory.com/)에 올라갑니다.

## 주요 기능

- 시장 데이터 수집 및 분석
  - 미국 주요 지수 (S&P 500, NASDAQ, DOW)
  - 한국 주요 지수 (KOSPI, KOSDAQ)
  - 미국 국채 수익률 (2년물, 10년물, 30년물) 및 정책금리
  - 주요 통화 환율 (USD, EUR, JPY, CNY)
- 경제 뉴스 수집
- 주요 경제지표 데이터 수집 (Investing.com 데이터)
  - 중요도(⭐⭐ 이상) 기반 필터링
  - 국가별 주요 경제지표
  - 실제/예상/이전 값 비교
- 시각화 차트 생성
- 마크다운 형식의 리포트 자동 생성

## 프로젝트 구조

```
market_report/
├── config/
│   ├── settings.py     # 프로젝트 설정
│   └── templates.py    # 리포트 템플릿
├── utils/
│   ├── forex.py        # 환율 데이터 수집
│   ├── kr_market.py    # 한국 시장 데이터 수집
│   ├── us_market.py    # 미국 시장 데이터 수집
│   ├── us_treasury.py  # 미국 국채 데이터 수집
│   ├── news.py        # 뉴스 데이터 수집
│   ├── calendar.py    # 경제지표 데이터 수집
│   └── chart_generator.py  # 차트 생성
├── src/
│   ├── data_processor.py    # 데이터 처리 및 분석
│   ├── markdown_builder.py  # 마크다운 리포트 생성
│   ├── logger.py           # 로깅
│   └── report_generator.py  # 리포트 생성 총괄
├── reports/             # 생성된 리포트 저장
│   └── images/         # 차트 이미지 저장
└── .github/workflows/  # GitHub Actions
```

## 설치 및 실행

1. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

2. 환경변수 설정 (.env 파일 생성):
```
NEWSAPI_KEY=your_newsapi_key
FEDAPI_KEY=your_fedapi_key
```

3. Chrome 웹드라이버 설치:
```bash
# Windows
choco install chromedriver

# Linux
apt-get install chromium-chromedriver
```

4. 리포트 생성 실행:
```python
from src.report_generator import generate_daily_report

report_path = generate_daily_report()
print(f"Report generated: {report_path}")
```

## 데이터 흐름

1. 데이터 수집 (`utils/`)
   - yfinance: 시장 데이터
   - NewsAPI: 경제 뉴스
   - FEDAPI: 미국 정책금리
   - Investing.com: 경제지표 데이터
   - Selenium: 웹 스크래핑

2. 데이터 처리 (`src/data_processor.py`)
   - 수집된 데이터 분석
   - 시장 동향 요약 생성
   - 경제지표 중요도 기반 필터링
   - 차트 생성

3. 리포트 생성 (`src/markdown_builder.py`)
   - 마크다운 형식 변환
   - 차트 이미지 포함
   - 최종 리포트 저장

## 자동화 설정

GitHub Actions를 통해 매일 지정된 시간에 자동으로 리포트를 생성합니다:

1. `.github/workflows/daily_report.yml` 설정
2. Secrets에 필요한 API 키 등록
3. Chrome 웹드라이버 설정
4. 리포트 자동 생성 및 저장

## 에러 처리 및 로깅

- 각 단계별 로그 기록
- 데이터 수집 실패 시 대체 로직
- 웹 스크래핑 예외 처리
- 상세한 에러 메시지 및 스택 트레이스 저장

## 문서화

- 코드 내 상세한 주석
- 함수별 독스트링
- 타입 힌팅 사용
- 예외 처리 명시

## 변경 이력

- 2024-12-25: 경제지표 수집 기능 개선
   - Investing.com 데이터 수집 추가
   - 중요도(⭐) 기반 필터링 구현
   - 상세 경제지표 정보 표시

- 2025-01-03: 데이터 분석 방법 개선
   - setting에 기준 분석 기간 30일에서 365일로 변경
   - 인덱스 거래량  20일 이동평균 대비 상대값으로 분석
   - 채권 분석
      - 수익률 곡선의 역전 여부와 함의를 더 자세히 분석
      - 3개월/6개월 평균 대비 현재 수준을 통한 추세 분석
      - 변동성의 장기 평균 대비 현재 수준 분석
      - 기준금리와의 스프레드를 통한 통화정책 기대 반영