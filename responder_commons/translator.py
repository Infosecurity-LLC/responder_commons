from sqlalchemy import Column, Integer, String, Date, Boolean, JSON, PrimaryKeyConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, exc, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
import sqlalchemy
import logging

logging.basicConfig(level='DEBUG')
logger = logging.getLogger('db_manager')
Base = declarative_base()


class BDError(Exception):
    pass


class Translate(Base):
    __tablename__ = 'translate'
    lang_id = Column(String, primary_key=True)
    position = Column(String, primary_key=True)
    word = Column(String, primary_key=True)
    translate = Column(String)
    PrimaryKeyConstraint('lang_id', 'position', 'word', name='translate_pk')


class Templates(Base):
    __tablename__ = 'templates'
    template_name = Column(String, primary_key=True)
    template = Column(JSON)


class Translator:
    def __init__(self, db_engine, db_user, db_pass, db_host, db_port, db_name):
        """
        Подключаемся к базе
        :param db_engine:
        :param db_user:
        :param db_pass:
        :param db_host:
        :param db_port:
        :param db_name:
        """
        sql_alchemy_database_uri = f'{db_engine}{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}'
        self.__engine = create_engine(sql_alchemy_database_uri, echo=False, pool_recycle=7200, encoding='utf-8')
        # self.create_tables()
        db_session = sessionmaker(bind=self.__engine)
        self.session = db_session()

    def create_tables(self):
        Base.metadata.bind = self.__engine
        try:
            logger.info('Create tables in DB [ START ]')
            Base.metadata.create_all(self.__engine)
        except sqlalchemy.exc.OperationalError as err:
            raise BDError(f'Ошибка доступа к базе. Ошибка: {err}')
        else:
            logger.info('Create tables in DB [ OK ]')

    def add_template(self, tpl_name: str, data: dict):
        """ Добавить новый шаблон в базу """
        import json
        tpl = json.dumps(data)
        tpl = Templates(template_name=tpl_name, template=tpl)
        self.session.add(tpl)
        try:
            self.session.commit()
        except sqlalchemy.exc.IntegrityError:
            logger.warning(f'Template {tpl_name} already exist')
            self.session.rollback()
            return False
        return True

    def get_template(self, tpl_name):
        """ Получить шаблон по имени """
        query = self.session.query(Templates.template).filter(Templates.template_name == tpl_name)
        try:
            template = query.one()
        except sqlalchemy.orm.exc.NoResultFound:
            return False
        except Exception as err:
            logger.exception(err)
            return False
        return template[0]

    def add_translation(self, lang_id=None, position=None, word=None, translate=None):
        """ Добавить новый перевод """
        new_data = Translate(lang_id=lang_id, position=position, word=word, translate=translate)
        self.session.add(new_data)
        try:
            self.session.commit()
        except sqlalchemy.exc.IntegrityError:
            logger.warning(f'Translation write already exist')
            self.session.rollback()
            return False
        return True

    def get_translation(self, lang_id: str):
        """ Получаем переводы"""
        lang_id = str(lang_id).lower()
        items_translate = []
        try:
            data = self.session.execute(
                select([Translate]).where(
                    Translate.lang_id == lang_id)
            ).fetchall()
            for result in data:
                items_translate.append(dict(
                    position=result.position,
                    word=result.word,
                    translate=result.translate
                ))
        except sqlalchemy.orm.exc.NoResultFound:
            logger.error(f'Не удалось найти перевод parameters: [lang_id: {lang_id}]')
        except Exception as err:
            raise BDError(f'Ошибка работы с базой! [ get_events ] Error: {err}')
        return items_translate

    def translate(self, lang_id: str, tpl_name: str = None):
        if not tpl_name:
            tpl_name = 'default'
        template = self.get_template(tpl_name)
        if not template:
            logger.error('Not found default template in DB!')
            return False
        translate = self.get_translation(lang_id)
        return dict(template=template, translate=translate)
