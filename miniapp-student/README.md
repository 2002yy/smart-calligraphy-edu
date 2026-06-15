# 智慧书法学生小程序

学生端微信小程序 MVP，基于 uni-app + Vue 3 + Pinia，复用现有 FastAPI 后端。

## 功能范围

- 学生登录与 token 保存
- 今日任务/任务列表
- 拍照或相册上传作品
- 发起 AI 评分并查看结果
- 历史作品
- 成长档案/个人中心

## 本地运行

```bash
npm install
npm run dev:mp-weixin
```

默认后端地址为 `http://127.0.0.1:8000`。如需修改：

```bash
VITE_API_BASE_URL=https://your-api.example.com npm run dev:mp-weixin
```

微信小程序真机调试和正式发布需要 HTTPS 域名，并在小程序后台配置 request/uploadFile 合法域名。
