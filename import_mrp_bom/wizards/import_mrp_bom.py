# Copyright 2018 Xavier Jiménez <xavier.jimenez@qubiq.es>
# Copyright 2018 Sergi Oliva <sergi.oliva@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, exceptions, _
from datetime import datetime

import base64
import csv
from io import StringIO

import logging
_logger = logging.getLogger(__name__)


class ImportMrpBom(models.TransientModel):
    _name = 'import.mrp.bom'

    data = fields.Binary(string='File', required=True)
    name = fields.Char(string='Filename')
    delimeter = fields.Char(
        string='Delimiter',
        default=',',
        help='Default delimiter ","',
    )

    '''
        Function to assign not direct mapping data.

        :param values: Dict with the values to import.

        :return Dict with the correct mapping.
    '''
    def _assign_product_data(self, values):
        # Search for the manufactured product
        if values['product_tmpl']:
            product_tmpl = self.env['product.template'].search([(
                'default_code', '=', values['product_tmpl'])])
            if product_tmpl:
                values.update({
                    'product_tmpl': product_tmpl.id,
                })

        # Search for the component product
        if values['product_comp']:
            product_comp = self.env['product.product'].search([(
                'default_code', '=', values['product_comp'])])
            if product_comp:
                values.update({
                    'product_comp': product_comp.id,
                })

        return values

    '''
        Function to create the mrp nom.

        :param values: Dict with the values to import.
    '''
    def _create_new_mrp_bom(self, values):
        mrp_bom_obj = self.env['mrp.bom'].search([(
            'code', '=', values['code'])])
        updated_values = self._assign_product_data(values)
        line_values = {
            'product_id': updated_values['product_comp'],
            'product_qty': updated_values['comp_qty'],
        }

        if mrp_bom_obj:
            mrp_bom_obj.write({
                'bom_line_ids': [(0, 0, line_values)]
            })
            _logger.info(
                "Adding component line for BOM: %s", values['code'])
        else:
            mrp_bom_obj.create({
                'code': updated_values['code'],
                'product_tmpl_id': updated_values['product_tmpl'],
                'product_qty': updated_values['tmpl_qty'],
                'bom_line_ids': [(0, 0, line_values)]
            })
            _logger.info(
                "Creating BOM: %s", values['code'])

    '''
        Function to read the csv file and convert it to a dict.

        :return Dict with the columns and its value.
    '''
    def action_import(self):
        """Load Inventory data from the CSV file."""
        if not self.data:
            raise exceptions.Warning(_("You need to select a file!"))
        # Decode the file data
        data = base64.b64decode(self.data).decode('utf-8')
        file_input = StringIO(data)
        file_input.seek(0)

        reader_info = []
        if self.delimeter:
            delimeter = str(self.delimeter)
        else:
            delimeter = ','
        reader = csv.reader(file_input, delimiter=delimeter,
                            lineterminator='\r\n')
        try:
            reader_info.extend(reader)
        except Exception:
            raise exceptions.Warning(_("Not a valid file!"))
        keys = reader_info[0]

        # Get column names
        keys_init = reader_info[0]
        keys = []
        for k in keys_init:
            temp = k.replace(' ', '_')
            keys.append(temp)

        del reader_info[0]
        values = {}

        for i in range(len(reader_info)):
            # Don't read rows that start with ( , ' ' or are empty
            if not (reader_info[i][0] is '' or reader_info[i][0][0] == '('
                    or reader_info[i][0][0] == ' '):
                field = reader_info[i]
                values = dict(zip(keys, field))
                self._create_new_mrp_bom(values)

        return {'type': 'ir.actions.act_window_close'}
