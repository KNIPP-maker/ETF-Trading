import requests
from bs4 import BeautifulSoup
from datetime import datetime

class MarketScanner:
    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0'}

    def _get_soup(self, url):
        try:
            res = requests.get(url, headers=self.headers, timeout=5)
            return BeautifulSoup(res.text, 'html.parser')
        except Exception as e:
            print(f"⚠️ 접속 실패 ({url}): {e}")
            return None

    def get_us_market(self):
        """미국 주요 지수 (네이버 금융)"""
        print("\n🇺🇸 [미국 증시 마감]")
        url = "https://finance.naver.com/world/"
        soup = self._get_soup(url)
        if not soup: return

        # 네이버 금융 해외증시 구조 파싱
        # 주요 지수: 다우, 나스닥, S&P500, 필라델피아반도체
        targets = ["다우산업", "나스닥종합", "S&P500", "필라델피아반도체"]
        
        # 테이블 데이터 찾기
        rows = soup.select('.section_strategy li') # 또는 테이블 구조 확인
        
        # 네이버 월드 페이지 구조가 복잡하므로, 주요 데이터 테이블(일별시세 등)을 직접 타겟팅
        # 데이터가 있는 테이블(class 'data') 파싱
        data_rows = soup.select('.tb_td2 tr') # 예시 선택자, 실제로는 유동적일 수 있음
        
        # 더 확실한 방법: 주요 홈 화면의 지수 섹션
        # 여기서는 안정성을 위해 개별 지수 URL을 쏘는 것이 낫습니다.
        
        indices = {
            "다우존스": "DJI@DJI",
            "나스닥": "NAS@IXIC",
            "S&P500": "SPI@SPX",
            "필라델피아반도체": "PHI@SOX"
        }
        
        for name, code in indices.items():
            try:
                sub_url = f"https://finance.naver.com/world/sise.naver?symbol={code}"
                sub_soup = self._get_soup(sub_url)
                if not sub_soup: continue
                
                # 현재가
                price_tag = sub_soup.select_one('.no_today .no_up') or sub_soup.select_one('.no_today .no_down')
                if not price_tag:
                    price_tag = sub_soup.select_one('.no_today')
                
                # 등락률
                rate_tag = sub_soup.select_one('#rate_area .blind') # 텍스트 추출 필요
                
                # 파싱 (네이버 페이지 구조 의존)
                # 간편하게: h2 태그 옆의 가격 정보
                price = sub_soup.select_one('p.no_today').get_text(strip=True).split(' ')[0]
                
                # 전일대비
                ex_day = sub_soup.select_one('.no_exday')
                change = ex_day.get_text(strip=True)
                
                # 상승/하락 기호
                icon = "🔺" if "상승" in str(ex_day) else "▼" if "하락" in str(ex_day) else "-"
                
                print(f"  - {name}: {price} ({icon} {change})")
                
            except:
                print(f"  - {name}: 조회 실패")

    def get_exchange_rate(self):
        """환율 조회"""
        print("\n🌍 [환율 정보]")
        url = "https://finance.naver.com/marketindex/"
        soup = self._get_soup(url)
        if not soup: return

        try:
            usd = soup.select_one('#exchangeList .on > a.head.usd > div > span.value').text
            change = soup.select_one('#exchangeList .on > a.head.usd > div > span.change').text
            direction = soup.select_one('#exchangeList .on > a.head.usd > div > span.blind').text
            
            icon = "🔺" if direction == "상승" else "▼"
            print(f"  - USD/KRW: {usd} 원 ({icon} {change})")
        except:
            print("  - 환율 파싱 실패")

    def get_news(self):
        """주요 뉴스"""
        print("\n📰 [주요 뉴스]")
        url = "https://finance.naver.com/news/news_list.naver?mode=LSS2D&sid2=259" # 시황 뉴스
        soup = self._get_soup(url)
        if not soup: return

        news_items = soup.select('.newsList li dl')
        for i, item in enumerate(news_items[:5]):
            title = item.select_one('.articleSubject a').get_text(strip=True)
            print(f"  {i+1}. {title}")

    def run(self):
        print("="*40)
        print(f"🚀 SOLAB Morning Briefing ({datetime.now().strftime('%Y-%m-%d')})")
        print("="*40)
        self.get_us_market()
        self.get_exchange_rate()
        self.get_news()
        print("="*40)

if __name__ == "__main__":
    scanner = MarketScanner()
    scanner.run()