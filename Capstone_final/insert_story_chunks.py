# from bs4 import BeautifulSoup
# import pymysql

# # [1] HTML 파일에서 슬라이드 문단 추출
# with open("templates/ButterflyDream.html", "r", encoding="utf-8") as f:
#     soup = BeautifulSoup(f, "html.parser")

# slides = soup.select("div.story-slide")  # 여기만 바뀜!
# chunks = []

# for slide in slides:
#     text = slide.get_text(separator=" ", strip=True)
#     if text:
#         chunks.append(text)

# print(f"✔ 슬라이드 수: {len(slides)}")
# print(f"✔ 저장할 문단 수: {len(chunks)}")

# # [2] DB에 저장
# conn = pymysql.connect(
#     host="localhost",
#     user="root",
#     password="1234",
#     db="fairy_db",
#     charset="utf8mb4",
#     cursorclass=pymysql.cursors.DictCursor
# )
# cursor = conn.cursor()

# cursor.execute("DELETE FROM story_chunks")

# for chunk in chunks:
#     cursor.execute("INSERT INTO story_chunks (chunk_text) VALUES (%s)", (chunk,))

# conn.commit()
# conn.close()

# print(f"🎉 완료! {len(chunks)}개의 문단이 story_chunks 테이블에 저장되었습니다.")

from bs4 import BeautifulSoup
import pymysql

def run():
    # [1] HTML 파일에서 슬라이드 문단 추출
    with open("templates/ButterflyDream.html", "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    slides = soup.select("div.story-slide")  # 여기만 바뀜!
    chunks = []

    for slide in slides:
        text = slide.get_text(separator=" ", strip=True)
        if text:
            chunks.append(text)

    print(f"✔ 슬라이드 수: {len(slides)}")
    print(f"✔ 저장할 문단 수: {len(chunks)}")

    # [2] DB에 저장
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="1234",
        db="fairy_db",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )
    cursor = conn.cursor()

    cursor.execute("DELETE FROM story_chunks")

    for chunk in chunks:
        cursor.execute("INSERT INTO story_chunks (chunk_text) VALUES (%s)", (chunk,))

    conn.commit()
    conn.close()

    print(f"🎉 완료! {len(chunks)}개의 문단이 story_chunks 테이블에 저장되었습니다.")