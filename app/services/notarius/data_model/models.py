# -*- coding: utf-8 -*-
from bson import ObjectId

from datetime import datetime, timedelta
from common_utils import day_short_name, word_from_num

from sqlalchemy import Column, Unicode, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from fw.db.sql_base import db as sqldb
from fw.documents.address_enums import RFRegionsEnum
from fw.documents.fields.general_doc_fields import DocAddressField
from fw.documents.fields.simple_doc_fields import DocDateTimeField

day_end = lambda x: x + timedelta(days=1) - timedelta(seconds=1)

ONE_DAY = timedelta(days=1)


class ScheduleTypeEnum(object):
    ST_NORMAL = 'normal'
    ST_CYCLIC = 'cyclic'

    _NAMES = {
        ST_NORMAL: u"обычная рабочая неделя",
        ST_CYCLIC: u"два через два, например"
    }

class NotariusObject(sqldb.Model):
    __tablename__ = "notarius"

    id = Column(String, primary_key=True)

    surname = Column(Unicode, nullable=False)
    name = Column(Unicode, nullable=False)
    patronymic = Column(Unicode, nullable=True)

    schedule = Column(JSONB, nullable=False)
    schedule_caption = Column(Unicode, nullable=True)
    title = Column(Unicode, nullable=True)
    address = Column(JSONB)
    region = Column(Unicode, nullable=False)
    metro_station = Column(Unicode, nullable=True)

    @staticmethod
    def make_slots(notarius, this_day, earliest_time=None):
        slots = []
        notarius_schedule = notarius.schedule
        bookings = NotariusBookingObject.query.filter(
            NotariusBookingObject.dt.__ge__(this_day),
            NotariusBookingObject.dt.__le__(day_end(this_day)),
            NotariusBookingObject.notarius==notarius,
            NotariusBookingObject._discarded==False)
        busy_slots = [i.dt for i in bookings]

        t = datetime.strptime("2014-01-01T" + notarius_schedule['start_time'] + ":00", DocDateTimeField.FORMAT)
        t = datetime(this_day.year, this_day.month, this_day.day, t.hour, t.minute, 0)
        end_t = datetime.strptime("2014-01-01T" + notarius_schedule['end_time'] + ":00", DocDateTimeField.FORMAT)
        end_t = datetime(this_day.year, this_day.month, this_day.day, end_t.hour, end_t.minute, 0)

        lunch_start = datetime.strptime("2014-01-01T" + notarius_schedule['lunch_start'] + ":00",
                                        DocDateTimeField.FORMAT) if 'lunch_start' in notarius_schedule else None
        lunch_start = datetime(this_day.year, this_day.month, this_day.day, lunch_start.hour, lunch_start.minute,
                               0) if lunch_start else None
        lunch_end = datetime.strptime("2014-01-01T" + notarius_schedule['lunch_end'] + ":00",
                                      DocDateTimeField.FORMAT) if 'lunch_end' in notarius_schedule else None
        lunch_end = datetime(this_day.year, this_day.month, this_day.day, lunch_end.hour, lunch_end.minute,
                             0) if lunch_end else None
        while t < end_t:
            if earliest_time and t < earliest_time:
                t += timedelta(seconds=1800)
                continue
            middle = t + timedelta(seconds=900)
            if lunch_start and lunch_end:
                if lunch_start <= middle <= lunch_end:
                    t += timedelta(seconds=1800)
                    continue

            found = False
            for busy in busy_slots:
                busy_start = busy
                busy_end = busy + timedelta(seconds=1800)
                if busy_start <= middle <= busy_end:
                    found = True
                    break
            if found:
                t += timedelta(seconds=1800)
                continue

            slots.append({
                'slot_start': t.strftime("%H:%M"),
                'slot_end': (t + timedelta(seconds=1800)).strftime("%H:%M")
            })
            t += timedelta(seconds=1800)
        return slots

    @staticmethod
    def is_weekend(notarius, target_day):
        if notarius.schedule['type'] == ScheduleTypeEnum.ST_NORMAL:
            cur_day = target_day
            week_day = cur_day.date().isoweekday()
            return week_day in notarius.schedule['weekends']
        else:
            working_days_count = notarius.schedule['working_days_count']
            weekends_count = notarius.schedule['weekends_count']
            cycle_len = working_days_count + weekends_count
            start_day = datetime.strptime(notarius.schedule['start_working_day'], "%Y-%m-%d")
            days_to_day_to = (target_day - start_day).days
            if days_to_day_to < 0:
                return True
            cur_day = start_day + timedelta(days=int(days_to_day_to / cycle_len) * cycle_len)
            is_working_day = True
            cycle_i = 0
            while cur_day <= target_day:
                cycle_i += 1
                if cycle_i > working_days_count + weekends_count:
                    is_working_day = True
                    cycle_i = 1
                elif cycle_i > working_days_count:
                    is_working_day = False
                if cur_day == target_day:
                    return is_working_day
                cur_day += ONE_DAY

    @staticmethod
    def get_notarius_schedule(notarius, day_from=None, day_to=None):
        def make_day_info(day, earliest_time=None):

            return {
                'nearest_time': day.strftime(DocDateTimeField.FORMAT),
                'slots': NotariusObject.make_slots(notarius, day, earliest_time)
            }

        days = []
        if day_to < day_from:
            raise Exception(u"Invalid date range")

        notarius_schedule = notarius.schedule
        if notarius_schedule['type'] == ScheduleTypeEnum.ST_NORMAL:
            cur_day = day_from
            while cur_day < day_to:
                week_day = cur_day.date().isoweekday()
                if week_day not in notarius_schedule['weekends']:
                    days.append(make_day_info(cur_day, day_from))
                cur_day += ONE_DAY
        else:
            working_days_count = notarius_schedule['working_days_count']
            weekends_count = notarius_schedule['weekends_count']
            cycle_len = working_days_count + weekends_count
            start_day = datetime.strptime(notarius_schedule['start_working_day'], "%Y-%m-%d")
            days_to_day_to = (day_from - start_day).days
            if days_to_day_to < 0:
                return days
            cur_day = start_day + timedelta(days=int(days_to_day_to / cycle_len) * cycle_len)
            is_working_day = True
            cycle_i = 0
            while cur_day < day_to:
                cycle_i += 1
                if cycle_i > working_days_count + weekends_count:
                    is_working_day = True
                    cycle_i = 1
                elif cycle_i > working_days_count:
                    is_working_day = False
                if cur_day >= day_from and is_working_day:
                    days.append(make_day_info(cur_day, day_from))
                cur_day += ONE_DAY

        return days

    def make_working_hours(self):
        if self.schedule_caption:
            return self.schedule_caption

        if self.schedule['type'] == ScheduleTypeEnum.ST_NORMAL:
            lunch = u" с перерывом на обед с %s до %s" % (self.schedule['lunch_start'], self.schedule['lunch_end']) if (
                self.schedule.get('lunch_start', None) and self.schedule.get('lunch_end', None)) else u""
            weekends = u", %s - выходной" % ", ".join(day_short_name(day) for day in
                                                      self.schedule.get('weekends',
                                                          [])) if self.schedule.get('weekends',
                                                                                               None) else u""
            return u"с %s до %s%s%s" % (self.schedule['start_time'], self.schedule['end_time'], lunch, weekends)
        return u"%d %s через %d %s" % (
            self.schedule['working_days_count'], word_from_num(u"дня", self.schedule['working_days_count']),
            self.schedule['weekends_count'], word_from_num(u"дня", self.schedule['weekends_count']))

    def get_api_structure(self):
        result = {
            'id': self.id,
            'surname': self.surname,
            'name': self.name,
            'patronymic': self.patronymic,

            'schedule_caption': self.schedule_caption,
            'title': self.title,
            'address': self.address,
            'region': {
                'code': self.region,
                'title': RFRegionsEnum.get_name(self.region)
            },
            'metro_station': self.metro_station
        }
        del_null_items = lambda x: dict([(k, v) for k, v in x.items() if v is not None])
        result = del_null_items(result)
        schedule = NotariusObject.make_slots(self, datetime.utcnow())
        result['working_hours'] = self.make_working_hours()
        caption = result.get('metro_station', u"")
        if caption:
            caption = u"м. %s (" % caption
        else:
            caption = u"("
        title = u"%s, " % self.title if self.title else u""
        address_field = DocAddressField()
        address_field.parse_raw_value(self.address, api_data=False)
        caption += result['working_hours'] + u") — %s" % title + address_field.as_string_friendly()
        # м. Пл.Александра Невского (с 9 до 18 по будним дням) — Новгородская ул. д.6
        result['caption'] = caption
        result['schedule'] = schedule
        address_str = address_field.as_string_friendly()
        if self.title:
            address_str += u" " + self.title
        return result


class NotariusBookingObject(sqldb.Model):
    __tablename__ = "notarius_booking"

    id = Column(String, primary_key=True, default=lambda: str(ObjectId()))
    batch_id = Column(String, ForeignKey('doc_batch.id'), nullable=True)
    batch = relationship("DocumentBatchDbObject", uselist=False)

    owner_id = Column(Integer, ForeignKey('authuser.id'), index=True)
    owner = relationship("AuthUser", uselist=False)

    notarius_id = Column(String, ForeignKey('notarius.id'), index=True)
    notarius = relationship("NotariusObject", uselist=False)

    dt = Column(DateTime, nullable=False)
    address = Column(Unicode, nullable=False)
    _discarded = Column(Boolean, default=False)

    def get_api_structure(self):
        result = {
            'id': self.id,
            'batch_id': self.batch_id,
            'notarius': self.notarius.get_api_structure(),
            'dt': self.dt.strftime(DocDateTimeField.FORMAT),
            'address': self.address
        }
        return result
