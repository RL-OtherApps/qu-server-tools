# -*- coding: utf-8 -*-
# Copyright 2017 valentin vinagre <valentin.vinagre@qubiq.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from openerp import models, api
import iban
import logging
_logger = logging.getLogger(__name__)


class ResPartnerBankConfirm(models.TransientModel):
    _name = 'res.partner.bank.confirm'

    """
    Proceso que gracias al archivo iban.py transforma los ccc en iban.
    Tiene en cuenta que todos los paises son ES.
    https://www.lawebdelprogramador.com/codigo/Python/3276-Calculo-del-IBAN.html
    """
    @api.multi
    def calculo_iban_proceso(self):
        _logger.info("-->> ENTRO calculo_iban_proceso")
        for company in self.env['res.company'].search([]):
            for bank in self.env['res.partner.bank'].search([
                ('company_id', '=', company.id),
                ('acc_type', '=', 'bank')
                    ]):
                _logger.info("BANCOOOOOOO")
                _logger.info(bank)
                _logger.info(bank.acc_number)
                _logger.info("CONVERTIRRRR")
                number = bank.acc_number
                if number[:2] in ('ES', 'es'):
                    number = number[2:]
                iban_number = iban.convertir(number)
                _logger.info(iban_number)
                if ('Error') not in iban_number:
                    bank.acc_number = iban_number
        _logger.info("-->> FIN calculo_iban_proceso")
