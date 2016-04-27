# -*- coding: utf-8 -*-
import json
import os
import codecs

from manage_commands import BaseManageCommand, get_single
from fw.db.sql_base import db as sqldb
from services.notarius.data_model.models import NotariusObject, ScheduleTypeEnum


class FilenameSimpleValidator(object):
    def validate(self, val):
        if not os.path.exists(val):
            return False
        return True

    def get_value(self, value):
        return value


class AddNotariusCommand(BaseManageCommand):
    NAME = "add_notarius"

    def run(self):
        self.logger.info(u"Добавление нотариуса")
        self.logger.info(u'=' * 50)

        filename_str = get_single(u'File name: ', validator=FilenameSimpleValidator(), error_hint=u"File not found")

        with codecs.open(filename_str, encoding='utf8') as f:
            content = f.read()
            try:
                data = json.loads(content)
                notarius = NotariusObject(
                    id = data['id'],
                    surname = data.get('surname', u''),
                    name = data.get('name', u''),
                    patronymic = data.get('patronymic', None),

                    schedule = data['schedule'],
                    schedule_caption = data['schedule_caption'],
                    title = data['title'],
                    address = data['address'],
                    region = data['region'],
                    metro_station = data.get('metro_station', u'')
                )
                sqldb.session.add(notarius)
                sqldb.session.commit()
            except Exception, ex:
                self.logger.exception(u"Не удалось прочитать файл. Проверьте формат.")


class ListNotariusCommand(BaseManageCommand):
    NAME = "list_notarius"

    def run(self):
        self.logger.info(u"Нотариусы в системе:")
        self.logger.info(u'=' * 50)

        DAYS = {
            1: u"понедельник",
            2: u"вторник",
            3: u"среда",
            4: u"четверг",
            5: u"пятница",
            6: u"суббота",
            7: u"воскресенье"
        }

        for notarius in NotariusObject.query.filter():
            self.logger.info(u"Наименование: %s" % notarius.title)
            if notarius.patronymic:
                self.logger.info(u"ФИО: %s %s %s" % (notarius.surname, notarius.name, notarius.patronymic))
            else:
                self.logger.info(u"ФИО: %s %s" % (notarius.surname, notarius.name))

            self.logger.info(u"Адрес: %s" % json.dumps(notarius.address))
            if notarius.schedule['type'] == ScheduleTypeEnum.ST_NORMAL:
                weekends = set(notarius.schedule['weekends'])
                work_days = {1, 2, 3, 4, 5, 6, 7} - weekends

                schedule = u"%s - рабочий день, %s - выходной" % (
                    u",".join([DAYS[i] for i in work_days]), u",".join([DAYS[i] for i in weekends]))
            else:
                schedule = u"%d рабочих, затем %d выходных" % (
                    notarius.schedule['working_days_count'], notarius.schedule['weekends_count'])
            self.logger.info(u"Расписание: %s" % schedule)

            time = u"С %s до %s" % (notarius.schedule['start_time'], notarius.schedule['end_time'])
            if 'lunch_start' in notarius.schedule and 'lunch_end' in notarius.schedule:
                time += u" с перерывом с %s до %s" % (notarius.schedule['lunch_start'], notarius.schedule['lunch_end'])
            else:
                time += u" без обеда"
            self.logger.info(u"Время работы: %s" % time)
            self.logger.info(u"id: %s" % notarius.id)
