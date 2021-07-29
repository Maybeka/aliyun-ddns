import json
from Utils import tprint

class ConfigParser:
    def __init__(self, cfg_file='config.json') -> None:
        self.cfg_file       = cfg_file
        self.dict           = {}  # configuration parsed from config.json
        self.first_domain   = ''  # 1st domain name from config.json
        self.second_domains = []  # list of 2nd domain names from config.json

        self.UPDATE_DNS_PERIOD  = 300  # in seconds
        self.UPDATE_CFG_PERIOD  = 30   # in times
        self.FAST_NETCHK_NUM    = 10   # in times
        self.NET_CHECK_NUM      = 20   # in times
        self.FAST_NETCHK_PERIOD = 10   # in seconds
        self.NET_CHECK_PERIOD   = 600  # in seconds

        self.rr_names  = []  # 2nd domain list from dns
        self.rr_id_map = {}  # map from 2nd domain to its record id
        self.rr_ip_map = {}  # map from 2nd domain to its ip address

        self.debug    = False  # debug mode: run with a lot messages

    # 从config.json中获取配置信息JSON串
    def getConfigJson(self):
        with open(self.cfg_file) as file:
            self.dict = json.loads(file.read())
        self.first_domain   = self.dict[ 'First-level-domain' ]
        self.second_domains = self.dict['Second-level-domains']
        if self.debug:
            for key in self.dict:
                tprint('getConfigJson cfgDict:', key, '->', self.dict[key])
            tprint('getConfigJson first_domain:', self.first_domain)
            tprint('getConfigJson second_domains:', self.second_domains)
        if 'Update-DNS-Period'  in self.dict: self.UPDATE_DNS_PERIOD  = self.dict['Update-DNS-Period' ]
        if 'Update-Cfg-Period'  in self.dict: self.UPDATE_CFG_PERIOD  = self.dict['Update-Cfg-Period' ]
        if 'Fast-NetChk-Num'    in self.dict: self.FAST_NETCHK_NUM    = self.dict['Fast-NetChk-Num'   ]
        if 'Network-Check-Num'  in self.dict: self.NET_CHECK_NUM      = self.dict['Network-Check-Num' ]
        if 'Fast-NetChk-Period' in self.dict: self.FAST_NETCHK_PERIOD = self.dict['Fast-NetChk-Period']
        if 'Net-Check-Period'   in self.dict: self.NET_CHECK_PERIOD   = self.dict['Net-Check-Period'  ]
        if 'Debug-Mode'         in self.dict: self.debug              = self.dict['Debug-Mode'        ]