# from sentence_transformers import SentenceTransformer
# import pymysql
# import json

# # 1. 모델 로딩
# model = SentenceTransformer("all-MiniLM-L6-v2")
# print("✅ 임베딩 모델 로딩 완료!")

# # 2. DB 연결
# conn = pymysql.connect(
#     host="localhost",
#     user="root",
#     password="1234",
#     db="fairy_db",
#     charset="utf8mb4",
#     cursorclass=pymysql.cursors.DictCursor
# )
# cursor = conn.cursor()

# # 3. 임베딩이 비어 있는 문단 가져오기
# cursor.execute("SELECT id, chunk_text FROM story_chunks WHERE embedding IS NULL")
# chunks = cursor.fetchall()

# print(f"🔍 임베딩할 문단 수: {len(chunks)}")

# # 4. 임베딩 수행 + DB 저장
# for chunk in chunks:
#     emb = model.encode(chunk["chunk_text"]).tolist()  # numpy → list 변환
#     emb_json = json.dumps(emb)

#     cursor.execute(
#         "UPDATE story_chunks SET embedding = %s WHERE id = %s",
#         (emb_json, chunk["id"])
#     )

# conn.commit()
# conn.close()

# print("🎉 모든 문단 임베딩이 완료되어 DB에 저장되었습니다.")

from sentence_transformers import SentenceTransformer
import pymysql
import json

def run():
    # 1. 모델 로딩
    model = SentenceTransformer("all-MiniLM-L6-v2")
    print("✅ 임베딩 모델 로딩 완료!")

    # 2. DB 연결
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="1234",
        db="fairy_db",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )
    cursor = conn.cursor()

    # 3. 임베딩이 비어 있는 문단 가져오기
    cursor.execute("SELECT id, chunk_text FROM story_chunks WHERE embedding IS NULL")
    chunks = cursor.fetchall()

    print(f"🔍 임베딩할 문단 수: {len(chunks)}")

    # 4. 임베딩 수행 + DB 저장
    for chunk in chunks:
        emb = model.encode(chunk["chunk_text"]).tolist()  # numpy → list 변환
        emb_json = json.dumps(emb)

        cursor.execute(
            "UPDATE story_chunks SET embedding = %s WHERE id = %s",
            (emb_json, chunk["id"])
        )

    conn.commit()
    conn.close()

    print("🎉 모든 문단 임베딩이 완료되어 DB에 저장되었습니다.")