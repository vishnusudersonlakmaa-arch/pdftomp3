from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # ── Public ──────────────────────────────────────────────────────────────
    path("",                       views.index,              name="index"),
    path("about/",                 views.about,              name="about"),
    path("privacy/",               views.privacy,            name="privacy"),

    # ── Auth ────────────────────────────────────────────────────────────────
    path("login/",                 views.login,              name="Login"),
    path("logout/",                views.logout_view,        name="Logout"),
    path("signup/",                views.signin,             name="Sigup"),
    path("verify/",                views.sigin_verification, name="verify"),

    # ── Password reset ──────────────────────────────────────────────────────
    path("send-otp/",              views.send_otp,           name="send_otp"),
    path("verify-otp/",            views.verify_otp,         name="verify_otp"),
    path("reset-password/",        views.reset_password,     name="reset_password"),

    # ── Dashboard ───────────────────────────────────────────────────────────
    path("dashboard/",             views.dashboard,          name="Dashboard"),

    # ── Profile ─────────────────────────────────────────────────────────────
    path("profile/",               views.profile,            name="Profile"),
    path("profile/edit/",          views.edit_profile,       name="edit_profile"),
    path("profile/delete/",        views.deleteProfile,      name="delete"),
    path("settings/",              views.settings_view,      name="settings"),

    # ── Files ───────────────────────────────────────────────────────────────
    path("upload/",                views.single_upload,      name="single_upload"),
    path("files/",                 views.file_list,          name="file_list"),
    path("pdffiles/",              views.pdf_files_view,     name="pdffiles"),
    path("mp3files/",              views.audio_files_view,   name="mp3files"),

    path("preview/<int:pdf_id>/",  views.preview_pdf,        name="preview_pdf"),
    path("voice/<int:pdf_id>/",    views.Voicetype,          name="voice_type"),

    path("download/<int:mp3_id>/", views.download_mp3,       name="download_mp3"),
    path("delete-mp3/<int:mp3_id>/", views.delete_mp3,       name="delete_mp3"),
    path("delete-pdf/<int:pdf_id>/", views.delete_pdf,       name="delete_pdf"),

    # ── Playback ────────────────────────────────────────────────────────────
    path("play/<int:id>/",         views.playtime,           name="playtime"),

    # ── Celery progress ─────────────────────────────────────────────────────
    path("progress/",              views.progress,           name="progress"),
    path("progressing/",           views.progress_view,      name="progress_view"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)