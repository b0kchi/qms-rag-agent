# txt 파일의 바이트 데이터를 문자열로 안전하게 변환하는 함수
'''
    TXT 파일은 내부적으로 바이트(binary)로 저장돼 있다.
    문자를 읽으려면 바이트를 디코딩해야 한다. 
'''
def extract_text_from_txt_bytes(data: bytes) -> str:
    try:
        return data.decode("utf-8").strip() # 바이트를 utf-8 방식으로 디코딩
    except UnicodeDecodeError: # 디코딩 실패 에러
        return data.decode("cp949", errors="ignore").strip() # erros="ignore": 깨지는 문자가 있을 시 문제되는 문자를 무시한다.