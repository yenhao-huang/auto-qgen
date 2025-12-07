"""
OCR Library

提供統一的 OCR 處理介面和多種 OCR 引擎實作
"""

from schemas.schema import OCRLLMPayload
from lib.ocr.base_ocr import BaseOCR
from lib.ocr.paddleocr_vl import PaddleOCR
from lib.ocr.dotsocr import DotsOCR
from lib.ocr.chandra import ChandraOCR
from lib.ocr.nv_nemotron import NVNemotronOCR

__all__ = [
    "OCRLLMPayload",
    "BaseOCR",
    "PaddleOCR",
    "DotsOCR",
    "ChandraOCR",
    "NVNemotronOCR",
]
