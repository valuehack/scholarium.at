import inspect
import csv
from datetime import datetime, date

from django.shortcuts import render, reverse
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse

# from .forms import Rechnung2PdfForm
from Grundgeruest.models import ScholariumProfile
from . import utils

skripte_dir = "/home/scholarium/Skripte/"
python_bin = skripte_dir+"venv/bin/python3.6"


@staff_member_required
def control_view(request):

    menu = {
        'Skripte': reverse('Workflow:skripte'),
        'Rechnungen': reverse('Workflow:rechnungen'),
        'CSV (E-Mail: Unterstützer & Interessenten)':
            reverse('Workflow:csv', args={'alle'}),
        'CSV (E-Mail: nur Unterstützer)':
            reverse('Workflow:csv', args={'unterstuetzer'}),
        'CSV (E-Mail: nur Interessenten)':
            reverse('Workflow:csv', args={'interessenten'}),
        'CSV (E-Mail: nur Abgelaufende)':
            reverse('Workflow:csv', args={'abgelaufen'}),
        
    }
    context = {
        'menu': menu,
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
def csv_export(request, value):
    """
    Generates csv-files with email addresses for manual import to Sendgrid
    (to send the newsletter); *value* has 3 cases according to which button is
    clicked (see control_view): alle, unterstuetzer and interessenten.
    """
    formatted_date = datetime.now().strftime('%d-%m-%Y_%H-%M')
    csv_filename = 'email_{0}_{1}.csv'.format(value, formatted_date)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = \
    'attachment; filename="{}"'.format(csv_filename)

    writer = csv.writer(response)
    
    if value == 'alle':
        writer.writerow(['Email'])  # header-row
        for one in ScholariumProfile.objects.all():
            writer.writerow(['{}'.format(one.user.email)])
    elif value == 'unterstuetzer':
        writer.writerow(['Email'])  # header-row
        for one in ScholariumProfile.objects.filter(stufe__gte=1):
            writer.writerow(['{}'.format(one.user.email)])
    elif value == 'interessenten':
        writer.writerow(['Email'])  # header-row
        for one in ScholariumProfile.objects.filter(stufe=0):
            writer.writerow(['{}'.format(one.user.email)])
    elif value == 'abgelaufen':
        writer.writerow(['Vorname','Nachname','Email','Ablaufdatum'])  # header-row
        for one in ScholariumProfile.objects.filter(datum_ablauf__lt=date.today()):
            writer.writerow([one.user.first_name, one.user.last_name,one.user.email,one.datum_ablauf])

    return response
