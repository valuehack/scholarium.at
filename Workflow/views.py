from django.shortcuts import render, reverse
from django.contrib.admin.views.decorators import staff_member_required
# from .forms import Rechnung2PdfForm
from django.conf import settings
from . import utils
import inspect

skripte_dir = "/home/scholarium/Skripte/"
python_bin = skripte_dir+"venv/bin/python3.6"



@staff_member_required
def control_view(request):
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
        'Trello to PDF': {
            'name': utils.trelloToSQL.__name__,
            'sig': inspect.signature(utils.trelloToSQL), # Not used
            'doc': inspect.getdoc(utils.trelloToSQL),
        },
        'String drucken': {
            'name': utils.druck.__name__,
            'doc': inspect.getdoc(utils.druck),

        },
    }
    context = {
        'menu': menu,
        'methods': methods
    }

    return render(request, 'workflow/skripte-view.html', context)


def rechnung_view(request):
    if request.method == 'POST':
        pass #TODO: import Rechnung2Pdf
    
    # form = Rechnung2PdfForm

    context = {
        # 'form': form
    }
    return render(request, 'workflow/rechnung-view.html', context)
