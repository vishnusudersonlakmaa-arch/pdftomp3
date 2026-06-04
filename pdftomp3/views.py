from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404, JsonResponse
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.mail import EmailMultiAlternatives
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Sum, F, ExpressionWrapper, DurationField
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.html import strip_tags
from django.utils.timezone import now
from celery.result import AsyncResult
import os
import random

from .forms import Registrationform, ProfileUpdateForm, PDFUploadForm
from .models import PDFFile, Profile, MP3File, UserActivity
from .tasks import convert_pdf_to_mp3_task


# ─── Utilities ────────────────────────────────────────────────────────────────

def _get_profile(request):
    """Single helper to retrieve the profile — avoids duplicating get_object_or_404 everywhere."""
    return get_object_or_404(Profile.objects.select_related("user"), user=request.user)


def send_otp_email(receiver_email: str, otp: int, username: str, template: str):
    subject = "Your OTP Code"
    html_content = render_to_string(f"pdftomp3/{template}", {"otp": otp, "Username": username})
    text_content = strip_tags(html_content)
    email = EmailMultiAlternatives(
        subject, text_content, "your_email@gmail.com", [receiver_email]
    )
    email.attach_alternative(html_content, "text/html")
    email.send()


# ─── Public views ─────────────────────────────────────────────────────────────

def index(request):
    return render(request, "pdftomp3/index.html")


def about(request):
    return render(request, "pdftomp3/about.html", {"tab": "About"})


def privacy(request):
    return render(request, "pdftomp3/privacy.html", {"tab": "Privacy"})


# ─── Auth ─────────────────────────────────────────────────────────────────────

def login(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            UserActivity.objects.create(user=user, start_time=now())
            return redirect(reverse_lazy("Dashboard"))
        return render(request, "pdftomp3/login.html", {"error": "Invalid username or password"})
    return render(request, "pdftomp3/login.html")


def signin(request):
    form = Registrationform(request.POST or None)
    if request.method == "POST" and form.is_valid():
        otp = random.randint(1000, 9999)
        send_otp_email(form.cleaned_data["email"], otp, form.cleaned_data["username"], "email_template.html")
        request.session["form_data"] = form.cleaned_data
        request.session["otp"] = otp
        return redirect(reverse_lazy("verify"))
    return render(request, "pdftomp3/sign.html", {"form": form})


def sigin_verification(request):
    if request.method == "POST":
        entered_otp = "".join([request.POST.get(f"otp{i}", "") for i in range(1, 5)])
        saved_otp   = request.session.get("otp")

        if str(entered_otp) == str(saved_otp):
            form_data = request.session.get("form_data")
            if form_data:
                form = Registrationform(form_data)
                if form.is_valid():
                    form.save()
                    del request.session["form_data"]
                    del request.session["otp"]
                    return redirect(reverse_lazy("Login"))
        return render(request, "pdftomp3/sigin_verification.html", {"error": "Invalid OTP"})
    return render(request, "pdftomp3/sigin_verification.html")


@login_required
def logout_view(request):
    profile = _get_profile(request)
    if request.method == "POST":
        # Close the open session rather than creating a new row
        UserActivity.objects.filter(user=request.user, end_time__isnull=True).update(end_time=now())
        logout(request)
        return redirect(reverse_lazy("index"))
    return render(request, "pdftomp3/logout.html", {"username": profile.username})


# ─── Password reset ───────────────────────────────────────────────────────────

def send_otp(request):
    if request.method == "POST":
        receiver_email = request.POST.get("email", "").strip()
        user = User.objects.filter(email=receiver_email).select_related().first()
        if not user:
            return render(request, "pdftomp3/send_otp.html", {"error": "No account found for that email."})
        otp = random.randint(1000, 9999)
        send_otp_email(receiver_email, otp, user.username, "forgot_template.html")
        request.session["otp"] = otp
        request.session["receiver_email"] = receiver_email
        return redirect("verify_otp")
    return render(request, "pdftomp3/send_otp.html")


def verify_otp(request):
    if request.method == "POST":
        entered_otp = "".join([request.POST.get(f"otp{i}", "") for i in range(1, 5)])
        if str(entered_otp) == str(request.session.get("otp")):
            return redirect("reset_password")
        return render(request, "pdftomp3/verify_otp.html", {"error": "Invalid OTP"})
    return render(request, "pdftomp3/verify_otp.html")


def reset_password(request):
    if request.method == "POST":
        receiver_email = request.session.get("receiver_email")
        new_password    = request.POST.get("new_password")
        confirm         = request.POST.get("confirm_password")

        try:
            user = User.objects.get(email=receiver_email)
        except User.DoesNotExist:
            messages.error(request, "No user found with this email.")
            return render(request, "pdftomp3/reset_password.html")

        if new_password != confirm:
            messages.error(request, "Passwords do not match.")
            return render(request, "pdftomp3/reset_password.html")

        user.password = make_password(new_password)
        user.save(update_fields=["password"])       # only write the password column
        messages.success(request, "Password updated successfully.")
        return render(request, "pdftomp3/success.html")
    return render(request, "pdftomp3/reset_password.html")


# ─── Dashboard ────────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    profile = _get_profile(request)

    # Single query each with prefetch instead of separate .count() calls
    pdfs     = profile.pdfs.order_by("-date")[:4]
    mp3s     = profile.mp3s.order_by("-date")[:4]
    total_pdfs = profile.pdfs.count()
    total_mp3s = profile.mp3s.count()

    # Correct aggregation: sum durations of *completed* sessions only
    total_time = (
        UserActivity.objects
        .filter(user=request.user, end_time__isnull=False)
        .annotate(duration=ExpressionWrapper(F("end_time") - F("start_time"), output_field=DurationField()))
        .aggregate(total=Sum("duration"))["total"]
    )
    total_seconds  = total_time.total_seconds() if total_time else 0
    total_hours    = int(total_seconds // 3600)
    total_minutes  = int((total_seconds % 3600) // 60)

    return render(request, "pdftomp3/dashboard.html", {
        "tab":          "Dashboard",
        "pdf":          pdfs,
        "mp3_files":    mp3s,
        "profile":      profile,
        "total_files":  total_pdfs + total_mp3s,
        "total_mp3s":   total_mp3s,
        "total_pdfs":   total_pdfs,
        "total_hours":  total_hours,
        "total_minutes": total_minutes,
    })


# ─── Profile ──────────────────────────────────────────────────────────────────

@login_required
def profile(request):
    profile = _get_profile(request)
    mp3_files = MP3File.objects.filter(user=profile).order_by("-id")
    return render(request, "pdftomp3/profile.html", {
        "profile":               profile,
        "total_files_converted": profile.pdfs.count(),
        "total_audio_duration":  profile.mp3s.count(),
        "last_conversion":       mp3_files.first(),
        "mp3_files":             mp3_files[:5],
        "tab":                   "Users",
    })


@login_required
def edit_profile(request):
    profile = _get_profile(request)
    form = ProfileUpdateForm(request.POST or None, request.FILES or None, instance=profile)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("Profile")
    return render(request, "pdftomp3/profile_form.html", {"form": form, "tab": "Users", "profile": profile})


@login_required
def settings_view(request):
    return render(request, "pdftomp3/settings.html", {"profile": _get_profile(request), "tab": "Menu"})


@login_required
def deleteProfile(request):
    profile = _get_profile(request)
    if request.method == "POST":
        profile.delete()     # cascades to User via signal/OneToOne
        return redirect("index")
    return render(request, "pdftomp3/Delete.html", {"profile": profile.name})


# ─── PDF / MP3 File Management ────────────────────────────────────────────────

@login_required
def single_upload(request):
    profile = _get_profile(request)
    form = PDFUploadForm(request.POST or None, request.FILES or None)
    if request.method == "POST":
        if form.is_valid():
            pdf_file = form.save(commit=False)
            pdf_file.user  = profile
            pdf_file.title = pdf_file.pdf_file.name
            pdf_file.save()
            return redirect("preview_pdf", pdf_id=pdf_file.id)
        return render(request, "pdftomp3/upload.html", {
            "tab": "single_upload", "form": form, "error": form.errors, "profile": profile,
        })
    return render(request, "pdftomp3/upload.html", {
        "tab": "single_upload", "form": form, "profile": profile,
    })


@login_required
def preview_pdf(request, pdf_id):
    profile  = _get_profile(request)
    pdf_file = get_object_or_404(PDFFile, id=pdf_id, user=profile)
    return render(request, "pdftomp3/preview.html", {"pdf_file": pdf_file, "tab": "Files", "profile": profile})


@login_required
def Voicetype(request, pdf_id):
    profile  = _get_profile(request)
    pdf_file = get_object_or_404(PDFFile, id=pdf_id, user=profile)

    if request.method == "POST":
        voice    = request.POST.get("voiceType", "male")
        pdf_path = pdf_file.pdf_file.path
        title    = os.path.splitext(pdf_file.title)[0]
        try:
            task = convert_pdf_to_mp3_task.delay(voice, pdf_path, title, profile.id)
            request.session["task_id"] = task.id
            return redirect("progress_view")
        except Exception as e:
            return render(request, "pdftomp3/voice_type.html", {
                "pdf_file": pdf_file, "tab": "Files", "profile": profile, "error": str(e),
            })
    return render(request, "pdftomp3/voice_type.html", {"pdf_file": pdf_file, "tab": "Files", "profile": profile})


@login_required
def file_list(request):
    profile   = _get_profile(request)
    pdf_files = PDFFile.objects.filter(user=profile).order_by("-date")
    page_obj  = Paginator(pdf_files, 4).get_page(request.GET.get("page", 1))
    mp3_files = MP3File.objects.filter(user=profile).order_by("-id")[:4]
    return render(request, "pdftomp3/file_list.html", {
        "pdf_files": page_obj, "mp3_files": mp3_files, "tab": "Files", "profile": profile,
    })


@login_required
def audio_files_view(request):
    profile = _get_profile(request)
    qs      = profile.mp3s.all().order_by("id")
    search  = request.GET.get("search", "").strip()
    if search:
        qs = qs.filter(title__icontains=search)

    page_obj = Paginator(qs, 8).get_page(request.GET.get("page", 1))

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        html = render_to_string("pdftomp3/partials/mp3files.html", {"mp3_files": page_obj})
        return JsonResponse({"html": html})

    return render(request, "pdftomp3/mp3files.html", {
        "mp3_files":            page_obj,
        "has_previous":         page_obj.has_previous(),
        "has_next":             page_obj.has_next(),
        "previous_page_number": page_obj.previous_page_number() if page_obj.has_previous() else None,
        "next_page_number":     page_obj.next_page_number()     if page_obj.has_next()     else None,
        "current_page":         page_obj.number,
        "total_pages":          page_obj.paginator.num_pages,
        "tab":                  "Play",
        "profile":              profile,
    })


@login_required
def pdf_files_view(request):
    profile = _get_profile(request)
    qs      = profile.pdfs.all().order_by("id")
    search  = request.GET.get("search", "").strip()
    if search:
        qs = qs.filter(title__icontains=search)

    page_obj = Paginator(qs, 8).get_page(request.GET.get("page", 1))

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        html = render_to_string("pdftomp3/partials/pdffile.html", {"pdf_files": page_obj})
        return JsonResponse({"html": html})

    return render(request, "pdftomp3/pdffile.html", {
        "pdf_files":            page_obj,
        "has_previous":         page_obj.has_previous(),
        "has_next":             page_obj.has_next(),
        "previous_page_number": page_obj.previous_page_number() if page_obj.has_previous() else None,
        "next_page_number":     page_obj.next_page_number()     if page_obj.has_next()     else None,
        "current_page":         page_obj.number,
        "total_pages":          page_obj.paginator.num_pages,
        "tab":                  "Files",
        "profile":              profile,
    })


# ─── Playback ─────────────────────────────────────────────────────────────────

@login_required
def playtime(request, id):
    profile  = _get_profile(request)
    mp3_all  = list(profile.mp3s.order_by("id"))
    mp3      = get_object_or_404(MP3File, id=id, user=profile)
    try:
        current_index = mp3_all.index(mp3)
    except ValueError:
        current_index = 0

    return render(request, "pdftomp3/playtime.html", {
        "tab":          "Play",
        "mp3fileall":   mp3_all,
        "mp3file":      mp3,
        "current_index": current_index,
        "total_songs":  len(mp3_all),
        "profile":      profile,
    })


# ─── Downloads & Deletes ──────────────────────────────────────────────────────

@login_required
def download_mp3(request, mp3_id):
    profile  = _get_profile(request)
    mp3_file = get_object_or_404(MP3File, id=mp3_id, user=profile)
    file_path = mp3_file.mp3_file.path
    if os.path.exists(file_path):
        with open(file_path, "rb") as fh:
            response = HttpResponse(fh.read(), content_type="audio/mpeg")
            response["Content-Disposition"] = f'attachment; filename="{mp3_file.title}.mp3"'
            return response
    raise Http404("MP3 file not found on disk.")


@login_required
def delete_mp3(request, mp3_id):
    if request.method == "DELETE":
        mp3_file  = get_object_or_404(MP3File, id=mp3_id, user=request.user.profile)
        file_path = mp3_file.mp3_file.path
        mp3_file.delete()
        if os.path.exists(file_path):
            os.remove(file_path)
        return JsonResponse({"success": True})
    return JsonResponse({"success": False}, status=400)


@login_required
def delete_pdf(request, pdf_id):
    if request.method == "DELETE":
        pdf_file  = get_object_or_404(PDFFile, id=pdf_id, user=request.user.profile)
        file_path = pdf_file.pdf_file.path
        pdf_file.delete()
        if os.path.exists(file_path):
            os.remove(file_path)
        return JsonResponse({"success": True})
    return JsonResponse({"success": False}, status=400)


# ─── Celery Progress ──────────────────────────────────────────────────────────

@login_required
def progress_view(request):
    return render(request, "pdftomp3/progress.html")


@login_required
def progress(request):
    task_id = request.session.get("task_id")
    if not task_id:
        return JsonResponse({"status": "error", "message": "No task ID found."}, status=400)

    task_result = AsyncResult(task_id)
    status = task_result.status

    if status == "SUCCESS":
        request.session.pop("task_id", None)
        return JsonResponse({"status": "SUCCESS", "redirect_url": f"/play/{task_result.result['id']}/"})
    if status == "FAILURE":
        return JsonResponse({"status": "FAILURE", "message": str(task_result.result)})
    return JsonResponse({"status": status})


# ─── Error Handlers ───────────────────────────────────────────────────────────

def error_404_view(request, exception):
    return render(request, "pdftomp3/404.html", status=404)


def error_500_view(request):
    return render(request, "pdftomp3/500.html", status=500)