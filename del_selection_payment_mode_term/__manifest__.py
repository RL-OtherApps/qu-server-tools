# Copyright 2018 Xavier Piernas <xavier.piernas@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Del Selection Payment Mode Term",
    "summary": "Avoids creating on payment mode and payment term",
    "version": "11.0.1.0.0",
    "category": "Custom",
    "website": "https://www.qubiq.es",
    "author": "QubiQ, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "account",
        "account_payment_partner",
        "account_payment_sale"
    ],
    "data": [
        "views/account_invoice.xml",
        "views/res_partner.xml",
        "views/sale_order.xml"
    ],
}
