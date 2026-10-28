<p align="center">
  <a href="https://sorax.ai">
    <picture>
      <source srcset="packages/console/app/src/asset/logo-ornate-dark.svg" media="(prefers-color-scheme: dark)">
      <source srcset="packages/console/app/src/asset/logo-ornate-light.svg" media="(prefers-color-scheme: light)">
      <img src="packages/console/app/src/asset/logo-ornate-light.svg" alt="SORAX logo">
    </picture>
  </a>
</p>
<p align="center">Otwartoźródłowy agent kodujący AI.</p>
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

### Instalacja

```bash
# YOLO
curl -fsSL https://sorax.ai/v2/install | bash

# Menedżery pakietów
npm i -g @sorax/cli@latest      # albo bun/pnpm/yarn
brew install anomalyco/tap/sorax-v2 # macOS i Linux (polecane, zawsze aktualne)
brew install sorax              # macOS i Linux (oficjalna formuła brew, rzadziej aktualizowana)
sudo pacman -S sorax            # Arch Linux (Stable)
paru -S sorax-beta              # Arch Linux (Latest from AUR)
mise use -g sorax               # dowolny system
nix run github:anomalyco/sorax  # Nix
```

> [!TIP]
> Przed instalacją usuń wersje starsze niż 0.1.x.

### Aplikacja desktopowa (BETA)

SORAX jest także dostępny jako aplikacja desktopowa. Pobierz ją z [sorax.ai/download](https://sorax.ai/download).

| Platforma             | Pobieranie                         |
| --------------------- | ---------------------------------- |
| macOS (Apple Silicon) | `sorax-desktop-mac-arm64.dmg`   |
| macOS (Intel)         | `sorax-desktop-mac-x64.dmg`     |
| Windows               | `sorax-desktop-win-x64.exe`     |
| Linux                 | `.deb`, `.rpm` lub AppImage        |

```bash
# macOS (Homebrew)
brew install --cask sorax-desktop
```

#### Katalog instalacji

Skrypt instalacyjny instaluje SORAX w `$HOME/.sorax/bin`.

### Agents

SORAX zawiera dwóch wbudowanych agentów, między którymi możesz przełączać się klawiszem `Tab`.

- **build** - Domyślny agent z pełnym dostępem do pracy developerskiej
- **plan** - Agent tylko do odczytu do analizy i eksploracji kodu
  - Domyślnie odmawia edycji plików
  - Pyta o zgodę przed uruchomieniem komend bash
  - Idealny do poznawania nieznanych baz kodu lub planowania zmian

Dodatkowo jest subagent **general** do złożonych wyszukiwań i wieloetapowych zadań.
Jest używany wewnętrznie i można go wywołać w wiadomościach przez `@general`.

Dowiedz się więcej o [agents](https://sorax.ai/v2/docs/agents).

### Dokumentacja

Więcej informacji o konfiguracji SORAX znajdziesz w [**dokumentacji**](https://sorax.ai/v2/docs).

### Współtworzenie

Jeśli chcesz współtworzyć SORAX, przeczytaj [contributing docs](./CONTRIBUTING.md) przed wysłaniem pull requesta.

### Budowanie na SORAX

Jeśli pracujesz nad projektem związanym z SORAX i używasz "sorax" jako części nazwy (na przykład "sorax-dashboard" lub "sorax-mobile"), dodaj proszę notatkę do swojego README, aby wyjaśnić, że projekt nie jest tworzony przez zespół SORAX i nie jest z nami w żaden sposób powiązany.

---

**Dołącz do naszej społeczności** [Discord](https://discord.gg/sorax) | [X.com](https://x.com/sorax)
