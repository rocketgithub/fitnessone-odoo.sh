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

class ChannelAttributetMappings(models.Model):

	_name="channel.attribute.mappings"
	_inherit = ['channel.mappings']

	store_attribute_id =  fields.Char('Store Attribute ID' ,required=True)
	store_attribute_name =  fields.Char('Store Attribute Name' )
	attribute_name = fields.Many2one('product.attribute',string='Odoo Attribute Name', required=True)
	odoo_attribute_id = fields.Integer(string='Odoo Attribute ID',required=True)

	def _compute_name(self):
		for record in self:
			if record.attribute_name:
				record.name = record.attribute_name.name
			else:
				record.name = 'Deleted'

	@api.onchange('attribute_name')
	def change_odoo_id(self):
		self.odoo_attribute_id = self.attribute_name.id


class ChannelAttributetValueMappings(models.Model):

	_name="channel.attribute.value.mappings"
	_inherit = ['channel.mappings']

	store_attribute_value_id =  fields.Char('Store Attribute Value ID',required=True)
	store_attribute_value_name =  fields.Char('Store Attribute Value Name' )
	attribute_value_name = fields.Many2one('product.attribute.value',string='Odoo Attribute Value Name', required=True)
	odoo_attribute_value_id = fields.Integer('Odoo Value ID',required=True)

	@api.onchange('attribute_value_name')
	def change_odoo_id(self):
		self.odoo_attribute_value_id = self.attribute_value_name.id
	def _compute_name(self):
		for record in self:
			if record.attribute_value_name:
				record.name = record.attribute_value_name.name
			else:
				record.name = 'Deleted'
