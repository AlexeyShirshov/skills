# Egg-drop experiment — индекс результатов

Исторический доменный бенчмарк PDCA. Здесь собраны все результаты экспериментов; перенос
описан в [TRANSFER-RECEIPT.json](TRANSFER-RECEIPT.json). Исходное задание —
[egg-drop-test.md](egg-drop-test.md) — не изменялось и лежит по прежнему пути.

## Прогоны (`runs/`)

| Прогон | Что это | Точки входа |
| --- | --- | --- |
| [20261024-original](runs/20261024-original/) | архив состояния до перезапуска (2026-10-24T10:54Z) | [answer-a.md](runs/20261024-original/experiments/egg-drop/answer-a.md) · [статус](runs/20261024-original/.pdca/status/egg-drop-answer-a-1.md) · [ARCHIVE-RECEIPT.md](runs/20261024-original/ARCHIVE-RECEIPT.md) |
| [20261024-pdca](runs/20261024-pdca/) | архив состояния перед новым прогоном (2026-10-24T17:16Z) | [answer.md](runs/20261024-pdca/experiments/egg-drop/answer.md) · [статус](runs/20261024-pdca/.pdca/status/egg-drop-1.md) · [ARCHIVE-RECEIPT.md](runs/20261024-pdca/ARCHIVE-RECEIPT.md) |
| [20261024-incremental](runs/20261024-incremental/) | рабочие выходы прогона `pdca-incremental`: ответ, чекер, фикстуры, пакеты `m001` / `check-r1` / `verify-v001` | [answer.md](runs/20261024-incremental/experiments/egg-drop/answer.md) · [статус](runs/20261024-incremental/.pdca/status/egg-drop-1.md) · [baseline.md](runs/20261024-incremental/.pdca/egg-drop/rv1/baseline.md) · [scratch/](runs/20261024-incremental/scratch/) |

Внутри каждого `runs/*/` сохранены исходные относительные пути (`experiments/egg-drop/...`,
`.pdca/...`), поэтому ссылки на них в исторических пакетах, логах и статусах остаются
валидными. В `runs/20261024-incremental/scratch/` — вспомогательные скрипты и отчёты прогона,
на которые ссылаются эти пакеты.

## Ретроспективы (`retrospectives/`)

- [20261024-pdca-vs-sol](retrospectives/20261024-pdca-vs-sol/report.md) — аудит стоимости и
  времени обычного цикла против прямого ответа модели (`results.json`, `summary.json` рядом).
- [20261024-incremental](retrospectives/20261024-incremental/report.md) — аудит прогона
  `pdca-incremental` (`results.json`, `summary.json`, `hashes.json`, `timeline.json`).

Это выверенные сводки. Сырая телеметрия API (дампы сессий и сообщений, `models.json`) в
репозиторий не входит: она содержит приватные учётные данные и полные транскрипты. Оригиналы
поэтому остаются вне репозитория, в приватных каталогах `/tmp` с правами `0700`. Абсолютные
пути `/tmp/...` внутри отчётов и пакетов — исторические свидетельства, они не переписаны.

## Целостность

Хэши до и после переноса, сверка с исходными архивными инвентарями и перечень исключённого —
в [TRANSFER-RECEIPT.json](TRANSFER-RECEIPT.json).
