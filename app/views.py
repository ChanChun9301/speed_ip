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
import socket
import threading
import subprocess
import platform
import requests
import time
import json
import re



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

def capture_netstat():
    try:
        result = subprocess.run(['netstat', '-an'], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            lines = result.stdout.splitlines()
            for line in lines:
                if line.startswith(('Proto', 'TCP', 'UDP')):
                    log_entry = line.strip()
                    print(f"Logging entry: {log_entry}")  # Debug statement
                    a = TrafficLog.objects.create(
                        method='Netstat Capture',
                        path=log_entry,
                        duration=0,
                        timestamp=timezone.now()
                    )
                    print('>>>>>'+str(a)+'\n')
        else:
            print(f"Error running netstat: {result.stderr}")
    except Exception as e:
        print(f"An error occurred: {e}")

def run_netstat_capture():
    while True:
        capture_netstat()
        time.sleep(5)  # Capture every 60 seconds

def start_netstat_capture_thread():
    capture_thread = threading.Thread(target=run_netstat_capture)
    capture_thread.daemon = True
    capture_thread.start()

def traffic_logs(request):
    logs = TrafficLog.objects.all().order_by('-timestamp')
    return render(request, 'speed_tester/traffic.html', {'logs': logs})

def run_speed_test(ip_address):
    """Executes ping and speed tests for the given IP address."""
    results = {
        'ip_address': ip_address,
        'ping_ms': None,
        'download_speed_kbps': None,
        'upload_speed_kbps': None
    }

    # Ping
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '4', ip_address]

    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_bytes, stderr_bytes = process.communicate(timeout=10)

        # Try decoding output with multiple encodings
        for encoding in ['utf-8', 'cp1251', 'latin-1', 'windows-1252']:
            try:
                stdout = stdout_bytes.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            stdout = stdout_bytes.decode(errors='ignore')

        print('Code:'+str(process.returncode))
        if process.returncode == 0:
            for line in stdout.split('\n'):
                line_lower = line.lower()
                if 'время' in line_lower and 'мс' in line_lower: # Handle individual ping times
                    parts = line.split('время=')
                    if len(parts) > 1:
                        time_part = parts[1].split()[0].replace('мс', '').replace('<', '').strip()
                        try:
                            ping_ms = float(time_part)
                            if results['ping_ms'] is None or ping_ms < results['ping_ms']: # Keep track of the minimum if individual times are the only option
                                results['ping_ms'] = ping_ms
                            print('milli sekund (время=):', ping_ms)
                        except ValueError:
                            print(f"Could not convert ping time (время=) to float: {time_part}")
                elif any(keyword in line_lower for keyword in ['минимальное =', 'максимальное =', 'среднее =']):
                    parts = line.split('=')
                    print(parts)
                    if len(parts) > 1:
                        time_part = parts[1].strip().split()[0].replace('мсек', '').strip()
                        try:
                            ping_ms = float(time_part)
                            results['ping_ms'] = ping_ms
                            print('milli sekund (мин/макс/среднее):', ping_ms)
                            break # Found the average, no need to continue
                        except ValueError:
                            print(f"Could not convert ping time (мин/макс/среднее) to float: {time_part}")
                elif any(keyword in line_lower for keyword in ['мин.', 'макс.']): # Keep this for other variations
                    numbers = [float(s.replace(',', '.').replace('ms', '').replace('мсек', '').strip()) for s in line.split() if s.replace(',', '').replace('.', '').isdigit()]
                    if numbers and len(numbers) >= 2:
                        results['ping_ms'] = numbers[1] # Assuming average is the second number after min/max
                        print('milli sekund (мин/макс):', numbers[1])
                        break
                elif 'time' in line_lower: # For some English outputs
                    parts = line.split('time=')[1].split()[0].replace('ms', '').strip()
                    try:
                        ping_ms = float(parts)
                        results['ping_ms'] = ping_ms
                        print('milli sekund (time=):', ping_ms)
                        break
                    except ValueError:
                        print(f"Could not convert ping time (time=) to float: {parts}")

        else:
            print(f"Ping error for {ip_address} (code {process.returncode}): {stderr_bytes.decode(errors='ignore')}")
            results['ping_ms'] = None

    except subprocess.TimeoutExpired:
        print(f"Ping timeout for {ip_address}")
        results['ping_ms'] = -1
        # print(results['ping_ms'])
    except Exception as e:
        print(f"Unexpected ping error: {e}")

    # Download Speed Test (commented out)
    # ...

    # Upload Speed Test (commented out)
    # ...

    # print(results)
    return results

def speed_test_view(request):
    if request.method == 'POST':
        form = IPAddressForm(request.POST)
        if form.is_valid():
            ip_address = form.cleaned_data['ip_addresses']
            test_result = run_speed_test(ip_address)
            print(test_result)

             # Ensure all values are not None
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
    history = SpeedTestResult.objects.all().order_by('-timestamp')[:10]
    return render(request, 'speed_tester/history.html', {'history': history})

def com_list(request):
    results = Commands.objects.all()
    return render(request, 'speed_tester/command_list.html', {'results': results})

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
def save_search(request):
    if request.method == 'POST':
        full_query = request.POST.get('full_query')
        text_inputs_json = request.POST.get('text_inputs')
        dork_commands_json = request.POST.get('dork_commands')

        try:
            text_inputs = json.loads(text_inputs_json)
            dork_commands = json.loads(dork_commands_json)

            for text_input, dork_command in zip(text_inputs, dork_commands):
                search_query = SearchQuery(
                    user=request.user,
                    text_input=text_input.strip(),
                    dork_command=dork_command.strip(),
                    full_query=full_query.strip()
                )
                search_query.save()

            return JsonResponse({'status': 'success'}) # Optionally return a success response
        except json.JSONDecodeError as e:
            return JsonResponse({'status': 'error', 'message': f'JSON dekodirlenende ýalňyşlyk: {e}'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Gözleg saklanylanda ýalňyşlyk: {e}'}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Diňe POST isleglerine rugsat berilýär.'}, status=405)


def search_history_view(request):
    history = SearchQuery.objects.all()
    return render(request, 'speed_tester/search_history.html', {'history': history})

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
