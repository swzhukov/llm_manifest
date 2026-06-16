# Media Transcription Workflow

Source: DS | Date: 2026-06-02 | Messages: 11 | ID: 433ca401-97e1-4821-9283-e95dcd1fce1b

---

## user


**Token management:**
- Get: `curl -X POST https://bit-auth.1bitai.ru/request-token -H "Content-Type: application/json" -d '{"email":"user@email.com"}'`
- Use: `export NEWTON_TOKEN="..."` or in `.env` → `docker-compose.yml` → container env

## 🚦 Design Rules for This Project
1. **Paths**: Always use container paths (`/opt/newton-tmp/...`) in n8n nodes. Host paths (`/opt/beget/n8n/...`) are for Sprut.io/SSH only.
2. **Token**: Never hardcode. Use `process.env.NEWTON_TOKEN` or pass via Flask wrapper env.
3. **File names**: Always append `Date.now()` or `$(date +%s)` to avoid race conditions.
4. **Timeouts**: Set `timeout: 300000` (5 min) for HTTP Request nodes calling Newton (YouTube fetch can be slow).
5. **Error handling**: Log `stderr` from wrapper; show user-friendly errors in Telegram.
6. **Cleanup**: Use host CronTab (Beget panel) or container `crond` to delete `/opt/newton-tmp/*` older than 24h.

## 🛡️ Troubleshooting Matrix (Learned from Experience)
| Symptom | Root Cause | Fix |
|---|---|---|
| `404` on webhook | Undefined Traefik middleware | Remove `middlewares=n8n@docker` from labels |
| `curl: not found` in healthcheck | n8n image lacks curl | Use `wget -q --spider` instead |
| `apt-get: not found` in Dockerfile | Wrong base image (not Debian) | Use multi-stage build or install Newton on host |
| `newton: command not found` in container | Newton installed on host, not in container | Call via `docker exec` or HTTP wrapper |
| `401 Unauthorized` from Newton | Missing/invalid `NEWTON_TOKEN` | Verify token in `.env` and wrapper env |
| `Permission denied` on `/opt/newton-tmp` | Volume owned by root, container runs as `node` | `chmod 777 /opt/beget/n8n/newton-tmp` on host |
| YouTube `503` | Server IP blocked by YouTube | Use `--wait` + longer timeout; fallback to `parakeet` |
| Workflow not triggering | Not activated or webhook not registered | Toggle workflow to **Active**; test via Executions tab |

## 🤖 Agent Interaction Protocol
- **Response format**: TL;DR (1-2 sentences) → Structured details (tables/lists) → Code/JSON → Step-by-step instructions.
- **Code**: Minimal comments; explicit parameters (never rely on defaults); validate JSON before output.
- **Uncertainty**: If data is missing, state it clearly and ask ONE clarifying question.
- **Safety**: Never suggest editing production workflows without backup. Always mark placeholders (`REPLACE_*`).
- **Context awareness**: Assume Beget VPS + Sprut.io + Docker Compose. Avoid SSH-dependent steps unless unavoidable.
- **Validation**: Before outputting a workflow JSON, verify: node versions match v2.17.7, paths are container-relative, credentials are parameterized.

## 🎯 Current Task Status
✅ Infrastructure: n8n v2.17.7 running on Beget VPS, Traefik routing HTTPS, volumes mounted.  
✅ Newton CLI: Installed on host, `newton health` OK.  
✅ HTTP Wrapper: Flask API running on `127.0.0.1:8080`, accepts POST `/transcribe`.  
✅ Telegram Bot: Credential created in n8n, webhook registered via Traefik.  
⏳ Workflow: JSON imported, needs final testing with real media.  

**Next actions for LLM:**
1. Help user test the workflow with a short voice message.
2. Add error handling/logging for failed transcriptions.
3. Optional: Extend to support YouTube links (`newton fetch`) and summarization (`newton summarize`).
4. Optional: Add TTS reply (`newton tts`) for voice responses.

## 📦 Reference Snippets
**Flask wrapper (`newton-api.py`) minimal version:**
```python
#!/usr/bin/env python3
import os, subprocess, json
from flask import Flask, request, jsonify
app = Flask(__name__)
TOKEN = os.environ.get('NEWTON_TOKEN', '')

@app.route('/transcribe', methods=['POST'])
def transcribe():
    data = request.json
    file_path = data.get('file')
    engine = data.get('engine', 'v3')
    if not file_path or not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 400
    out_path = f"/tmp/out_{os.getpid()}.txt"
    cmd = ['newton', 'transcribe', file_path, '-e', engine, '-o', out_path]
    env = os.environ.copy(); env['NEWTON_TOKEN'] = TOKEN
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if res.returncode != 0:
        return jsonify({'error': res.stderr}), 500
    with open(out_path) as f: text = f.read()
    os.remove(out_path)
    return jsonify({'text': text})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

**n8n HTTP Request node config for Newton:**
```json
{
  "method": "POST",
  "url": "http://172.17.0.1:8080/transcribe",
  "sendHeaders": true,
  "headerParameters": [{ "name": "Content-Type", "value": "application/json" }],
  "sendBody": true,
  "bodyParameters": [{ "name": "file", "value": "=/opt/newton-tmp/{{ $json.fileName }}" }],
  "options": { "response": { "responseFormat": "json" } },
  "timeout": 300000
}


это всё контекст среды. сделай мне воркфлоу с такой логикой - я передаю в чат-боте либо ссылку на медиа-файл, либо сам файл, либо на потоковый сервис, типа ютуба. переданная информация транскрибируется и отдаётся обратно в чат в виде текстового файла

---

## user

на первом же узле:
Problem running workflow
Unrecognized node type: n8n-nodes-base.fileOperations

---

## user

Напиши полностью инструкцию и добавь отдельным блоком контекст среды исполнения с учётом выявленных проблем и ошибок

---

## user

ты опять ошибся: The file does not contain valid JSON data

---

## user

А зачем столько настроек? У меня же всё это есть почти - директория и т.д. и я бы хотел по минимуму пользоваться командными строками

---

## user

креды в первом узле почему-то недоступны для выбора

---

## user

я не понимаю. у меня же есть креда на бота, но тут при нажатии Set up credential выпадает не список, а новый элемент Telegram account 2

---

## user

Кликни по полю Credential в узле Telegram Trigger.
В выпадающем списке выбери нужный пункт (например, Telegram account или Telegram account 2).
Повтори то же самое для узлов Download File и Send Transcript.

Недоступно для выбора, я же говорил. Мне кажется, ты что-то со схемой накосячил

---

## user

Нет, сделай полный джейсон и перепиши весь известный тебе контекст среды исполнения для передачи ллм к будущим задачам с учётом всех выявленных проблем и твоих ошибок

---

## user

второй узел опять с ошибкой: Problem in node ‘Has File?‘
compareOperationFunctions[compareData.operation] is not a function

и перепиши весь известный тебе контекст среды исполнения для передачи ллм к будущим задачам с учётом всех выявленных проблем и твоих ошибок - желательно, единым блоком.

---

## user

Учти ещё и этот контекст в описании среды исполнения. Перепиши всё важное для постановки будущих задач любой ЛЛМ единым блоком - чтобы я по 100 раз не уточнял контекст задачи.

---

