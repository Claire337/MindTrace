# MindTrace — Project Plan
**COMP390 Honours Year Project 2025-26**

---

## Project Summary

A web application for daily mood tracking with AI-powered psychological insights. Users log their emotions and journal entries; the system analyses them using NLP and generates personalised insights via an LLM API.

**Tech Stack:** Flask · SQLite · TextBlob · LLM API (TBD) · Chart.js · Bootstrap 5 · Flask-Babel (EN/ZH)

---

## Development Phases

### Phase 1 — Foundation & User System
**Feb 9 – Feb 22**

- Set up Flask project structure (App Factory + Blueprints)
- Database models: `User`, `MoodEntry`, `AIInsight`
- User registration, login, logout (Flask-Login + Werkzeug password hashing)
- Bilingual UI framework (Flask-Babel, EN/ZH language switcher)
- Base layout with Bootstrap 5 navbar

---

### Phase 2 — Mood Recording
**Feb 23 – Mar 1**

- Daily check-in form: mood type, intensity (1–10), journal text, tags, date picker
- Mood history page (timeline view, pagination, filter by mood/date)
- Entry edit, delete, and back-fill for past dates

---

### Phase 3 — NLP Analysis
**Mar 2 – Mar 8**

- TextBlob sentiment analysis (Positive / Neutral / Negative)
- Emotion classification via keyword matching (anxiety, stress, loneliness, anger, etc.)
- Keyword extraction; auto-generated one-line summary per entry
- Display analysis results on entry detail page

---

### Phase 4 — LLM AI Insights
**Mar 9 – Mar 15**

- Integrate LLM API (provider decided at start of this phase)
- Daily insight card: emotional summary + likely cause + 2 actionable suggestions
- Weekly pattern summary based on 7-day entry aggregation
- Small task suggestion: "one small thing you could do today"
- Rule-based personalised recommendations (fallback if API unavailable)

---

### Phase 5 — Visualisation, Toolbox & Dissertation Start
**Mar 16 – Mar 22**

- Mood trend line chart and mood distribution bar chart (Chart.js, 7-day / 30-day)
- Stats summary: average intensity, most frequent mood, weekly comparison
- Breathing trainer: 4-7-8 technique with CSS animation
- Emotion first aid card: 3-step grounding guide
- Fake data seeder script (30 days of demo entries)

*Dissertation: Introduction, Literature Review, Requirements & Design, Implementation (all chapters drafted based on completed code)*

---

### Phase 6 — Polish & Dissertation Completion
**Mar 23 – Mar 29**

- User settings page (change username, password, language preference)
- UI polish, error handling, mobile responsiveness
- Full functional testing

*Dissertation: Evaluation (functional tests, NLP accuracy check, ethical reflection), Conclusion, Abstract; full proofread (~8,000–10,000 words)*

---

## Key Design Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Database | SQLite | Zero-config, sufficient for a demo |
| NLP | TextBlob | Lightweight, easy to integrate, good for English text |
| LLM | TBD (Phase 4) | API-agnostic abstraction layer for flexibility |
| UI Language | EN + ZH toggle | Demonstrates i18n awareness; Flask-Babel |
| Test Data | Fake seeder | Avoids collecting real personal data (ethical compliance) |

---

## Ethical Note

No real personal data will be collected. All demonstrations use seeded fake data. LLM-generated content will include a disclaimer that it is not a substitute for professional mental health support.
