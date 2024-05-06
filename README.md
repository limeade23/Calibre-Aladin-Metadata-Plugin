# Calibre Aladin OpenAPI Metadata Source Plugin

Aladin OpenAPI를 이용한 캘리버 메타데이터 다운로드 플러그인

## 설치 방법
1. [알라딘 OpenAPI](https://www.aladin.co.kr/ttb/wblog_manage.aspx)에서 API를 발급
2. `__init__.py` 파일을 열고 `API_KEY`에는 Open API 인증키를 입력한다.
3. `__init__.py` 파일을 압축 후 Calibre에서 플러그인을 등록한다.
4. 메타데이터 편집하기에서 메타데이터 다운로드를 클릭하면 책 정보와 책 표지를 받아오게 된다.

### 참고사항
- calibre 7.10에서 테스트되었습니다.
- 언어는 한국어로 고정되어 있습니다.
- 알라딘 카테고리가 태그로 분류됩니다.
- 사용자 리뷰 평점이 반영됩니다.
- 알라딘에서 반환된 저자의 옮긴이와 지은이는 모두 포함되어 저장됩니다.