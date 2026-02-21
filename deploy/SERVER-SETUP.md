# 服务器初始配置指南

本指南假设你在腾讯云 Lighthouse 控制台通过 OrcaTerm 首次登录服务器。

## 第一步：首次登录

在腾讯云控制台点击「登录」→ 选择「密码/密钥登录」→ OrcaTerm 会打开一个终端。
默认用户名是 `ubuntu`（不是 root）。

```bash
# 确认你在 Ubuntu 上
cat /etc/os-release | head -3
```

## 第二步：系统更新

```bash
sudo apt update && sudo apt upgrade -y
```

## 第三步：安全加固 — 修改 SSH 端口

```bash
# 备份 SSH 配置
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak

# 修改 SSH 端口（将 22 改成你选择的端口，例如 2222）
sudo sed -i 's/^#Port 22/Port 2222/' /etc/ssh/sshd_config

# 重启 SSH 服务
sudo systemctl restart sshd
```

> ⚠️ 重要：修改端口前，先在腾讯云防火墙里开放新端口！
> 控制台 → 防火墙 → 添加规则 → TCP 端口 2222
> 同时确保 80 和 443 端口也是开放的。

## 第四步：创建部署用户

```bash
# 创建 deploy 用户（用于 GitHub Actions rsync）
sudo adduser --disabled-password --gecos "" deploy

# 创建网站目录并赋权
sudo mkdir -p /var/www/production /var/www/staging
sudo chown -R deploy:deploy /var/www/
```

## 第五步：配置 SSH 密钥（在你的本地电脑上操作）

```bash
# 在本地生成一对 SSH 密钥（用于部署）
ssh-keygen -t ed25519 -f ~/.ssh/palimpsestus-deploy -C "deploy@palimpsestus"

# 将公钥复制到服务器
ssh-copy-id -i ~/.ssh/palimpsestus-deploy.pub -p 2222 deploy@110.42.215.140

# 测试连接
ssh -i ~/.ssh/palimpsestus-deploy -p 2222 deploy@110.42.215.140
```

> 将 `~/.ssh/palimpsestus-deploy` 的**私钥内容**复制，
> 稍后添加到 GitHub 仓库的 Secrets 中（名称: `SERVER_SSH_KEY`）。

## 第六步：禁用密码登录（确认密钥登录成功后再操作！）

```bash
sudo sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/^PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart sshd
```

## 第七步：配置防火墙

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 2222/tcp comment 'SSH'
sudo ufw allow 80/tcp comment 'HTTP'
sudo ufw allow 443/tcp comment 'HTTPS'
sudo ufw enable
sudo ufw status
```

## 第八步：安装 Docker（如果未预装）

```bash
# 确认 Docker 是否已安装
docker --version

# 如果没有，安装：
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ubuntu

# 安装 Docker Compose 插件
sudo apt install docker-compose-plugin -y

# 验证
docker compose version
```

## 第九步：部署 Nginx 容器

```bash
# 创建部署目录
sudo mkdir -p /opt/palimpsestus/{nginx/ssl/production,nginx/ssl/staging,nginx/conf.d,logs/nginx}

# 上传配置文件（从你的本地电脑）
# scp -P 2222 deploy/docker-compose.yml ubuntu@110.42.215.140:/opt/palimpsestus/
# scp -P 2222 deploy/nginx/nginx.conf ubuntu@110.42.215.140:/opt/palimpsestus/nginx/
# scp -P 2222 deploy/nginx/conf.d/palimpsestus.conf ubuntu@110.42.215.140:/opt/palimpsestus/nginx/conf.d/

# 上传 SSL 证书
# 腾讯云下载的证书通常包含：
#   xxx.crt (或 fullchain.crt) → 重命名为 fullchain.pem
#   xxx.key                     → 重命名为 privkey.pem
# scp -P 2222 fullchain.pem ubuntu@110.42.215.140:/opt/palimpsestus/nginx/ssl/production/
# scp -P 2222 privkey.pem ubuntu@110.42.215.140:/opt/palimpsestus/nginx/ssl/production/

# 生成 staging Basic Auth 密码文件
sudo apt install apache2-utils -y
htpasswd -cb /opt/palimpsestus/nginx/htpasswd myouza 'Palimpsestus2026!'

# 修正目录权限（deploy 用户需要写权限，nginx 只需读权限）
sudo chown -R deploy:deploy /var/www/

# 启动容器
cd /opt/palimpsestus
sudo docker compose up -d

# 查看状态
sudo docker compose ps
sudo docker compose logs nginx
```

## 第十步：验证

```bash
# 测试 HTTP → HTTPS 重定向
curl -I http://palimpsestus.art

# 测试 HTTPS
curl -I https://palimpsestus.art

# 测试 staging Basic Auth
curl -I https://stage.palimpsestus.art
# 应返回 401 Unauthorized

curl -u myouza:'Palimpsestus2026!' https://stage.palimpsestus.art
# 应返回 200
```

## GitHub Secrets 配置

在公开仓库 (palimpsestus-site) 的 Settings → Secrets → Actions 中添加：

| Secret 名称 | 值 |
|---|---|
| `SERVER_HOST` | `110.42.215.140` |
| `SERVER_SSH_PORT` | `2222`（你设定的端口） |
| `SERVER_USER` | `deploy` |
| `SERVER_SSH_KEY` | 部署私钥的完整内容 |
| `CONTENT_REPO` | `你的用户名/palimpsestus-content` |
| `CONTENT_DEPLOY_KEY` | 内容仓库 Deploy Key 的私钥 |

在私有仓库 (palimpsestus-content) 的 Secrets 中添加：

| Secret 名称 | 值 |
|---|---|
| `FRAMEWORK_DISPATCH_TOKEN` | GitHub PAT（需要 `repo` 权限） |
| `FRAMEWORK_REPO` | `你的用户名/palimpsestus-site` |

## SSL 证书续期提醒

腾讯云免费 SSL 证书有效期为 1 年。到期前：
1. 去腾讯云控制台申请新证书
2. 下载 Nginx 格式的证书文件
3. 替换服务器上 `/opt/palimpsestus/nginx/ssl/` 里的文件
4. 重启容器：`sudo docker compose restart nginx`
