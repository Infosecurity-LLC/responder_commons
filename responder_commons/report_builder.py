import os
import logging
import json
import copy
from benedict import benedict
from responder_commons.exc import TemplateFileNotExist

logger = logging.getLogger('responder_commons')


class Builder:
    def __init__(self, translate_params):
        # self.translate_collection = benedict(translate_params)
        self.translate_collection = translate_params
        self.tpl_name = 'default'
        self.normal_thive_incident = {}

    @staticmethod
    def __load_tpl(tpl_name: str) -> dict:
        tpl_path = os.path.join(os.getcwd(), f'templates/{tpl_name}.json')
        if not os.path.exists(tpl_path):
            logger.error(f'Error getting setting. Check your settings file in {tpl_path}')
            raise TemplateFileNotExist(f"File {tpl_path} doesn't exist")
        with open(tpl_path, encoding='utf-8') as f:
            tpl = json.load(f)
        return tpl

    def __get_tpl(self, tpl: str = None) -> dict:
        if not tpl:
            logger.debug('Имя шаблона не задано, будет использован default')
            return self.__load_tpl("default")
        logger.debug(f'Будет использован шаблон {tpl}')
        return self.__load_tpl(tpl_name=tpl)

    def __get_recursively(self, search_obj: object, field: str, d_path: str = None) -> dict:
        """ Получаем список объектов, которые нужно заменить """
        paths_to_fields = {}
        if isinstance(search_obj, list):
            for i, value in enumerate(search_obj):
                new_d_path = None
                if d_path:
                    new_d_path = f'{d_path}[{i}]'
                results = self.__get_recursively(value, field, new_d_path)
                paths_to_fields = {**paths_to_fields, **results}

        if isinstance(search_obj, dict):
            for key, value in search_obj.items():
                if field in value:
                    if not d_path:
                        paths_to_fields.update({key: value})
                    if d_path:
                        paths_to_fields.update({f'{d_path}.{key}': value})

                elif isinstance(value, dict):
                    if d_path:
                        key = d_path + '.' + key
                    results = self.__get_recursively(value, field, key)
                    paths_to_fields = {**paths_to_fields, **results}

                elif isinstance(value, list):
                    if d_path:
                        key = d_path + '.' + key
                    results = self.__get_recursively(value, field, key)
                    paths_to_fields = {**paths_to_fields, **results}

        return paths_to_fields

    def get_translate_of_word(self, word: str = None, position: str = None):
        translate_list = self.translate_collection
        if not word:
            return word
        for write in translate_list:
            if isinstance(write, dict) and write['word'] == word:
                if position:
                    # position может быть обязательным для сравнения
                    if write['position'] == position:
                        return write['translate']
                else:
                    return write['translate']
            if isinstance(write, str) and write in self.translate_collection:
                return self.translate_collection[word]
        return word  # Если не найдено перевода - оставляем как есть

    @staticmethod
    def __sort_thive_list(thdict: dict):
        """ Сортируем словарь-список thive """
        thsort = sorted(thdict, key=lambda x: thdict[x]['order'])

        def cast(value_type, value):
            from datetime import datetime
            if not value:
                return None
            if value_type == 'date':
                return datetime.fromtimestamp(value / 1e3).isoformat()
            if value_type == 'string':
                return str(value)
            if value_type == 'numder':
                return int(value)
            return value

        def get_value(v: dict):
            v.pop('order')
            for value_type, value in v.items():
                return cast(value_type, value)

        fdict = {}
        for key in thsort:
            v = get_value(thdict[key])
            fdict.update({key: v})
        return fdict

    def __normalize_thive_dict(self, data):
        """ Нормализуем инцидент для респондера """
        normalize_incident = copy.deepcopy(data)
        normalize_incident.update({"customFields": self.__sort_thive_list(normalize_incident['customFields'])})
        return normalize_incident

    def __get_value_of_the_path(self, value_bank: benedict, value_path: str) -> object:
        """ Получение значения по пути через точку """
        _value_bank = copy.deepcopy(value_bank)

        def get_value(_data, _v):
            _data = _data.get(_v)
            return _data

        if "soc_inc>" in value_path:
            """ soc_inc>{что взять из инцидента} """
            v = value_path.replace("soc_inc>", '')
            data_value = get_value(_value_bank, v)
            return data_value

        if "soc_static_field>" in value_path:
            """ soc_static_field>{где}.{по какому word взять translate}"""
            v = value_path.replace("soc_static_field>", '')
            translate_path = v.split('.')
            if translate_path[0] == "items_translate":
                return self.get_translate_of_word(word=translate_path[1])
            if len(translate_path) == 1:
                return self.get_translate_of_word(word=v)

        if "soc_inc_rows>" in value_path:
            """Отрисовать список"""
            v = value_path.replace("soc_inc_rows>", '')
            rows_data = get_value(_value_bank, v)
            rows = []
            for k, v in self.normal_thive_incident['customFields'].items():
                rows.append({"left": self.get_translate_of_word(word=k, position='left'),
                             "right": self.get_translate_of_word(word=v, position='right')})
            return rows

        return value_path

    @staticmethod
    def __clean_format_tpl(data):
        """ Очистка щаполненного шаблона от пустых блоков"""

        def is_rows_null(section):
            """ тут проверяем, пустой блок или нет"""
            for item in section['blocks'][0]['rows']:
                if item['right'] is not None:
                    return False
            return True

        from copy import deepcopy
        final_format_tpl = deepcopy(data)
        for i in data['categories'][0]['sections']:
            if is_rows_null(i):
                final_format_tpl['categories'][0]['sections'].remove(i)

        return final_format_tpl

    def build(self, data: dict, tpl: dict) -> dict:
        if not data:
            logger.warning('No data')
            return {}

        self.normal_thive_incident = self.__normalize_thive_dict(data)
        format_data = benedict(self.normal_thive_incident)
        format_tpl = benedict(copy.deepcopy(tpl))

        replacement_list = self.__get_recursively(benedict(copy.deepcopy(tpl)), 'soc_inc')
        for repl_key, repl_value in replacement_list.items():
            format_tpl.set(repl_key, self.__get_value_of_the_path(format_data, repl_value))

        replacement_list = self.__get_recursively(benedict(copy.deepcopy(tpl)), 'soc_static_field')
        for repl_key, repl_value in replacement_list.items():
            format_tpl.set(repl_key, self.__get_value_of_the_path(self.translate_collection, repl_value))
        final_format_tpl = self.__clean_format_tpl(format_tpl)
        return final_format_tpl

    def translate_other_items(self, data: dict):
        """ Перевод дополнительных полей """
        if not data:
            return None
        translate_result = {}
        for k, v in data.items():
            translate_result[k] = self.get_translate_of_word(word=v, position=k)
        return translate_result
