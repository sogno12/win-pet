import os
import base64
import requests
from core.config_manager import ConfigManager
from core.logger import PetLogger

class VisionAgent:
    """Gemini Vision API를 활용하여 캡처된 이미지를 분석하거나 OCR 텍스트를 추출하는 클래스"""

    @classmethod
    def encode_image(cls, image_path: str) -> tuple[str, str]:
        """이미지 파일을 Base64 문자열과 mime_type으로 변환"""
        ext = os.path.splitext(image_path)[1].lower().replace(".", "")
        mime_type = "image/png" if ext == "png" else ("image/jpeg" if ext in ["jpg", "jpeg"] else f"image/{ext}")
        
        with open(image_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        return encoded, mime_type

    @classmethod
    def analyze_image(cls, image_path: str, user_prompt: str = "") -> str:
        """캡처된 이미지와 사용자 질문을 Gemini Vision 모델로 전송하여 분석 결과 리턴"""
        api_key = ConfigManager.get_api_key()
        if not api_key:
            return "🔑 Gemini API 키가 입력되지 않았어요! [🔑 API 키 설정]에서 키를 넣어주세요."

        if not os.path.exists(image_path):
            return "❌ 캡처된 이미지 파일을 찾을 수 없습니다."

        base64_data, mime_type = cls.encode_image(image_path)
        
        prompt_text = user_prompt.strip() if user_prompt and user_prompt.strip() else \
            "이 이미지의 내용을 상세하게 분석해줘. 화면에 보이는 UI, 텍스트, 데이터, 에러 메시지, 코드 등을 빠짐없이 파악하고, 주요 내용·맥락·특이점을 구체적으로 설명해줘. 에러나 문제가 보이면 원인과 해결책도 함께 제시해줘."

        config = ConfigManager.load_config()
        model_name = config.get("llm_model", "gemini-3.1-flash-lite").strip()

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}

        payload = {
            "systemInstruction": {
                "parts": [{"text": "너는 사용자가 캡처한 화면 이미지를 정밀 분석하는 AI 어시스턴트다. 이미지에 담긴 내용을 빠짐없이 꼼꼼하게 분석하고, 사용자가 물어보는 내용에 대해 충분한 근거와 함께 상세하게 답변해라. 분량을 인위적으로 줄이지 말고, 필요한 만큼 충분히 설명해라."}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt_text},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": base64_data
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 2048
            }
        }

        try:
            res = requests.post(url, headers=headers, json=payload, timeout=20)
            if res.status_code == 200:
                data = res.json()
                usage = data.get("usageMetadata", {})
                if usage:
                    PetLogger.log_api_usage(
                        usage.get("promptTokenCount", 0),
                        usage.get("candidatesTokenCount", 0),
                        usage.get("totalTokenCount", 0),
                        f"{model_name}-vision"
                    )
                candidate = data.get("candidates", [{}])[0]
                parts = candidate.get("content", {}).get("parts", [])
                if parts:
                    for pt in parts:
                        if "text" in pt:
                            ans = pt["text"].strip()
                            PetLogger.log_tool("analyze_image", {"image": image_path, "prompt": prompt_text}, ans)
                            return ans
                return "이미지 분석 결과를 파싱하지 못했어요."
            elif res.status_code in (400, 404):
                # Vision을 지원하지 않는 모델이거나 잘못된 API 경로일 때
                PetLogger.log_error(f"Vision API {res.status_code}: {res.text[:200]}")
                return (
                    f"⚠️ 현재 설정된 모델 '{model_name}'이 이미지 분석(Vision)을 지원하지 않거나 모델명이 잘못되었어요.\n\n"
                    f"📌 Vision 기능을 사용하려면 [🔑 API 키 설정] 화면의 모델 설정에서 Vision 지원 모델로 변경해주세요.\n"
                    f"(예: gemini-2.0-flash, gemini-2.5-flash, gemini-3.1-flash-lite 등)"
                )
            else:
                err_msg = f"Vision API 오류 ({res.status_code}): {res.text[:100]}"
                PetLogger.log_error(err_msg)
                return f"❌ {err_msg}"
        except Exception as e:
            err_msg = f"Vision API 통신 오류: {e}"
            PetLogger.log_error(err_msg)
            return f"❌ {err_msg}"

    @classmethod
    def extract_text_ocr(cls, image_path: str) -> str:
        """캡처된 이미지 내의 텍스트(OCR)를 추출하여 텍스트 문자열 리턴"""
        prompt = "이 이미지에 포함된 모든 텍스트(한글, 영어, 숫자, 코드 등)를 있는 그대로 정확히 추출해서 텍스트로만 출력해줘. 불필요한 설명은 생략해."
        result = cls.analyze_image(image_path, prompt)
        PetLogger.log_tool("extract_text_ocr", {"image": image_path}, result)
        return result
