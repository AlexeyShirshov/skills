# pdca-slides

Дека (Slidev) по статье [`../pdca.md`](../pdca.md) — доменно-нейтральный контракт цикла
`pdca`: PLAN → DO → CHECK → ACT, роли и тиры, выходы фаз, счётчики, режимы, память, учебная история STOP.

## Запуск

```bash
npm install     # Node.js >= 22.12
npm run dev     # http://localhost:3030 (+ /presenter для режима докладчика)
```

## Экспорт

Экспорт рендерится браузером: `playwright-chromium` уже в `devDependencies`, но в WSL
headless-shell падает с `libnspr4.so`. Два пути — один раз на машине:

```bash
sudo npx playwright install-deps chromium     # Ubuntu: libnspr4, libnss3 и прочее
```

или **без sudo** — вытащить библиотеки из .deb рядом и подсунуть их chromium:

```bash
mkdir -p /tmp/opencode/chromium-deps && cd /tmp/opencode/chromium-deps
apt-get download libnspr4 libnss3
for f in *.deb; do dpkg-deb -x "$f" root/; done
cd -   # вернуться в каталог деки

export LD_LIBRARY_PATH=/tmp/opencode/chromium-deps/root/usr/lib/x86_64-linux-gnu
npm run export                       # PDF
npm run export:pptx                  # PPTX картинками
npm run export:pptx-editable         # PPTX с нативными объектами
```

```bash
npm run export                  # PDF (slides-export.pdf)
npm run export:pptx             # PPTX, слайды картинками + заметки докладчика
npm run export:pptx-editable    # PPTX с нативными объектами PowerPoint
npm run build                   # статичный SPA в dist/ (GitHub Pages, Netlify…)
```

Полезные варианты: `npm run export -- --with-clicks` — по странице на каждый клик;
`--dark` — тёмная схема принудительно.

## Структура

| Файл | Что это |
|---|---|
| `slides.md` | сама дека (заметки докладчика — в `<!-- -->` под слайдом) |
| `public/pdca-state-dark.svg` | граф состояний (кадрированная вырезка) — слайд «Машина состояний» |
| `public/pdca-contract-dark.svg` | схема контракта целиком — слайд «Контракт целиком» |

Обе схемы — побайтовые копии `skills/pdca/assets/diagram/pdca-*-dark.svg`. Чтобы обновить их,
запустите `tools/pdca/diagrams/pdca/gen_pdca.py` из `skills/pdca/assets/diagram/` и
скопируйте полученные вырезки в `public/`:
`tests/pdca/test_diagram_artifacts.py` сверяет копии и проверяет, что кропы
вертикально покрывают исходник.

Источник фактов — контракты семейства `skills/pdca*` и [техническая статья](../pdca.md).
Для первого запуска и готовых промптов см. [руководство пользователя](../guide/README.md).
Готовый файл для чтения: [PDF-презентация](slides-export.pdf).
