# PRD: RAG для документации Volta Banking

**Версия:** 1.0  
**Дата:** 2026-04-01  
**Автор:** Data Analytics Team  
**Статус:** Draft

---

## 📋 Summary

| Поле | Значение |
|------|----------|
| **Проект** | RAG для документации Volta Banking |
| **Тип** | Internal Tool |
| **Приоритет** | High |
| **Срок MVP** | 4 недели |
| **Владелец** | Data Analytics Team |

---

## 🎯 Problem Statement

### Current State

Команда Volta Banking сталкивается с проблемами поиска информации:

1. **Документация разрознена** — метрики, процессы, определения хранятся в разных местах (Notion, Google Docs, Slack)
2. **Поиск неэффективен** — keyword search находит нерелевантные документы
3. **Онбординг новых сотрудников** — занимает 2-3 недели на изучение документации
4. **Потеря контекста** — одни и те же термины используются по-разному

### Problem Evidence

| Метрика | Значение | Источник |
|---------|----------|----------|
| Время поиска информации | 15-30 мин/день на сотрудника | Internal survey |
| % успешных поисковых запросов | ~60% | Notion analytics |
| Время онбординга | 2-3 недели | HR metrics |
| Дублирование документации | ~25% документов | Content audit |

---

## 🎯 Goals

### Must Have (MVP)

1. **Единый поиск** — поиск по всей документации через один интерфейс
2. **Точные ответы** — не просто ссылки, а конкретные ответы на вопросы
3. **Источники** — всегда указывать источник ответа (документ, раздел)
4. **Безопасность** — доступ только к документации уровня пользователя

### Should Have (V2)

1. **История запросов** — сохранение и поиск по прошлым вопросам
2. **Обратная связь** — thumbs up/down для оценки качества ответов
3. **Интеграции** — Slack, Notion, Google Docs

### Won't Have (Out of Scope)

1. **Генерация новой документации** — только поиск по существующей
2. **Изменение прав доступа** — использование существующих permissions
3. **Мобильное приложение** — только web-интерфейс

---

## 👥 User Stories

### Persona 1: Новый менеджер продукта

**Имя:** Анна, 28 лет  
**Роль:** Product Manager (новый в компании)  
**Цель:** Быстро найти определения метрик и процессы

**User Stories:**
- Как новый PM, я хочу быстро найти определение "MAU" и "Retention", чтобы понимать отчеты
- Как новый PM, я хочу узнать процесс запуска A/B теста, чтобы запланировать эксперимент
- Как новый PM, я хочу найти последние результаты онбординг-анализа, чтобы подготовить презентацию

**Acceptance Criteria:**
- Ответ на вопрос "Что такое MAU?" находится за <5 секунд
- Ответ содержит ссылку на источник (документ + раздел)
- Ответ включает формулу расчета, если применимо

---

### Persona 2: Аналитик данных

**Имя:** Никита, 30 лет  
**Роль:** Data Analyst  
**Цель:** Найти прошлые анализы и SQL запросы

**User Stories:**
- Как аналитик, я хочу найти SQL запрос для расчета cohort retention, чтобы не писать с нуля
- Как аналитик, я хочу найти прошлый анализ воронки, чтобы сравнить с текущими данными
- Как аналитик, я хочу узнать, какие метрики используются в дашборде CEO, чтобы подготовить данные

**Acceptance Criteria:**
- Поиск по коду (SQL, Python) работает корректно
- Найденные запросы можно скопировать в один клик
- Указана дата последнего обновления запроса

---

### Persona 3: Разработчик

**Имя:** Максим, 25 лет  
**Роль:** Backend Developer  
**Цель:** Найти API документацию и процессы деплоя

**User Stories:**
- Как разработчик, я хочу найти документацию по внутреннему API, чтобы интегрировать новый сервис
- Как разработчик, я хочу узнать процесс деплоя на production, чтобы выкатить фичу
- Как разработчик, я хочу найти контакты ответственных за сервис, чтобы задать вопрос

**Acceptance Criteria:**
- API документация включает примеры запросов/ответов
- Процессы описаны пошагово с ссылками на инструменты
- Контакты актуальны (проверка даты обновления)

---

## 🏗️ System Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────────────┐
│                    RAG SYSTEM                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐   │
│  │   Sources    │     │   Indexing   │     │   Query      │   │
│  │              │     │   Pipeline   │     │   Engine     │   │
│  │ • Notion     │────▶│              │────▶│              │   │
│  │ • Google Docs│     │ • Chunking   │     │ • Retrieval  │   │
│  │ • Slack      │     │ • Embeddings │     │ • Reranking  │   │
│  │ • Confluence │     │ • Vector DB  │     │ • Generation │   │
│  └──────────────┘     └──────────────┘     └──────────────┘   │
│                                                │                │
│                                                ▼                │
│                                         ┌──────────────┐       │
│                                         │   Response   │       │
│                                         │              │       │
│                                         │ • Answer     │       │
│                                         │ • Sources    │       │
│                                         │ • Confidence │       │
│                                         └──────────────┘       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Components

| Component | Technology | Description |
|-----------|------------|-------------|
| **Data Sources** | Notion API, Google Drive API, Slack API | Источники документации |
| **Chunking** | LangChain / LlamaIndex | Разбиение документов на chunks |
| **Embeddings** | Voyage AI / OpenAI | Векторное представление текста |
| **Vector DB** | Pinecone / Chroma | Хранение и поиск эмбеддингов |
| **Retrieval** | Hybrid (Vector + BM25) | Поиск релевантных chunks |
| **Reranking** | Cohere Rerank / Jina | Уточнение релевантности |
| **Generation** | Claude Sonnet 4.6 | Генерация ответов с контекстом |
| **Backend** | FastAPI / Flask | API сервер |
| **Frontend** | React / Streamlit | Web интерфейс |

---

## 📊 Data Model

### Document Schema

```python
class Document(BaseModel):
    id: str  # Уникальный ID
    source: str  # notional, google_docs, slack, confluence
    source_url: str  # Ссылка на оригинал
    title: str  # Заголовок документа
    content: str  # Полный текст
    chunks: List[Chunk]  # Разбиение на chunks
    metadata: DocumentMetadata
    created_at: datetime
    updated_at: datetime
    embeddings_version: str  # Версия модели эмбеддингов


class DocumentMetadata(BaseModel):
    author: str  # Автор документа
    last_modified_by: str  # Кто последний редактировал
    tags: List[str]  # Теги/категории
    access_level: str  # public, internal, confidential
    department: List[str]  # Какие отделы имеют доступ
    language: str  # ru, en


class Chunk(BaseModel):
    id: str  # Уникальный ID чанка
    document_id: str  # Ссылка на документ
    chunk_index: int  # Порядок в документе
    content: str  # Текст чанка
    embedding: List[float]  # Векторное представление
    metadata: ChunkMetadata


class ChunkMetadata(BaseModel):
    start_char: int  # Позиция начала в документе
    end_char: int  # Позиция конца
    section_title: str  # Заголовок секции
    page_number: int  # Номер страницы (если есть)
    has_table: bool  # Содержит ли таблицу
    has_code: bool  # Содержит ли код
```

---

## 🔌 API Design

### Endpoints

#### POST /api/v1/query

**Request:**
```json
{
    "question": "Что такое MAU и как его считают?",
    "user_id": "user_123",
    "filters": {
        "sources": ["notion", "google_docs"],
        "max_age_days": 365
    },
    "top_k": 5
}
```

**Response:**
```json
{
    "query_id": "q_abc123",
    "answer": "MAU (Monthly Active Users) — количество уникальных пользователей, которые совершили хотя бы одно целевое действие за месяц...",
    "sources": [
        {
            "document_id": "doc_456",
            "title": "Метрики продукта Volta",
            "url": "https://notion.so/volta/metrics-456",
            "section": "Activation Metrics",
            "relevance_score": 0.92,
            "excerpt": "MAU рассчитывается как COUNT(DISTINCT user_id) WHERE..."
        }
    ],
    "confidence": 0.89,
    "latency_ms": 1250,
    "follow_up_questions": [
        "Как считают DAU?",
        "В чем разница между MAU и WAU?"
    ]
}
```

#### GET /api/v1/query/{query_id}

**Request:**
```
GET /api/v1/query/q_abc123
```

**Response:**
```json
{
    "query_id": "q_abc123",
    "question": "Что такое MAU и как его считают?",
    "answer": "...",
    "sources": [...],
    "feedback": null,
    "created_at": "2026-04-01T10:30:00Z"
}
```

#### POST /api/v1/feedback

**Request:**
```json
{
    "query_id": "q_abc123",
    "rating": "thumbs_up",
    "comment": "Ответ полный и точный"
}
```

---

## 📈 Evaluation Metrics

### Primary Metrics

| Метрика | Target | Measurement |
|---------|--------|-------------|
| **Answer Relevance** | ≥4.0/5.0 | User feedback (thumbs up/down) |
| **Response Latency** | <3 seconds | P95 latency |
| **Search Success Rate** | ≥80% | % queries with thumbs up |
| **Time to Information** | <30 seconds | User session duration |

### Secondary Metrics

| Метрика | Target | Measurement |
|---------|--------|-------------|
| **Precision@5** | ≥0.7 | Human eval of top-5 chunks |
| **Recall@5** | ≥0.8 | Human eval |
| **Groundedness** | ≥0.9 | LLM eval (ответ основан на контексте) |
| **Coverage** | ≥90% | % документов в индексе |

### Evaluation Pipeline

```python
def evaluate_rag(test_questions: List[dict]) -> dict:
    """
    Evaluate RAG system on test set

    test_questions: [
        {
            "question": "...",
            "expected_answer": "...",
            "expected_sources": ["doc_1", "doc_2"]
        }
    ]
    """
    results = []

    for q in test_questions:
        response = rag_query(q["question"])

        # Metrics
        relevance = llm_eval_relevance(q["expected_answer"], response["answer"])
        groundedness = llm_eval_groundedness(response["answer"], response["sources"])
        precision = calculate_precision(response["sources"], q["expected_sources"])

        results.append(
            {
                "question": q["question"],
                "relevance": relevance,
                "groundedness": groundedness,
                "precision": precision,
                "latency_ms": response["latency_ms"],
            }
        )

    return {
        "avg_relevance": np.mean([r["relevance"] for r in results]),
        "avg_groundedness": np.mean([r["groundedness"] for r in results]),
        "avg_precision": np.mean([r["precision"] for r in results]),
        "p95_latency": np.percentile([r["latency_ms"] for r in results], 95),
    }
```

---

## 📅 Timeline

### Phase 1: MVP (Weeks 1-4)

| Week | Tasks | Deliverables |
|------|-------|--------------|
| **1** | Setup infrastructure, Notion integration | Working pipeline for Notion docs |
| **2** | Chunking, embeddings, vector DB | Indexed Notion documentation |
| **3** | Retrieval, generation, basic UI | Working Q&A interface |
| **4** | Testing, evaluation, bug fixes | MVP ready for beta |

### Phase 2: V2 (Weeks 5-8)

| Week | Tasks | Deliverables |
|------|-------|--------------|
| **5** | Google Docs integration | Multi-source indexing |
| **6** | Hybrid search, reranking | Improved relevance |
| **7** | Feedback system, analytics | User feedback loop |
| **8** | Slack integration, polish | Full release |

### Phase 3: Future (Weeks 9+)

- Slack bot для вопросов
- Персонализация (учитывает роль пользователя)
- Аналитика использования (какие документы популярны)
- Автоматическое обновление индекса

---

## ⚠️ Risks

### Technical Risks

| Риск | Вероятность | Влияние | Митигация |
|------|-------------|---------|-----------|
| **Низкое качество эмбеддингов** | Medium | High | Тестировать разные модели (Voyage, OpenAI) |
| **Медленный поиск** | Medium | Medium | Hybrid search, кэширование |
| **Галлюцинации LLM** | Medium | High | Строгий prompt, проверка groundedness |
| **Устаревшая документация** | High | Medium | Индикация даты, авто-обновление |

### Security Risks

| Риск | Вероятность | Влияние | Митигация |
|------|-------------|---------|-----------|
| **Утечка конфиденциальной информации** | Low | Critical | Access control, audit logging |
| **SQL injection** | Low | High | Parameterized queries |
| **API abuse** | Medium | Medium | Rate limiting, authentication |

### Organizational Risks

| Риск | Вероятность | Влияние | Митигация |
|------|-------------|---------|-----------|
| **Низкое adoption** | Medium | High | Onboarding, training, champions |
| **Сопротивление изменениям** | Medium | Medium | Demonstrate value early |
| **Нехватка ресурсов** | Low | High | Prioritize MVP, iterate |

---

## 💰 Resources

### Team

| Role | FTE | Duration |
|------|-----|----------|
| ML Engineer | 1.0 | 8 weeks |
| Backend Engineer | 0.5 | 8 weeks |
| Frontend Engineer | 0.5 | 4 weeks |
| Data Analyst | 0.25 | 8 weeks |
| Product Manager | 0.25 | 8 weeks |

### Infrastructure Costs (Monthly)

| Resource | Cost | Notes |
|----------|------|-------|
| **Vector DB (Pinecone)** | $70-140/mo | Starter plan |
| **Embeddings API** | $50-100/mo | Voyage AI |
| **LLM API** | $100-300/mo | Claude API |
| **Hosting** | $50-100/mo | AWS/GCP |
| **Total** | **$270-640/mo** | ~$3-8K/year |

---

## 📎 Appendices

### Appendix A: Test Questions

```python
TEST_QUESTIONS = [
    {
        "question": "Что такое MAU и как его считают?",
        "expected_answer": "MAU (Monthly Active Users) — количество уникальных пользователей...",
        "expected_sources": ["Метрики продукта Volta", "Product Analytics Handbook"],
        "difficulty": "easy",
    },
    {
        "question": "Как запустить A/B тест? Опиши процесс.",
        "expected_answer": "Процесс запуска A/B теста включает: 1) Формулировка гипотезы...",
        "expected_sources": ["A/B Testing Process", "Experimentation Playbook"],
        "difficulty": "medium",
    },
    {
        "question": "Какой SQL запрос используется для расчета retention?",
        "expected_answer": "SELECT ... cohort analysis query ...",
        "expected_sources": ["SQL Queries Library", "Retention Analysis Notebook"],
        "difficulty": "hard",
    },
]
```

### Appendix B: Prompt Templates

```python
RAG_PROMPT = """Ты помощник для поиска информации в документации Volta Banking.

Правила:
1. Отвечай ТОЛЬКО на основе предоставленного контекста
2. Если ответа нет в контексте, скажи "Не могу найти ответ в документации"
3. Всегда указывай источник (название документа)
4. Для чисел указывай единицы измерения
5. Для формул приводи точную формулу из документации

Контекст:
{context}

Вопрос: {question}

Ответ:"""
```

### Appendix C: Chunking Strategy

```python
CHUNKING_CONFIG = {
    "chunk_size": 500,  # tokens
    "chunk_overlap": 50,  # tokens
    "separator": "\n\n",  # paragraph boundaries
    "add_metadata": {
        "section_title": True,
        "page_number": True,
        "has_table": True,
        "has_code": True,
    },
}
```

---

## 🔗 Related Documents

- [[RAG для аналитика данных]] — Obsidian заметка с архитектурой
- [[Text-to-SQL с Claude]] — смежный проект
- `capabilities/retrieval_augmented_generation/guide.ipynb` — Anthropic guide

---

## 📝 Changelog

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-04-01 | Data Analytics Team | Initial draft |
