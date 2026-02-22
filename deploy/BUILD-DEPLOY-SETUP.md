# Palimpsestus 服务器构建部署指南

## 架构概览

```
GitHub push → Actions SSH 到服务器（deploy 用户）→ 服务器本地构建 → 部署

服务器目录结构：
/opt/palimpsestus/
├── fonts/                               ← 完整字体源文件（ubuntu 所有）
│   ├── NotoSerifCJKsc-Regular.otf       ← 400（正文）  ← 实际使用
│   ├── NotoSerifCJKsc-SemiBold.otf      ← 600（标题）  ← 实际使用
│   ├── NotoSerifCJKsc-Bold.otf          ← 700（加粗）  ← 实际使用
│   └── (其余字重可保留备用，但脚本不会使用)
├── venv/                                ← Python 虚拟环境（deploy 所有）
├── repos/                               ← deploy 所有
│   ├── framework/                       ← palimpsestus-site 仓库
│   └── content/                         ← 私有内容仓库

/var/www/                           ← deploy 所有
├── production/                     ← main 分支部署目标
└── staging/                        ← preview 分支部署目标
```

**权限原则：**
- `ubuntu`：系统管理员，只负责建目录、装全局包、分配权限
- `deploy`：自动化专员，拥有 nvm/Node.js、SSH 密钥、仓库、构建产物
- GitHub Actions 通过 `SERVER_USER=deploy` 连接服务器，永远不碰 `ubuntu`

---

## 第一步：以 ubuntu 身份创建目录并分配权限

先检查现有状态：
```bash
# 检查 deploy 用户是否存在
id deploy

# 检查目录现状
ls -la /opt/palimpsestus/
ls -la /var/www/
```

执行：
```bash
# 创建仓库目录，交给 deploy
sudo mkdir -p /opt/palimpsestus/repos
sudo chown -R deploy:deploy /opt/palimpsestus/repos

# 确保字体目录 deploy 可读（不需要写权限）
sudo chmod -R a+rX /opt/palimpsestus/fonts

# 创建 Web 目录，交给 deploy
sudo mkdir -p /var/www/production /var/www/staging
sudo chown -R deploy:deploy /var/www/production /var/www/staging
```

确保系统有 python3-venv（虚拟环境需要）：
```bash
# 检查
python3 --version
dpkg -l | grep python3-venv

# 如果 python3-venv 没装：
sudo apt update
sudo apt install python3-venv -y
```

---

## 第二步：切换到 deploy 身份，安装 nvm 和 Node.js

```bash
sudo su - deploy
```

提示符应变为 `deploy@VM-0-15-ubuntu:~$`。**以下第二步到第六步都在 deploy 身份下操作。**

先检查：
```bash
node -v 2>/dev/null && echo "Node.js 已安装" || echo "Node.js 未安装"
command -v nvm 2>/dev/null && echo "nvm 已安装" || echo "nvm 未安装"
```

如果未安装：
```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
source ~/.bashrc
nvm install 20
nvm alias default 20
```

验证：
```bash
node -v   # v20.x.x
npm -v    # 10.x.x
```

---

## 第三步：创建 Python 虚拟环境并安装 fonttools

先检查：
```bash
ls /opt/palimpsestus/venv/bin/activate 2>/dev/null && echo "venv 已存在" || echo "venv 不存在"
```

如果不存在：
```bash
python3 -m venv /opt/palimpsestus/venv
source /opt/palimpsestus/venv/bin/activate
pip install fonttools brotli
deactivate
```

验证（不需要手动 activate，直接用绝对路径）：
```bash
/opt/palimpsestus/venv/bin/python3 -c "from fontTools.subset import Subsetter; print('fonttools OK')"
```

---

## 第四步：配置 SSH 密钥

deploy 需要一把钥匙来拉取你的私有内容仓库。

先检查：
```bash
ls ~/.ssh/palimpsestus-content-deploy 2>/dev/null && echo "密钥已存在" || echo "密钥不存在"
```

如果不存在：
```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh

nano ~/.ssh/palimpsestus-content-deploy
# 在 Windows 上打开你之前生成的私钥文件，复制全部内容
# 粘贴到 nano 里，Ctrl+O 保存，Ctrl+X 退出

chmod 600 ~/.ssh/palimpsestus-content-deploy
```

配置 SSH 别名（先检查是否已配过）：
```bash
grep 'github.com-content' ~/.ssh/config 2>/dev/null && echo "已配置" || echo "未配置"
```

如果未配置：
```bash
cat >> ~/.ssh/config << 'EOF'
Host github.com-content
    HostName github.com
    User git
    IdentityFile ~/.ssh/palimpsestus-content-deploy
    IdentitiesOnly yes
EOF

chmod 600 ~/.ssh/config
```

测试连接：
```bash
ssh -T github.com-content
# 应该看到：Hi xxx/palimpsestus-content! You've successfully authenticated...
```

---

## 第五步：克隆两个仓库

先检查：
```bash
ls /opt/palimpsestus/repos/framework/package.json 2>/dev/null && echo "框架仓库已克隆" || echo "未克隆"
ls /opt/palimpsestus/repos/content/ 2>/dev/null && echo "内容仓库已克隆" || echo "未克隆"
```

如果未克隆：
```bash
cd /opt/palimpsestus/repos

# 框架仓库（公开，HTTPS）
git clone https://github.com/你的用户名/palimpsestus-site.git framework

# 内容仓库（私有，deploy key）
git clone git@github.com-content:你的用户名/palimpsestus-content.git content
```

把 `你的用户名` 替换成你的 GitHub 用户名。

安装框架依赖：
```bash
cd /opt/palimpsestus/repos/framework
npm install
```

---

## 第六步：手动测试完整构建

```bash
cd /opt/palimpsestus/repos/framework
bash scripts/server-deploy.sh main main
```

期望输出：

```
╔══════════════════════════════════════════╗
║  Palimpsestus Deploy                     ║
╚══════════════════════════════════════════╝
  Framework: main
  Content:   main
  Target:    production → /var/www/production

✓ nvm loaded (Node v20.x.x)
✓ Prerequisites verified

── Pulling framework (main) ──
── Pulling content (main) ──
── Merging content ──
── Subsetting fonts ──
Font subsetting for Palimpsestus
========================================
  Scanning N content files...
  Total unique characters: ~2000
  Covered by font: ~1800 (CJK + Latin/symbols)

  Generating 3 weight variants...
    SiteSerif-400.woff2  (~150 KB)
    SiteSerif-600.woff2  (~160 KB)
    SiteSerif-700.woff2  (~170 KB)

  Total font size: ~480 KB

── Building site ──
── Deploying to /var/www/production ──
✓ Deployed 22 pages

╔══════════════════════════════════════════╗
║  ✓ Deploy complete: production
╚══════════════════════════════════════════╝
```

看到这个输出就说明整套流程跑通了。

```bash
# 退回 ubuntu 身份
exit
```

---

## 第七步：确认 Nginx 配置

```bash
# 以 ubuntu 身份
grep 'root' /etc/nginx/sites-available/palimpsestus 2>/dev/null || \
grep 'root' /etc/nginx/conf.d/*.conf 2>/dev/null
# 确认指向 /var/www/production

# 如果需要修改：
sudo nano /etc/nginx/sites-available/palimpsestus
sudo nginx -t && sudo systemctl reload nginx
```

---

## 第八步：确认 GitHub Secrets

**不需要改任何 Secret。** 核实一下现有值即可：

| Secret | 应有的值 |
|--------|---------|
| `SERVER_HOST` | 你的服务器 IP |
| `SERVER_SSH_PORT` | `2222`（或你设的端口） |
| `SERVER_USER` | **`deploy`**（绝对不能是 ubuntu） |
| `SERVER_SSH_KEY` | deploy 用户的 SSH 私钥 |

`CONTENT_REPO` 和 `CONTENT_DEPLOY_KEY` 留着不影响，但新架构下不再使用。

---

## 第九步：推送代码触发自动部署

把交付的 tar.gz 解压到本地框架仓库，用 GitHub Desktop 推送。

注意推送前确认：
- `.gitignore` 里有 `public/fonts/SiteSerif-*.woff2`
- `public/fonts/` 里只有 `.gitkeep`，没有旧的 woff2 文件

推送后 GitHub Actions 会 SSH 到你的服务器，以 deploy 身份执行 `server-deploy.sh`，全自动完成构建部署。

---

## 日常使用

一切就绪后，日常工作流不变：

- **改内容** → push 到内容仓库 → 自动触发
- **改框架** → push 到框架仓库 → 自动触发
- **改字体** → 以 ubuntu 身份上传新 TTF 到 `/opt/palimpsestus/fonts/`，改 `subset-fonts.py` 和 CSS，push

## 添加新字体

1. 上传完整字体到 `/opt/palimpsestus/fonts/`（ubuntu 身份）
2. 编辑 `scripts/subset-fonts.py` 的 `RANGES` 字典，加一个条目
3. 编辑 `src/styles/global.css`，加对应的 `@font-face` 和 `unicode-range`
4. Push，自动生效

注意：NushuSerif（女书）不走子集化流程。`public/fonts/NushuSerif.woff2`（55KB）是官方
网页字体，直接提交在 Git 仓库里。服务器上的 NyushuFengQi.ttf 可以删除。

## 故障排查

```bash
# 切到 deploy 身份手动跑
sudo su - deploy
cd /opt/palimpsestus/repos/framework
bash scripts/server-deploy.sh main main

# 检查 nvm 是否可用
source ~/.nvm/nvm.sh && node -v

# 检查 fonttools（通过 venv）
/opt/palimpsestus/venv/bin/python3 -c "from fontTools.subset import Subsetter; print('OK')"

# 检查字体源文件
ls -lh /opt/palimpsestus/fonts/

# 检查生成的子集
ls -lh /opt/palimpsestus/repos/framework/public/fonts/

# 检查 deploy 对 Web 目录的权限
ls -la /var/www/production/
```
