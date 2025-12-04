"""
MinerU批量处理优化模块
MVP实现：简化版批量PDF处理功能
"""
import os
import json
import time
from pathlib import Path
from typing import List, Dict, Optional
import zipfile
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# ====================== 批量处理配置 ======================
MAX_WORKERS = 2  # 并发处理数量
MAX_RETRY = 60  # 最大重试次数
RETRY_INTERVAL = 10  # 重试间隔(秒)
SAVE_DIR = "/data/parse_results"  # 结果保存目录

# 确保保存目录存在
os.makedirs(SAVE_DIR, exist_ok=True)

# ====================== 核心功能函数 ======================

def apply_upload_url(token: str, filename: str) -> Optional[tuple]:
    """申请临时上传URL"""
    url = "https://mineru.net/api/v4/file-urls/batch"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "files": [{"name": filename}],
        "model_version": "vlm"
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        result = response.json()

        if result["code"] == 0:
            return result["data"]["batch_id"], result["data"]["file_urls"][0]
        else:
            print(f"❌ 申请URL失败: {result['msg']}")
            return None
    except Exception as e:
        print(f"❌ 申请URL异常: {str(e)}")
        return None

def upload_pdf(upload_url: str, pdf_path: str) -> bool:
    """通过PUT方式上传PDF"""
    try:
        with open(pdf_path, "rb") as f:
            response = requests.put(upload_url, data=f, timeout=60)
        return response.status_code in (200, 201)
    except Exception as e:
        print(f"❌ 上传异常: {str(e)}")
        return False

def poll_result(token: str, batch_id: str, filename: str) -> Optional[str]:
    """轮询解析结果"""
    query_url = f"https://mineru.net/api/v4/extract-results/batch/{batch_id}"

    for retry in range(MAX_RETRY):
        try:
            # 查询状态
            response = requests.get(query_url, headers={"Authorization": f"Bearer {token}"}, timeout=30)
            response.raise_for_status()  # 捕获HTTP错误（4xx/5xx）
            result = response.json()

            # 校验接口返回码
            if result["code"] != 0:
                print(f"❌ 第{retry+1}次查询失败：{result['msg']}")
                time.sleep(RETRY_INTERVAL)
                continue

            # 提取核心字段（严格匹配接口返回结构）
            extract_result = result["data"]["extract_result"]
            if not extract_result:
                print(f"❌ 第{retry+1}次查询：extract_result为空")
                time.sleep(RETRY_INTERVAL)
                continue

            task_info = extract_result[0]
            task_state = task_info["state"]
            task_err_msg = task_info.get("err_msg", "")
            full_zip_url = task_info.get("full_zip_url", "")

            # 打印关键日志（便于排查）
            zip_url_preview = full_zip_url[:60] if full_zip_url else "空"
            print(f"📌 第{retry+1}/{MAX_RETRY}次查询 | 状态：{task_state} | ZIP链接：{zip_url_preview} | 错误：{task_err_msg}")

            # 状态判断逻辑
            if task_state == "done":
                if full_zip_url:
                    # 下载压缩包
                    zip_save_path = os.path.join(SAVE_DIR, f"{batch_id}.zip")
                    print(f"\n✅ 解析完成！开始下载压缩包：{full_zip_url[:60]}...")
                    zip_response = requests.get(full_zip_url, timeout=60)
                    zip_response.raise_for_status()
                    with open(zip_save_path, "wb") as f:
                        f.write(zip_response.content)
                    print(f"✅ 压缩包下载完成：{zip_save_path}")

                    # 解压并提取MD文件
                    pdf_name = os.path.splitext(filename)[0]
                    md_filename = f"{pdf_name}.md"
                    with ZipFile(zip_save_path, "r") as zf:
                        zf.extractall(SAVE_DIR)

                    # 验证MD文件
                    md_file_path = os.path.join(SAVE_DIR, md_filename)
                    if os.path.exists(md_file_path):
                        print(f"✅ MD文件提取成功！路径：{md_file_path}")
                        # 预览MD文件前200字符
                        with open(md_file_path, "r", encoding="utf-8") as f:
                            preview = f.read(200)
                            print(f"\n📝 MD文件内容预览：\n{preview}...")
                        return md_file_path
                    else:
                        print(f"❌ 解压成功但未找到MD文件：{md_filename}")
                        # 列出解压后的文件，便于排查
                        extracted_files = os.listdir(SAVE_DIR)
                        print(f"📂 解压后的文件列表：{extracted_files}")
                        return None
                else:
                    print(f"⚠️ 状态为done，但full_zip_url为空，终止轮询")
                    return None
            elif task_state == "failed":
                print(f"❌ 解析任务失败：{task_err_msg}")
                return None
            else:
                # 任务仍在处理中（pending/running/converting）
                time.sleep(RETRY_INTERVAL)

        except Exception as e:
            print(f"❌ 第{retry+1}次查询异常：{str(e)}")
            time.sleep(RETRY_INTERVAL)

    # 轮询超时
    print(f"\n❌ 轮询超时（已重试{MAX_RETRY}次），请手动查询：")
    print(f"手动查询URL：{query_url}")
    return None

def process_single_pdf(pdf_path: str, token: str) -> Dict:
    """
    处理单个PDF文件
    :param pdf_path: PDF文件路径
    :param token: MinerU API Token
    :return: 处理结果字典 {文件路径, 成功状态, 结果路径/错误信息}
    """
    result = {
        "pdf_path": pdf_path,
        "success": False,
        "result": None
    }

    if not os.path.exists(pdf_path):
        result["result"] = f"文件不存在: {pdf_path}"
        return result

    filename = os.path.basename(pdf_path)
    print(f"\n{'='*60}")
    print(f"处理文件: {filename}")
    print(f"{'='*60}")

    try:
        # 1. 申请临时上传URL
        print(f"📤 申请上传URL...")
        batch_info = apply_upload_url(token, filename)
        if not batch_info:
            result["result"] = "申请上传URL失败"
            return result

        batch_id, upload_url = batch_info

        # 2. 上传文件
        print(f"📤 上传文件...")
        if not upload_pdf(upload_url, pdf_path):
            result["result"] = "文件上传失败"
            return result

        # 3. 轮询解析结果
        print(f"⏳ 等待解析完成...")
        md_path = poll_result(token, batch_id, filename)

        if md_path:
            result["success"] = True
            result["result"] = md_path
            print(f"✅ 解析完成: {md_path}")
        else:
            result["result"] = "解析失败"

    except Exception as e:
        result["result"] = f"处理异常: {str(e)}"
        print(f"❌ {result['result']}")

    return result

def process_batch(pdf_paths: List[str], token: str) -> Dict:
    """
    批量处理PDF文件
    :param pdf_paths: PDF文件路径列表
    :param token: MinerU API Token
    :return: 处理结果字典 {文件路径: 结果}
    """
    results = {}
    success_count = 0
    fail_count = 0

    print(f"📦 开始批量处理 {len(pdf_paths)} 个PDF文件")

    # 使用线程池并行处理
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_pdf = {executor.submit(process_single_pdf, pdf_path, token): pdf_path
                        for pdf_path in pdf_paths}

        for future in as_completed(future_to_pdf):
            pdf_path = future_to_pdf[future]
            try:
                result = future.result()
                results[pdf_path] = result["result"]

                if result["success"]:
                    success_count += 1
                    print(f"✅ 成功: {os.path.basename(pdf_path)}")
                else:
                    fail_count += 1
                    print(f"❌ 失败: {os.path.basename(pdf_path)} - {result['result']}")

            except Exception as e:
                results[pdf_path] = f"处理异常: {str(e)}"
                fail_count += 1
                print(f"❌ 异常: {os.path.basename(pdf_path)} - {str(e)}")

    # 打印汇总
    print(f"\n{'='*60}")
    print("批量处理汇总:")
    print(f"{'='*60}")
    print(f"总数: {len(pdf_paths)} | 成功: {success_count} | 失败: {fail_count}")

    return results

# ====================== 便捷函数 ======================

def get_pdf_files(directory: str) -> List[str]:
    """获取目录中的所有PDF文件"""
    if not os.path.exists(directory):
        print(f"❌ 目录不存在: {directory}")
        return []

    pdf_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.pdf')]
    return sorted(pdf_files)

def process_directory(directory: str, token: str) -> Dict:
    """处理目录中的所有PDF文件"""
    pdf_files = get_pdf_files(directory)
    if not pdf_files:
        print(f"❌ 目录中没有PDF文件: {directory}")
        return {}

    return process_batch(pdf_files, token)

# ====================== 主函数 ======================
if __name__ == "__main__":
    # 示例：处理目录中的所有PDF
    import sys
    if len(sys.argv) > 1:
        directory = sys.argv[1]
        token = os.getenv("MINERU_API_TOKEN", "your_token_here")
        process_directory(directory, token)
    else:
        print("用法: python mineru_batch.py <PDF目录路径>")