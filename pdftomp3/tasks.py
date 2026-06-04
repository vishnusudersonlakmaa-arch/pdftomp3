from celery import shared_task
from .models import Profile, MP3File
import fitz  # PyMuPDF
import edge_tts
import os
import asyncio
from langdetect import detect, DetectorFactory
from PIL import Image
import pytesseract
import io

DetectorFactory.seed = 0  # Make detection consistent

LANGUAGE_VOICE_MAP = {
    "en": {"male": "en-US-GuyNeural", "female": "en-US-JennyNeural"},
    "es": {"male": "es-ES-AlvaroNeural", "female": "es-ES-ElviraNeural"},
    "fr": {"male": "fr-FR-HenriNeural", "female": "fr-FR-DeniseNeural"},
    "de": {"male": "de-DE-KlausNeural", "female": "de-DE-AmalaNeural"},
    "it": {"male": "it-IT-DiegoNeural", "female": "it-IT-ElsaNeural"},
    "hi": {"male": "hi-IN-MadhurNeural", "female": "hi-IN-SwaraNeural"},
    "zh-cn": {"male": "zh-CN-YunxiNeural", "female": "zh-CN-XiaoxiaoNeural"},
    "ja": {"male": "ja-JP-KeitaNeural", "female": "ja-JP-NanamiNeural"},
    "ko": {"male": "ko-KR-InJoonNeural", "female": "ko-KR-SunHiNeural"},
    "ru": {"male": "ru-RU-DmitryNeural", "female": "ru-RU-SvetlanaNeural"},
    "ta": {"male": "ta-IN-ValluvarNeural", "female": "ta-IN-PallaviNeural"},
}

TESSERACT_LANG_MAP = {
    "en": "eng",
    "es": "spa",
    "fr": "fra",
    "de": "deu",
    "it": "ita",
    "hi": "hin",
    "zh-cn": "chi_sim",
    "ja": "jpn",
    "ko": "kor",
    "ru": "rus",
    "ta": "tam",
}

def detect_language_from_text(text):
    try:
        return detect(text)
    except:
        return "en"

def select_voice(detected_lang, preferred_gender="male"):
    voice_options = LANGUAGE_VOICE_MAP.get(detected_lang, LANGUAGE_VOICE_MAP["en"])
    return voice_options.get(preferred_gender, "en-US-GuyNeural")

def run_ocr_on_page(page, lang, zoom=2):
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    img_data = pix.tobytes("png")
    img = Image.open(io.BytesIO(img_data))
    return pytesseract.image_to_string(img, lang=lang).strip()

def extract_text_and_detect_language(pdf_path):
    doc = fitz.open(pdf_path)
    if len(doc) == 0:
        return "en"  # fallback

    # ✅ 1. Read first page text without OCR
    first_page_text = doc[0].get_text().strip()
    print(f"Extracted text from first page (no OCR): {first_page_text[:100]}...")

    # ✅ 2. Detect language from that extracted text
    if first_page_text:
        detected_lang = detect_language_from_text(first_page_text)
        print(f"Detected language from native text: {detected_lang}")
    else:
        print("No text extracted from first page! Defaulting to English.")
        detected_lang = "en"

    return detected_lang

def perform_ocr_on_entire_pdf(pdf_path, detected_lang_code, zoom=2):
    doc = fitz.open(pdf_path)
    ocr_lang = TESSERACT_LANG_MAP.get(detected_lang_code, "eng")
    full_text = ""
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = run_ocr_on_page(page, lang=ocr_lang, zoom=zoom)
        full_text += f"\n{text}\n"
    return full_text.strip()

@shared_task
def convert_pdf_to_mp3_task(preferred_gender, pdf_path, title, profile_id):
    async def pdf_to_mp3(pdf_file, output_file, voice_gender):
        try:
            # ✅ Step 1: Extract text from first page and detect language
            detected_lang = extract_text_and_detect_language(pdf_file)
            print(detected_lang)

            # ✅ Step 2: OCR entire PDF with detected lang
            ocr_text = perform_ocr_on_entire_pdf(pdf_file, detected_lang)
            print(ocr_text)

            # ✅ Step 3: Generate MP3
            detected_voice = select_voice(detected_lang, voice_gender)
            print(detected_voice)
            communicate = edge_tts.Communicate(ocr_text, detected_voice)
            await communicate.save(output_file)
            print(f"MP3 file saved as: {output_file}")
        except Exception as e:
            print(f"An error occurred: {e}")

    output_dir = "media/mp3s"
    os.makedirs(output_dir, exist_ok=True)
    gender_label = "male" if preferred_gender == "male" else "female"
    sanitized_title = title.replace(" ", "_")
    output_file = os.path.join(output_dir, f"{sanitized_title}_[{gender_label}].mp3")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(pdf_to_mp3(pdf_path, output_file, preferred_gender))

    # ✅ Save to database
    user_profile = Profile.objects.get(id=profile_id)
    mp3_file = MP3File(mp3_file=f"mp3s/{sanitized_title}_[{gender_label}].mp3", title=title, user=user_profile)
    mp3_file.save()

    return {"status": "success", "id": mp3_file.id, "user": profile_id}