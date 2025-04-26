from django.shortcuts import render
from .forms import IPAddressForm
from .models import SpeedTestResult
import subprocess
import platform
# import speedtest as st_lib
from pyspeedtest import SpeedTest

def run_speed_test(ip_address):
    """Выполняет ping и измерение скорости для заданного IP-адреса с учетом ОС и кодировки."""
    results = {'ip_address': ip_address, 'ping_ms': None, 'download_speed_kbps': None, 'upload_speed_kbps': None}

    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '4', ip_address]

    # Пинг
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
            print(lines)
            for line in lines:
                if 'avg' in line or 'Average' in line:
                    parts = line.split('=')[1].split('/') if '=' in line else line.split(': ')[1].split(', ')[0].split('ms')[0]
                    try:
                        results['ping_ms'] = float(parts[0]) if isinstance(parts, list) else float(parts)
                    except ValueError:
                        pass
        else:
            print(f"Ошибка при пинге {ip_address} (код {process.returncode}): {stderr}")
            results['ping_ms'] = None
    except subprocess.TimeoutExpired:
        results['ping_ms'] = -1  # Указываем, что время ожидания истекло
        print(f"Пинг {ip_address} истекло время ожидания.")
    except Exception as e:
        print(f"Произошла неожиданная ошибка при пинге {ip_address}: {e}")
        results['ping_ms'] = None

    # Измерение скорости download/upload (требует подключения к интернету на сервере)
    try:
        process = subprocess.Popen(['speedtest-cli', '--simple'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_bytes, stderr_bytes = process.communicate(timeout=30)  # Увеличим таймаут
        stdout = stdout_bytes.decode('utf-8', errors='ignore').strip()
        stderr = stderr_bytes.decode('utf-8', errors='ignore').strip()

        if stdout:
            parts = stdout.split('\n')
            ping_cli = None
            download_cli = None
            upload_cli = None
            for part in parts:
                if 'Ping:' in part:
                    try:
                        ping_cli = float(part.split(': ')[1].split(' ms')[0])
                    except ValueError:
                        pass
                elif 'Download:' in part:
                    try:
                        download_cli = float(part.split(': ')[1].split(' Mbit/s')[0]) * 1000  # Convert to kbps
                    except ValueError:
                        pass
                elif 'Upload:' in part:
                    try:
                        upload_cli = float(part.split(': ')[1].split(' Mbit/s')[0]) * 1000  # Convert to kbps
                    except ValueError:
                        pass
            results['ping_ms'] = ping_cli
            results['download_speed_kbps'] = download_cli
            results['upload_speed_kbps'] = upload_cli
        else:
            print(f"Ошибка speedtest-cli для {ip_address}: {stderr}")

    except Exception as e:
        print(f"Произошла ошибка при запуске speedtest-cli: {e}")
        results['download_speed_kbps'] = None
        results['upload_speed_kbps'] = None

    return results


def speed_test_view(request):
    if request.method == 'POST':
        form = IPAddressForm(request.POST)
        if form.is_valid():
            ip_addresses_text = form.cleaned_data['ip_addresses']
            ip_addresses = [ip.strip() for ip in ip_addresses_text.split('\n') if ip.strip()]
            results = []
            for ip in ip_addresses:
                test_result = run_speed_test(ip)
                print(test_result)
                SpeedTestResult.objects.create(
                    ip_address=test_result['ip_address'],
                    ping_ms=test_result['ping_ms'],
                    download_speed_kbps=test_result['download_speed_kbps'],
                    upload_speed_kbps=test_result['upload_speed_kbps']
                )
                results.append(test_result)
            return render(request, 'speed_tester/results.html', {'results': results})
    else:
        form = IPAddressForm()
    return render(request, 'speed_tester/speed_test_form.html', {'form': form})


def history_view(request):
    """Отображает историю последних 10 результатов тестов."""
    history = SpeedTestResult.objects.all().order_by('-timestamp')[:10]
    return render(request, 'speed_tester/history.html', {'history': history})