from responder_commons.mailreporter_client import MailReporterClient
from responder_commons.report_builder import Builder
from responder_commons.translator import Translator
from responder_commons.exc import *
import logging

logger = logging.getLogger('responder_commons')


class IncidentReportMaker:
    def __init__(self, settings: dict):
        self.settings = settings
        self.translator = None
        self.mail_reporter = None
        self.__init()

    def __init(self):
        if 'translator' not in self.settings:
            raise TranslatorSettingsNotExist("Not found 'translator' section in settings")
        self.translator = Translator(**self.settings['translator'])
        if 'mail_reporter' not in self.settings:
            raise MailReporterSettingsNotExist("Not found 'mail_reporter' section in settings")
        self.mail_reporter = MailReporterClient(self.settings['mail_reporter']['host'])

    def make_report(self, language_name: str,
                    is_mail_alert: bool = False,
                    incident: dict = None,
                    template_name: str = False,
                    template: dict = None,
                    b64: bool = False,
                    other_translation: dict = None):
        if not incident and not other_translation:
            raise InvalidInputData(f'Incorrect input data')

        if incident and b64:
            logger.info(f"Starting making b64_report for incident {incident.get('id')}")
        if incident and not b64:
            logger.info(f"Starting making report for incident {incident.get('id')}")

        translation_items_result = None
        render = None

        translation = self.translator.translate(lang_id=language_name, tpl_name=template_name)
        # import json
        # print(json.dumps(translation['template']))
        builder = Builder(translation['translate'])
        if incident:
            if template:
                report = builder.build(data=incident, tpl=template)
            else:
                report = builder.build(data=incident, tpl=translation['template'])
            if is_mail_alert:
                report["url"] = "cid:"
            render = self.mail_reporter.get_html_report(report, b64=b64)
        if other_translation:
            translation_items_result = builder.translate_other_items(other_translation)
        return dict(report=render, other_translation=translation_items_result)
