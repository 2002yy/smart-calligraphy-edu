# teacher-web

教师端前端项目，基于 `Vue 3 + Vite + vue-router + Pinia + Axios`，已接入 `api-server`，可用于本地演示、答辩展示和接口联调。

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
cd c:\Users\96967\Desktop\大创\code\teacher-web
npm install
npm run dev
```

### 方式二：使用项目自带脚本

`cmd` 方式：

```cmd
cd /d c:\Users\96967\Desktop\大创\code
scripts\start-teacher-web.cmd
```

PowerShell 方式：

```powershell
cd c:\Users\96967\Desktop\大创\code
powershell -ExecutionPolicy Bypass -File .\scripts\start-teacher-web.ps1
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

- 教师登录与当前用户信息获取
- 课程创建与课程列表展示
- 班级创建与班级切换
- 练习任务发布
- 教学看板展示
- 作业批阅记录展示
- 班级报告展示
- 页面路由化导航与状态提示
