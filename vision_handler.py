import os
import shutil
import logging
from PIL import Image
import pytesseract
import torch

from transformers import BlipProcessor, BlipForConditionalGeneration

try:
    import cv2
except ImportError:
    cv2 = None

logger = logging.getLogger(__name__)


class VisionHandler:
    def __init__(self, blip_model_path=None):
        self._blip_processor = None
        self._blip_model = None
        self._ocr_ready = False
        self._blip_ready = False
        self._device = "cuda" if torch.cuda.is_available() else "cpu"

        # default to environment variable or passed path
        self.blip_model_path = (
            blip_model_path or os.environ.get("BLIP_MODEL", "Salesforce/blip-image-captioning-base")
        )

    # ---------- OCR ----------
    def _ensure_tesseract_config(self):
        if self._ocr_ready:
            return
        tcmd = os.environ.get("TESSERACT_CMD")
        if tcmd and os.path.exists(tcmd):
            pytesseract.pytesseract.tesseract_cmd = tcmd
            self._ocr_ready = True
            return

        found = shutil.which("tesseract")
        if found:
            self._ocr_ready = True
            return

        for p in [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        ]:
            if os.path.exists(p):
                pytesseract.pytesseract.tesseract_cmd = p
                self._ocr_ready = True
                return

        logger.warning("Tesseract not found. Install Tesseract or set TESSERACT_CMD.")

    def _preprocess_for_ocr_pil(self, img_pil):
        try:
            if cv2 is None:
                return img_pil.convert("L")
            import numpy as np

            arr = np.array(img_pil.convert("RGB"))
            gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
            gray = cv2.GaussianBlur(gray, (3, 3), 0)
            _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            clean = cv2.morphologyEx(th, cv2.MORPH_OPEN, kernel, iterations=1)
            return Image.fromarray(clean)
        except Exception:
            return img_pil.convert("L")

    def extract_text(self, image_path: str) -> str:
        self._ensure_tesseract_config()
        try:
            img = Image.open(image_path)
            img = self._preprocess_for_ocr_pil(img)
            cfg = "--oem 1 --psm 6"
            text = pytesseract.image_to_string(img, lang="eng", config=cfg)
            return text.strip()
        except Exception:
            logger.exception("OCR failed for %s", image_path)
            return ""

    # ---------- BLIP ----------
    def _load_blip_if_needed(self):
        if self._blip_ready:
            return True
        try:
            self._blip_processor = BlipProcessor.from_pretrained(
                self.blip_model_path, local_files_only=True
            )
            self._blip_model = BlipForConditionalGeneration.from_pretrained(
                self.blip_model_path, local_files_only=True
            ).to(self._device)
            self._blip_ready = True
            logger.info("BLIP model loaded on %s", self._device)
            return True
        except Exception:
            logger.exception("Failed to load BLIP model")
            return False

    def describe_image(self, image_path: str, max_new_tokens: int = 64) -> str:
        if not self._load_blip_if_needed():
            return "BLIP not available"
        try:
            img = Image.open(image_path).convert("RGB")
            inputs = self._blip_processor(images=img, return_tensors="pt").to(self._device)
            with torch.no_grad():
                out = self._blip_model.generate(**inputs, max_new_tokens=max_new_tokens)
            return self._blip_processor.decode(out[0], skip_special_tokens=True).strip()
        except Exception:
            logger.exception("BLIP captioning failed for %s", image_path)
            return "Image (no description available)"
