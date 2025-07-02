import os
import json
import pymysql
import numpy as np
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from sentence_transformers import SentenceTransformer
from openai import OpenAI

from gtts import gTTS
from flask import send_file
import io
from io import BytesIO

from collections import defaultdict, Counter
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from sklearn.cluster import DBSCAN
import random

app = Flask(__name__, template_folder="templates")
CORS(app)

# DB 연결
connection = pymysql.connect(
    host='127.0.0.1',
    port=3306,
    user='root',
    password='1234',
    db='fairy_db',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)
cursor = connection.cursor()

# 임베딩 모델 로딩
model = SentenceTransformer("all-MiniLM-L6-v2")

# LM Studio 클라이언트 설정
client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio"  # 아무 문자열
)

# 코사인 유사도
def cosine_similarity(vec1, vec2):
    v1, v2 = np.array(vec1), np.array(vec2)
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))

# 질문 저장
def save_question(text, slide_index):
    try:
        page_num = slide_index + 1  # ✅ HTML상 페이지 번호와 맞추기 위한 보정
        cursor.execute("INSERT INTO questions (questions, page_num) VALUES (%s, %s)", (text, page_num))
        connection.commit()
        return cursor.lastrowid
    except Exception as e:
        print("❌ 질문 저장 오류:", e)
        return None

# 질문 임베딩 저장
def save_question_embedding(qid, embedding):
    try:
        cursor.execute("INSERT INTO question_embeddings (question_id, embedding) VALUES (%s, %s)", (qid, json.dumps(embedding)))
        connection.commit()
    except Exception as e:
        print("❌ 질문 임베딩 저장 오류:", e)

# 답변 저장
def save_answer(qid, answer):
    try:
        cursor.execute("INSERT INTO answers (question_id, answers) VALUES (%s, %s)", (qid, answer))
        connection.commit()
    except Exception as e:
        print("❌ 답변 저장 오류:", e)

# 유사 질문 찾기
def find_similar_question(embedding):
    cursor.execute("SELECT question_id, embedding FROM question_embeddings")
    best_score, best_id = 0, None
    for row in cursor.fetchall():
        e = json.loads(row['embedding'])
        score = cosine_similarity(embedding, e)
        if score > best_score:
            best_score, best_id = score, row['question_id']
    return best_id if best_score > 0.9 else None

# 해당 질문의 답변 가져오기
def get_answer_by_question_id(qid):
    cursor.execute("SELECT answers FROM answers WHERE question_id = %s", (qid,))
    row = cursor.fetchone()
    return row["answers"] if row else None

# story_chunks에서 유사 문단 찾기
def find_relevant_story_chunks(embedding, top_n=3):
    cursor.execute("SELECT id, chunk_text, embedding FROM story_chunks WHERE embedding IS NOT NULL")
    chunks = cursor.fetchall()
    scored = []
    for row in chunks:
        chunk_emb = json.loads(row["embedding"])
        score = cosine_similarity(embedding, chunk_emb)
        scored.append((score, row["chunk_text"]))
    scored.sort(reverse=True, key=lambda x: x[0])
    return [chunk for _, chunk in scored[:top_n]]

# GPT에게 답변 요청
def get_gpt_answer_with_context(question, context_chunks):
    story_context = "\n".join(context_chunks)
    messages = [
        {"role": "system", "content": f"이건 어린이 동화에 대한 질문이야. 아래 내용을 참고해서 아이가 이해하기 쉽고 따뜻하게 대답해줘:\n\n{story_context}"},
        {"role": "user", "content": question}
    ]
    try:
        response = client.chat.completions.create(
            model="openhermes-2.5-mistral-7b",                 #"mathstral-7b-v0.1",  # LM Studio 실행 중인 모델 이름
            messages=messages,
            temperature=0.7,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("❌ GPT 응답 오류:", e)
        return "GPT 답변을 가져오는 중 오류가 발생했습니다."

# 페이지별 질문 Top 3 클러스터 대표 질문 추출
def get_top3_questions_by_page(page_num):
    # 1. 해당 페이지의 질문과 임베딩 조회
    cursor.execute("""
        SELECT q.id, q.questions, qe.embedding
        FROM questions q
        JOIN question_embeddings qe ON q.id = qe.question_id
        WHERE q.page_num = %s
    """, (page_num,))
    rows = cursor.fetchall()

    if not rows:
        return []
    
    # 질문이 1개뿐이면 그냥 반환
    if len(rows) == 1:
        return [{"question": rows[0]['questions'], "count": 1}]

    embeddings = [json.loads(row['embedding']) for row in rows]
    questions = [row['questions'] for row in rows]

    # 2D 배열로 변환 (질문이 1개여도 안전하게 처리)
    embeddings = np.array(embeddings).reshape(-1, len(embeddings[0]))

    # 2. 클러스터링 (1개만 있어도 클러스터 인정)
    clustering = DBSCAN(eps=0.4, min_samples=1, metric='cosine').fit(embeddings)
    labels = clustering.labels_

    # 3. 클러스터별 대표 질문 추출
    cluster_map = defaultdict(list)
    for label, q in zip(labels, questions):
        if label != -1:
            cluster_map[label].append(q)

    cluster_counts = sorted(cluster_map.items(), key=lambda x: len(x[1]), reverse=True)
    top_questions = []

    # 대표 질문 추출
    for _, qs in cluster_counts[:3]:
        representative = Counter(qs).most_common(1)[0][0]
        top_questions.append({"question": representative, "count": len(qs)})

    # 4. 클러스터가 3개 미만이면, 나머지는 임의 질문으로 채우기
    if len(top_questions) < 3:
        remaining = 3 - len(top_questions)
        used_questions = set(q['question'] for q in top_questions)
        remaining_pool = [q for q in questions if q not in used_questions]
        random.shuffle(remaining_pool)
        for q in remaining_pool[:remaining]:
            top_questions.append({"question": q, "count": 1})

    return top_questions


# 질문 API
@app.route('/ask', methods=['POST'])
def ask():
    try:
        data = request.get_json()
        question = data.get("question")
        slide_index = data.get("slide_index")

        if not question:
            return jsonify({"error": "질문이 없습니다."}), 400

        if not question:
            return jsonify({"error": "질문이 없습니다."}), 400

        # 1. 질문 임베딩
        q_embedding = model.encode(question).tolist()

        # 2. 유사 질문 확인
        similar_id = find_similar_question(q_embedding)
        if similar_id:
            answer = get_answer_by_question_id(similar_id)
            qid = save_question(question, slide_index)
            if qid:
                save_question_embedding(qid, q_embedding)
                save_answer(qid, answer)
            return jsonify({"question": question, "answer": answer})

        # 3. 관련 문단 추출
        context_chunks = find_relevant_story_chunks(q_embedding)

        # 4. GPT로 답변 생성
        answer = get_gpt_answer_with_context(question, context_chunks)

        # 5. 저장
        qid = save_question(question, slide_index)
        if qid:
            save_question_embedding(qid, q_embedding)
            save_answer(qid, answer)

        return jsonify({"question": question, "answer": answer})

    except Exception as e:
        print("❌ /ask 처리 오류:", e)
        return jsonify({"error": "서버 오류 발생"}), 500

@app.route("/story", methods=["GET"])
def index():
    return render_template("ButterflyDream.html")

@app.route("/")
def home():
    return "<h2>Hello! Go to <a href='/story'>/story</a></h2>"

@app.route("/tts", methods=["POST"])
def tts():
    try:
        data = request.get_json()
        text = data.get("text")
        print("📩 클라이언트에서 받은 TTS 텍스트:", text)  # ✅ 추가

        if not text:
            return jsonify({"error": "텍스트가 없습니다."}), 400

        tts = gTTS(text, lang='ko')
        mp3_fp = BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)

        return send_file(mp3_fp, mimetype="audio/mpeg")

    except Exception as e:
        print("❌ /tts 처리 오류:", e)
        return jsonify({"error": "TTS 오류 발생"}), 500

@app.route("/top3_questions", methods=["GET"])
def top3_questions():
    page_num = request.args.get("page", type=int)
    if page_num is None:
        return jsonify({"error": "page 번호가 필요합니다."}), 400

    top_questions = get_top3_questions_by_page(page_num)
    return jsonify(top_questions)


if __name__ == '__main__':
    app.run(debug=True)