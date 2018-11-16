# -*- coding: utf-8 -*-
# Copyright 2018 Xavier Piernas <xavier.piernas@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "POS Invoice SQL View",
    "summary": "Creates an SQL view from invoices and POS data",
    "version": "10.0.1.0.0",
    "category": "SQL View",
    "website": "https://www.qubiq.es",
    "author": "QubiQ",
    "license": "AGPL-3",
    "post_init_hook": "post_init_hook",
    "depends": [
        "bi_sql_editor"
    ],
    "data": [
        "data/sql_view_todas.xml"
    ],
    "application": False,
    "installable": True,
}
