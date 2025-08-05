from rest_framework import serializers

class AddCustomColumnSerializer(serializers.Serializer):
    title = serializers.CharField()
    data_type = serializers.ChoiceField(choices=[
        ('decimal', 'Decimal'),
        ('integer', 'Integer'),
        ('string', 'Text'),
        ('date', 'Date'),
        ('url', 'URL'),
    ])