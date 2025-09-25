from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import login as django_login, logout as django_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
import socket
import json
import threading
import time
import logging
import speedtest
import subprocess

from .models import *
from .forms import IPAddressForm, CustomUserCreationForm

logger = logging.getLogger(__name__)


def first_visit(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return redirect('home')


@login_required
def index(request):
    return render(request, 'speed_tester/index.html')


def auth_view(request):
    login_form = AuthenticationForm()
    register_form = CustomUserCreationForm()
    return render(request, 'speed_tester/login.html', {'login_form': login_form, 'register_form': register_form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            django_login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}!')
            return redirect('home')
        else:
            return render(request, 'speed_tester/login.html', {'login_form': form, 'register_form': UserCreationForm()})
    return redirect('auth')


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            django_login(request, user)
            messages.success(request, f'Аккаунт создан: {user.username}!')
            return redirect('home')
    return redirect('auth')


def logout_view(request):
    django_logout(request)
    messages.info(request, "Вы вышли из системы.")
    return redirect('auth')


def get_ip_address(domain):
    try:
        return socket.gethostbyname(domain)
    except socket.gaierror:
        return None


def run_speed_test(ip_address=None):
    results = {
        'input': ip_address,
        'destination_ip': None,
        'ping_ms': None,
        'download_speed_kbps': None,
        'upload_speed_kbps': None
    }
    if ip_address:
        results['destination_ip'] = get_ip_address(ip_address)
    try:
        s = speedtest.Speedtest()
        s.get_best_server()
        s.download()
        s.upload()
        res = s.results.dict()
        results['ping_ms'] = res.get('ping') * 1000 if res.get('ping') else None
        results['download_speed_kbps'] = res.get('download') / 1000 if res.get('download') else None
        results['upload_speed_kbps'] = res.get('upload') / 1000 if res.get('upload') else None
        results['ip_address'] = res.get('client', {}).get('ip', ip_address)
    except Exception as e:
        logger.error(f"Ошибка speedtest для {ip_address}: {e}")
        results['error'] = str(e)
    return results


def speed_test_view(request):
    if request.method == 'POST':
        form = IPAddressForm(request.POST)
        if form.is_valid():
            ip_addresses_text = form.cleaned_data['ip_addresses']
            input_list = [item.strip() for item in ip_addresses_text.split('\n') if item.strip()]
            all_results = []

            for item in input_list:
                test_result = run_speed_test(item)
                all_results.append(test_result)
                if 'error' not in test_result:
                    SpeedTestResult.objects.create(
                        ip_address=item,
                        destination_ip=test_result.get('destination_ip'),
                        ping_ms=test_result['ping_ms'],
                        download_speed_kbps=test_result['download_speed_kbps'],
                        upload_speed_kbps=test_result['upload_speed_kbps']
                    )

            return render(request, 'speed_tester/results.html', {'results': all_results})
        return render(request, 'speed_tester/speed_test_form.html', {'form': form, 'error': 'Неверный формат IP или домена.'})
    return render(request, 'speed_tester/speed_test_form.html', {'form': IPAddressForm()})


@login_required
def save_search(request):
    if request.method == 'POST':
        full_query = request.POST.get('full_query')
        text_inputs_json = request.POST.get('text_inputs')
        dork_commands_json = request.POST.get('dork_commands')

        try:
            text_inputs = json.loads(text_inputs_json)
            dork_commands = json.loads(dork_commands_json)

            search_objects = [
                SearchQuery(
                    user=request.user,
                    text_input=ti.strip(),
                    dork_command=dc.strip(),
                    full_query=full_query.strip()
                )
                for ti, dc in zip(text_inputs, dork_commands)
            ]
            SearchQuery.objects.bulk_create(search_objects)

            logger.info(f"Сохранен поиск для пользователя {request.user}")
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Только POST'}, status=405)

import threading
import time
from django.utils import timezone
from .models import TrafficLog
import subprocess
import logging

logger = logging.getLogger(__name__)

def capture_netstat():
    try:
        result = subprocess.run(['netstat', '-an'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            lines = result.stdout.splitlines()
            for line in lines:
                if line.startswith(('Proto', 'TCP', 'UDP')):
                    TrafficLog.objects.create(
                        method='Netstat Capture',
                        path=line.strip(),
                        duration=0,
                        timestamp=timezone.now()
                    )
        else:
            logger.error(f"Ошибка netstat: {result.stderr}")
    except Exception as e:
        logger.error(f"Ошибка при захвате netstat: {e}")

def run_netstat_capture():
    while True:
        capture_netstat()
        time.sleep(5)  # интервал 5 секунд

def start_netstat_capture_thread():
    """Запускает поток для фонового захвата netstat"""
    capture_thread = threading.Thread(target=run_netstat_capture)
    capture_thread.daemon = True
    capture_thread.start()

def history_view(request):
    history = SpeedTestResult.objects.all().order_by('-timestamp')
    return render(request, 'speed_tester/history.html', {'history': history})

def search_history_view(request):
    history = SearchQuery.objects.all().order_by('-search_date')
    return render(request, 'speed_tester/search_history.html', {'history': history})

from .models import ExploitExample

def get_commands(request):
    """
    Возвращает список команд с примерами ExploitDB.
    """
    commands = Commands.objects.all()
    data = []

    for cmd in commands:
        # Берем первые 3 примера ExploitDB по категории команды
        examples = ExploitExample.objects.filter(category__icontains=cmd.command)[:3]
        examples_data = [{"description": e.description, "url": e.url} for e in examples]

        data.append({
            "id": cmd.id,
            "dork_command": cmd.command,
            "description": cmd.description,
            "examples": examples_data
        })

    return JsonResponse({"commands": data})


def traffic_logs(request):
    logs = TrafficLog.objects.all().order_by('-timestamp')
    return render(request, 'speed_tester/traffic.html', {'logs': logs})

def com_list(request):
    results = Commands.objects.all()
    return render(request, 'speed_tester/command_list.html', {'results': results})

def speed_test_results_list(request):
    results = SpeedTestResult.objects.all().order_by('-timestamp')
    return render(request, 'speed_tester/results_list.html', {'results': results})


def speed_test_results_detail(request, result_id):

    """Displays details for a specific speed test result."""
    try:
        result = SpeedTestResult.objects.get(pk=result_id)
    except SpeedTestResult.DoesNotExist:
        return render(request, 'speed_tester/result_not_found.html', {'result_id': result_id}, status=404)
    return render(request, 'speed_tester/results_detail.html', {'result': result})


def exploit_list_view(request):
    category = request.GET.get('category')
    if category:
        exploits = ExploitExample.objects.filter(category__icontains=category)
    else:
        exploits = ExploitExample.objects.all()[:50]  # первые 50 записей
    return render(request, "speed_tester/exploit_list.html", {"exploits": exploits})
