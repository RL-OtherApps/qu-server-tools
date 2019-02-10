# Copyright 2018 Sergi Oliva <sergi.oliva@qubiq.es>
# Copyright 2018 Xavier Jiménez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, exceptions, _

import base64
import csv
from io import StringIO

import logging
_logger = logging.getLogger(__name__)


class ImportPartnerSupplier(models.TransientModel):
    _name = 'import.partner.supplier'

    data = fields.Binary('File', required=True)
    name = fields.Char('Filename')
    delimeter = fields.Char('Delimiter', default=',',
                            help='Default delimiter ","')

    '''
        Function to update and correct some values.

        :param values: Dict with the values to import.

        :return Dict with the modified values modifieds.
    '''
    def _update_values(self, values):
        for k, v in values.items():
            if v == 'True':
                values[k] = True
            elif v == 'False':
                values[k] = False

        if values['zip'] and values['country'] is 'ES':
            values['zip'] = values['zip'].zfill(5)

        return values

    '''
        Function to assign not direct mapping data.

        :param values: Dict with the values to import.

        :return Dict with the correct mapping.
    '''
    def _assign_partner_data(self, values):
        partner_data = {}

        # Assign country and state
        if values['country']:
            country_obj = self.env['res.country'].search([(
                'code', '=', values['country'])])
            if country_obj:
                partner_data.update({
                    'country_id': country_obj.id,
                })
        del values['country']

        if values['state']:
            state_obj = self.env[
                'res.country.state'].search([(
                    'name', '=', values['state'])])
            if not state_obj:
                state_obj = state_obj.create({
                    'name': values['state'],
                    'country_id': country_obj.id,
                    'code': values['state'][:4].upper(),
                })

            partner_data.update({
                    'state_id': state_obj.id,
                })
        del values['state']

        # Create and assign bank account
        if values['iban']:
            bank_acc_obj = self.env['res.partner.bank'].search([(
                'acc_number', '=', values['iban'])])
            if not bank_acc_obj:
                bank_values = {}
                bank_code = values['iban'][4:8]
                bank_obj = self.env['res.bank'].search([(
                    'code', '=', bank_code)])
                bank_values = {
                    'acc_number': values['iban'],
                }
                if bank_obj:
                    bank_values.update({
                        'bank_id': bank_obj.id,
                    })
                bank_acc_obj = bank_acc_obj.create(bank_values)

            partner_data.update({
                'bank_ids': [(6, 0, [bank_acc_obj.id])],
            })
        del values['iban']

        # Assign category
        if values['category_id']:
            category_obj = self.env['res.partner.category'].search([(
                'name', '=', values['category_id'])])
            if not category_obj:
                category_values = {}
                category_values = {
                    'name': values['category_id'],
                    'active': True,
                }
                category_obj = category_obj.create(category_values)

            partner_data.update({
                'category_id': [(6, 0, [category_obj.id])],
            })

        # Assign payment mode
        if values['payment_mode']:
            if values['customer'] is True:
                payment_mode_obj = self.env['account.payment.mode'].search([
                    ('payment_type', '=', 'inbound'),
                    ('name', '=', values['payment_mode'])])
                if payment_mode_obj:
                    partner_data.update({
                        'customer_payment_mode_id': payment_mode_obj.id,
                    })
            if values['supplier'] is True:
                payment_mode_obj = self.env['account.payment.mode'].search([
                    ('payment_type', '=', 'outbound'),
                    ('name', '=', values['payment_mode'])])
                if payment_mode_obj:
                    partner_data.update({
                        'supplier_payment_mode_id': payment_mode_obj.id,
                    })
        del values['payment_mode']

        # Assign payment term
        if values['payment_term']:
            payment_term_obj = self.env['account.payment.term'].search([
                ('name', '=', values['payment_term'])])
            if payment_term_obj:
                if values['customer'] is True:
                    partner_data.update({
                        'property_payment_term_id': payment_term_obj.id,
                    })
                if values['supplier'] is True:
                    partner_data.update({
                        'property_supplier_payment_term_id': payment_term_obj.id,
                    })
        del values['payment_term']

        # Assign pricelist
        if values['currency']:
            currency_obj = self.env[
                'res.currency'].search([(
                    'name', '=', values['currency'])])
            if currency_obj:
                pricelist_obj = self.env['product.pricelist'].search([(
                    'currency_id', '=', currency_obj.id)])
                if pricelist_obj:
                    partner_data.update({
                        # We get the first pricelist per currency
                        'property_product_pricelist': pricelist_obj[0].id,
                    })
        del values['currency']

        # Assign fiscal position
        if values['fiscal_position']:
            fiscal_obj = self.env[
                'account.fiscal.position'].search([(
                    'name', '=', values['fiscal_position'])])
            if fiscal_obj:
                partner_data.update({
                    'property_account_position_id': fiscal_obj.id,
                })
        del values['fiscal_position']

        # Create and assign a contact
        if values['contact_name']:
            contact_obj = self.env[
                'res.partner'].search([
                    ('name', '=', values['contact_name']),
                    ('parent_id', '!=', False)])
            new_contact = True
            if contact_obj:
                for contact in contact_obj:
                    if contact.parent_id.unique_code == values['unique_code']:
                        partner_data.update({
                                'child_ids': [(1, contact.id, {
                                    'function': values['contact_function'],
                                    'email': values['contact_email'],
                                    'mobile': values['contact_mobile'],
                                    })],
                            })
                        new_contact = False
                        break
            if new_contact:
                partner_data.update({
                        'child_ids': [(0, 0, {
                            'name': values['contact_name'],
                            'function': values['contact_function'],
                            'email': values['contact_email'],
                            'mobile': values['contact_mobile'],
                            })],
                    })

        del values['contact_name']
        del values['contact_function']
        del values['contact_email']
        del values['contact_mobile']

        if values['language']:
            language_obj = self.env[
                'res.lang'].search([
                    ('iso_code', '=', values['language'])])
            if language_obj:
                partner_data.update({
                    'lang': language_obj.code,
                })

        del values['language']

        return partner_data

    '''
        Function to create or write the partner / supplier.

        :param values: Dict with the values to import.
    '''
    def _create_new_partner(self, values):
        # Update existing customers
        current_partner = self.env['res.partner'].search([
            ('unique_code', '=', values['unique_code'])])
        fields = {}
        fields = self._assign_partner_data(values)
        if current_partner:
            current_partner.write(values)
            _logger.info("Updating partner: %s", current_partner.unique_code)
        else:
            current_partner = current_partner.create(values)
            _logger.info("Creating partner: %s", current_partner.unique_code)

        current_partner.write(fields)

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
            # Don't read rows that start with ( or are empty
            if not (reader_info[i][0] is '' or reader_info[i][0][0] == '('
                    or reader_info[i][0][0] == ' '):
                field = reader_info[i]
                values = dict(zip(keys, field))
                new_values = self._update_values(values)
                self._create_new_partner(new_values)

        return {'type': 'ir.actions.act_window_close'}
