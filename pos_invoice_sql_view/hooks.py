# -*- coding: utf-8 -*-
# Copyright 2018 Xavier Piernas <xavier.piernas@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
    sql_view_id = env['bi.sql.view'].search([
        ('technical_name', '=', 'todas')
    ])
    sql_view_id.button_validate_sql_expression()
    sql_view_id.bi_sql_view_field_ids.filtered(
        lambda x: x.name == 'x_producto'
    ).write({
        'ttype': 'many2one',
    })
    sql_view_id.bi_sql_view_field_ids.filtered(
        lambda x: x.name == 'x_producto'
    ).write({
        'many2one_model_id': env['ir.model'].search([
            ('model', '=', 'product.product')
        ]).id
    })
    sql_view_id.bi_sql_view_field_ids.filtered(
        lambda x: x.name == 'x_diario_venta'
    ).write({
        'ttype': 'many2one',
        'many2one_model_id': env['ir.model'].search([
            ('model', '=', 'account.journal')
        ]).id
    })
    sql_view_id.button_create_sql_view_and_model()
    sql_view_id.button_create_ui()
