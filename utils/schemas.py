#!/usr/bin/env python3
"""
Pydantic schemas for LLM evaluation pipeline
統一所有資料格式，確保型別安全和預設值
"""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# ==================== 基礎資料結構 ====================

class GroundTruth(BaseModel):
    """標準答案資料結構"""
    file_name: str = Field(..., description="正確的檔案名稱")
    item_id: List[int] = Field(..., description="正確的項目 ID 列表")

    class Config:
        json_schema_extra = {
            "example": {
                "file_name": "一般服務/表12-4.xlsx",
                "item_id": [1, 20, 21]
            }
        }


class Prediction(BaseModel):
    """預測結果資料結構"""
    rank: int = Field(..., description="排名（1-based）")
    file: str = Field(..., description="預測的檔案名稱")
    year: int = Field(..., description="預測的年份")
    row: int = Field(..., description="預測的行數")
    is_correct: bool = Field(default=False, description="是否為正確答案")
    path: List[str] = Field(default_factory=list, description="資料路徑")
    score: Optional[float] = Field(default=None, description="相似度分數")

    class Config:
        json_schema_extra = {
            "example": {
                "rank": 1,
                "file": "專款項目/表1-2.xlsx",
                "year": 112,
                "row": 15,
                "is_correct": False,
                "path": ["巡迴醫療", "目標執行數", "--總服務人次"],
                "score": 0.85
            }
        }

class AugmenterInput(BaseModel):
    """原始回答資料（Pipeline 輸入）"""
    keyword: Dict[str, Any] = Field(..., description="問題增生關鍵字")
    ground_truth: GroundTruth = Field(..., description="標準答案")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="額外的 metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "keyword": {
                    "title": "表12-4中醫門診總額一般服務項目執行情形\n",
                    "製表人": "製表人：陳聿萱，分機：2626",
                    "備註": "註：1.各年度預算數：112年編列預算如下，合計714.6百萬元，後續年度預數算為前一年預算\n        ×(1+當年一般服務成長率)。\n     (1)協商因素之「多重慢性疾病之中醫醫療照護密集度」經費為476.7百萬元。\n     (2)非協商因素之「醫療服務成本指數改變率」經費為237.9百萬元。\n    2.112年新增「多重慢性疾病之中醫醫療照護密集度」，預算476.7百萬元，新增支付標準A91\n      整合醫療照護費加計(70點/件)，自112.3.1生效，支付標準規定：\n     (1)收案對象：慢性病或重大傷病，且為多重疾病。\n     (2)診療時間合計10分鐘以上，並根據診斷結果至少提供1項中醫醫療衛教(如中醫飲食衛教、\n         穴位經絡衛教、簡易中醫運動衛教或各類中藥使用衛教等)，並於病歷記錄評估結果及\n        所提供之中醫醫療衛教項目。\n    3.執行目標及預期效益評估指標如上表，以112年修訂支付標準後之實施時程等比率換算目\n       標值，112年執行目標人次為567.5萬人次(681萬人次×10/12)。\n    4.114年預算執行率，以申報點數為分子，並擷取到總額協商前可取得之月份(如1~6月或1~5月)。",
                },
                "ground_truth": {
                    "file_name": "一般服務/表12-4.xlsx",
                    "item_id": [1, 20, 21]
                },
                "metadata": {"category": "一般服務"}
            }
        }


class AugmentedQuery(BaseModel):
    """LLM 增強後的查詢（LLMAugmenter 輸出）"""
    augmented_queries: List[str] = Field(default_factory=list, description="LLM 生成的擴展查詢")
    ground_truth: GroundTruth = Field(..., description="標準答案")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="額外的 metadata")

    class Config:
        json_schema_extra = {
            "augmenter_output_by_query": {
                "augmented_queries": [
                    "民國112年執行目標人次數",
                    "2023年度目標執行數",
                    "112年服務人次目標值"
                ],
                "ground_truth": {
                    "file_name": "一般服務/表12-4.xlsx",
                    "item_id": [1, 20, 21]
                },
                "metadata": {
                    "query_id": 7,
                    "original_query": "112年這個項目設定了多少人次的執行目標？",
                }
            },
            "augmenter_output_by_keyword": {
                "augmented_queries": [
                    "民國112年執行目標人次數",
                    "2023年度目標執行數",
                    "112年服務人次目標值"
                ],
                "ground_truth": {
                    "file_name": "一般服務/表12-4.xlsx",
                    "item_id": [1, 20, 21]
                },
                "metadata": {
                    "keyword": {
                        "title": "表12-4中醫門診總額一般服務項目執行情形\n",
                        "製表人": "製表人：陳聿萱，分機：2626",
                        "備註": "註：1.各年度預算數：112年編列預算如下，合計714.6百萬元，後續年度預數算為前一年預算\n        ×(1+當年一般服務成長率)。\n     (1)協商因素之「多重慢性疾病之中醫醫療照護密集度」經費為476.7百萬元。\n     (2)非協商因素之「醫療服務成本指數改變率」經費為237.9百萬元。\n    2.112年新增「多重慢性疾病之中醫醫療照護密集度」，預算476.7百萬元，新增支付標準A91\n      整合醫療照護費加計(70點/件)，自112.3.1生效，支付標準規定：\n     (1)收案對象：慢性病或重大傷病，且為多重疾病。\n     (2)診療時間合計10分鐘以上，並根據診斷結果至少提供1項中醫醫療衛教(如中醫飲食衛教、\n         穴位經絡衛教、簡易中醫運動衛教或各類中藥使用衛教等)，並於病歷記錄評估結果及\n        所提供之中醫醫療衛教項目。\n    3.執行目標及預期效益評估指標如上表，以112年修訂支付標準後之實施時程等比率換算目\n       標值，112年執行目標人次為567.5萬人次(681萬人次×10/12)。\n    4.114年預算執行率，以申報點數為分子，並擷取到總額協商前可取得之月份(如1~6月或1~5月)。",
                    },
                }
            }
        }