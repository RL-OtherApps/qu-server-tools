# -*- coding: utf-8 -*-
# Copyright 2017 valentin vinagre <valentin.vinagre@qubiq.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from openerp import models, api, fields
from datetime import datetime, timedelta, date
import logging
from heapq import merge

_logger = logging.getLogger(__name__)


class mandate_create_confirm(models.TransientModel):
    _name = "mandate.create.confirm"
    date_signature = fields.Date(string='Fecha de firma del mandato')
    lanzar_todo = fields.Boolean(string="Para todas las cuentas?", default=True)
    format = fields.Selection(
        [('basic', 'Mandato Básico'), ('sepa', 'Mandato SEPA')],
        default='basic', required=True,
        string='Formato')
    scheme = fields.Selection(
        [('CORE', 'Básico CORE'), ('B2B', 'Empresa (B2B)')],
        default='CORE', required=True, string="Esquema"
        )
    type = fields.Selection(
        [('recurrent', 'Recurrente'), ('oneoff', 'Único')],
        default='recurrent', string="Tipo de mandato"
        )
    recurrent_sequence_type = fields.Selection(
        [('first', 'Inicial'), ('recurring', 'Periódico'), ('final', 'Final')],
        default='recurring', string="Tipo de sequencia para el próximo cobro"
        )

    @api.multi
    def confirm(self):
        # Buscamos las cuentas bancarias que tienen un partner
        # asociado que sea cliente
        sql = """
            select id
            from res_partner_bank
            where partner_id in (   select id
                                    from res_partner
                                    where customer = True and parent_id is null)
            """
        # Esta segunda sql se puede utilizar en caso de que se requiera pasar
        # el proceso solamente para las cuentas bancarias restantes obviando
        # la resta
        sql_faltantes = """
            select id
            from res_partner_bank
            where id not in(
                    select 	rpb.id
                    from 	res_partner_bank rpb, account_banking_mandate abm
                    where 	rpb.partner_id in (	select id
                                    from res_partner
                                    where customer = True and parent_id is null)
                        and rpb.id = abm.partner_bank_id
                    group by rpb.id
                    having count(abm.*) > 0
            )
        """
        if self.lanzar_todo:
            self._cr.execute(sql)
        else:
            self._cr.execute(sql_faltantes)
        res = self._cr.fetchall()
        res = reduce(lambda x, y: list(merge(x, y)), res)
        if res:
            for bank in self.env['res.partner.bank'].browse(res):
                # Miramos si el cliente tiene compañia
                company_list = map(lambda obj: obj.id, bank.partner_id.company_id)
                if not company_list:
                    company_list = map(lambda obj: obj.id, self.env['res.company'].search([]))
                for company in company_list:
                    data_dict = {
                        'company_id': company,
                        'type': self.type,
                        'signature_date': self.date_signature,
                        'partner_bank_id': bank.id
                    }
                    if self.format == 'sepa':
                        data_dict['scheme'] = self.scheme
                        data_dict['type'] = self.type
                        if self.type == 'recurrent':
                            data_dict['recurrent_sequence_type'] = self.recurrent_sequence_type
                    # Search for mandate
                    mandate_obj = self.env['account.banking.mandate'].search([
                                ('partner_bank_id', '=', bank.id),
                                ('partner_id', '=', bank.partner_id.id),
                                ('company_id', '=', company)])
                    if not mandate_obj:
                        _logger.info(bank.partner_id.name)
                        res = mandate_obj.create(data_dict)
                        _logger.info('valida')
                        try:
                            res.validate()
                        except Exception, e:
                            pass
        return {'type': 'ir.actions.act_window_close'}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
