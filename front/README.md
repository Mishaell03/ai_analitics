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

Обложку курса можно выбрать прямо в форме создания и редактирования
курса. Файл отправляется отдельным запросом **после** сохранения курса:
у нового курса до этого нет `slug`, к которому привязывается обложка, а
у изменённого `slug` мог поменяться. Загружается обложка по `slug` из
ответа API, а не по значению из формы.

`Markdown` принимает файлы урока и раскрывает ссылки по идентификатору:

```jsx
<Markdown content={lesson.content} media={mediaByKey} onMediaError={refreshMediaUrl}/>
```

### Задания и правильные ответы

Задание лежит в Markdown урока, а правильный ответ — в базе. Связь идёт
через `exercise_id`: идентификатор задания.

```markdown
:::test
id: python-variables
Текст задания
- [ ] Вариант 1
- [ ] Вариант 2
:::
```

- `src/api/exercises.js` — API-клиент ответов: список, сохранение, удаление;
- `src/services/exercises.js` — разбор заданий, отметки `- [x]`, сборка
  и разбор ответа;
- `src/pages/Admin/Lessons/LessonExercisesPanel.jsx` — панель заданий
  в редакторе урока.

Отметки правильных вариантов живут только в редакторе: в файл урока
варианты уходят без отметок (`- [ ]`), а в базу ответ попадает отдельно.
При правке урока отметки восстанавливаются из базы.

Для выбора **одного** ответа используются круглые скобки:

```markdown
:::test
id: single-answer
Выберите один вариант
- ( ) Вариант 1
- ( ) Вариант 2
:::
```

В админке правильный вариант отмечается как `- (х)`: выбор другого
снимает предыдущую отметку. В БД сохраняется отдельный JSON
`{"type":"single_choice","correct":["Вариант 1"]}`, а в Markdown — только
`- ( )`. Сервер проверяет ответ и принимает ровно один непустой вариант.
Смешивать `- [ ]` и `- ( )` в одном задании нельзя; сервер также
отклоняет сохранение Markdown с отметками правильных ответов.

Код решения — это **эталонный ответ урока**, а не ответ задания: пример
идеального решения, с которым код ученика автоматически не сравнивается.
Он хранится в той же таблице ответов, но под собственным ключом
`reference` (`REFERENCE_ANSWER_ID` в `src/services/exercises.js`), поэтому:

- код сохраняется, даже если у задания нет `id:` в Markdown;
- переименование `id` задания не теряет эталонный ответ;
- в сам код идентификатор не добавляется — он уходит в базу как есть.

В редакторе урока эталонный ответ вводится отдельным полем над списком
заданий. Ответы с вариантами по-прежнему привязаны к `exercise_id`.

В режиме чтения ответы подставляются в задание:

```jsx
<Markdown content={lesson.content} answers={answersByExerciseId} labels={{answer: "Правильный ответ"}}/>
```

### Решение от эксперта

В кодовых заданиях `:::code python` / `:::code sql` после успешной проверки
под редактором появляется блок «Решение от эксперта» с подсветкой кода.
Компонент получает эталон через отдельный пользовательский endpoint
`GET /courses/{slug}/modules/{moduleId}/lessons/{lessonId}/exercises/{exerciseId}/expert-solution`.
В Markdown эталона нет. Решение доступно и при повторном открытии пройденного
задания; ошибка загрузки не скрывает результат ученика и допускает повторный запрос.

### Команды

```bash
npm run dev          # запуск dev-сервера
npm run build        # сборка
npm run lint         # линтер
npm test             # тесты сервисов Markdown, Media и Exercises
npm run test:render  # проверка отрисовки Markdown и админки
npm run test:render:single-choice # проверка выбора одного ответа
npm run test:render:expert-solution # проверка отображения решения эксперта
```
