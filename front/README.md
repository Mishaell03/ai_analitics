# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some Oxlint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the Oxlint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and Oxlint's TypeScript related rules in your project.

---

## Markdown уроков

Сервис `src/services/markdown` разбирает Markdown урока в дерево блоков,
а компоненты `src/components/Markdown` только показывают его.

```jsx
import Markdown from "@/components/Markdown/Markdown.jsx";

<Markdown content={lesson.content}/>
```

Сервис отвечает за:

- разбор блочной и инлайн-разметки (заголовки, списки, таблицы, цитаты,
  блоки кода, картинки, кастомные блоки);
- безопасность ссылок: `javascript:`, `data:` и прочие опасные протоколы
  не превращаются в ссылки, а остаются текстом;
- подсветку синтаксиса в блоках кода.

HTML и скрипты из урока не выполняются: разметка собирается React-элементами,
а не вставляется через `dangerouslySetInnerHTML`.

### Кастомные блоки

Блок `:::test ... :::` разбирается сервисом и показывается заглушкой.
Свой тип блока добавляется в два шага:

```js
// 1. разбор содержимого блока в данные
import {CustomBlockHandler, markdownService} from "@/services/markdown/MarkdownService.js";

class TestBlockHandler extends CustomBlockHandler {
    constructor() {
        super("test");
    }

    parse(content) {
        return {type: this.type, content, implemented: true, data: {question: content}};
    }
}

markdownService.registerCustomBlock(new TestBlockHandler());

// 2. отрисовка блока
import {registerCustomBlockRenderer} from "@/components/Markdown/customBlockRenderers.js";

registerCustomBlockRenderer("test", (block) => <TestBlock block={block}/>);
```

### Медиафайлы

Файлы лежат в приватном хранилище: клиент видит только логический
идентификатор и временную ссылку. В Markdown попадает идентификатор,
а не ссылка:

```markdown
![Схема работы](asset:m_0123456789abcdef)
```

- `src/api/media.js` — API-клиент: обложка курса, медиафайлы урока,
  обновление ссылки, удаление;
- `src/services/media.js` — правила файлов (типы, размеры), разбор
  ссылки `asset:` и сборка Markdown-вставки;
- `src/hooks/useFileUpload.js` — загрузка с прогрессом и отменой запроса
  при уходе со страницы.

Ссылка на файл живёт недолго, поэтому список медиафайлов всегда
приходит со свежими ссылками, а протухшая ссылка обновляется
запросом `POST /admin/media/{media_key}/url`.

`Markdown` принимает файлы урока и раскрывает ссылки по идентификатору:

```jsx
<Markdown content={lesson.content} media={mediaByKey} onMediaError={refreshMediaUrl}/>
```

### Команды

```bash
npm run dev          # запуск dev-сервера
npm run build        # сборка
npm run lint         # линтер
npm test             # тесты сервисов Markdown и Media
npm run test:render  # проверка отрисовки Markdown
```
