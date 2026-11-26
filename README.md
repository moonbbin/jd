# 我的美国优选 IP 自动更新列表

全美国版 Cloudflare 优选 IP 列表，每 6 小时自动更新，给 edgetunnel 用。
格式和 LancelotRar/best-cf-ips 一样，一行一个：`IP:443#US 🇺🇸`

## 它怎么来的

`update.py` 每 6 小时去拉 4 个公开来源，只留美国的、而且是真 Cloudflare 边缘 IP 的，去重后写成：
- `best-cf-us.txt`：全部美国 IP（2026-11-26 实测 26 个）
- `best-cf-us-top20.txt`：前 20 个

来源：
- LancelotRar/best-cf-ips 的 top400（只筛 #US，今天只有 4 个）
- bestcf.pages.dev 的天诚 US、天诚2 US、Gslege US 三个美国专表（会过滤掉里面混的非 Cloudflare 的 ProxyIP）

拉不到或少于 5 个时不覆盖旧文件，避免一次上游故障把节点清空。

## 部署步骤（只做一次）

### 第 1 步：建 GitHub 仓库
在 GitHub 新建一个**公开**仓库，比如叫 `my-cf-us`，不要勾选自动生成 README。

### 第 2 步：上传文件
把这个文件夹里的全部文件传到仓库根目录，保持结构：
```
my-cf-us/
  update.py
  best-cf-us.txt
  best-cf-us-top20.txt
  README.md
  .github/workflows/update.yml
```
注意 `.github` 是隐藏文件夹，别漏传。用网页上传时如果传不上去这个文件夹，就在仓库里点 Create new file，文件名写 `.github/workflows/update.yml`，把内容粘进去。

### 第 3 步：先手动跑一次
进仓库的 Actions 页，点左边 `Update US CF IP list`，再点 Run workflow。等它变绿，说明自动更新通了。以后每 6 小时它自己跑（北京时间 08:00 / 14:00 / 20:00 / 02:00）。

### 第 4 步：拿到你的链接
你的链接就是把下面这条里的用户名和仓库名换成你自己的：
```
https://raw.githubusercontent.com/你的用户名/my-cf-us/main/best-cf-us-top20.txt
```
先在浏览器里打开它，能看到 IP 列表就是对的。

### 第 5 步：填回 edgetunnel
打开 edgetunnel 后台，把上面这条链接粘到“自定义优选”框里（不要点“订阅接口”），点开始优选，再点保存。然后到手机客户端更新订阅，选 US 节点。

## 注意事项

- **全美国 = 延迟高。** 从国内连美国 Cloudflare 节点一般 150–250ms，刷视频、测速都比 SG 慢，这是正常的。图快就用 SG，图美国出口才用这个。
- **美国节点不保证能解锁 Muse 视频生成。** Muse 之前提示的地区不可用，不只看 IP，还看账号注册地区、时区等。换美国 IP 只能解决“IP 地区”这一层，账号层锁住了还是生成不了。先用这份测一次，不行就别反复提交生成请求。
- **优选 IP 的国家是按扫描方路由标注的。** Cloudflare 是 anycast，同一个 IP 在不同运营商下可能落到不同国家。标注 US 不等于你这边连过去出口一定是美国，以客户端实际测速和出口 IP 查询为准。
- 想改成别的国家（比如 SG+US），改 `update.py` 里的 `SOURCES` 和筛选条件就行，结构不用动。
