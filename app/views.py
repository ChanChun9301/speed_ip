from django.shortcuts import render,redirect
from django.urls import reverse
import requests
from bs4 import BeautifulSoup
from .forms import *
from .models import *
from django.http import JsonResponse
import subprocess
import platform
from django.contrib.auth import login, authenticate
# import speedtest as st_lib
from pyspeedtest import SpeedTest
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.template import loader, Context, RequestContext
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

def index(request):
    return render(request,'speed_tester/index.html',{})

def auth_view(request):
    login_form = AuthenticationForm()
    register_form = CustomUserCreationForm()
    return render(request, 'speed_tester/login.html', {'login_form': login_form, 'register_form': register_form})

def get_commands(request):
    commands = Commands.objects.all()
    data = [{'id': cmd.id, 'dork_command': cmd.command, 'description': cmd.description} for cmd in commands]
    return JsonResponse({'commands': data})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            django_login(request, user)
            messages.success(request, f'Hoş geldiňiz, {user.username}!')
            return redirect('home')  # Redirect to your homepage
        else:
            # Re-render the auth page with login errors
            login_form = form
            register_form = UserCreationForm()
            return render(request, 'speed_tester/login.html', {'login_form': login_form, 'register_form': register_form})
    else:
        return redirect('auth') # Redirect to the page with both forms

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Hasap döredildi: {username}! Indi ulanyp bilersiňiz.')
            django_login(request, user) # Optionally log the user in immediately
            return redirect('home') # Redirect to your homepage
        else:
            # Re-render the auth page with registration errors
            login_form = AuthenticationForm()
            register_form = form
            return render(request, 'speed_tester/login.html', {'login_form': login_form, 'register_form': register_form})
    else:
        return redirect('auth') # Redirect to the page with both forms

def logout_view(request):
    django_logout(request)
    messages.info(request, "Ulgamdan çykdyňyz.")
    return redirect('auth') # Redirect back to the login/register page

    return render(request, 'speed_tester/login.html', {'login_form': login_form})  

def traffic_logs(request):
    logs = TrafficLog.objects.all().order_by('-timestamp')
    return render(request, 'speed_tester/traffic.html', {'logs': logs})

import subprocess
import platform
import requests
import time

def run_speed_test(ip_address):
    """Berlen IP salgysy üçin ping we tizlik ölçemegini ýerine ýetirýär."""
    results = {'ip_address': ip_address, 'ping_ms': None, 'download_speed_kbps': None, 'upload_speed_kbps': None}

    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '4', ip_address]

    # Ping
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_bytes, stderr_bytes = process.communicate(timeout=10)
        stdout = ''
        stderr = ''
        for encoding in ['utf-8', 'cp1251', 'latin-1', 'windows-1252']:
            try:
                stdout = stdout_bytes.decode(encoding)
                stderr = stderr_bytes.decode(encoding)
                break
            except UnicodeDecodeError:
                pass

        if process.returncode == 0:
            lines = stdout.split('\n')
            for line in lines:
                if 'avg' in line or 'Average' in line or 'Среднее' in line:
                    parts = line.split('=')[1].split('/') if '=' in line else line.split(': ')[1].split(', ')[0].split('ms')[0].replace('мс', '').strip()
                    try:
                        results['ping_ms'] = float(parts[0]) if isinstance(parts, list) else float(parts)
                    except ValueError:
                        pass
        else:
            print(f"Pingde ýalňyşlyk {ip_address} (kod {process.returncode}): {stderr}")
            results['ping_ms'] = None
    except subprocess.TimeoutExpired:
        results['ping_ms'] = -1  # Wagt gutarandygyny görkezýäris
        print(f"Ping {ip_address} wagty gutardy.")
    except Exception as e:
        print(f"Ping wagtynda garaşylmadyk ýalňyşlyk ýüze çykdy {ip_address}: {e}")
        results['ping_ms'] = None

    # Download speed test using a known file
    download_url = 'http://ipv4.download.thinkbroadband.com/1MB.zip'  # Sample file URL
    try:
        start_time = time.time()
        response = requests.get(download_url, stream=True)
        total_length = 0

        for data in response.iter_content(chunk_size=8192):
            total_length += len(data)

        end_time = time.time()
        download_time = end_time - start_time
        if download_time > 0:
            results['download_speed_kbps'] = (total_length / 1024) / download_time  # kbps
    except Exception as e:
        print(f"Download üçin ýalňyşlyk: {e}")
        results['download_speed_kbps'] = None

    # Upload speed test (uploading a small file to a server)
    try:
        upload_url = 'https://httpbin.org/post'  # Sample upload URL
        upload_data = b'x' * 1024 * 1024  # 1 MB of data
        start_time = time.time()
        response = requests.post(upload_url, data=upload_data)
        end_time = time.time()
        upload_time = end_time - start_time

        if upload_time > 0:
            results['upload_speed_kbps'] = (len(upload_data) / 1024) / upload_time  # kbps
    except Exception as e:
        print(f"Upload üçin ýalňyşlyk: {e}")
        results['upload_speed_kbps'] = None

    print(results)
    return results

def speed_test_view(request):
    if request.method == 'POST':
        form = IPAddressForm(request.POST)
        if form.is_valid():
            ip_address = form.cleaned_data['ip_addresses']
            test_result = run_speed_test(ip_address)
            print(test_result)
            SpeedTestResult.objects.create(
                ip_address=test_result['ip_address'],
                ping_ms=test_result['ping_ms'],
                download_speed_kbps=test_result['download_speed_kbps'],
                upload_speed_kbps=test_result['upload_speed_kbps']
            )
            return render(request, 'speed_tester/results.html', {'results': [test_result]})
    else:
        form = IPAddressForm()
    return render(request, 'speed_tester/speed_test_form.html', {'form': form})


def history_view(request):
    """Отображает историю последних 10 результатов тестов."""
    history = SpeedTestResult.objects.all().order_by('-timestamp')[:10]
    return render(request, 'speed_tester/history.html', {'history': history})

@login_required
def google_dorking_view(request):
    form = GoogleDorkingForm()
    results = []
    if request.method == 'POST':
        form = GoogleDorkingForm(request.POST)
        if form.is_valid():
            text_input = form.cleaned_data['text_input']
            dork_command = form.cleaned_data['dork_command']

            full_query = f"{dork_command} {text_input}".strip() if dork_command else text_input
            search_query = SearchQuery(user=request.user, text_input=text_input, dork_command=dork_command, full_query=full_query)
            search_query.save()

            # *** ВНИМАНИЕ: Google не приветствует автоматизированные запросы (скрейпинг). ***
            # *** Это может привести к блокировке вашего IP-адреса. ***
            # *** Используйте Google Custom Search API (платный/бесплатный с ограничениями) для легального доступа к результатам поиска. ***

            # Пример очень простого (и ненадежного для реального использования) скрейпинга:
            try:
                url = f"https://www.google.com/search?q={full_query.replace(' ', '+')}"
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'}
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                search_results = soup.find_all('div', class_='tF2Cxc') # Пример класса, может меняться
                results = [{'title': res.find('h3').text if res.find('h3') else 'Нет заголовка',
                            'link': res.find('a')['href'] if res.find('a') else '#'} for res in search_results[:10]] # Ограничим первыми 10 результатами
                search_query.results_count = len(results)
                search_query.save()

            except requests.exceptions.RequestException as e:
                results = [{'error': f"Ошибка при выполнении поиска: {e}"}]

            return render(request, 'google_dorking.html', {'form': form, 'results': results})

    return render(request, 'google_dorking.html', {'form': form})

@login_required
def search_history_view(request):
    history = SearchQuery.objects.filter(user=request.user).order_by('-search_date')
    return render(request, 'search_history.html', {'history': history})

def update_exploit_db_dorks(request):
    url = "https://www.exploit-db.com/google-hacking-database"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', {'class': 'table'})
        if table:
            tbody = table.find('tbody')
            rows = tbody.find_all('tr')
            for row in rows:
                columns = row.find_all('td')
                if len(columns) >= 3:
                    category = columns[1].text.strip()
                    description = columns[2].text.strip()
                    link_tag = columns[2].find('a')
                    link = f"https://www.exploit-db.com{link_tag['href']}" if link_tag and 'href' in link_tag.attrs else None
                    dork_command = columns[3].text.strip()

                    ExploitDbDork.objects.update_or_create(
                        dork_command=dork_command,
                        defaults={'category': category, 'description': description, 'link': link}
                    )
            return redirect(reverse('exploit_db_dorks_view'))
        else:
            return render(request, 'error.html', {'message': 'Не удалось найти таблицу на странице Exploit-DB.'})
    except requests.exceptions.RequestException as e:
        return render(request, 'error.html', {'message': f'Ошибка при получении данных с Exploit-DB: {e}'})

def exploit_db_dorks_view(request):
    dorks = ExploitDbDork.objects.all().order_by('category', 'dork_command')
    return render(request, 'exploit_db_dorks.html', {'dorks': dorks})


def speed_test_results_list(request):
    """Displays a list of speed test results."""
    results = SpeedTestResult.objects.all().order_by('-timestamp')
    return render(request, 'speed_tester/results_list.html', {'results': results})

def speed_test_results_detail(request, result_id):
    """Displays details for a specific speed test result."""
    try:
        result = SpeedTestResult.objects.get(pk=result_id)
    except SpeedTestResult.DoesNotExist:
        # Handle the case where the result doesn't exist (e.g., 404 page)
        return render(request, 'speed_tester/result_not_found.html', {'result_id': result_id}, status=404)
    return render(request, 'speed_tester/results_detail.html', {'result': result})

def search_query_list(request):
    """Displays a list of search queries."""
    queries = SearchQuery.objects.all().order_by('-search_date')
    return render(request, 'search/query_list.html', {'queries': queries})

def search_interface(request):
    """Displays the search interface with the form."""
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            text_input = form.cleaned_data['text_input']
            dork_command = form.cleaned_data.get('dork_command', '')  # Get with default if not provided
            full_query = text_input  # Basic implementation, adjust based on how you build full query
            if dork_command:
                full_query = f"{dork_command} {text_input}"

            search_query = SearchQuery.objects.create(
                text_input=text_input,
                dork_command=dork_command,
                full_query=full_query
                # You might want to trigger the actual search here and store results_count
            )
            return render(request, 'search/search_results.html', {'query': search_query}) # Basic feedback
    else:
        form = SearchForm()
    return render(request, 'search/search_form.html', {'form': form})

def exploit_db_dork_list(request):
    """Displays a list of Exploit-DB dorks."""
    dorks = ExploitDbDork.objects.all().order_by('category', 'dork_command')
    return render(request, 'exploitdb/dork_list.html', {'dorks': dorks})

def exploit_db_dork_detail(request, dork_id):
    """Displays details for a specific Exploit-DB dork."""
    try:
        dork = ExploitDbDork.objects.get(pk=dork_id)
    except ExploitDbDork.DoesNotExist:
        return render(request, 'exploitdb/dork_not_found.html', {'dork_id': dork_id}, status=404)
    return render(request, 'exploitdb/dork_detail.html', {'dork': dork})