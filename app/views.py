from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as django_login, logout as django_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator

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


from django.db.models import Avg
from django.contrib.auth.decorators import login_required

@login_required(login_url='/login/')
def dashboard_view(request):
    # SpeedTest статистика
    speed_tests = SpeedTestResult.objects.all()
    total_tests = speed_tests.count()
    avg_ping = speed_tests.aggregate(Avg('ping_ms'))['ping_ms__avg']
    avg_download = speed_tests.aggregate(Avg('download_speed_kbps'))['download_speed_kbps__avg']
    avg_upload = speed_tests.aggregate(Avg('upload_speed_kbps'))['upload_speed_kbps__avg']
    latest_tests = speed_tests.order_by('-timestamp')[:5]

    # SearchQuery статистика
    search_count = SearchQuery.objects.count()
    latest_searches = SearchQuery.objects.order_by('-search_date')[:5]

    # TrafficLog статистика
    traffic_count = TrafficLog.objects.count()
    latest_logs = TrafficLog.objects.order_by('-timestamp')[:5]

    # ExploitExamples
    latest_exploits = ExploitExample.objects.order_by('-id')[:5]

    context = {
        'total_tests': total_tests,
        'avg_ping': avg_ping,
        'avg_download': avg_download,
        'avg_upload': avg_upload,
        'latest_tests': latest_tests,
        'search_count': search_count,
        'latest_searches': latest_searches,
        'traffic_count': traffic_count,
        'latest_logs': latest_logs,
        'latest_exploits': latest_exploits,
    }

    return render(request, 'dashboard.html', context)


# ============================================================
#                     АВТОРИЗАЦИЯ
# ============================================================

def first_visit(request):
    return redirect('home') if request.user.is_authenticated else redirect('login')


@login_required
def index(request):
    return render(request, 'speed_tester/index.html')


def auth_view(request):
    return render(request, 'speed_tester/login.html', {
        'login_form': AuthenticationForm(),
        'register_form': CustomUserCreationForm()
    })


def login_view(request):
    if request.method != 'POST':
        return redirect('auth')

    form = AuthenticationForm(request, data=request.POST)

    if form.is_valid():
        user = form.get_user()
        django_login(request, user)
        messages.success(request, f'Добро пожаловать, {user.username}!')
        return redirect('home')

    return render(request, 'speed_tester/login.html', {
        'login_form': form,
        'register_form': CustomUserCreationForm()
    })


def register_view(request):
    if request.method != 'POST':
        return redirect('auth')

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


# ============================================================
#                     УТИЛИТЫ
# ============================================================

def paginate(request, queryset, per_page=20):
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number), paginator


def get_ip_address(domain: str):
    try:
        return socket.gethostbyname(domain)
    except socket.gaierror:
        return None


def run_speed_test(ip_address=None):
    """Выполняет speedtest — полностью безопасная обертка."""

    results = {
        'input': ip_address,
        'destination_ip': get_ip_address(ip_address) if ip_address else None,
        'ping_ms': None,
        'download_speed_kbps': None,
        'upload_speed_kbps': None
    }

    try:
        s = speedtest.Speedtest()
        s.get_best_server()
        s.download()
        s.upload()
        res = s.results.dict()

        results.update({
            'ping_ms': res.get('ping') * 1000 if res.get('ping') else None,
            'download_speed_kbps': res.get('download') / 1000,
            'upload_speed_kbps': res.get('upload') / 1000,
            'ip_address': res.get('client', {}).get('ip')
        })

    except Exception as e:
        logger.error(f"Ошибка SpeedTest: {e}")
        results['error'] = str(e)

    return results


# ============================================================
#                     SPEED TEST
# ============================================================

@login_required
def speed_test_view(request):
    if request.method == 'POST':
        form = IPAddressForm(request.POST)
        if form.is_valid():
            input_list = [
                ip.strip() for ip in form.cleaned_data['ip_addresses'].split('\n')
                if ip.strip()
            ]

            results = []

            for ip in input_list:
                res = run_speed_test(ip)
                results.append(res)

                if 'error' not in res:
                    SpeedTestResult.objects.create(
                        ip_address=ip,
                        destination_ip=res.get('destination_ip'),
                        ping_ms=res['ping_ms'],
                        download_speed_kbps=res['download_speed_kbps'],
                        upload_speed_kbps=res['upload_speed_kbps'],
                    )

            return render(request, 'speed_tester/results.html', {'results': results})

        return render(request, 'speed_tester/speed_test_form.html', {
            'form': form,
            'error': 'Неверный формат IP или домена.'
        })

    return render(request, 'speed_tester/speed_test_form.html', {'form': IPAddressForm()})


@login_required
def history_view(request):
    queryset = SpeedTestResult.objects.all().order_by('-timestamp')
    page_obj, paginator = paginate(request, queryset, 20)
    return render(request, 'speed_tester/history.html', {
        'history': page_obj,
        'paginator': paginator,
        'page_obj': page_obj
    })


# ============================================================
#                     GOOGLE DORKING (ПОИСК)
# ============================================================

@login_required
def save_search(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Только POST'}, status=405)

    print('!!!!',request.POST)

    try:
        full_query = request.POST.get('full_query', '').strip()
        if not full_query:
            return JsonResponse({'status': 'error', 'message': 'full_query пустой'}, status=400)

        # Получение массивов из POST
        text_inputs = json.loads(request.POST.get('text_inputs', '[]'))
        dork_commands = json.loads(request.POST.get('dork_commands', '[]'))

        # Если клиент прислал пустые массивы — значит сохраняем только full_query
        if not text_inputs and not dork_commands:
            SearchQuery.objects.create(
                user=request.user,
                text_input='',
                dork_command='',
                full_query=full_query
            )
            return JsonResponse({'status': 'success'})

        if len(text_inputs) != len(dork_commands):
            return JsonResponse({
                'status': 'error',
                'message': 'Размеры text_inputs и dork_commands не совпадают'
            }, status=400)

        objects = []

        for text, dork in zip(text_inputs, dork_commands):
            objects.append(SearchQuery(
                user=request.user,
                text_input=(text or '').strip(),
                dork_command=(dork or '').strip(),
                full_query=full_query
            ))

        SearchQuery.objects.bulk_create(objects)

        return JsonResponse({'status': 'success'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
def search_history_view(request):
    queryset = SearchQuery.objects.all().order_by('-search_date')
    page_obj, paginator = paginate(request, queryset, 20)
    return render(request, 'speed_tester/search_history.html', {
        'history': page_obj,
        'paginator': paginator,
        'page_obj': page_obj
    })


# ============================================================
#                     NETSTAT MONITOR
# ============================================================

def capture_netstat():
    try:
        result = subprocess.run(['netstat', '-an'], capture_output=True, text=True, timeout=10)

        if result.returncode != 0:
            logger.error(f"netstat error: {result.stderr}")
            return

        for line in result.stdout.splitlines():
            if line.startswith(('Proto', 'TCP', 'UDP')):
                TrafficLog.objects.create(
                    method='Netstat Capture',
                    path=line.strip(),
                    duration=0,
                    timestamp=timezone.now()
                )
    except Exception as e:
        logger.error(f"Ошибка netstat: {e}")


def run_netstat_capture():
    while True:
        capture_netstat()
        time.sleep(5)


def start_netstat_capture_thread():
    t = threading.Thread(target=run_netstat_capture, daemon=True)
    t.start()


@login_required
def traffic_logs(request):
    logs = TrafficLog.objects.all().order_by('-timestamp')

    # Фильтры
    if method := request.GET.get('method'):
        logs = logs.filter(method=method)
    if status := request.GET.get('status'):
        logs = logs.filter(status_code=status)
    if ip := request.GET.get('ip'):
        logs = logs.filter(ip_address__icontains=ip)

    page_obj, paginator = paginate(request, logs, 25)

    return render(request, 'speed_tester/traffic.html', {
        'logs': page_obj,
        'paginator': paginator,
        'page_obj': page_obj
    })


# ============================================================
#                     COMMANDS + EXPLOITS
# ============================================================

def get_commands(request):
    result = []
    for cmd in Commands.objects.all():
        examples = ExploitExample.objects.filter(category__icontains=cmd.command)[:3]
        result.append({
            'id': cmd.id,
            'dork_command': cmd.command,
            'description': cmd.description,
            'examples': [{'description': e.description, 'url': e.url} for e in examples]
        })
    return JsonResponse({'commands': result})


def com_list(request):
    return render(request, 'speed_tester/command_list.html', {
        'results': Commands.objects.all()
    })


def exploit_list_view(request):
    category = request.GET.get('category')
    exploits = ExploitExample.objects.filter(category__icontains=category) if category else ExploitExample.objects.all()[:50]

    return render(request, 'speed_tester/exploit_list.html', {
        'exploits': exploits
    })


# ============================================================
#                     DETAIL VIEW
# ============================================================

def speed_test_results_detail(request, result_id):
    try:
        result = SpeedTestResult.objects.get(pk=result_id)
    except SpeedTestResult.DoesNotExist:
        return render(request, 'speed_tester/result_not_found.html', {
            'result_id': result_id
        }, status=404)

    return render(request, 'speed_tester/results_detail.html', {
        'result': result
    })


def speed_test_results_list(request):
    results = SpeedTestResult.objects.all().order_by('-timestamp')
    return render(request, 'speed_tester/results_list.html', {'results': results})




def exploit_list_view(request):
    category = request.GET.get('category')
    if category:
        exploits = ExploitExample.objects.filter(category__icontains=category)
    else:
        exploits = ExploitExample.objects.all()[:50]  # первые 50 записей
    return render(request, "speed_tester/exploit_list.html", {"exploits": exploits})
