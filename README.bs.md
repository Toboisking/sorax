<p align="center">
  <a href="https://sorax.ai">
    <picture>
      <source srcset="packages/console/app/src/asset/logo-ornate-dark.svg" media="(prefers-color-scheme: dark)">
      <source srcset="packages/console/app/src/asset/logo-ornate-light.svg" media="(prefers-color-scheme: light)">
      <img src="packages/console/app/src/asset/logo-ornate-light.svg" alt="SORAX logo">
    </picture>
  </a>
</p>
<p align="center">SORAX je open source AI agent za programiranje.</p>
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

### Instalacija

```bash
# YOLO
curl -fsSL https://sorax.ai/v2/install | bash

# Package manageri
npm i -g @sorax/cli@latest      # ili bun/pnpm/yarn
brew install anomalyco/tap/sorax-v2 # macOS i Linux (preporučeno, uvijek ažurno)
brew install sorax              # macOS i Linux (zvanična brew formula, rjeđe se ažurira)
sudo pacman -S sorax            # Arch Linux (Stable)
paru -S sorax-beta              # Arch Linux (Latest from AUR)
mise use -g sorax               # Bilo koji OS
nix run github:anomalyco/sorax  # Nix
```

> [!TIP]
> Ukloni verzije starije od 0.1.x prije instalacije.

### Desktop aplikacija (BETA)

SORAX je dostupan i kao desktop aplikacija. Preuzmi je sa [sorax.ai/download](https://sorax.ai/download).

| Platforma             | Preuzimanje                        |
| --------------------- | ---------------------------------- |
| macOS (Apple Silicon) | `sorax-desktop-mac-arm64.dmg`   |
| macOS (Intel)         | `sorax-desktop-mac-x64.dmg`     |
| Windows               | `sorax-desktop-win-x64.exe`     |
| Linux                 | `.deb`, `.rpm`, ili AppImage       |

```bash
# macOS (Homebrew)
brew install --cask sorax-desktop
```

#### Instalacijski direktorij

Instalacijska skripta instalira SORAX u `$HOME/.sorax/bin`.

### Agenti

SORAX uključuje dva ugrađena agenta između kojih možeš prebacivati tasterom `Tab`.

- **build** - Podrazumijevani agent sa punim pristupom za razvoj
- **plan** - Agent samo za čitanje za analizu i istraživanje koda
  - Podrazumijevano zabranjuje izmjene datoteka
  - Traži dozvolu prije pokretanja bash komandi
  - Idealan za istraživanje nepoznatih codebase-ova ili planiranje izmjena

Uključen je i **general** pod-agent za složene pretrage i višekoračne zadatke.
Koristi se interno i može se pozvati pomoću `@general` u porukama.

Saznaj više o [agentima](https://sorax.ai/v2/docs/agents).

### Dokumentacija

Za više informacija o konfiguraciji SORAX-a, [**pogledaj dokumentaciju**](https://sorax.ai/v2/docs).

### Doprinosi

Ako želiš doprinositi SORAX-u, pročitaj [upute za doprinošenje](./CONTRIBUTING.md) prije slanja pull requesta.

### Gradnja na SORAX-u

Ako radiš na projektu koji je povezan s SORAX-om i koristi "sorax" kao dio naziva, npr. "sorax-dashboard" ili "sorax-mobile", dodaj napomenu u svoj README da projekat nije napravio SORAX tim i da nije povezan s nama.

---

**Pridruži se našoj zajednici** [Discord](https://discord.gg/sorax) | [X.com](https://x.com/sorax)
