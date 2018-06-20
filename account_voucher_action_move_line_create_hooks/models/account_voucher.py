# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Jordi Ballester (Eficent)
#    Copyright 2015 Eficent
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import api, models


class AccountVoucher(models.Model):
    _inherit = "account.voucher"

    @api.model
    def _finalize_voucher(self, voucher):
        return voucher

    @api.model
    def _finalize_line_total(self, voucher, line_total,
                             move_id, company_currency,
                             current_currency):
        return line_total

    @api.model
    def action_move_line_writeoff_hook(self, voucher, ml_writeoff):
        if ml_writeoff:
            if isinstance(ml_writeoff, dict):
                ml_writeoff = [ml_writeoff]
            self.env['account.move.line'].create(ml_writeoff[0])
        return True

    @api.model
    def action_move_line_create_hook(self, voucher,
                                     rec_list_ids):
        for rec_ids in rec_list_ids:
            if len(rec_ids) >= 2:
                move_lines = self.env['account.move.line'].browse(rec_ids)
                move_lines.reconcile_partial(
                    writeoff_acc_id=voucher.writeoff_acc_id.id,
                    writeoff_period_id=voucher.period_id.id,
                    writeoff_journal_id=voucher.journal_id.id
                )
        return True

    @api.model
    def _set_local_context(self):
        context = self._context
        local_context = dict(
            context,
            force_company=self.journal_id.company_id.id
        )
        return local_context

    @api.multi
    def action_move_line_create(self):
        """ Add HOOK """
        # HOOK: To bypass this method completely
        if self._context.get('bypass', False):
            return True
        # --
        context = self._context
        move_pool = self.env['account.move']
        move_line_pool = self.env['account.move.line']
        for voucher in self:
            #  local_context = dict(
            # context,
            # force_company=voucher.journal_id.company_id.id)
            local_context = voucher._set_local_context()  # HOOK
            if voucher.move_id:
                continue
            company_currency = self._get_company_currency(voucher.id)
            current_currency = self._get_current_currency(voucher.id)
            # we select the context to use accordingly if
            # it's a multicurrency case or not
            context = self.with_context(context)._sel_context(voucher.id)
            # But for the operations made by _convert_amount, we always
            # need to give the date in the context
            ctx = context.copy()
            ctx.update({'date': voucher.date})
            # Create the account move record.
            move = move_pool.with_context(context).\
                create(self.with_context(context).account_move_get(voucher.id))
            # Get the name of the account_move just created
            name = move.name
            # Create the first line of the voucher
            move_line = move_line_pool.with_context(local_context).create(
                self.with_context(local_context).first_move_line_get(
                    voucher.id, move.id, company_currency, current_currency))
            line_total = move_line.debit - move_line.credit
            rec_list_ids = []

            if voucher.type == 'sale':
                line_total = line_total - \
                    self.with_context(ctx)._convert_amount(voucher.tax_amount,
                                                           voucher.id)
            elif voucher.type == 'purchase':
                line_total = line_total + \
                    self.with_context(ctx)._convert_amount(voucher.tax_amount,
                                                           voucher.id)

            # Create one move line per voucher line where amount is not 0.0
            line_total, rec_list_ids = \
                self.with_context(context).voucher_move_line_create(
                    voucher.id, line_total, move.id,
                    company_currency, current_currency)
            # HOOK
            line_total = self.with_context(context).\
                _finalize_line_total(voucher, line_total, move.id,
                                     company_currency, current_currency)
            # --
            # Create the writeoff line if needed
            ml_writeoff = self.with_context(local_context).\
                writeoff_move_line_get(voucher.id, line_total, move.id, name,
                                       company_currency, current_currency)
            # HOOK
            self.action_move_line_writeoff_hook(voucher, ml_writeoff)
            # We post the voucher.
            voucher.write({
                'move_id': move.id,
                'state': 'posted',
                'number': name,
            })
            # HOOK
            voucher = self._finalize_voucher(voucher)
            # --
            if voucher.journal_id.entry_posted:
                move.post()
            # We automatically reconcile the account move lines.
            # reconcile = False (not in use when refactor)
            # HOOK
            self.action_move_line_create_hook(voucher, rec_list_ids)
        return True
