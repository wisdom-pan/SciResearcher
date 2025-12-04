# 🚀 快速部署指南

欢迎使用 SciResearcher！本指南将帮助您在 5 分钟内将应用部署到魔搭创空间。

## 📋 部署前准备

### 1️⃣ 获取必要信息

您需要准备以下信息：

- **魔搭账号**: 访问 [www.modelscope.cn](https://www.modelscope.cn) 注册
- **访问Token**: [创建访问Token](https://www.modelscope.cn/my/accesstoken)
- **创空间**: [创建创空间](https://www.modelscope.cn/studios/)

### 2️⃣ 记录您的信息

```
魔搭用户名: _______________
创空间项目名: _______________
访问Token: ms-______________
```

## ⚡ 快速部署（3 步完成）

### 步骤 1: 配置
```bash
cp deploy_config.example deploy_config.sh
```

编辑 `deploy_config.sh`，填入您的信息：
```bash
MODELSCOPE_TOKEN="ms-您的Token"
USERNAME="您的用户名"
PROJECT_NAME="您的项目名"
```

### 步骤 2: 运行
```bash
chmod +x deploy_to_studio.sh
./deploy_to_studio.sh
```

### 步骤 3: 配置环境变量
1. 访问您的创空间
2. 点击"设置" → "环境变量"
3. 添加:
   - `MODELSCOPE_API_KEY`: 您的魔搭API密钥
   - `MINERU_API_TOKEN`: 您的MinerU Token
4. 保存并重启

## ✅ 完成！

5-10 分钟后，您的应用就可以使用了！

访问链接: `https://www.modelscope.cn/studios/您的用户名/您的项目名`

---

## 🔗 相关链接

- [魔搭社区](https://www.modelscope.cn/)
- [创空间](https://www.modelscope.cn/studios/)
- [访问Token](https://www.modelscope.cn/my/accesstoken)
- [API密钥](https://dashscope.console.aliyun.com/apiKey)
- [MinerU](https://mineru.net)

---

## 🆘 需要帮助？

- 查看 [README.md](./README.md) 了解完整文档
- 查看 [部署文档](./README.md#魔搭创空间部署) 了解详细步骤
- 查看 [故障排除](./README.md#故障排除) 解决常见问题
