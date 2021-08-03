import csv
import io
from datetime import datetime
from itertools import islice, groupby
from django.core.cache import cache
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from deal.models import Deal
from deal.serializer import FileUploadSerializer


class GetStatistic(generics.ListAPIView):
    """
    GET STATISTIC - получение информации о клиентах
    """
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Deal.objects.all()
    # serializer_class = PostSerializer

    def list(self, request, *args, **kwargs):
        csv_api_cache = cache.get('csv_api')
        response = {'Error': 'Cache is empty, please upload file first!'}
        if csv_api_cache:
            response = {'top_5': cache.get('csv_api')[:4]}
        try:
            top_5_gems = set()
            if (kwargs['username'] is not None) & (response['top_5'] is not None):
                for item in response['top_5']:
                    top_5_gems.update(item['gems'])
                    if item['username'] == kwargs['username']:
                        response.update({'customer_info': item})
                response.update({'common_gems': set.intersection(top_5_gems, response['customer_info']['gems'])})
        except KeyError:
            pass
        return Response(response)


class FileUpload(generics.CreateAPIView):
    """
    FILE UPLOAD - загрузка файла для чтения данных и записи в БД
    """
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = FileUploadSerializer

    def post(self, request, *args, **kwargs):
        # data prepare
        timezone.now()
        Deal.objects.all().delete()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reader = csv.reader(io.StringIO(serializer.validated_data['file'].read().decode()))
        source = [[item for item in line] for line in reader]
        next(reader, None)

        # database upload
        objs = (Deal(customer=row[0],
                     item=row[1],
                     total=row[2],
                     quantity=row[3],
                     date=datetime.strptime(row[4], '%Y-%m-%d %H:%M:%S.%f')) for row in reader)
        batch_size = 100
        while True:
            batch = list(islice(objs, batch_size))
            if not batch:
                break
            Deal.objects.bulk_create(batch, batch_size)

        # statistic treatment and cache
        list_of_customers = []
        for _ in source[1:]:
            list_of_customers.append({
                source[0][0]: _[0],
                source[0][1]: _[1],
                source[0][2]: _[2],
                source[0][3]: _[3],
                source[0][4]: _[4],
            })

        grouped_list_of_customers = []
        context_structure = {}
        list_of_customers = sorted(list_of_customers, key=lambda item: item['customer'])
        for key, group_items in groupby(list_of_customers, key=lambda item: item['customer']):
            context_structure = {
                'username': key,
                'gems': set(),
                'spent_money': 0,
                source[0][3]: 0,
            }
            for item in group_items:
                context_structure['gems'].add(item[source[0][1]])
                context_structure['spent_money'] += int(item[source[0][2]])
                context_structure[source[0][3]] += int(item[source[0][3]])
            grouped_list_of_customers.append(context_structure)
        grouped_list_of_customers = sorted(grouped_list_of_customers, key=lambda item: item['spent_money'], reverse=True)
        cache.set('csv_api', grouped_list_of_customers, 30)
        return Response(status=status.HTTP_204_NO_CONTENT)
