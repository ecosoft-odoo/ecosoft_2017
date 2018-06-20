# -*- coding: utf-8 -*-
from lxml import etree
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
import openerp.addons.decimal_precision as dp
from openerp import tools
import ast


class HRExpenseExpense(models.Model):
    _inherit = "hr.expense.expense"
    _rec_name = "number"

    is_employee_advance = fields.Boolean(
        string='Employee Advance',
        default=False,
    )
    is_advance_clearing = fields.Boolean(
        string='Advance Clearing',
        default=False,
    )
    advance_expense_id = fields.Many2one(
        'hr.expense.expense',
        string='Clear Advance',
    )
    advance_clearing_ids = fields.One2many(
        'hr.expense.clearing',
        'advance_expense_id',
        string='Advance Clearing Expenses',
    )
    amount_to_clearing = fields.Float(
        string='Advanced Balance',
        compute='_compute_amount_to_clearing',
        search='_search_amount_to_clearing',
        copy=False,
    )
    amount_advanced = fields.Float(
        string='Advanced Amount',
        readonly=True,
    )
    outstanding_advance_count = fields.Integer(
        string='Outstanding Advance Count',
        compute='_compute_outstanding_advance_count',
    )
    residual = fields.Float(
        string='Balance',
        digits=dp.get_precision('Account'),
        related='invoice_id.residual',
    )

    @api.model
    def _prepare_inv_header(self, partner_id, expense):
        res = super(HRExpenseExpense, self)._prepare_inv_header(partner_id,
                                                                expense)
        res.update({'advance_expense_id': expense.advance_expense_id.id})
        return res

    @api.model
    def _get_outstanding_advance_domain(self):
        domain = [('employee_id', '=', self.employee_id.id),
                  ('is_employee_advance', '=', True),
                  ('amount_to_clearing', '>', 0.0)]
        return domain

    @api.multi
    def _compute_outstanding_advance_count(self):
        for rec in self:
            domain = rec._get_outstanding_advance_domain()
            rec.outstanding_advance_count = len(self.search(domain))

    @api.multi
    def action_open_outstanding_advance(self):
        self.ensure_one()
        action = self.env.ref('hr_expense_advance_clearing.'
                              'action_expense_advance')
        result = action.read()[0]
        domain = self._get_outstanding_advance_domain()
        result.update({'domain': domain})
        context = ast.literal_eval(result['context'])
        context.update({'search_default_confirm': False})
        result['context'] = context
        return result

    @api.model
    def _search_amount_to_clearing(self, operator, value):
        # This method is valid only for Advance
        recs = self.search([('invoice_id.state', 'in', ('open', 'paid')),
                            ('is_employee_advance', '=', True)])
        if operator == '=':
            recs = recs.filtered(lambda x: x.amount_to_clearing == value)
        if operator == '>':
            recs = recs.filtered(lambda x: x.amount_to_clearing > value)
        if operator == '<':
            recs = recs.filtered(lambda x: x.amount_to_clearing < value)
        return [('id', 'in', recs.ids)]

    @api.multi
    @api.depends('advance_clearing_ids')
    def _compute_amount_to_clearing(self):
        for expense in self:
            amount_advanced = (expense.invoice_id.state in ('open', 'paid') and
                               expense.amount_advanced or 0.0)
            clearing_amount = sum([x.clearing_amount
                                   for x in expense.advance_clearing_ids])
            expense.amount_to_clearing = (amount_advanced -
                                          clearing_amount)

    @api.model
    def default_get(self, field_list):
        result = super(HRExpenseExpense, self).default_get(field_list)
        advance_account = self.env.user.company_id.employee_advance_account_id
        if not advance_account:
            raise ValidationError(_('No Employee Advance Account has been '
                                    'set in Account Settings!'))
        if result.get('is_employee_advance', False):
            ExpLine = self.env['hr.expense.line']
            line = [(0, 0, {'date_value': fields.Date.context_today(self),
                            'name': advance_account.name,
                            'uom_id': ExpLine._get_uom_id(),
                            'unit_quantity': 1.0,
                            'is_advance_product_line': True, })]
            result.update({'line_ids': line})
        return result

    @api.model
    def _module_installed(self, module_name):
        if not module_name:
            return False
        self._cr.execute("SELECT count(*) FROM ir_module_module\
                            WHERE name='%s' AND \
                            state='installed'" % module_name)
        return self._cr.fetchone()[0] == 1

    @api.model
    def fields_view_get(self, view_id=None, view_type=False,
                        toolbar=False, submenu=False):
        res = super(HRExpenseExpense, self).\
            fields_view_get(view_id=view_id, view_type=view_type,
                            toolbar=toolbar, submenu=submenu)
        if self._context.get('is_employee_advance', False) and \
                view_type == 'form':
            viewref = res['fields']['line_ids']['views']['tree']
            doc = etree.XML(viewref['arch'])
            nodes = doc.xpath("/tree")
            for node in nodes:
                node.set('create', 'false')
                node.set('delete', 'false')
            viewref['arch'] = etree.tostring(doc)
        return res

    @api.multi
    def expense_confirm(self):
        for expense in self:
            if not expense.is_advance_clearing and expense.amount <= 0.0:
                raise ValidationError(_('This expense have no lines,\
                or all lines with zero amount.'))
        return super(HRExpenseExpense, self).expense_confirm()

    @api.model
    def _create_negative_clearing_line(self, expense, invoice):
        employee_advance = expense.amount
        if expense.amount > expense.advance_expense_id.amount_to_clearing:
            employee_advance = \
                expense.advance_expense_id.amount_to_clearing
        invoice_line = expense.advance_expense_id.invoice_id.invoice_line
        if not invoice_line:
            raise ValidationError(_('No advance product line to reference'))
        advance_line = invoice_line[0]
        advance_line.copy({'invoice_id': invoice.id,
                           'price_unit': -employee_advance,
                           'sequence': 1, })

    @api.multi
    def _create_supplier_invoice_from_expense(self):
        self.ensure_one()
        expense = self
        invoice = super(HRExpenseExpense, self).\
            _create_supplier_invoice_from_expense()
        if expense.is_advance_clearing:
            self._create_negative_clearing_line(expense, invoice)
            invoice.write({'supplier_invoice_type':
                           'advance_clearing_invoice'})
        elif expense.is_employee_advance:
            invoice.write({'supplier_invoice_type':
                           'expense_advance_invoice'})
        else:
            invoice.write({'supplier_invoice_type':
                           'expense_expense_invoice'})
        return invoice

    @api.model
    def create(self, vals):
        if vals.get('is_employee_advance', False) and \
                vals.get('number', '/') == '/':
            vals['number'] = self.env['ir.sequence'].get('hr.expense.advance')
        return super(HRExpenseExpense, self).create(vals)

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=80):
        if self._context.get('advance_partner_id', False):
            Partner = self.env['res.partner']
            partner = Partner.browse(self._context['advance_partner_id'])
            ref_employee_id = (partner.user_ids and
                               partner.user_ids[0] and
                               partner.user_ids[0].employee_ids and
                               partner.user_ids[0].employee_ids[0].id or
                               False)
            domain = [('is_employee_advance', '=', True),
                      ('state', 'in', ('open', 'paid')),
                      ('employee_id', '=', ref_employee_id),
                      ('amount_to_clearing', '>', 0.0)]
            args += domain
        return super(HRExpenseExpense, self).\
            name_search(name=name, args=args, operator=operator, limit=limit)


class HRExpenseLine(models.Model):
    _inherit = "hr.expense.line"

    is_advance_product_line = fields.Boolean('Advance Product Line')

    @api.model
    def _get_non_product_account_id(self):
        # If Advance Line, get from setup account
        if self.is_advance_product_line:
            advance_account = \
                self.env.user.company_id.employee_advance_account_id
            if not advance_account:
                raise ValidationError(
                    _('No Employee Advance Code setup!'))
            else:
                return advance_account.id
        else:
            return super(HRExpenseLine, self)._get_non_product_account_id()

    @api.model
    def _prepare_analytic_line(self, reverse=False, currency=False):
        if self.is_advance_product_line:
            return False
        res = super(HRExpenseLine, self).\
            _prepare_analytic_line(reverse=reverse, currency=currency)
        return res


class HRExpenseClearing(models.Model):
    _name = 'hr.expense.clearing'
    _auto = False

    advance_expense_id = fields.Many2one(
        'hr.expense.expense',
        string='Advance Expense',
    )
    expense_id = fields.Many2one(
        'hr.expense.expense',
        string='Expense',
    )
    invoice_id = fields.Many2one(
        'account.invoice',
        string='Invoice',
    )
    expense_amount = fields.Float(
        sting='Expense Amount',
    )
    clearing_amount = fields.Float(
        sting='Clearing Amount',
    )
    invoiced_amount = fields.Float(
        sting='Invoiced Amount',
    )

    def _sql_select_1(self):
        return """
            create_date as date, advance_expense_id, id as expense_id,
            null as invoice_id, amount as expense_amount,
            null as clearing_amount, null as invoiced_amount
        """

    def _sql_select_2(self):
        return """
            date, advance_expense_id, expense_id, invoice_id,
            expense_amount, clearing_amount,
            case when type in ('in_invoice')
            then amount_total + clearing_amount
            else amount_total end as invoiced_amount
        """

    def _sql_select_3(self):
        return """
            coalesce(exp.create_date, ai.create_date) as date,
            ai.advance_expense_id, ai.type, expense_id,
            ail.invoice_id, exp.amount as expense_amount,
            case when ai.type in ('in_invoice')
            and ail.price_subtotal < 0.0 then -ail.price_subtotal
            when ai.type in ('out_invoice') then ai.amount_total
            else 0.0 end as clearing_amount, ai.amount_total
        """

    def init(self, cr):
        tools.drop_view_if_exists(cr, self._table)

        _sql = """
        select row_number() over (order by date) as id, * from (
        (select %s
            from hr_expense_expense
            where state = 'accepted' and advance_expense_id is not null)
        UNION ALL
            (select %s
            from (
                select %s
                from account_invoice ai join account_invoice_line ail
                        on ai.id = ail.invoice_id
                    left outer join hr_expense_expense exp
                        on exp.id = ai.expense_id
                where ((ai.type in ('in_invoice') and ail.price_subtotal < 0.0)
                    or ai.type in ('out_invoice'))
                    and ai.state in ('open', 'paid')
            ) a
            where advance_expense_id is not null)) b
        """ % (self._sql_select_1(),
               self._sql_select_2(),
               self._sql_select_3(),)

        cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" %
                   (self._table, _sql,))
