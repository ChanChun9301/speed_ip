from django.shortcuts import render,redirect
import requests
from bs4 import BeautifulSoup
from .forms import *
from .models import *
from django.http import JsonResponse
import subprocess
from pyspeedtest import SpeedTest
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
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
import speedtest



def first_visit(request):
    if not request.user.is_authenticated:
        return redirect('login')  
    else:
        return redirect('home')

@login_required
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
            return redirect('home')  
        else:
            login_form = form
            register_form = UserCreationForm()
            return render(request, 'speed_tester/login.html', {'login_form': login_form, 'register_form': register_form})
    else:
        return redirect('auth') 

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Hasap döredildi: {username}! Indi ulanyp bilersiňiz.')
            django_login(request, user) 
            return redirect('home')
            login_form = AuthenticationForm()
            register_form = form
            return render(request, 'speed_tester/login.html', {'login_form': login_form, 'register_form': register_form})
    else:
        return redirect('auth') 

def logout_view(request):
    django_logout(request)
    messages.info(request, "Ulgamdan çykdyňyz.")
    return redirect('auth') 

    return render(request, 'speed_tester/login.html', {'login_form': login_form})  

def capture_netstat():
    try:
        result = subprocess.run(['netstat', '-an'], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            lines = result.stdout.splitlines()
            for line in lines:
                if line.startswith(('Proto', 'TCP', 'UDP')):
                    log_entry = line.strip()
                    print(f"Logging entry: {log_entry}") 
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
        time.sleep(5) 

def start_netstat_capture_thread():
    capture_thread = threading.Thread(target=run_netstat_capture)
    capture_thread.daemon = True
    capture_thread.start()

def traffic_logs(request):
    logs = TrafficLog.objects.all().order_by('-timestamp')
    return render(request, 'speed_tester/traffic.html', {'logs': logs})

def get_ip_address(domain):
    try:
        ip_address = socket.gethostbyname(domain)
        return ip_address
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
        destination_ip = get_ip_address(ip_address)
        results['destination_ip'] = destination_ip

    try:
        s = speedtest.Speedtest()
        s.get_best_server()
        s.download()
        s.upload()
        res = s.results.dict()

        results['ping_ms'] = res.get('ping') * 1000 if res.get('ping') is not None else None
        results['download_speed_kbps'] = res.get('download') / 1000 if res.get('download') is not None else None
        results['upload_speed_kbps'] = res.get('upload') / 1000 if res.get('upload') is not None else None
        results['ip_address'] = res.get('client', {}).get('ip', ip_address)

    except speedtest.SpeedtestException as e:
        print(f"Speedtest error for {ip_address}: {e}")
        results['error'] = str(e)
    except Exception as e:
        print(f"An unexpected error occurred during speed test for {ip_address}: {e}")
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
                print(test_result)
                all_results.append(test_result)
                if 'input' in test_result and 'ping_ms' in test_result and \
                   'download_speed_kbps' in test_result and 'upload_speed_kbps' in test_result and 'error' not in test_result:
                    SpeedTestResult.objects.create(
                        ip_address=ip_addresses_text, 
                        destination_ip=test_result.get('destination_ip'), 
                        ping_ms=test_result['ping_ms'],
                        download_speed_kbps=test_result['download_speed_kbps'],
                        upload_speed_kbps=test_result['upload_speed_kbps']
                    )

            return render(request, 'speed_tester/results.html', {'results': all_results})
        else:
            return render(request, 'speed_tester/speed_test_form.html', {'form': form, 'error': 'Nädogry IP salgy ýa-da domen ady formaty.'})
    else:
        form = IPAddressForm()

    return render(request, 'speed_tester/speed_test_form.html', {'form': form})


def history_view(request):
    history = SpeedTestResult.objects.all().order_by('-timestamp')
    return render(request, 'speed_tester/history.html', {'history': history})

def com_list(request):
    results = Commands.objects.all()
    return render(request, 'speed_tester/command_list.html', {'results': results})

@login_required
def save_search(request):
    if request.method == 'POST':
        full_query = request.POST.get('full_query')
        text_inputs_json = request.POST.get('text_inputs')
        dork_commands_json = request.POST.get('dork_commands')
        

        try:
            text_inputs = json.loads(text_inputs_json)
            dork_commands = json.loads(dork_commands_json)
            print(full_query)
            print(text_inputs_json)
            print(request.user)

            for text_input, dork_command in zip(text_inputs, dork_commands):
                search_query = SearchQuery(
                    user=request.user,
                    text_input=text_input.strip(),
                    dork_command=dork_command.strip(),
                    full_query=full_query.strip()
                )
                print(search_query)
                search_query.save()

            return JsonResponse({'status': 'success'}) 
        except json.JSONDecodeError as e:
            return JsonResponse({'status': 'error', 'message': f'JSON dekodirlenende ýalňyşlyk: {e}'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Gözleg saklanylanda ýalňyşlyk: {e}'}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Diňe POST isleglerine rugsat berilýär.'}, status=405)


def search_history_view(request):
    history = SearchQuery.objects.all().order_by('-search_date')
    return render(request, 'speed_tester/search_history.html', {'history': history})


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
