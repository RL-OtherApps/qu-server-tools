# -*- coding: utf-8 -*-
# Copyright 2017 valentin vinagre <valentin.vinagre@qubiq.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

{
    'name': 'Iban Converter',
    'summary': 'Conversión de CCC to IBAN',
    'version': '10.0.1.0.0',
    'category': 'Custom',
    'author': 'QubiQ',
    'website': 'https://www.qubiq.es',
    'depends': [
          'sales_team',
          'account',
                ],
    'data': [
         'wizard/iban_converter_view.xml',
            ],
    'application': False,
    'auto_install': False,
    'installable': True,
}
