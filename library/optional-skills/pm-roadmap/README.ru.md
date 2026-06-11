# Roadmap Update Skill

![Иллюстрация скилла](assets/illustration.png)

Сводит статус итерации в roadmap Now/Next/Later с атрибуцией задержек, health score и обрезкой scope. Часть продуктового toolkit Personal Corp.

## Проблема

Roadmap устаревает после одного спринта — milestones, задержки и смена приоритетов не фиксируются.

## Решение

Агент собирает статус спринта, прогресс milestones, зависимости и выдаёт обновлённый roadmap с явными trade-offs.

## Когда применять

- Конец спринта или итерации
- Перед стейкхолдер-ревью
- Когда нужно объяснить задержки

## Установка

```bash
cp -r skills/pm-roadmap ~/.claude/skills/
```

## Пример промпта

```text
Обнови roadmap по статусу Sprint 14 и milestones Q2. Два пункта съехали из-за dependency risk.
```

Slash-команда: `/pm-roadmap`

## Связанные скиллы

- /pm-prioritize
- /pm-metrics
- /pm-brainstorm

## См. также

- [SKILL.md](SKILL.md) — полное определение скилла
- [README.md](README.md) — English version
