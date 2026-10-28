<p align="center">
  <a href="https://sorax.ai">
    <picture>
      <source srcset="packages/console/app/src/asset/logo-ornate-dark.svg" media="(prefers-color-scheme: dark)">
      <source srcset="packages/console/app/src/asset/logo-ornate-light.svg" media="(prefers-color-scheme: light)">
      <img src="packages/console/app/src/asset/logo-ornate-light.svg" alt="Logo do SORAX">
    </picture>
  </a>
</p>
<p align="center">O agente de programação com IA de código aberto.</p>
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

### Instalação

```bash
# YOLO
curl -fsSL https://sorax.ai/v2/install | bash

# Gerenciadores de pacotes
npm i -g @sorax/cli@latest      # ou bun/pnpm/yarn
brew install anomalyco/tap/sorax-v2 # macOS e Linux (recomendado, sempre atualizado)
brew install sorax              # macOS e Linux (fórmula oficial do brew, atualiza menos)
sudo pacman -S sorax            # Arch Linux (Stable)
paru -S sorax-beta              # Arch Linux (Latest from AUR)
mise use -g sorax               # qualquer sistema
nix run github:anomalyco/sorax  # Nix
```

> [!TIP]
> Remova versões anteriores a 0.1.x antes de instalar.

### App desktop (BETA)

O SORAX também está disponível como aplicativo desktop. Baixe em [sorax.ai/download](https://sorax.ai/download).

| Plataforma            | Download                           |
| --------------------- | ---------------------------------- |
| macOS (Apple Silicon) | `sorax-desktop-mac-arm64.dmg`   |
| macOS (Intel)         | `sorax-desktop-mac-x64.dmg`     |
| Windows               | `sorax-desktop-win-x64.exe`     |
| Linux                 | `.deb`, `.rpm` ou AppImage         |

```bash
# macOS (Homebrew)
brew install --cask sorax-desktop
```

#### Diretório de instalação

O script de instalação instala o SORAX em `$HOME/.sorax/bin`.

### Agents

O SORAX inclui dois agents integrados, que você pode alternar com a tecla `Tab`.

- **build** - Padrão, agent com acesso total para trabalho de desenvolvimento
- **plan** - Agent somente leitura para análise e exploração de código
  - Nega edições de arquivos por padrão
  - Pede permissão antes de executar comandos bash
  - Ideal para explorar codebases desconhecidas ou planejar mudanças

Também há um subagent **general** para buscas complexas e tarefas em várias etapas.
Ele é usado internamente e pode ser invocado com `@general` nas mensagens.

Saiba mais sobre [agents](https://sorax.ai/v2/docs/agents).

### Documentação

Para mais informações sobre como configurar o SORAX, [**veja nossa documentação**](https://sorax.ai/v2/docs).

### Contribuir

Se você tem interesse em contribuir com o SORAX, leia os [contributing docs](./CONTRIBUTING.md) antes de enviar um pull request.

### Construindo com SORAX

Se você estiver trabalhando em um projeto relacionado ao SORAX e estiver usando "sorax" como parte do nome (por exemplo, "sorax-dashboard" ou "sorax-mobile"), adicione uma nota no README para deixar claro que não foi construído pela equipe do SORAX e não é afiliado a nós de nenhuma forma.

---

**Junte-se à nossa comunidade** [Discord](https://discord.gg/sorax) | [X.com](https://x.com/sorax)
