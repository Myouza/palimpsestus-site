/**
 * Site-wide configuration — the single source of truth for all
 * UI text, metadata, and structural constants.
 *
 * Components import from here instead of hardcoding strings.
 * To localize or rebrand, edit only this file.
 */

// ── Site Identity ──────────────────────────────────────────
export const site = {
  name: '六宫月影',
  nameEn: 'Palimpsestus',
  fullName: '六宫月影 Palimpsestus',
  author: 'Myouza',
  description: '六宫月影 — 原创文学',
  url: 'https://palimpsestus.art',
  icp: '沪ICP备2026003645号',
  icpUrl: 'https://beian.miit.gov.cn/',
  license: 'CC BY-NC-SA 4.0',
  licenseUrl: 'https://creativecommons.org/licenses/by-nc-sa/4.0/',
  copyrightYear: '2026',
} as const;

// ── Navigation & UI Labels ─────────────────────────────────
export const ui = {
  nav: {
    home: '六宫月影',
    toc: '目录',
    expandChapter: '展开',
    collapseChapter: '收起',
    openDrawer: '打开目录',
    drawerTitle: '目录',
    prevSection: '上一节',
    nextSection: '下一节',
    prevArrow: '←',
    nextArrow: '→',
    breadcrumbSep: '›',
  },
  settings: {
    label: '阅读设置',
    bgLabel: '背景',
    fontSizeLabel: '字号',
    sidenotesLabel: '边注',
    themes: {
      paper: '米色',
      white: '白色',
      dark: '暗色',
    } as Record<string, string>,
    fontSizes: {
      small: '小',
      medium: '中',
      large: '大',
    } as Record<string, string>,
    sidenotes: {
      showAll: '展开全部',
      hideAll: '收起全部',
    },
  },
  sidenote: {
    ariaExpand: '展开注释',
    ariaCollapse: '收起注释',
  },
  error: {
    notFoundCode: '404',
    notFoundTitle: '此页无迹可寻',
    notFoundMessage: '你寻找的页面或许从未存在，或许已随覆写而消散。',
    backToHome: '返回目录',
  },
} as const;
