# -*- coding: utf-8 -*-

from openerp import models, api, _
from openerp.exceptions import except_orm
from openerp.tools import float_compare


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.model
    def get_tax_key(self, tax_id):
        tax = self.env['account.invoice.tax'].browse(tax_id)
        key = (tax.tax_code_id.id, tax.base_code_id.id, tax.account_id.id)
        return key

    @api.model
    def check_missing_tax(self):
        return True

    @api.multi
    def check_tax_lines(self, compute_taxes):
        account_invoice_tax = self.env['account.invoice.tax']
        company_currency = self.company_id.currency_id
        if not self.tax_line:
            for tax in compute_taxes.values():
                account_invoice_tax.create(tax)
        else:
            tax_key = []
            precision = self.env['decimal.precision'].precision_get('Account')
            for tax in self.tax_line:
                if tax.manual:
                    continue
                key = self.get_tax_key(tax.id)
                tax_key.append(key)
                if key not in compute_taxes:
                    raise except_orm(_('Warning!'),
                                     _('Global taxes defined,\
                                     but they are not in invoice lines !'))
                base = compute_taxes[key]['base']
                if float_compare(abs(base - tax.base),
                                 company_currency.rounding,
                                 precision_digits=precision) == 1:
                    raise except_orm(_('Warning!'),
                                     _('Tax base different!\nClick\
                                     on compute to update the tax base.'))
            for key in compute_taxes:
                if self.check_missing_tax():
                    if key not in tax_key:
                        raise except_orm(_('Warning!'),
                                         _('Taxes are missing!\nClick\
                                         on compute button.'))
