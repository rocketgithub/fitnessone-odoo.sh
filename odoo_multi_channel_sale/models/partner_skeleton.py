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
from odoo.exceptions import ValidationError
PartnerType = [
	('contact','Contact'),
	('invoice','Invoice'),
	('delivery','Delivery'),
]
class ChannelOrderMappings(models.Model):
	_name="channel.partner.mappings"
	_inherit = ['channel.mappings']
	type = fields.Selection(
		selection = PartnerType,
		default='contact',
		required=1
	)
	store_customer_id =  fields.Char('Store Customer ID',required=True)
	odoo_partner_id = fields.Integer(string='Odoo Partner ID',required=True)
	odoo_partner = fields.Many2one('res.partner',string='Odoo Partner', required=True)
	_sql_constraints = [
		('channel_store_customer_id_uniq',
		'unique(channel_id, store_customer_id,type)',
		'Store partner ID must be unique for channel partner mapping!'),
		# ('channel_odoo_partner_id_uniq',
		#   	'unique(channel_id, odoo_partner_id)',
		#   	'Odoo partner ID must be unique for channel partner mapping!'),
	]

	@api.onchange('odoo_partner')
	def change_odoo_id(self):
		self.odoo_partner_id = self.odoo_partner.id

	def _compute_name(self):
		for record in self:
			if record.odoo_partner:
				record.name = record.odoo_partner.name
			else:
				record.name = 'Deleted'
