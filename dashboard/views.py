from __future__ import absolute_import
import datetime
import operator
from django import http
from django.conf import settings
from django.shortcuts import render
from django.utils import simplejson
from django.forms.models import model_to_dict
from .models import Metric

def index(request):
    metrics = []
    for MC in Metric.__subclasses__():
        metrics.extend(MC.objects.filter(show_on_dashboard=True))
    metrics = sorted(metrics, key=operator.attrgetter('name'))

    data = []
    for metric in metrics:
        latest = metric.data.latest()
        data.append({'metric': metric, 'latest': latest})
    return render(request, 'dashboard/index.html', {'data': data})

def metric_detail(request, metric_slug):
    metric = _find_metric(metric_slug)
    return render(request, 'dashboard/detail.html', {
        'metric': metric,
        'latest': metric.data.latest(),
    })

def metric_json(request, metric_slug):
    metric = _find_metric(metric_slug)

    try:
        daysback = int(request.GET['days'])
    except (TypeError, KeyError):
        daysback = 30
    d = datetime.datetime.now() - datetime.timedelta(days=daysback)

    doc = model_to_dict(metric)
    doc['data'] = metric.gather_data(since=d)

    return http.HttpResponse(
        simplejson.dumps(doc, indent = 2 if settings.DEBUG else None),
        content_type = "application/json",
    )

def _find_metric(slug):
    for MC in Metric.__subclasses__():
        try:
            return MC.objects.get(slug=slug)
        except MC.DoesNotExist:
            continue
    raise http.Http404()
