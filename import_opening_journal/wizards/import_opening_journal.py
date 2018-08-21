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


class ImportOpeningJournal(models.TransientModel):
    _name = 'import.opening.journal'

    data = fields.Binary(string='File', required=True)
    name = fields.Char(string='Filename')
    delimeter = fields.Char(
        string='Delimiter',
        default=',',
        help='Default delimiter ","',
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True
    )

    '''
        Function to update and correct some values.

        :param values: Dict with the values to import.

        :return Dict with the modified values modifieds.
    '''
    def _update_values(self, values):
        if values['debit']:
            values['debit'] = values['debit'].replace('.', '')
            values['debit'] = values['debit'].replace(',', '.')

        if values['credit']:
            values['credit'] = values['credit'].replace('.', '')
            values['credit'] = values['credit'].replace(',', '.')

        return values

    '''
        Function to assign not direct mapping data.

        :param values: Dict with the values to import.

        :return Dict with the correct mapping.
    '''
    def _assign_product_data(self, values):
        # Search for the account
        if values['account']:
            account_obj = self.env['account.account'].search([
                ('code', '=', values['account']),
                ('company_id', '=', self.company_id.id),
            ])
            if account_obj:
                values.update({
                    'account_id': account_obj.id,
                })
        del values['account']

        # Search for the partner
        if values['unique_code']:
            partner_obj = self.env['res.partner'].search([(
                'unique_code', '=', values['unique_code'])])
            if partner_obj:
                values.update({
                    'partner_id': partner_obj.id,
                })
        del values['unique_code']

        # Change date maturity to datetime obj
        if values['date_maturity']:
            date_maturity = datetime.strptime(
                values['date_maturity'], '%Y-%m-%d')
            values.update({
                'date_maturity': date_maturity,
            })

        values.update({
            'debit': float(values['debit']) if values['debit'] else 0.00,
            'credit': float(values['credit']) if values['credit'] else 0.00,
        })

        return values

    '''
        Function to create the opening journal lines.

        :param values: Dict with the values to import.
    '''
    def _create_new_opening_journal(self, values):
        opening_move_obj = self.env['account.move'].browse(
            int(values['move_id']))
        updated_values = self._assign_product_data(values)

        if opening_move_obj:
            _logger.info(updated_values)
            opening_move_obj.write({
                    'line_ids': [(0, 0, updated_values)]
            })
            _logger.info(
                "Adding journal line for account: %s", values['account_id'])

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
                new_values = self._update_values(values)
                self._create_new_opening_journal(new_values)

        return {'type': 'ir.actions.act_window_close'}
