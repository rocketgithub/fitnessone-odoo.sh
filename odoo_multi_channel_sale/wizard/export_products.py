# -*- coding: utf-8 -*-
##########################################################################
#
#    Copyright (c) 2017-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE URL <https://store.webkul.com/license.html/> for full copyright and licensing details.
##########################################################################
import logging
_logger = logging.getLogger(__name__)

from odoo import api, fields, models, _
class ExportOdooProducts(models.TransientModel):
	_inherit = ['export.products']
	_name  = "export.odoo.products"

	@api.multi
	def export_odoo_products(self):
		if hasattr(self, 'export_%s_products' % self.channel_id.channel):
			return getattr(self, 'export_%s_products' % self.channel_id.channel)()

	@api.multi
	def update_odoo_products(self):
		if hasattr(self, 'update_%s_products' % self.channel_id.channel):
			return getattr(self, 'update_%s_products' % self.channel_id.channel)()
