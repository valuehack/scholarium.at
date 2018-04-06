import inspect
import csv
from datetime import datetime, date

from django.shortcuts import render, reverse
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse

from .forms import CSVForm
from Grundgeruest.models import ScholariumProfile
from . import utils

skripte_dir = "/home/scholarium/Skripte/"
python_bin = skripte_dir + "venv/bin/python3.6"


@staff_member_required
def control_view(request):
    if request.method == 'POST':
        return csv_export(request)

    menu = {
        'Rechnungen': reverse('Workflow:rechnungen'),
    }

    csv_form = CSVForm()
    context = {
        'menu': menu,
        'csv_form': csv_form,
    }

    return render(request, 'workflow/control-frame.html', context)


@staff_member_required
def skripte_view(request):
    if request.method == 'POST':
        method = getattr(utils, request.POST['function'])
        args = method.__defaults__
        if args:
            method(*args)
        else:
            method()

    # form = Rechnung2PdfForm
    # for f in inspect.getmembers(utils, inspect.isfunction):
    #     print(f)
    menu = {
        'Skripte': reverse('Workflow:skripte'),
        'Rechnungen': reverse('Workflow:rechnungen')
    }
    methods = {
        'Trello zu PDF': {
            'name': utils.trelloToSQL.__name__,
            'sig': inspect.signature(utils.trelloToSQL),  # Not used
            'doc': inspect.getdoc(utils.trelloToSQL),
        },
        'String drucken': {
            'name': utils.druck.__name__,
            'doc': inspect.getdoc(utils.druck),

        },
        'Veröffentlichen': {
            'name': utils.publish.__name__,
            'doc': inspect.getdoc(utils.publish)
        }
    }
    context = {
        'menu': menu,
        'methods': methods
    }

    return render(request, 'workflow/skripte-view.html', context)


@staff_member_required
def rechnung_view(request):
    if request.method == 'POST':
        pass  # TODO: import Rechnung2Pdf
    menu = {
        'Skripte': reverse('Workflow:skripte'),
        'Rechnungen': reverse('Workflow:rechnungen'),
    }
    # form = Rechnung2PdfForm

    context = {
        # 'form': form
        'menu': menu
    }
    return render(request, 'workflow/rechnung-view.html', context)


@staff_member_required
def csv_export(request):
    """
    Generates csv-files with selected filters. (i.e. for manual import to Sendgrid)
    """
    values = request.POST.getlist('values')
    stufen = request.POST.getlist('stufen')
    states = request.POST.getlist('states')

    formatted_date = datetime.now().strftime('%d-%m-%Y_%H-%M')
    csv_filename = '{0}_{1}_{2}_{3}.csv'.format('+'.join(stufen),
                                                formatted_date,
                                                '+'.join(values),
                                                '+'.join(states))

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = \
        'attachment; filename="{}"'.format(csv_filename)

    writer = csv.writer(response)

    profiles = ScholariumProfile.objects.all()  # Not using Queryset filtering because of model functions.

    profile_list = []
    for profile in profiles:
        # Filter for seleceted tier
        if profile.get_stufe():
            print(profile.get_stufe().pk)
        stufe = profile.get_stufe().pk if profile.get_stufe() else 0
        if stufe not in [int(x) for x in stufen]:
            continue

        # Filter for aktiv/abgelaufen if existent
        ablauf = profile.get_ablauf()
        if ablauf:
            if 'abgelaufen' not in states and ablauf < date.today():
                continue
            if 'aktiv' not in states and ablauf >= date.today():
                continue

        profile_list.append(profile)

    # Split Nutzer values from Scholariumprofil values, because getattr() can't handle nested values
    user_values = []
    profile_values = []

    for i in values:
        if i in ['first_name', 'last_name', 'email']:
            user_values.append(i)
        else:
            profile_values.append(i)

    writer.writerow(user_values + profile_values)  # header-row
    for profile in profile_list:
        writer.writerow([getattr(profile.user, value) for value in user_values] + [getattr(profile, value) for value in profile_values])

    return response
