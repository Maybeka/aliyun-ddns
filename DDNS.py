import json, time, Utils, ConfigParser
from aliyunsdkcore.client  import AcsClient
from aliyunsdkcore.request import CommonRequest
from aliyunsdkcore.acs_exception.exceptions import ServerException, ClientException

class ddnsAliyun:
    def __init__(self, cfg_file='config.json') -> None:
        self._client  = AcsClient('', '', '')  # singleton of AcsClient
        self._request = CommonRequest()  # singleton of CommonRequest
        self.cfg      = ConfigParser.ConfigParser(cfg_file)

    def doOneRequest(self, action, query_params):
        self._request.set_domain('alidns.aliyuncs.com')
        self._request.set_version('2015-01-09')
        self._request.set_action_name(action)
        for param in query_params: self._request.add_query_param(param, query_params[param])
        return self._client.do_action_with_exception(self._request)

    def getRecordId(self):  # 获取二级域名的RecordId
        resp = self.doOneRequest('DescribeDomainRecords', {'DomainName': self.cfg.first_domain})
        jsonObj = json.loads(resp.decode("UTF-8"))
        records = jsonObj["DomainRecords"]["Record"]
        self.cfg.rr_id_map = {record['RR']:record['RecordId'] for record in records}
        self.cfg.rr_ip_map = {record['RR']:record['Value'   ] for record in records}

    def updateAllCfg(self):
        self.cfg.getConfigJson()
        self._client = AcsClient(self.cfg.dict['AccessKeyId'], self.cfg.dict['AccessKeySecret'], 'cn-hangzhou')
        self.getRecordId()

    def doUpdateForRR(self, rr):
        type = self.cfg.dict[rr+'-Record-Type'] if rr+'-Record-Type' in self.cfg.dict else 'A'
        ip   = Utils.getIPAddrs(self.cfg.dict, domain=rr, use_v6=(type=='AAAA'))[-1]
        if rr in self.cfg.rr_ip_map and ip == self.cfg.rr_ip_map[rr]: return  # skip if ip has not changed
        query_params = {'RecordId': self.cfg.rr_id_map[rr], 'RR': rr, 'Type': type, 'Value': ip}
        if self.doOneRequest('UpdateDomainRecord', query_params): self.getRecordId()

    def updateDns(self):
        if Utils.checkOnlineStatus(self) == self.cfg.NET_CHECK_NUM: return  # network error: take no action now
        for rr in self.cfg.second_domains:
            try: self.doUpdateForRR(rr)
            except (ServerException, ClientException) as reason:
                print(f'updateDns ERROR: action for {rr} failed - reason - {reason.get_error_msg()}')
        time.sleep(self.cfg.UPDATE_DNS_PERIOD)

    def run(self):
        self.updateAllCfg()
        while (1): 
            self.updateDns()

if __name__ == "__main__":
    ddns = ddnsAliyun()
    ddns.run()