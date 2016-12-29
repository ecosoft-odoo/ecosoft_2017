# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

{
    'name': 'Thailand - Accounting for ECOSOFT',
    'version': '1.0',
    'category': 'Localization/Account Charts',
    'description': """
Chart of Accounts for ECOSOFT.
===============================

Thai accounting chart for ECOSOFT and localization.
    """,
    'author': 'Ecosoft',
    'website': 'http://www.ecosoft.co.th/',
    'depends': ['account_chart',
                'l10n_th_account', ],
    'data': [
        'data/account.account.type.csv',
        'data/account.account.template.csv',
        'data/account.tax.code.template.csv',
        'data/account.chart.template.csv',
        'data/account.tax.template.csv',
        'data/ir.actions.todo.csv',
        ],
    'installable': True,
    'images': ['images/config_chart_l10n_th.jpeg',
               'images/l10n_th_chart.jpeg'],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
