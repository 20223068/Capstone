CREATE DATABASE IF NOT EXISTS fairy_db;
USE fairy_db;

-- 질문 테이블 --
CREATE TABLE questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    questions TEXT,
    page_num INT
);

-- 답변 테이블 --
CREATE TABLE answers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    question_id INT,
    answers TEXT,
    FOREIGN KEY (question_id) REFERENCES questions(id)
);

-- 질문 임베딩 테이블 --
CREATE TABLE question_embeddings (
    question_id INT PRIMARY KEY,
    embedding JSON,
    FOREIGN KEY (question_id) REFERENCES questions(id)
);

-- 동화 문단 나누는 테이블 --
CREATE TABLE story_chunks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    chunk_text TEXT NOT NULL,
    embedding JSON DEFAULT NULL
);