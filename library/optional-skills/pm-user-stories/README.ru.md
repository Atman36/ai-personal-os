# User Stories Skill

![Иллюстрация скилла](assets/illustration.png)

Разбивает Epic или крупное требование на User Stories с проверкой INVEST, AC и Story Map. Часть продуктового toolkit Personal Corp.

## Проблема

PRD или Epic слишком крупный для одного спринта — инженерам нужны независимо поставляемые единицы.

## Решение

Агент декомпозирует требование на User Stories с Given-When-Then AC, проверкой INVEST, Story Points и Story Map для спринта.

## Когда применять

- После ревью PRD
- Перед планированием спринта
- Когда Epic нужно разбить для Jira/Linear/GitHub Issues

## Установка

```bash
cp -r skills/pm-user-stories ~/.claude/skills/
```

## Пример промпта

```text
Разбей этот раздел PRD на user stories с acceptance criteria и story points.
```

Slash-команда: `/pm-user-stories`

## Связанные скиллы

- /pm-prd
- /pm-prioritize

## См. также

- [SKILL.md](SKILL.md) — полное определение скилла
- [README.md](README.md) — English version
