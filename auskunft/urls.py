from django.conf.urls import patterns, url

from auskunft.views import InformationRequestWizard, FileGenerator, AuftraggeberList, ApplicationList
from auskunft.forms import AuftraggeberForm, AddressForm, AdditionalInfoForm, ProofOfIdentityForm

ir_wizard_forms = [AuftraggeberForm,AddressForm,AdditionalInfoForm,ProofOfIdentityForm]

urlpatterns = patterns('',
    url(r'^auftraggeber$', AuftraggeberList.as_view()),
    url(r'^applications$', ApplicationList.as_view()),
    url(r'^generate$', FileGenerator.as_view()),
    url(r'^$', InformationRequestWizard.as_view(ir_wizard_forms)),
)
