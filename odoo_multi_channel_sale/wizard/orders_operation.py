# -*- coding: utf-8 -*-
##########################################################################
#
#    Copyright (c) 2017-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE URL <https://store.webkul.com/license.html/> for full copyright and licensing details.
##########################################################################
from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger(__name__)
from odoo import api, fields, models, _
Source = [
	('all','All'),
	('order_ids','Order ID(s)'),
]
class Importorders(models.TransientModel):
    _inherit = ['import.operation']
    _name = "import.orders"

    source = fields.Selection(
        Source,
        required=1,
        default='all'
    )

    order_ids = fields.Text(
        string='Order ID(s)'
    )


class ExportOrders(models.TransientModel):

    _inherit = ['export.operation']
    _name = "export.orders"

    @api.model
    def _get_order_domain(self):
        return []
    @api.model
    def default_get(self,fields):
        res=super(ExportOrders,self).default_get(fields)
        if not res.get('order_ids') and self._context.get('active_model')=='sale.order':
            res['order_ids']=self._context.get('active_ids')
        return res

    order_ids = fields.Many2many(
        'sale.order',
        string='Sale order',
    )
