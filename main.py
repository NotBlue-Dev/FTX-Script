import time
import urllib.parse
import json
from requests import Request, Session, Response
import hmac
import threading
import logging

#Settings
json_file = 'settings.json'

#Logging config
log_format = (
    '[%(asctime)s] %(levelname)-2s %(name)-2s %(message)s')

logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    filename=('ftxData.log'),
)

#FTXCLIENT API PART
class FtxClient:
    _ENDPOINT = 'https://ftx.com/api/'

    def __init__(self, api_key=None, api_secret=None, subaccount_name=None) -> None:
        self._session = Session()
        self._api_key = api_key
        self._api_secret = api_secret
        self._subaccount_name = subaccount_name

    def _get(self, path: str):
        return self._request('GET', path)

    def _request(self, method: str, path: str, **kwargs):
        request = Request(method, self._ENDPOINT + path, **kwargs)
        self._sign_request(request)
        response = self._session.send(request.prepare())
        return self._process_response(response)

    def _sign_request(self, request: Request) -> None:
        ts = int(time.time() * 1000)
        prepared = request.prepare()
        signature_payload = f'{ts}{prepared.method}{prepared.path_url}'.encode()
        if prepared.body:
            signature_payload += prepared.body
        signature = hmac.new(self._api_secret.encode(), signature_payload, 'sha256').hexdigest()
        request.headers['FTX-KEY'] = self._api_key
        request.headers['FTX-SIGN'] = signature
        request.headers['FTX-TS'] = str(ts)
        if self._subaccount_name:
            request.headers['FTX-SUBACCOUNT'] = urllib.parse.quote(self._subaccount_name)

    def _process_response(self, response: Response):
        try:
            data = response.json()
        except ValueError:
            response.raise_for_status()
            logging.error('Process response')
            raise
        else:
            if not data['success']:
                raise Exception(data['error'])
                logging.error('Data Error')
            return data['result']

    def get_lending_rates(self):
        return self._get(f'spot_margin/lending_rates')

    def get_lending_history(self):
        return self._get(f'spot_margin/lending_history')

def main():
    #Open Setting.json
    try:
        with open(json_file) as json_data:
            data = json.load(json_data)
    except:
        logging.error('JSON Reading')

    #Some security
    try:
        api = FtxClient(data['account']['api_key'],data['account']['api_secret'], data['account']['subaccount'])
    except:
        logging.error('Apikey/secret is empty')

    times = data['settings']['time']
    coin = data['settings']['coin']

    if times == '' or times == 0:
        times = 60.0
        logging.error('Time is empty 60.0 has been set by default')

    if times != float:
        float(times)
        logging.error('Your times value is not a float, a conversion has been applied')

    if len(coin) == 0:
        coin = ['USD']
        logging.error('Coin is empty USD has been set by default')
        
    print('### DATA IS RETRIEVE ###')
    #some beauty in this code
    if data['settings']['prettyprint'] == "True": pretty = 3 
    else: pretty = None
    indexes = []
    #Restart every x times
    threading.Timer(times, main).start()
    #lending rate part
    getLendingRate = api.get_lending_rates()
    logging.info('\nLending Rates ' + json.dumps(getLendingRate,indent = pretty))
    #lending history part
    getLendingHistory = api.get_lending_history()
    for i in range(0,len(coin)):
        findcoin = next((index for (index, d) in enumerate(getLendingHistory) if d['coin'] == coin[i]), None)
        indexes.append(findcoin) 
    LendingHistory = []
    for i in range(0,len(indexes)):
        LendingHistory.append(getLendingHistory[indexes[i]])
    logging.info('\nLending History(Custom) ' + json.dumps(LendingHistory,indent = pretty))
main()
