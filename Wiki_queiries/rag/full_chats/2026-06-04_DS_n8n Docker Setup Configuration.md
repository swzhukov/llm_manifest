# n8n Docker Setup Configuration

Source: DS | Date: 2026-06-04 | Messages: 6 | ID: 19314611-31ad-419b-8e79-c5248d558b39

---

## user

Давай продолжим разговор, который начали в файле во вложении. 
Давай всегда полностью текст файлов, а не "вставь" - чтобы я полностью скопировал и вставил, а не искал секции. Полные тексты у тебя есть в контексте:

volumes:
  traefik_data:
    driver: local-persist
    driver_opts:
      mountpoint: /opt/beget/n8n/traefik_data
  n8n_storage:
    driver: local-persist
    driver_opts:
      mountpoint: /opt/beget/n8n/n8n_storage
  db_storage:
    driver: local-persist
    driver_opts:
      mountpoint: /opt/beget/n8n/db_storage
  redis_storage:
    driver: local-persist
    driver_opts:
      mountpoint: /opt/beget/n8n/redis_storage
  newton_tmp:
    driver: local-persist
    driver_opts:
      mountpoint: /opt/beget/n8n/newton-tmp

x-shared: &shared
  restart: always
  image: docker.n8n.io/n8nio/n8n:2.17.7
  env_file: .env
  environment:
    - NEWTON_TOKEN=${NEWTON_TOKEN}
    - N8N_USER_FOLDER=/home/node/.n8n
    - GENERIC_TIMEZONE=Europe/Moscow
  links:
    - postgres
    - redis
  volumes:
    - n8n_storage:/home/node/.n8n
    - newton_tmp:/opt/newton-tmp
    - ./healthcheck.js:/healthcheck.js:ro
  depends_on:
    redis:
      condition: service_healthy
    postgres:
      condition: service_healthy

services:
  traefik:
    image: traefik:3.6.5
    restart: always
    command:
      - "--api=true"
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.web.http.redirections.entryPoint.to=websecure"
      - "--entrypoints.web.http.redirections.entrypoint.scheme=https"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.mytlschallenge.acme.tlschallenge=true"
      - "--certificatesresolvers.mytlschallenge.acme.email=Swzhukov@gmail.com"
      - "--certificatesresolvers.mytlschallenge.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - traefik_data:/letsencrypt
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - n8n_net

  postgres:
    image: postgres:16
    restart: always
    env_file: .env
    volumes:
      - db_storage:/var/lib/postgresql/data
      - ./init-data.sh:/docker-entrypoint-initdb.d/init-data.sh:ro
    ports:
      - 127.0.0.1:5432:5432
    healthcheck:
      test: ['CMD-SHELL', 'pg_isready -h localhost -U ${POSTGRES_USER} -d ${POSTGRES_DB}']
      interval: 5s
      timeout: 5s
      retries: 10
    networks:
      - n8n_net

  redis:
    image: redis:6-alpine
    restart: always
    volumes:
      - redis_storage:/data
    healthcheck:
      test: ['CMD', 'redis-cli', 'ping']
      interval: 5s
      timeout: 5s
      retries: 10
    networks:
      - n8n_net

  n8n:
    <<: *shared
    container_name: n8n-n8n-1
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.n8n.rule=Host(`seefeesnahurid.beget.app`)"
      - "traefik.http.routers.n8n.entrypoints=websecure"
      - "traefik.http.routers.n8n.tls=true"
      - "traefik.http.routers.n8n.tls.certresolver=mytlschallenge"
      - "traefik.http.services.n8n.loadbalancer.server.port=5678"
    ports:
      - 127.0.0.1:5678:5678
    healthcheck:
      test: ["CMD-SHELL", "wget -q --spider http://localhost:5678/healthz || exit 0"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 90s
    networks:
      - n8n_net

  n8n-worker:
    <<: *shared
    container_name: n8n-n8n-worker-1
    command: worker
    depends_on:
      - n8n
    healthcheck:
      test: ["CMD-SHELL", "wget -q --spider http://localhost:5678/healthz || exit 0"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - n8n_net

networks:
  n8n_net:
    driver: bridge
    name: n8n_net

---

## user

И имей в виду, что я стараюсь по минимуму пользоваться терминалам и пользуюсь файловым менеджером Beget - SPRUT.io.

---

## user

Дай полный json для моего воркфлоу

---

## user

# Активация автозапуска Flask через systemd
systemctl daemon-reload
systemctl enable newton-api
systemctl restart newton-apiroot@wxvwmvycks:~#
root@wxvwmvycks:~# # Применение изменений в Docker
root@wxvwmvycks:~# cd /opt/beget/n8n
root@wxvwmvycks:/opt/beget/n8n# docker-compose up -d
[+] up 5/5
 ✔ Container n8n-redis-1      Healthy                                                                               4.4s
 ✔ Container n8n-traefik-1    Running                                                                               0.0s
 ✔ Container n8n-n8n-worker-1 Started                                                                              10.1s
 ✔ Container n8n-postgres-1   Healthy                                                                               7.5s
 ✔ Container n8n-n8n-1        Started                                                                               7.2s
root@wxvwmvycks:/opt/beget/n8n#
root@wxvwmvycks:/opt/beget/n8n# # Активация автозапуска Flask через systemd
root@wxvwmvycks:/opt/beget/n8n# systemctl daemon-reload
root@wxvwmvycks:/opt/beget/n8n# systemctl enable newton-api
Failed to enable unit: Unit file newton-api.service does not exist.
root@wxvwmvycks:/opt/beget/n8n# systemctl restart newton-api
Failed to restart newton-api.service: Unit newton-api.service not found.
root@wxvwmvycks:/opt/beget/n8n#

и дай полный json для моего воркфлоу

---

## user

root@wxvwmvycks:/opt/beget/n8n# cat > /etc/systemd/system/newton-api.service << 'EOF'
> [Unit]
> Description=Newton Flask Wrapper
> After=network.target
>
> [Service]
> Type=simple
> User=root
> WorkingDirectory=/opt/beget/n8n
> Environment="NEWTON_TOKEN=r-Tt-qYR9-IGhqW7Saaao46V0o8aV9LCVRHmn1-LNQU"
> EnvironmentFile=/opt/beget/n8n/.env
> ExecStart=/usr/bin/python3 /opt/beget/n8n/newton-api.py
> Restart=always
> RestartSec=5
>
> [Install]
> WantedBy=multi-user.target
> EOF

systemctl daemon-reload
systemctl enable newton-api
sysroot@wxvwmvycks:/opt/beget/n8n#
root@wxvwmvycks:/opt/beget/n8n# systemctl daemon-reload
temctl start newton-api
systemctl status newton-api --no-pagerroot@wxvwmvycks:/opt/beget/n8n# systemctl enable newton-api
root@wxvwmvycks:/opt/beget/n8n# systemctl start newton-api
root@wxvwmvycks:/opt/beget/n8n# systemctl status newton-api --no-pager
● newton-api.service - Newton Flask Wrapper
     Loaded: loaded (/etc/systemd/system/newton-api.service; enabled; preset: enabled)
     Active: active (running) since Thu 2026-06-04 07:35:14 UTC; 4min 54s ago
   Main PID: 1865041 (python3)
      Tasks: 1 (limit: 2315)
     Memory: 24.7M (peak: 24.9M)
        CPU: 354ms
     CGroup: /system.slice/newton-api.service
             └─1865041 /usr/bin/python3 /opt/beget/n8n/newton-api.py

Jun 04 07:35:14 wxvwmvycks systemd[1]: Started newton-api.service - Newton Flask Wrapper.
Jun 04 07:35:14 wxvwmvycks python3[1865041]:  * Tip: There are .env or .flaskenv files present. Do "pip install …e them.
Jun 04 07:35:14 wxvwmvycks python3[1865041]:  * Serving Flask app 'newton-api'
Jun 04 07:35:14 wxvwmvycks python3[1865041]:  * Debug mode: off
Jun 04 07:35:14 wxvwmvycks python3[1865041]: WARNING: This is a development server. Do not use it in a productio…nstead.
Jun 04 07:35:14 wxvwmvycks python3[1865041]:  * Running on all addresses (0.0.0.0)
Jun 04 07:35:14 wxvwmvycks python3[1865041]:  * Running on http://127.0.0.1:8080
Jun 04 07:35:14 wxvwmvycks python3[1865041]:  * Running on http://217.114.7.5:8080
Jun 04 07:35:14 wxvwmvycks python3[1865041]: Press CTRL+C to quit
Hint: Some lines were ellipsized, use -l to show in full.
root@wxvwmvycks:/opt/beget/n8n#

И обрати внимание на все инструкции, которые есть в проекте и во всём контексте этой беседы и той, что во вложении

---

## user

Сформулируй правильный запрос к тебя, чтобы сразу получить последнее решение. Пусть включается цель решения (зачем оно нужно) т.е. стратегический уровень и тактический (как это решать).

---

