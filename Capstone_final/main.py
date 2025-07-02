import app_emb_gpt
import insert_story_chunks
import embed_story_chunks

import webbrowser
import time
import threading

def open_browser():
    time.sleep(2)  # 서버가 켜질 시간을 약간 줌
    webbrowser.open("http://127.0.0.1:5000/story")

if __name__ == "__main__":
    insert_story_chunks.run()
    embed_story_chunks.run()
    threading.Thread(target=open_browser).start()
    app_emb_gpt.app.run(debug=True)