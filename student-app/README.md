# student-app

学生端前端项目，基于 `Vue 3 + Vite + vue-router + Pinia + Axios`，已接入 `api-server`，可用于本地双端联调和答辩演示。

## 技术栈

- Vue 3
- Vite
- vue-router
- Pinia
- Axios
- TypeScript

## 启动步骤

### 方式一：直接在项目目录运行

```powershell
cd c:\Users\96967\Desktop\大创\code\student-app
npm install
npm run dev
```

### 方式二：使用项目自带脚本

`cmd` 方式：

```cmd
cd /d c:\Users\96967\Desktop\大创\code
scripts\start-student-app.cmd
```

PowerShell 方式：

```powershell
cd c:\Users\96967\Desktop\大创\code
powershell -ExecutionPolicy Bypass -File .\scripts\start-student-app.ps1
```

如果依赖还没装好，可先执行：

```cmd
cd /d c:\Users\96967\Desktop\大创\code
scripts\install-frontends.cmd
```

## 环境变量

参考 `.env.example`：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## 当前已接通功能

- 学生登录与当前用户信息获取
- 班级选择与加入班级
- 任务列表与任务详情查看
- 作业提交
- AI 评测触发与结果查看
- 成长档案展示
- 页面路由化导航与状态提示
