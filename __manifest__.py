# -*- coding: utf-8 -*-
{
    'name': 'Digital Bank Application Form',
    'version': '1.0',
    'summary': 'Digital Bank Application Form',
    'description': """
        This module allows users to submit a digital application for a bank account.
        It collects essential details such as PAN, Aadhaar, address, KYC documents, etc.
    """,
    'author': "Dinesh Kumar Reddy",
    'website': "https://yourportfolio.com",
    'category': 'Tools',
    'depends': ['base','web','mail','website'],
    'data': [
        'data/model_data.xml',
        'data/ir_sequence_data.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False
}
