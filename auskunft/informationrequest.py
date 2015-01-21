#! /usr/bin/env python
import datetime
from io import BytesIO

from django.utils.translation import ugettext as _

from dinbrief.document import Document
from dinbrief.template import BriefTemplate
from dinbrief.styles import styles
from reportlab.platypus import Spacer, Paragraph, ListFlowable, ListItem
from reportlab.platypus.tables import Table, TableStyle
from reportlab.lib.units import cm,mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle

from auskunft.models import Auftraggeber, Application

class InformationRequest():
    def __init__(self):
        self.sender_name = ""
        self.sender_address = [ "" ]
        self.recipient_address = [ "" ]
        self.add_info = None
        self.table_apps = None

    def set_sender(self,name,address,email):
        self.sender_name = name
        self.sender_address = [ name ] + address.splitlines()
        if email:
            self.sender_address += [ "E-Mail: " + email ]

    def set_auftraggeber(self,auftraggeber):
        self.recipient_address = [ auftraggeber.name ] + auftraggeber.address.splitlines()
        if auftraggeber.email:
            self.recipient_address += [ "E-Mail: " + auftraggeber.email ]

    def set_add_info(self,add_info):
        self.add_info = add_info

    def set_relevant_apps(self,apps):
        table_style = TableStyle([
                ('VALIGN',(0,0),(0,-1),'TOP')
            ])

        list_apps = [
            [Paragraph(x.number,styles['Message']),
            Paragraph(x.description,styles['Message'])] for x in apps]

        self.table_apps = Table(list_apps,colWidths=[3*cm,14*cm])
        self.table_apps.setStyle(table_style)

    def pdf_response(self):
        # create document structure
        document = Document(
            sender = self.sender_address,
            recipient = self.recipient_address,
            date = datetime.datetime.now().strftime("%d.%m.%Y"),
            content = self._content()
        )

        # build letter template
        buff = BytesIO()
        template = BriefTemplate(buff, document)
        template.build(document.content)
        pdf_response = buff.getvalue()
        buff.close()
        
        return pdf_response

    def _content(self):
        # TODO: move styles somewhere else
        # style for additional information box
        ibs = ParagraphStyle('inputBoxStyle',styles['Message'])
        ibs.fontName = 'Courier'
        ibs.leftIndent = cm
        ibs.spaceBefore = 0.2*cm
        ibs.spaceAfter = 0.5*cm
        # font style for letter subject
        styles['Subject'].fontName = 'Helvetica-Bold'

        content = [
            Paragraph(_("auskunft_subject"), styles['Subject']),
            Paragraph(_("auskunft_greeting"), styles['Greeting']),
            Spacer(0,0.5*cm),
            Paragraph(_("auskunft_question_text"), styles['Message']),
            ListFlowable([
                ListItem(Paragraph(_("auskunft_question_1"),styles['Message'])),
                ListItem(Paragraph(_("auskunft_question_2"),styles['Message'])),
                ListItem(Paragraph(_("auskunft_question_3"),styles['Message'])),
                ListItem(Paragraph(_("auskunft_question_4"),styles['Message'])),
                ],
                bulletType='bullet',
                start='square'
            ),
            Paragraph(_("auskunft_reference"), styles['Message']),
            Paragraph(_("auskunft_par_10"), styles['Message']),
            Paragraph(_("auskunft_par_4"), styles['Message']),
            Paragraph(_("auskunft_par_12"), styles['Message']),

            Paragraph(_("auskunft_standard_application"), styles['Message'])
        ]

        # Registered Applications
        if self.table_apps:
            content += [
                Paragraph(_("auskunft_registered_application_pre"),styles['Message']),
                self.table_apps,
                Paragraph(_("auskunft_registered_application_post"),styles['Message'])
            ]

        # Additional Information
        if self.add_info:
            content += [
                Paragraph(_("auskunft_additional_info_text"), styles['Message']),
                Paragraph(self.add_info,ibs)
            ]

        content += [
            Paragraph(_("auskunft_method_identity"),styles['Message']),
            Paragraph(_("auskunft_expected_response"),styles['Message']),

            Spacer(0,0.5*cm),
            Paragraph(_("auskunft_signature"),styles['Signature']),
            Spacer(0,1.5*cm),
            Paragraph(self.sender_name,styles['Signature'])
        ]

        return content
