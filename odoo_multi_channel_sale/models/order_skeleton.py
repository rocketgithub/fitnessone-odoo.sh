# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2017-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
# Developed By: Jahangir Ahmad
#################################################################################
from odoo import fields , models,api
class ChannelOrderMappings(models.Model):
	_name="channel.order.mappings"
	_inherit = ['channel.mappings']
	odoo_order_id = fields.Integer(string='Odoo Order ID',required=True)
	order_name = fields.Many2one('sale.order',string='Odoo Order')
	odoo_partner_id = fields.Many2one(related='order_name.partner_id')
	store_order_id =  fields.Char('Store Order ID',required=True)
	@api.multi
	def unlink(self):
		for record in self:
			match = record.store_order_id and record.channel_id.match_order_feeds(record.store_order_id)
			if match: match.unlink()
		res = super(ChannelOrderMappings, self).unlink()
		return  res



	@api.onchange('order_name')
	def change_odoo_id(self):
		self.odoo_order_id = self.order_name.id

	def _compute_name(self):
		for record in self:
			if record.order_name:
				record.name = record.order_name.name
			else:
				record.name = 'Deleted'
