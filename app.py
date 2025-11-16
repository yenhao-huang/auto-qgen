#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI Application - Excel 數據增強服務 API
"""

import os
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel

from service.augment_service import AugmentService


# ==================== 應用程式初始化 ====================
app = FastAPI(
    title="Excel 數據增強服務 API",
    description="將 Excel 檔案解析並生成增強查詢的 API 服務",
    version="1.0.0"
)


# ==================== 異常處理器 ====================
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """處理請求驗證錯誤，提供詳細的錯誤信息"""
    print("\n" + "="*80)
    print("[DEBUG] 請求驗證失敗 (422 錯誤)")
    print(f"[DEBUG] 請求路徑: {request.url.path}")
    print(f"[DEBUG] 請求方法: {request.method}")
    print(f"[DEBUG] 驗證錯誤詳情:")
    for error in exc.errors():
        print(f"  - 欄位: {error.get('loc')}")
        print(f"    類型: {error.get('type')}")
        print(f"    訊息: {error.get('msg')}")
    print("="*80 + "\n")

    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "body": str(exc.body) if hasattr(exc, 'body') else None
        }
    )

# 創建臨時目錄用於存放上傳的檔案
TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)

RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)


# ==================== 資料模型 ====================
class AugmentResponse(BaseModel):
    """數據增強回應模型"""
    success: bool
    message: str
    parsed_data_path: Optional[str] = None
    augmented_queries_path: Optional[str] = None
    total_count: int = 0
    error: Optional[str] = None


class ConfigRequest(BaseModel):
    """配置請求模型"""
    parser_url: str = "https://openrouter.ai/api"
    parser_model: str = "z-ai/glm-4.5-air:free"
    parser_api_key: str
    parser_use_openrouter: bool = True
    parser_max_retries: int = 3

    augmenter_url: str = "https://openrouter.ai/api"
    augmenter_model: str = "openai/gpt-oss-20b:free"
    augmenter_api_key: str
    augmenter_use_openrouter: bool = True
    augmenter_max_retries: int = 3
    augmenter_prompt_name: str = "default"


# ==================== API 端點 ====================

@app.get("/")
async def root():
    """根端點 - 服務健康檢查"""
    return {
        "service": "Excel 數據增強服務 API",
        "status": "running",
        "version": "1.0.0"
    }


@app.post("/api/v1/data_augment", response_model=AugmentResponse)
async def data_augment(
    file: UploadFile = File(..., description="上傳的 Excel 檔案 (.xlsx)"),
    parser_url: str = Form(default="https://openrouter.ai/api"),
    parser_model: str = Form(default="z-ai/glm-4.5-air:free"),
    parser_api_key: str = Form(..., description="Parser LLM API Key"),
    parser_use_openrouter: bool = Form(default=True),
    parser_max_retries: int = Form(default=3),
    augmenter_url: str = Form(default="https://openrouter.ai/api"),
    augmenter_model: str = Form(default="openai/gpt-oss-20b:free"),
    augmenter_api_key: str = Form(..., description="Augmenter LLM API Key"),
    augmenter_use_openrouter: bool = Form(default=True),
    augmenter_max_retries: int = Form(default=3),
    augmenter_prompt_name: str = Form(default="default"),
    skip_parser: bool = Form(default=False)
):
    """
    數據增強 API 端點

    接收 Excel 檔案，執行解析和增強查詢生成，返回 JSON 結果

    Args:
        file: 上傳的 Excel 檔案
        parser_url: Parser LLM 服務 URL
        parser_model: Parser LLM 模型名稱
        parser_api_key: Parser LLM API Key
        parser_use_openrouter: 是否使用 OpenRouter
        parser_max_retries: Parser 最大重試次數
        augmenter_url: Augmenter LLM 服務 URL
        augmenter_model: Augmenter LLM 模型名稱
        augmenter_api_key: Augmenter LLM API Key
        augmenter_use_openrouter: 是否使用 OpenRouter
        augmenter_max_retries: Augmenter 最大重試次數
        augmenter_prompt_name: Augmenter Prompt 名稱
        skip_parser: 是否跳過 Parser 步驟

    Returns:
        AugmentResponse: 包含處理結果和輸出路徑的回應
    """

    print("\n" + "="*80)
    print("[DEBUG] data_augment API 被調用")
    print(f"[DEBUG] 接收檔案: {file.filename}")
    print(f"[DEBUG] Parser 配置: URL={parser_url}, Model={parser_model}")
    print(f"[DEBUG] Augmenter 配置: URL={augmenter_url}, Model={augmenter_model}")
    print(f"[DEBUG] skip_parser={skip_parser}")
    print("="*80 + "\n")

    # 驗證檔案類型
    print(f"[DEBUG] 驗證檔案類型: {file.filename}")
    if not file.filename.endswith(('.xlsx', '.xls')):
        print(f"[DEBUG] 檔案類型驗證失敗")
        raise HTTPException(
            status_code=400,
            detail="只接受 Excel 檔案格式 (.xlsx, .xls)"
        )
    print(f"[DEBUG] 檔案類型驗證通過")

    # 創建時間戳記
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"[DEBUG] 創建時間戳記: {timestamp}")

    # 儲存上傳的檔案
    temp_file_path = TEMP_DIR / f"{timestamp}_{file.filename}"
    print(f"[DEBUG] 臨時檔案路徑: {temp_file_path}")
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        print(f"[DEBUG] 檔案儲存成功")
    except Exception as e:
        print(f"[DEBUG] 檔案儲存失敗: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"檔案儲存失敗: {str(e)}"
        )
    finally:
        file.file.close()

    # 構建配置字典
    print(f"[DEBUG] 構建配置字典")
    config = {
        "parser": {
            "llm": {
                "url": parser_url,
                "model": parser_model,
                "api_key": parser_api_key,
                "use_openrouter": parser_use_openrouter,
                "max_retries": parser_max_retries
            }
        },
        "augmenter": {
            "llm": {
                "url": augmenter_url,
                "model": augmenter_model,
                "api_key": augmenter_api_key,
                "use_openrouter": augmenter_use_openrouter,
                "max_retries": augmenter_max_retries
            },
            "prompt_name": augmenter_prompt_name
        }
    }
    print(f"[DEBUG] 配置字典構建完成")

    # 初始化服務
    print(f"[DEBUG] 開始初始化 AugmentService")
    try:
        service = AugmentService(config=config, quiet=True)
        print(f"[DEBUG] AugmentService 初始化成功")
    except Exception as e:
        print(f"[DEBUG] AugmentService 初始化失敗: {str(e)}")
        # 清理臨時檔案
        if temp_file_path.exists():
            os.remove(temp_file_path)
        raise HTTPException(
            status_code=500,
            detail=f"服務初始化失敗: {str(e)}"
        )

    # 設定輸出目錄
    output_dir = RESULTS_DIR / f"api_{timestamp}"
    print(f"[DEBUG] 輸出目錄: {output_dir}")

    # 執行數據增強
    print(f"[DEBUG] 開始執行數據增強")
    try:
        result = service.run(
            input_file=temp_file_path,
            output_dir=output_dir,
            skip_parser=skip_parser
        )
        print(f"[DEBUG] service.run() 執行完成")
        print(f"[DEBUG] 結果: {result}")

        # 清理臨時檔案
        if temp_file_path.exists():
            os.remove(temp_file_path)
            print(f"[DEBUG] 臨時檔案已清理")

        if result["success"]:
            print(f"[DEBUG] 數據增強成功")
            print(f"[DEBUG] 解析數據路徑: {result['parsed_data_path']}")
            print(f"[DEBUG] 增強查詢路徑: {result['augmented_queries_path']}")
            print(f"[DEBUG] 總數量: {result['total_count']}")
            return AugmentResponse(
                success=True,
                message="數據增強完成",
                parsed_data_path=result["parsed_data_path"],
                augmented_queries_path=result["augmented_queries_path"],
                total_count=result["total_count"]
            )
        else:
            print(f"[DEBUG] 數據增強失敗")
            print(f"[DEBUG] 錯誤: {result.get('error', '未知錯誤')}")
            return AugmentResponse(
                success=False,
                message="數據增強失敗",
                error=result.get("error", "未知錯誤"),
                total_count=0
            )

    except Exception as e:
        print(f"[DEBUG] 執行過程發生異常: {str(e)}")
        import traceback
        print(f"[DEBUG] 異常堆棧:")
        traceback.print_exc()

        # 清理臨時檔案
        if temp_file_path.exists():
            os.remove(temp_file_path)

        raise HTTPException(
            status_code=500,
            detail=f"處理失敗: {str(e)}"
        )


@app.get("/api/v1/download/{file_type}/{timestamp}")
async def download_result(file_type: str, timestamp: str):
    """
    下載結果檔案

    Args:
        file_type: 檔案類型 ('parsed' 或 'augmented')
        timestamp: 結果檔案的時間戳記

    Returns:
        FileResponse: JSON 檔案
    """

    print(f"\n[DEBUG] download_result API 被調用")
    print(f"[DEBUG] file_type={file_type}, timestamp={timestamp}")

    # 驗證檔案類型
    if file_type not in ["parsed", "augmented"]:
        print(f"[DEBUG] 無效的檔案類型: {file_type}")
        raise HTTPException(
            status_code=400,
            detail="file_type 必須是 'parsed' 或 'augmented'"
        )

    # 構建檔案路徑
    result_dir = RESULTS_DIR / f"api_{timestamp}"
    if file_type == "parsed":
        file_path = result_dir / "parsed_data.json"
    else:
        file_path = result_dir / "augmented_queries.json"

    print(f"[DEBUG] 檔案路徑: {file_path}")

    # 檢查檔案是否存在
    if not file_path.exists():
        print(f"[DEBUG] 檔案不存在: {file_path}")
        raise HTTPException(
            status_code=404,
            detail=f"找不到檔案: {file_path}"
        )

    print(f"[DEBUG] 檔案存在，準備返回")
    return FileResponse(
        path=file_path,
        media_type="application/json",
        filename=file_path.name
    )


@app.get("/api/v1/health")
async def health_check():
    """健康檢查端點"""
    return {
        "status": "healthy",
        "service": "Excel 數據增強服務",
        "timestamp": datetime.now().isoformat()
    }


# ==================== 啟動應用程式 ====================
if __name__ == "__main__":
    import uvicorn

    # 啟動 FastAPI 應用程式
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
