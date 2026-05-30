# Cloudflare Tunnel 外网演示操作稿

## 1. 这份文档解决什么问题

这份操作稿用于把当前项目从“只能本机或同一局域网访问”，切换成“手机外网也能打开”的演示模式。

适用场景：

- 大创答辩现场演示
- 老师异地查看教师端、学生端页面
- 手机不和电脑处于同一局域网时的联调验证

注意：

- 这是一套“外网演示版”方案，不是长期正式部署方案
- Cloudflare Quick Tunnel 地址通常是临时的，重启后可能变化
- 因此脚本也分为“本地内网版”和“外网演示版”两套

## 2. 本地内网版和外网演示版的区别

### 2.1 本地内网版

适合：

- 电脑本机开发
- 同一 Wi-Fi 下的手机调试
- 日常改代码

使用脚本：

- `scripts\02_本地联调\1_启动后端_本地版.cmd`
- `scripts\02_本地联调\2_启动教师端_本地版.cmd`
- `scripts\02_本地联调\3_启动学生端_本地版.cmd`

特点：

- 前端通常使用 `npm run dev`
- 后端地址可以是 `http://127.0.0.1:8000`
- 不需要 Cloudflare Tunnel

### 2.2 外网演示版

适合：

- 非同一局域网访问
- 答辩展示
- 远程给老师看

使用脚本：

- `scripts\03_外网演示\1_启动后端_外网版.cmd`
- `scripts\03_外网演示\2_启动教师端_外网版.cmd`
- `scripts\03_外网演示\3_启动学生端_外网版.cmd`

特点：

- 后端使用 `0.0.0.0` 对外监听
- 前端使用 `build + preview`，更接近真实部署
- 需要额外运行 `cloudflared tunnel --url ...`
- 前端 `.env.local` 必须写成“后端公网地址”

## 3. 开始前准备

### 3.1 确认 cloudflared 已安装

在终端运行：

```cmd
cloudflared version
```

如果能看到版本号，说明已安装成功。

如果没有安装，请先参考 Cloudflare 官方下载页：

- <https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/>

### 3.2 确认项目依赖已经安装

后端：

```cmd
cd /d c:\Users\96967\Desktop\大创\code\api-server
python -m pip install -r requirements.txt
```

前端：

```cmd
cd /d c:\Users\96967\Desktop\大创\code
scripts\01_安装与修复\1_安装前端依赖.cmd
```

## 4. 外网演示的推荐启动顺序

必须按这个顺序来：

1. 启动 `api-server`
2. 给 `api-server` 开 Cloudflare Tunnel
3. 把后端公网地址写进两个前端的 `.env.local`
4. 启动 `teacher-web`
5. 启动 `student-app`
6. 给教师端开 Tunnel
7. 给学生端开 Tunnel
8. 手机上访问教师端 / 学生端公网地址

这样做的原因是：

- 前端必须先知道后端公网地址是什么
- 如果先启动前端，再去改 `.env.local`，你还得重新启动一遍

## 5. 第一步：启动后端公网模式

在终端 A 中运行：

```cmd
cd /d c:\Users\96967\Desktop\大创\code
scripts\03_外网演示\1_启动后端_外网版.cmd
```

它实际会启动：

```cmd
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

如果启动成功，本机可以访问：

- Swagger：`http://127.0.0.1:8000/docs`

## 6. 第二步：给后端开 Cloudflare Tunnel

在终端 B 中运行：

```cmd
cloudflared tunnel --url http://localhost:8000
```

成功后会看到一个公网地址，类似：

```text
https://abc-def-ghi.trycloudflare.com
```

这个地址就是：

- 后端公网 API 地址

请先把它记下来，后面两个前端都要用它。

## 7. 第三步：修改前端 .env.local

### 7.1 修改教师端

文件：

- `teacher-web\.env.local`

内容示例：

```env
VITE_API_BASE_URL=https://abc-def-ghi.trycloudflare.com
```

### 7.2 修改学生端

文件：

- `student-app\.env.local`

内容示例：

```env
VITE_API_BASE_URL=https://abc-def-ghi.trycloudflare.com
```

注意：

- 这里必须填写“后端 Tunnel 地址”
- 不能再写 `127.0.0.1`
- 不能写 `localhost`

## 8. 第四步：启动教师端公网模式

在终端 C 中运行：
```cmd
cd /d c:\Users\96967\Desktop\大创\code
scripts\03_外网演示\2_启动教师端_外网版.cmd
```
该脚本内部会自动切换目录并执行：
```cmd
cd /d c:\Users\96967\Desktop\大创\code\teacher-web
npm run build
npm run preview -- --host 0.0.0.0 --port 4174
```
本机访问地址：

http://localhost:4174

注意：

- 脚本必须从 code 目录调用
- 实际运行目录是 teacher-web
- 端口 4174 为教师端


## 9. 第五步：启动学生端公网模式

在终端 D 中运行：
```cmd
cd /d c:\Users\96967\Desktop\大创\code
scripts\03_外网演示\3_启动学生端_外网版.cmd
```
该脚本内部会自动切换目录并执行：
```cmd
cd /d c:\Users\96967\Desktop\大创\code\student-app
npm run build
npm run preview -- --host 0.0.0.0 --port 4175
```
本机访问地址：

http://localhost:4175

注意：

- 脚本必须从 code 目录调用
- 实际运行目录是 student-app
- 端口 4175 为学生端

## 10. 第六步：给教师端和学生端开 Tunnel

### 10.1 教师端 Tunnel

在终端 E 中运行：

```cmd
cloudflared tunnel --url http://localhost:4174
```

你会得到一个公网地址，类似：

```text
https://teacher-demo-123.trycloudflare.com
```

### 10.2 学生端 Tunnel

在终端 F 中运行：

```cmd
cloudflared tunnel --url http://localhost:4175
```

你会得到另一个公网地址，类似：

```text
https://student-demo-456.trycloudflare.com
```

## 11. 手机上最终访问哪个地址

手机最终访问的是两个前端公网地址：

- 教师端：教师端 Tunnel 地址
- 学生端：学生端 Tunnel 地址

例如：

- `https://teacher-demo-123.trycloudflare.com`
- `https://student-demo-456.trycloudflare.com`

前端内部会再去请求：

- `https://abc-def-ghi.trycloudflare.com`

也就是你的后端公网地址。

## 12. 你最终会同时开着哪些窗口

建议答辩前保持以下 6 个终端窗口都不要关：

1. 后端服务窗口
2. 后端 Tunnel 窗口
3. 教师端 preview 窗口
4. 教师端 Tunnel 窗口
5. 学生端 preview 窗口
6. 学生端 Tunnel 窗口

## 13. 常见报错排查

### 13.1 手机能打开页面，但接口失败

常见原因：

- `.env.local` 里还是 `127.0.0.1`
- 前端改了 `.env.local` 之后没有重新启动
- 后端 Tunnel 已断开

排查顺序：

1. 检查 `teacher-web\.env.local` 和 `student-app\.env.local`
2. 确认里面写的是 `https://...trycloudflare.com`
3. 重启教师端和学生端公网脚本
4. 确认后端 Tunnel 终端还在运行

### 13.2 手机能打开前端，但登录失败

常见原因：

- 前端请求到了错误的后端地址
- 后端没有正常运行
- 账号密码输错

建议先在电脑浏览器中测试：

1. 打开教师端公网地址
2. 尝试登录
3. 如果电脑也失败，就不是手机问题，而是后端或前端配置问题

### 13.3 前端 Tunnel 能打开，但页面空白

常见原因：

- `npm run build` 失败
- `npm run preview` 没有正常启动
- Tunnel 指向了错误端口

排查：

1. 本机先打开 `http://localhost:4174`
2. 本机再打开 `http://localhost:4175`
3. 本机都正常，再去看 Tunnel 地址

### 13.4 Swagger 正常，前端数据还是不出来

这通常说明：

- 后端本身是活的
- 但前端 `.env.local` 没改对
- 或者前端没有重启

优先检查：

- `.env.local`
- 前端 `preview` 是否重启过

### 13.5 Tunnel 地址突然失效

Quick Tunnel 是临时地址。

一旦：

- 关闭了 `cloudflared` 窗口
- 电脑休眠
- 网络中断

这个地址就可能失效，需要重新执行一次：

```cmd
cloudflared tunnel --url http://localhost:你的端口
```

然后重新替换前端 `.env.local` 中的后端地址。

## 14. 最简答辩演示版建议

如果你时间紧张，建议至少保住这三条：

1. 后端 Tunnel 正常
2. 教师端 Tunnel 正常
3. 学生端 Tunnel 正常

然后答辩时主讲：

- 教师端看板 / 任务编排 / 批阅复盘
- 学生端任务中心 / 提交评测 / 成长档案
- 后端 Swagger 作为技术闭环补充

## 15. 一句话记忆版

外网演示版的核心逻辑只有一句话：

先把后端变成公网地址，再把这个公网地址写进两个前端，然后分别把教师端和学生端页面也暴露到公网。
