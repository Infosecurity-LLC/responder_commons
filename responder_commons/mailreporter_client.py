import requests
import json
import logging
from base64 import standard_b64encode

logger = logging.getLogger(__name__)


class ReportGeneratorException(Exception):
    pass


class MailReporterClient:
    def __init__(self, host):
        self.host = host

    def clean_empty(self, d):
        """
        Delete all empty elements from dictionary recursively
        :param d: data
        :return:
        """
        if not isinstance(d, (dict, list)):
            return d
        if isinstance(d, list):
            return [v for v in (self.clean_empty(v) for v in d) if v]
        return {k: v for k, v in ((k, self.clean_empty(v)) for k, v in d.items()) if v}

    def get_html_report(self, data, host: str = None, b64: bool = False):
        """
        Сгенерировать отчёт
        :param data: dict
        :param host: service url
        :param b64: вернуть отчёт в base64?
        :return:
        """
        data = self.clean_empty(data)
        if not data:
            raise ReportGeneratorException('Нет данных для генерации отчета')
        host = self.host if not host else host
        if not host:
            raise ReportGeneratorException('Нет адреса генератора отчёта')
        header = {'Content-Type': 'application/json'}
        if host[-1] == "/":
            host = host[:-1]
        url = f'{host}/emailstats'
        try:
            resp = requests.post(url, data=json.dumps(data), headers=header, verify=False)
        except requests.exceptions.ConnectionError as err:
            raise ReportGeneratorException('Ошибка запроса к управляющему серверу: {}'.format(err))
        if resp.status_code != 200:
            raise ReportGeneratorException('Ошибка генерации отчета: {}'.format(resp.text))
        if b64:
            return standard_b64encode(resp.text.encode('utf-8')).decode('utf-8')
        return resp.text
