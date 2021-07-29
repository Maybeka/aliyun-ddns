import os, time, platform, subprocess
from urllib import request

# wrapper function for printing with timestamp
def tprint(*args, end='\n', file=None):  
    time_str = time.strftime('%Y-%m-%d %H:%M:%S ::', time.localtime())
    print(time_str, *args, end=end, file=file, flush=file!=None)

## get list of ip addresses for each domain
def getIPAddrs(cfg_dict, domain='local', use_v6=False):
    if domain+'-IP-Command' not in cfg_dict:
        return [localAddrFromUrls(use_v6)]
    else: # for domain with specific command to get ip
        ips = os.popen(cfg_dict[domain+'-IP-Command'])
        return [ip.strip() for ip in ips]

def localAddrFromUrls(use_v6 = False):
    # derived from https://github.com/mgsky1/DDNS/blob/master/src/IpGetter.py
    if use_v6:
        url = "https://v6.ident.me/.json"
        response = request.urlopen(url)
        return response.read().decode('utf-8').strip()
    else:
        try:
            url = 'https://api.ipify.org/?format=json'
            response = request.urlopen(url, timeout=60)
            return response.read().decode('utf-8')['ip']
        except:
            url = 'http://members.3322.org/dyndns/getip'
            response = request.urlopen(url, timeout=60)
            return response.read().decode('utf-8').strip()

#判断是否联网
def isOnline():
    userOs = platform.system() #获取操作系统平台
    try:
        if userOs == "Windows":
            subprocess.check_call(["ping", "-n", "2", "www.baidu.com"], stdout=subprocess.PIPE)
        else:
            subprocess.check_call(["ping", "-c", "2", "www.baidu.com"], stdout=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        return False

def checkOnlineStatus(cfg):
    offline_cnt = 0
    while not isOnline():
        if offline_cnt < cfg.FAST_NETCHK_NUM:
            sleep_seconds = cfg.FAST_NETCHK_PERIOD  
        else:
            sleep_seconds = cfg.NET_CHECK_PERIOD
        time.sleep(sleep_seconds)  # wait some time before next network check
        offline_cnt += 1
        if offline_cnt >= cfg.NET_CHECK_NUM: break
    return offline_cnt