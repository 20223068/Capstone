// 필요한 모듈 설치: express, body-parser, node-fetch, dotenv
require('dotenv').config();
const express = require('express');
const fetch = require('node-fetch');
const app = express();
app.use(express.json());

app.post('/ask', async (req, res) => {
    const { question } = req.body;

    try {
        const gptRes = await fetch("https://api.openai.com/v1/chat/completions", {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${process.env.OPENAI_API_KEY}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                model: "gpt-4",
                messages: [
                    { role: "system", content: "이건 어린이 동화 '나비의 꿈'에 대한 질문이야. 아이가 물어본 질문에 친절하고 이해하기 쉽게 대답해줘." },
                    { role: "user", content: question }
                ],
                temperature: 0.7
            })
        });

        const data = await gptRes.json();
        const answer = data.choices?.[0]?.message?.content ?? "죄송해요, 잘 모르겠어요.";
        res.json({ answer });
    } catch (error) {
        res.status(500).json({ answer: "GPT 응답 중 오류가 발생했어요." });
    }
});

app.listen(3000, () => {
    console.log('서버가 http://localhost:3000 에서 실행 중');
});
