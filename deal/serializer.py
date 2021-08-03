from rest_framework import serializers


class FileUploadSerializer(serializers.Serializer):
    """
    Сериализация для загрузки файла
    """
    file = serializers.FileField()

    class Meta:
        fields = ['file', ]
