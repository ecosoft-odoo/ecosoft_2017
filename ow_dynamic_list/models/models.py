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
from openerp import models, fields


class DynamicView(models.Model):
    _name = "dynamic.fields"

    view_id = fields.Many2one("ir.ui.view", "View")
    dynamic_list_text = fields.Text("Dynamic List")
    user_id = fields.Many2one("res.users", "User")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
