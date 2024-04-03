from rest_framework import ISO_8601
from rest_framework import serializers
from django.conf import settings
from django.db import models


class CustomDateTimeField(serializers.DateTimeField):

    def to_representation(self, value):
        if not value:
            return None
        print('hey')
        output_format = getattr(self, 'format', settings.DATETIME_FORMAT)

        if output_format is None or isinstance(value, str):
            return value

        value = self.enforce_timezone(value)

        if output_format.lower() == ISO_8601:
            value = value.isoformat()
        value = value.strftime(output_format)
        value = value.replace(tzinfo=None)
        return 'ok'

class CustomDateTimeModelField(models.DateTimeField):
    def value_to_string(self, obj):
        val = self.value_from_object(obj)
        if val:
            val.replace(tzinfo=None)
            return 'hhh'
        return ''
