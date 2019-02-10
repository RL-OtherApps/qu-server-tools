# Copyright 2019 Marçal Isern - QubiQ 2010 <marsal.isern@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Quick User Set Password Wizard',
    'summary': 'This module adds a wizard to create user passwords easily',
    'version': '11.0.1.0.0',
    'category': 'Others',

    'author': 'QubiQ, Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'installable': True,
    'depends': [
          'base',
                ],

    'data': [
        'wizards/user_password_easy_creation.xml',
    ],
}
