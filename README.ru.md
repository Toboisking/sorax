<p align="center">
  <a href="https://sorax.ai">
    <picture>
      <source srcset="packages/console/app/src/asset/logo-ornate-dark.svg" media="(prefers-color-scheme: dark)">
      <source srcset="packages/console/app/src/asset/logo-ornate-light.svg" media="(prefers-color-scheme: light)">
      <img src="packages/console/app/src/asset/logo-ornate-light.svg" alt="SORAX logo">
    </picture>
  </a>
</p>
<p align="center">Открытый AI-агент для программирования.</p>
<p align="center">
  <a href="https://sorax.ai/discord"><img alt="Discord" src="https://img.shields.io/discord/1391832426048651334?style=flat-square&label=discord" /></a>
  <a href="https://www.npmjs.com/package/@sorax/cli"><img alt="npm" src="https://img.shields.io/npm/v/@sorax/cli?style=flat-square" /></a>
  <a href="https://github.com/anomalyco/sorax/actions/workflows/publish.yml"><img alt="Build status" src="https://img.shields.io/github/actions/workflow/status/anomalyco/sorax/publish.yml?style=flat-square&branch=dev" /></a>
</p>

<p align="center">
  <a href="README.md">English</a> |
  <a href="README.zh.md">简体中文</a> |
  <a href="README.zht.md">繁體中文</a> |
  <a href="README.ko.md">한국어</a> |
  <a href="README.de.md">Deutsch</a> |
  <a href="README.es.md">Español</a> |
  <a href="README.fr.md">Français</a> |
  <a href="README.it.md">Italiano</a> |
  <a href="README.da.md">Dansk</a> |
  <a href="README.ja.md">日本語</a> |
  <a href="README.pl.md">Polski</a> |
  <a href="README.ru.md">Русский</a> |
  <a href="README.bs.md">Bosanski</a> |
  <a href="README.ar.md">العربية</a> |
  <a href="README.no.md">Norsk</a> |
  <a href="README.br.md">Português (Brasil)</a> |
  <a href="README.th.md">ไทย</a> |
  <a href="README.tr.md">Türkçe</a> |
  <a href="README.uk.md">Українська</a> |
  <a href="README.bn.md">বাংলা</a> |
  <a href="README.gr.md">Ελληνικά</a> |
  <a href="README.vi.md">Tiếng Việt</a>
</p>

[![SORAX Terminal UI](packages/web/src/assets/lander/screenshot.png)](https://sorax.ai)

---

### Установка

```bash
# YOLO
curl -fsSL https://sorax.ai/v2/install | bash

# Менеджеры пакетов
npm i -g @sorax/cli@latest      # или bun/pnpm/yarn
brew install anomalyco/tap/sorax-v2 # macOS и Linux (рекомендуем, всегда актуально)
brew install sorax              # macOS и Linux (официальная формула brew, обновляется реже)
sudo pacman -S sorax            # Arch Linux (Stable)
paru -S sorax-beta              # Arch Linux (Latest from AUR)
mise use -g sorax               # любая ОС
nix run github:anomalyco/sorax  # Nix
```

> [!TIP]
> Перед установкой удалите версии старше 0.1.x.

### Десктопное приложение (BETA)

SORAX также доступен как десктопное приложение. Скачайте его с [sorax.ai/download](https://sorax.ai/download).

| Платформа             | Загрузка                           |
| --------------------- | ---------------------------------- |
| macOS (Apple Silicon) | `sorax-desktop-mac-arm64.dmg`   |
| macOS (Intel)         | `sorax-desktop-mac-x64.dmg`     |
| Windows               | `sorax-desktop-win-x64.exe`     |
| Linux                 | `.deb`, `.rpm` или AppImage        |

```bash
# macOS (Homebrew)
brew install --cask sorax-desktop
```

#### Каталог установки

Скрипт установки устанавливает SORAX в `$HOME/.sorax/bin`.

### Agents

В SORAX есть два встроенных агента, между которыми можно переключаться клавишей `Tab`.

- **build** - По умолчанию, агент с полным доступом для разработки
- **plan** - Агент только для чтения для анализа и изучения кода
  - По умолчанию запрещает редактирование файлов
  - Запрашивает разрешение перед выполнением bash-команд
  - Идеален для изучения незнакомых кодовых баз или планирования изменений

Также включен сабагент **general** для сложных поисков и многошаговых задач.
Он используется внутренне и может быть вызван в сообщениях через `@general`.

Подробнее об [agents](https://sorax.ai/v2/docs/agents).

### Документация

Больше информации о том, как настроить SORAX: [**наши docs**](https://sorax.ai/v2/docs).

### Вклад

Если вы хотите внести вклад в SORAX, прочитайте [contributing docs](./CONTRIBUTING.md) перед тем, как отправлять pull request.

### Разработка на базе SORAX

Если вы делаете проект, связанный с SORAX, и используете "sorax" как часть имени (например, "sorax-dashboard" или "sorax-mobile"), добавьте примечание в README, чтобы уточнить, что проект не создан командой SORAX и не аффилирован с нами.

---

**Присоединяйтесь к нашему сообществу** [Discord](https://discord.gg/sorax) | [X.com](https://x.com/sorax)
