# Ошибка сборки Docker с apt-get

Source: QW | Date: 2026-05-27 | Fragments: 2 | ID: fe75827e-b522-4d47-96a2-4854b5cb92ce

---

## USER

Выведи всё содержимое

---

## AI

Вот полное содержимое из скриншота вашего терминала:

```bash
root@wvumvyucks:/opt/bget/n8n# docker compose build --no-cache
[+] Building 2.5s (9/12)
 => [internal] load local bake definitions                                                                              0.0s
 => => reading from stdin                                                                                               0.0s
 => [n8n-worker internal] load build definition from dockerfile                                                         0.0s
 => => transferring dockerfile: 847B                                                                                    0.0s
 => [n8n internal] load metadata for docker.io/n8nio/n8n:2.17.7                                                         0.0s
 => [n8n-worker internal] load .dockerignore                                                                            0.0s
 => => transferring context: 2B                                                                                         0.0s
 => CACHED [n8n stage-1 1/5] FROM docker.io/n8nio/n8n:2.17.7@sha256:a293b89bac876872a0c1ef0fbbb7ce056aa2d215f62917acf   0.0s
 => CACHED [n8n stage-1 2/5] FROM docker.io/library/alpine:3.19@sha256:6baf43584cb78f2e5847d1de515f23499913ac9f12bdf834  0.0s
 => [n8n-worker builder 2/2] RUN apk add --no-cache curl && curl -sL https://gitlab.com/fadeyev1/newton-cli/            0.0s
 => CANCELED [n8n-worker builder 2/2] RUN apk add --no-cache curl && curl -sL https://gitlab.com/fadeyev1/newton-cli/   0.9s
 => ERROR [n8n stage-1 2/5] RUN apt-get update && apt-get install -y --no-install-recommends python3 cron && apt-get clean && rm -rf /var/lib/apt/lists/*    0.9s
0.700 /bin/sh: apt-get: not found

[+] Building 0/2
 ✗ Image n8n-n8n-worker Building                                                                                        2.6s
 ✗ Image n8n-n8n-worker Building                                                                                        2.6s
dockerfile:13
--------------------
  12 |       # Install Python 3 (required for newton CLI) + cron for cleanup
  13 |       >>> RUN apt-get update && apt-get install -y --no-install-recommends python3 cron && \
  14 |       >>>     apt-get clean && rm -rf /var/lib/apt/lists/*
--------------------
target n8n: failed to solve: process "/bin/sh -c apt-get update && apt-get install -y --no-install-recommends python3 cron && apt-get clean && rm -rf /var/lib/apt/lists/*" did not complete successfully: exit code: 127
```

### Комментарий к ошибке:
Судя по логу, основная проблема скрывается в блоке `ERROR`. Вы используете базовый образ **Alpine** (строка `CACHED ... docker.io/library/alpine:3.19`), но пытаетесь установить пакеты через **apt-get** (команда для Ubuntu/Debian).

**Решение:** Вам нужно заменить в Dockerfile `apt-get update && apt-get install ...` на `apk add --no-cache python3 cron`, так как в Alpine используется менеджер пакетов `apk`.

---

