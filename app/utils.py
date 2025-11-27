import base64
from .forms import Base64Form,UrlForm, HashForm,TextToolForm
from django.shortcuts import render, redirect

def base64_tool(request):
    result = None
    mode = None

    if request.method == 'POST':
        form = Base64Form(request.POST)
        if form.is_valid():
            text = form.cleaned_data['text']

            try:
                # Попытка декодировать
                decoded = base64.b64decode(text).decode('utf-8')
                result = decoded
                mode = "decode"
            except:
                # Иначе — кодируем
                encoded = base64.b64encode(text.encode()).decode()
                result = encoded
                mode = "encode"

    else:
        form = Base64Form()

    return render(request, "speed_tester/base64_tool.html", {
        "form": form,
        "result": result,
        "mode": mode,
    })


import urllib.parse
import base64
from django.shortcuts import render
from .forms import UrlForm

def url_tool(request):
    result = None
    mode = None
    result_b64 = None
    result_b64_decoded = None

    if request.method == "POST":
        form = UrlForm(request.POST)
        if form.is_valid():
            text = form.cleaned_data["text"]
            action = request.POST.get("action")  # Читаем прямо из POST

            # Ручной режим
            if action == "encode":
                result = urllib.parse.quote(text)
                mode = "encode"
            elif action == "decode":
                result = urllib.parse.unquote(text)
                mode = "decode"
            else:
                # Авто-режим
                if "%" in text or "+" in text:
                    result = urllib.parse.unquote(text)
                    mode = "decode"
                else:
                    result = urllib.parse.quote(text)
                    mode = "encode"

            # Base64
            result_b64 = base64.urlsafe_b64encode(text.encode()).decode()
            try:
                result_b64_decoded = base64.urlsafe_b64decode(text.encode()).decode()
            except Exception:
                result_b64_decoded = None

    else:
        form = UrlForm()

    return render(request, "speed_tester/url_tool.html", {
        "form": form,
        "result": result,
        "mode": mode,
        "result_b64": result_b64,
        "result_b64_decoded": result_b64_decoded,
    })

import hashlib

def hash_tool(request):
    result = {}

    if request.method == "POST":
        form = HashForm(request.POST)
        if form.is_valid():
            text = form.cleaned_data["text"].encode()

            result = {
                "md5": hashlib.md5(text).hexdigest(),
                "sha1": hashlib.sha1(text).hexdigest(),
                "sha256": hashlib.sha256(text).hexdigest(),
                "sha512": hashlib.sha512(text).hexdigest(),
            }
    else:
        form = HashForm()

    return render(request, "speed_tester/hash_tool.html", {
        "form": form,
        "result": result
    })

import subprocess

def ping_check(request):
    host = request.GET.get("host")
    output = None

    if host:
        try:
            result = subprocess.run(
                ["ping", "-c", "4", host],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            output = result.stdout or result.stderr
        except Exception as e:
            output = str(e)

    return render(request, "speed_tester/ping_check.html", {"output": output})


import uuid
import random
import string

def text_tools(request):
    result = None

    if request.method == "POST":
        form = TextToolForm(request.POST)
        if form.is_valid():
            text = form.cleaned_data.get("text", "")
            mode = form.cleaned_data["mode"]

            if mode == "uuid":
                result = str(uuid.uuid4())

            elif mode == "random":
                result = ''.join(random.choices(string.ascii_letters + string.digits, k=16))

            elif mode == "stats":
                result = {
                    "chars": len(text),
                    "words": len(text.split()),
                    "lines": len(text.split("\n"))
                }

            elif mode == "upper":
                result = text.upper()

            elif mode == "lower":
                result = text.lower()

            elif mode == "uniq":
                result = "\n".join(sorted(set(text.split("\n"))))

    else:
        form = TextToolForm()

    return render(request, "speed_tester/text_tools.html", {
        "form": form,
        "result": result
    })
