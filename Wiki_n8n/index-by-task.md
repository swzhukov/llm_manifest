# Оглавление по типу задачи

Ищи не по порядку, а по тому, что именно ты сейчас делаешь.

## 🚀 Установка / деплой

- Хочу n8n на своём сервере одной командой → [01-installation.md §1.1](01-installation.md)
- Хочу n8n + Supabase + Flowise + Caddy + ComfyUI на одном сервере → [01-installation.md §1.3](01-installation.md)
- Обновление с сохранением данных → [01-installation.md §1.4](01-installation.md)
- Восстановление из бэкапа → [01-installation.md §1.5](01-installation.md)
- Платежи, домены, нюансы Beget → [01-installation.md §1.6](01-installation.md)

## 🧱 Строю воркфлоу

- Не понимаю разницу между триггером и экшеном → [02-interface-and-nodes.md §2.2](02-interface-and-nodes.md)
- Какие триггеры использовать для типовых задач → [02-interface-and-nodes.md §2.3](02-interface-and-nodes.md)
- IF-каскад: как не превратить workflow в спагетти → [02-interface-and-nodes.md §2.4](02-interface-and-nodes.md)
- Хочу сохранять состояние между запусками (память бота) → [06-vector-memory-rag.md](06-vector-memory-rag.md)
- Sticky Notes — зачем и как → [02-interface-and-nodes.md §2.5](02-interface-and-nodes.md)

## 🤖 Telegram-бот

- Завести бота через BotFather → [07-telegram-bots.md §7.1](07-telegram-bots.md)
- Inline-кнопки + callback_data → [07-telegram-bots.md §7.2](07-telegram-bots.md)
- Бот в групповом чате (user-bot, polling) → [07-telegram-bots.md §7.4](07-telegram-bots.md)
- Webhook vs polling — что выбрать → [07-telegram-bots.md §7.3](07-telegram-bots.md)
- Голосовой ввод (транскрибация) → [07-telegram-bots.md §7.5](07-telegram-bots.md)
- Отправить фото как альбом (media group) → [10-common-errors.md §10.10](10-common-errors.md)

## 🧠 Память и RAG

- Бот должен помнить контекст диалога → [06-vector-memory-rag.md §6.1](06-vector-memory-rag.md)
- Бот должен отвечать на вопросы по документам → [06-vector-memory-rag.md §6.2](06-vector-memory-rag.md)
- Чанки, overlap, размер → [06-vector-memory-rag.md §6.3](06-vector-memory-rag.md)
- Metadata filtering: как не свалить все документы в кучу → [06-vector-memory-rag.md §6.4](06-vector-memory-rag.md)

## 💰 LLM-экономика

- YandexGPT дёшево и на русском → [08-yandex-gpt.md](08-yandex-gpt.md)
- Считаем токены и расходы → [09-ai-agents.md §9.4](09-ai-agents.md)
- Temperature для фактологических ответов → [09-ai-agents.md §9.2](09-ai-agents.md)
- Бесплатные модели в роутере нестабильны → [10-common-errors.md §10.5](10-common-errors.md)

## 🛠 AI Agent

- Базовая сборка AI Agent + Chat Model + Memory → [09-ai-agents.md §9.1](09-ai-agents.md)
- Tool (support tool) для RAG-поиска → [09-ai-agents.md §9.3](09-ai-agents.md)
- Системный промпт для техподдержки → [12-system-prompts.md §12.1](12-system-prompts.md)
- Системный промпт для SEO-копирайтера → [12-system-prompts.md §12.2](12-system-prompts.md)

## 💾 Хранилище (Supabase / Postgres)

- Создать таблицу через SQL → [05-supabase.md §5.2](05-supabase.md)
- Включить векторное расширение → [05-supabase.md §5.3](05-supabase.md)
- Postgres-нода в n8n vs Supabase SQL Editor → [10-common-errors.md §10.7](10-common-errors.md)
- Хранение истории чата для бота → [06-vector-memory-rag.md §6.1](06-vector-memory-rag.md)

## ❌ Упало / не работает

- 500 / «lost connection to server» → [10-common-errors.md §10.1](10-common-errors.md)
- AI Agent: «too many requests from you» → [10-common-errors.md §10.5](10-common-errors.md)
- Telegram: «chat not found» → [10-common-errors.md §10.8](10-common-errors.md)
- YandexGPT не подключается → [10-common-errors.md §10.6](10-common-errors.md)
- Бот не видит сообщения в групповом чате → [10-common-errors.md §10.9](10-common-errors.md)
- Обновление стёрло .env → [10-common-errors.md §10.3](10-common-errors.md)
- Возвращается HTML вместо JSON (санкции) → [10-common-errors.md §10.2](10-common-errors.md)

## 🧹 Best practice / экономия

- Диск забит за неделю — что делать → [11-best-practices.md §11.1](11-best-practices.md)
- Save vs Don't Save для executions → [11-best-practices.md §11.2](11-best-practices.md)
- Workflow 24/7 на бесплатной версии → [10-common-errors.md §10.11](10-common-errors.md)
- Папки и теги для организации → [11-best-practices.md §11.3](11-best-practices.md)
