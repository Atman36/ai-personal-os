# Product Metrics Review Skill

![Иллюстрация скилла](assets/illustration.png)

Ревью продуктовых метрик: тренды, аномалии, воронка/retention, A/B и соответствие OKR. Часть продуктового toolkit Personal Corp.

## Проблема

Дашборды показывают движение, но не причину — команда реагирует на шум вместо root cause.

## Решение

Агент разбирает тренды, декомпозирует North Star, диагностирует retention/воронку и выдаёт приоритетные действия.

## Когда применять

- Еженедельный или месячный обзор метрик
- После завершения A/B
- Когда OKR pacing съехал

## Установка

```bash
cp -r skills/pm-metrics ~/.claude/skills/
```

## Пример промпта

```text
Разбери метрики Q1 по фиче X: DAU flat, activation -8%, retention week-4 вырос.
```

Slash-команда: `/pm-metrics`

## Связанные скиллы

- /pm-roadmap
- /pm-feedback
- /pm-prioritize

## См. также

- [SKILL.md](SKILL.md) — полное определение скилла
- [README.md](README.md) — English version
