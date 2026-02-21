# 六宫月影 Palimpsestus

Personal literary website built with Astro, deployed via Docker + Nginx on Tencent Cloud Lighthouse.

## Architecture

```
┌─────────────────────────────────────────────────┐
│  palimpsestus-site (public)                     │
│  Astro framework, components, styles, CI/CD     │
├─────────────────────────────────────────────────┤
│  palimpsestus-content (private)                 │
│  Markdown/MDX manuscripts, organized by volume  │
└────────────┬────────────────────────────────────┘
             │ GitHub Actions
             ▼
┌─────────────────────────────────────────────────┐
│  Tencent Cloud Lighthouse (Ubuntu 22.04)        │
│  Docker → Nginx → static HTML                   │
│                                                 │
│  palimpsestus.art          (production)         │
│  stage.palimpsestus.art    (staging, auth)      │
└─────────────────────────────────────────────────┘
```

## Tech Stack

- **Framework**: [Astro](https://astro.build/) v5 + MDX + Tailwind CSS
- **Fonts**: Noto Serif SC (宋体) · LXGW WenKai (楷体) · Noto Sans Nushu (女书)
- **Navigation**: View Transitions (SPA-like), reading progress bar, drawer sidebar
- **Deployment**: Docker Compose (Nginx Alpine), GitHub Actions, rsync
- **Security**: Rate limiting, AI crawler blocking, HTTPS, SSH hardening

## Content Structure

Flat-file tree with numeric IDs:

```
content/
└── 01/                    # Volume
    ├── meta.yaml          # { title: "卷名" }
    ├── 00.mdx             # Chapter: "其一"
    ├── 00-00.mdx          # Section: "其一之一"
    ├── 00-00-00.mdx       # Sub-section: "其一之一之一"
    ├── 00-01.mdx          # Section: "其一之三" (sparse OK)
    └── 01.mdx             # Chapter: "其二"
```

- File IDs = reading order (lexicographic sort)
- Chinese titles in frontmatter (fully decoupled from IDs)
- Tree relationships inferred from `-` delimited prefixes
- Supports arbitrary depth

## Local Development

```bash
npm install
npm run dev        # http://localhost:4321
npm run build      # Static output → dist/
```

## Unicode Support

Full rendering support for Nushu script (女书, U+1B170–1B2FF) via `unicode-range` font fallback.
The self-hosted Noto Sans Nushu font loads on-demand only when Nushu characters are present.

## License

Content: [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)
Framework code: MIT
