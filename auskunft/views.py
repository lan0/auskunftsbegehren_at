from django.contrib.formtools.wizard.views import CookieWizardView
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseBadRequest
import json
from django.db import connection

from auskunft.models import Auftraggeber, Application
from auskunft.informationrequest import InformationRequest

class InformationRequestWizard(CookieWizardView):
    template_name = "auskunft/wizard.html"

    def get_form(self, step=None, data=None, files=None):
        form = super(InformationRequestWizard, self).get_form(step, data, files)
        # determine the step if not given
        if step is None:
            step = self.steps.current

        # set queryset for applications
        if step == '2':
            auftragg = self.get_cleaned_data_for_step('0')['auftraggeber']
            apps = Application.objects.filter(auftraggeber=auftragg,state__contains="Registriert").distinct()
            form.fields['relevant_apps'].queryset = apps

        return form

    def done(self, form_list, **kwargs):
        # parse content of form list
        data = self.get_all_cleaned_data()
        print data
        # call create method
        ir = InformationRequest()
        ir.set_sender(data['name'],data['address'],data['email'])
        ir.set_auftraggeber(data['auftraggeber'])
        # TODO: Identitaetsnachweis abfragen
        # data['identity']
        if data['relevant_apps']:
            ir.set_relevant_apps(data['relevant_apps'])
        if data['additional_info']:
            ir.set_add_info(data['additional_info'])
        # return result page
        return ir.pdf_response()

class FileGenerator(View):

    # exempt from csrf protection
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(FileGenerator, self).dispatch(*args, **kwargs)

    def get(self, request):
        data = request.GET
        # call create method
        ir = InformationRequest()

        try:
            ir.set_sender(data['name'],data['address'],data['email'])
            ir.set_auftraggeber(Auftraggeber.objects.filter(id=data['auftraggeber'])[0])
            if 'relevant_apps[]' in data:
                apps = Application.objects.filter(pk__in=request.GET.getlist('relevant_apps[]'))
                ir.set_relevant_apps(apps)

            if 'additional_info' in data:
                ir.set_add_info(data['additional_info'])
            # return result page
            pdf = ir.pdf_response()
            # create response instance
            response = HttpResponse(content_type='application/pdf')
            filename = "dsg-2000-auskunft-" \
                + data['name'].replace(' ','-').lower() \
                + ".pdf"
            response['Content-Disposition'] = \
                'attachment; filename="' + filename + '"'
            response["Access-Control-Allow-Origin"] = "*"
            response.write(pdf)
            return response
        except KeyError:
            response = HttpResponseBadRequest('bad request')
            response["Access-Control-Allow-Origin"] = "*"
            return response

class AuftraggeberList(View):

    def get(self, request):
        data = json.dumps([{
            'id': o.pk,
            'name': o.name
            } for o in  Auftraggeber.objects.all()])
        response = HttpResponse(data, content_type='application/json')
        response["Access-Control-Allow-Origin"] = "*"
        return response

class ApplicationList(View):

    def get(self, request):
        if 'auftraggeber' in request.GET:
            apps = Application.objects.filter(auftraggeber=request.GET['auftraggeber'],state__contains="Registriert").distinct()
            data = json.dumps([{
                'number': o.number,
                'description': o.description,
                'id': o.pk
            } for o in  apps])
            response = HttpResponse(data, content_type='application/json')
        else:
            response = HttpResponseBadRequest('please provide "auftraggeber"')
        response["Access-Control-Allow-Origin"] = "*"
        return response
        