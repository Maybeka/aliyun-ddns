import sys, json, time
import Utils
from aliyunsdkcore.client  import AcsClient
from aliyunsdkcore.request import CommonRequest
from aliyunsdkcore.acs_exception.exceptions import ServerException
from aliyunsdkcore.acs_exception.exceptions import ClientException
from Utils import tprint
from ConfigParser import ConfigParser

class ddnsAliyun:
    def __init__(self, cfg_file='config.json', log_file='aliyun_ddns.log') -> None:
        self._client  = AcsClient('', '', '')  # singleton of AcsClient
        self._request = CommonRequest()  # singleton of CommonRequest

        self.run_cnt     = 0  # run times within one cfg update period
        self.upd_cfg_cnt = 0  # cfg update times
        
        self.log_file = open(log_file, 'w')  # log file recording basic info of one 'run()'
        self.cfg      = ConfigParser(cfg_file)

    def doOneRequest(self, action, query_params):
        self._request.set_domain('alidns.aliyuncs.com')
        self._request.set_version('2015-01-09')
        if self.cfg.debug: tprint('doOneRequest with action:', action)
        self._request.set_action_name(action)
        for param in query_params:
            if self.cfg.debug: tprint('doOneRequest with query param:', param, query_params[param])
            self._request.add_query_param(param, query_params[param])
        return self._client.do_action_with_exception(self._request)

    # 获取二级域名的RecordId
    def getRecordId(self):
        resp = self.doOneRequest('DescribeDomainRecords', {'DomainName': self.cfg.first_domain})
        jsonObj = json.loads(resp.decode("UTF-8"))
        records = jsonObj["DomainRecords"]["Record"]
        self.cfg.rr_names  = [record['RR']                    for record in records]
        self.cfg.rr_id_map = {record['RR']:record['RecordId'] for record in records}
        self.cfg.rr_ip_map = {record['RR']:record['Value'   ] for record in records}
        if self.cfg.debug: 
            for domain in self.cfg.rr_names:
                tprint('getRecordId dns records:', domain, self.cfg.rr_id_map[domain], self.cfg.rr_ip_map[domain])

    def updateAllCfg(self):
        if self.cfg.debug: tprint('updateAllCfg: updating all cfgs ...')
        self.cfg.getConfigJson()
        self._client = AcsClient(self.cfg.dict['AccessKeyId'], self.cfg.dict['AccessKeySecret'], 'cn-hangzhou')
        self.getRecordId  ()

    def doUpdateForRR(self, rr):
        type = self.cfg.dict[rr+'-Record-Type'] if rr+'-Record-Type' in self.cfg.dict else 'A'
        ip   = Utils.getIPAddrs(self.cfg.dict, domain=rr, use_v6=(type=='AAAA'))[-1]

        if self.cfg.debug: tprint('updateDns: current ip', ip, ', dns ip', self.cfg.rr_ip_map[rr])
        if rr in self.cfg.rr_ip_map and ip == self.cfg.rr_ip_map[rr]:  # skip all actions while ip has not changed since previous update
            if self.cfg.debug: tprint(f'updateDns: address for {rr} is the same with dns server record({self.cfg.rr_ip_map[rr]}), nothing will be changed.')
            tprint(f'updateDns: address for {rr} is the same with dns server record({self.cfg.rr_ip_map[rr]}), nothing will be changed.', file=self.log_file)
            return

        if rr in self.cfg.rr_names:  # update the record if second domain already exists in dns
            query_params = {'RecordId': self.cfg.rr_id_map[rr], 'RR': rr, 'Type': type, 'Value': ip}
            resp = self.doOneRequest('UpdateDomainRecord', query_params)
            if resp:
                if self.cfg.debug: tprint(f'updateDns: successfully updated {rr} address from {self.cfg.rr_id_map[rr]} to {ip}')
                tprint(f'updateDns: successfully updated {rr} address from {self.cfg.rr_ip_map[rr]} to {ip}', file=self.log_file)
            else:
                if self.cfg.debug: tprint(f'updateDns: failed to update {rr} address from {self.cfg.rr_ip_map[rr]} to {ip}', file=self.log_file)
                tprint(f'updateDns: failed to update {rr} address from {self.cfg.rr_id_map[rr]} to {ip}')
        else:  # add a record if second domain dose not exists in dns
            query_params = {'DomainName': self.cfg.first_domain, 'RR': rr, 'Type': type, 'Value': ip}
            resp = self.doOneRequest('AddDomainRecord', query_params)
            if resp:
                if self.cfg.debug: tprint(f'updateDns: successfully added {rr} with address {ip}')
                tprint(f'updateDns: successfully added {rr} with address {ip}', file=self.log_file)
            else:
                if self.cfg.debug: tprint(f'updateDns: failed to add {rr} with address {ip}')
                tprint(f'updateDns: failed to add {rr} with address {ip}', file=self.log_file)
        if self.cfg.debug: tprint('updateDns query_params:', query_params)
        if resp: self.getRecordId()

    def updateDns(self):
        check_times = Utils.checkOnlineStatus(self)
        if check_times == self.cfg.NET_CHECK_NUM:
            if self.cfg.debug: tprint(f'There is error in network after {self.cfg.NET_CHECK_NUM} times of check.')
            tprint(f'updateDns ERROR: no network after {self.cfg.NET_CHECK_NUM} times of check.', file=self.log_file)
            return False
        elif self.cfg.debug: tprint('updateDns: The network is ok.')
        if self.run_cnt == 0 or check_times > 0: self.updateAllCfg()
            
        for rr in self.cfg.second_domains:
            try:
                self.doUpdateForRR(rr)
            except (ServerException, ClientException) as reason:
                tprint(f'updateDns ERROR: action for {rr} failed - reason - {reason.get_error_msg()}', file=self.log_file)
        
        if self.run_cnt < self.cfg.UPDATE_CFG_PERIOD - 1:
            self.run_cnt += 1
        else:
            self.upd_cfg_cnt += 1
            self.run_cnt = 0

        if self.cfg.debug:
            tprint('updateDns: waiting for 10s to end.')
            time.sleep(10)
        else:
            time.sleep(self.cfg.UPDATE_DNS_PERIOD)

    def run(self):
        tprint('ddnsAliyun: start to run ...', file=ddns.log_file)
        while (1):
            if self.cfg.debug: 
                tprint('**********************************************************************')
                tprint(f'run: execute updateDns() for the {self.upd_cfg_cnt*self.cfg.UPDATE_CFG_PERIOD+self.run_cnt+1}st/rd/th time ...')
                tprint('**********************************************************************')
            self.updateDns()

if __name__ == "__main__":
    argc = len(sys.argv)
    cfg_file = 'config.json'     if argc < 2 else sys.argv[1]
    log_file = 'aliyun_ddns.log' if argc < 3 else sys.argv[2]
    ddns = ddnsAliyun(cfg_file, log_file)
    ddns.run()