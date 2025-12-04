#!/bin/bash
# SciResearcher 部署到魔搭创空间的通用脚本
# 使用方法: 1) 复制 deploy_config.example 为 deploy_config.sh
#          2) 修改 deploy_config.sh 中的配置
#          3) 运行 ./deploy_to_studio.sh

# 加载配置文件（如果存在）
if [ -f "deploy_config.sh" ]; then
    source deploy_config.sh
elif [ -f "deploy_config.example" ]; then
    echo "⚠️  未找到 deploy_config.sh，正在使用模板配置..."
    echo "💡 提示：复制 deploy_config.example 为 deploy_config.sh 并修改配置"
    echo ""
fi

# ===========================
# ⚙️ 默认配置（如果配置文件不存在）
# ===========================

# 您的魔搭访问token（从 https://www.modelscope.cn/my/accesstoken 获取）
MODELSCOPE_TOKEN="${MODELSCOPE_TOKEN:-ms-xxxxxxxxxxxxxxxxxxxxxxxx}"

# 您的创空间用户名
USERNAME="${USERNAME:-your_username}"

# 您的项目名称（创空间名称）
PROJECT_NAME="${PROJECT_NAME:-SciResearcher}"

# 完整的仓库URL（包含token）
REPO_URL="http://oauth2:${MODELSCOPE_TOKEN}@www.modelscope.cn/studios/${USERNAME}/${PROJECT_NAME}.git"

# 您的项目本地路径（如果脚本在项目根目录运行，可保持不变）
PROJECT_DIR="${PROJECT_DIR:-.}"

# Git分支
BRANCH="${BRANCH:-master}"

# ===========================
# 🚀 部署流程（无需修改）
# ===========================

echo "🚀 SciResearcher 部署到魔搭创空间"
echo "================================="
echo ""

# 验证配置
if [ "$MODELSCOPE_TOKEN" = "ms-xxxxxxxxxxxxxxxxxxxxxxxx" ]; then
    echo "❌ 错误：请先在脚本顶部配置您的 MODELSCOPE_TOKEN"
    echo ""
    echo "获取 Token 的步骤："
    echo "1. 访问 https://www.modelscope.cn/my/accesstoken"
    echo "2. 登录并创建新的访问Token"
    echo "3. 复制Token并替换脚本中的 MODELSCOPE_TOKEN 变量"
    echo ""
    exit 1
fi

if [ "$USERNAME" = "your_username" ]; then
    echo "❌ 错误：请先在脚本顶部配置您的 USERNAME"
    exit 1
fi

if [ "$PROJECT_NAME" = "SciResearcher" ] && [ "$MODELSCOPE_TOKEN" != "ms-xxxxxxxxxxxxxxxxxxxxxxxx" ]; then
    echo "⚠️  警告：您正在使用默认的 PROJECT_NAME: SciResearcher"
    echo "💡 建议修改为您的实际项目名以避免冲突"
    echo ""
fi

echo "✅ 配置验证通过"
echo ""
echo "部署信息："
echo "  - 用户名: $USERNAME"
echo "  - 项目名: $PROJECT_NAME"
echo "  - 仓库: $REPO_URL"
echo ""

# 检查Git
echo "📋 检查依赖..."
if ! command -v git &> /dev/null; then
    echo "❌ 错误：未找到 Git，请先安装 Git"
    exit 1
fi
echo "✅ Git 已安装"

# 安装 git lfs
echo ""
echo "📦 安装 Git LFS..."
git lfs install

# 克隆仓库
echo ""
echo "📥 克隆创空间仓库..."
if [ -d "$PROJECT_NAME" ]; then
    echo "📂 仓库已存在，更新代码..."
    cd $PROJECT_NAME
    git pull origin $BRANCH
else
    echo "📥 克隆新仓库..."
    git clone "$REPO_URL" $PROJECT_NAME
    cd $PROJECT_NAME
fi

# 复制项目文件
echo ""
echo "📋 同步项目文件..."
rsync -av --exclude='.git' --exclude=$PROJECT_NAME $PROJECT_DIR/ ./

# 提交更改
echo ""
echo "📤 提交更改..."
git add .
git commit -m "🚀 Deploy SciResearcher to ModelScope Studio - $(date +%Y-%m-%d)

✨ Features:
- Gradio Web UI for document analysis
- MinerU PDF parsing with OCR
- ChromaDB vector search
- Smart Q&A and deep research

📊 Capabilities:
- PDF upload (max 200MB)
- Multi-modal parsing (text, images, tables, formulas)
- RAG-based intelligent Q&A
- Multi-dimensional research analysis

🔧 Tech Stack:
- smolagents (Multi-Agent Framework)
- MinerU API (PDF Parsing)
- ChromaDB (Vector Database)
- Gradio (Web UI)
- ModelScope API (Qwen Models)"

# 推送到创空间
echo ""
echo "🚀 推送到创空间..."
git push origin $BRANCH

echo ""
echo "================================="
echo "✅ 部署成功完成！"
echo "================================="
echo ""
echo "🔗 访问您的应用："
echo "   https://www.modelscope.cn/studios/${USERNAME}/${PROJECT_NAME}"
echo ""
echo "⚙️  下一步："
echo "1. 登录创空间检查部署状态"
echo "2. 在设置中添加环境变量："
echo "   - MODELSCOPE_API_KEY: 您的魔搭API密钥"
echo "   - MINERU_API_TOKEN: 您的MinerU Token"
echo "3. 等待构建完成（首次可能需要5-10分钟）"
echo "4. 开始使用！"
echo ""
echo "💡 提示：首次构建期间请耐心等待，完成后会有邮件通知"
echo ""

