from celery import shared_task
from .models import Profile, MP3File
import fitz  # PyMuPDF
import edge_tts
import os
import asyncio
from langdetect import detect, DetectorFactory

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

def detect_language_from_text(text):
    try:
        return detect(text)
    except:
        return "en"

def select_voice(detected_lang, preferred_gender="male"):
    voice_options = LANGUAGE_VOICE_MAP.get(detected_lang, LANGUAGE_VOICE_MAP["en"])
    return voice_options.get(preferred_gender, "en-US-GuyNeural")

def extract_text_and_detect_language(pdf_path):
    doc = fitz.open(pdf_path)
    if len(doc) == 0:
        return "en", ""

    # ✅ Extract text from all pages
    full_text = ""
    for page in doc:
        text = page.get_text().strip()
        full_text += f"\n{text}"

    if full_text.strip():
        detected_lang = detect_language_from_text(full_text)
    else:
        detected_lang = "en"

    return detected_lang, full_text.strip()

@shared_task
def convert_pdf_to_mp3_task(preferred_gender, pdf_path, title, profile_id):
    async def pdf_to_mp3(pdf_file, output_file, voice_gender):
        try:
            # ✅ Step 1: Extract all text & detect language
            detected_lang, full_text = extract_text_and_detect_language(pdf_file)
            print(f"Detected language: {detected_lang}")
            print(f"Extracted text length: {len(full_text)}")

            # ✅ Step 2: Generate MP3
            detected_voice = select_voice(detected_lang, voice_gender)
            communicate = edge_tts.Communicate(full_text, detected_voice)
            await communicate.save(output_file)
            print(f"MP3 file saved as: {output_file}")
        except Exception as e:
            print(f"An error occurred: {e}")

    output_dir = "media/mp3s"
    os.makedirs(output_dir, exist_ok=True)
    gender_label = "male" if preferred_gender == "male" else "female"
    sanitized_title = title.replace(" ", "_")
    output_file = os.path.join(output_dir, f"{sanitized_title}_[{gender_label}].mp3")

    # ✅ Run async properly
    asyncio.run(pdf_to_mp3(pdf_path, output_file, preferred_gender))

    # ✅ Save to database
    user_profile = Profile.objects.get(id=profile_id)
    mp3_file = MP3File(
        mp3_file=f"mp3s/{sanitized_title}_[{gender_label}].mp3",
        title=title,
        user=user_profile,
    )
    mp3_file.save()

    return {"status": "success", "id": mp3_file.id, "user": profile_id}
