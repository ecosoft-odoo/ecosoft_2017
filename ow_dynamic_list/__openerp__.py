# -*- encoding: utf-8 -*-
##############################################################################
#
#    OdooWare Dynamic List Module for Odoo
#    Copyright (C) 2016 OdooWare Services(http://www.odooware.com).
#    @author OdooWare Services <hello@odooware.com>
#
#    It is forbidden to publish, distribute, sublicense, 
#    or sell copies of the Software or modified copies of the Software.
#
#    The above copyright notice and this permission notice must be included 
#    in all copies or substantial portions of the Software.


#
##############################################################################

{
    'name': 'OdooWare Dynamic List',
    'summary': 'Web/Report Management',
    'description': """
     A Module to Show/hide columns on the list view On the fly without any technical knowledge.
     Enables a feature to Download Unlimited print screen report.
    """,
    'author': 'OdooWare Services',
    'website': 'http://odooware.com',
    'category': 'Web',
    'version': '2.3',
    'license': 'AGPL-3',
    'depends': ['web'],
    'price': 299,
    'currency': 'EUR', 
    'data': [
        'views/web_list_columns.xml',
    ],
    'qweb': ["static/src/xml/*.xml"],
    'auto_install': False,
    'app': True,
    'installable': True,
}
