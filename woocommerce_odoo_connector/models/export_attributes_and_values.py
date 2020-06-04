#!/usr/bin/env python
# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE file for full copyright and licensing details.
#################################################################################

from odoo import api,fields,models
from odoo.tools.translate import _
from odoo.exceptions import UserError
import logging
_logger	 = logging.getLogger(__name__)
try:
	from woocommerce import API
except ImportError:
	_logger.info('**Please Install Woocommerce Python Api=>(cmd: pip3 install woocommerce)')

class MultiChannelSale(models.Model):
	_inherit = "multi.channel.sale"

	@api.multi
	def export_all_woocommerce_values(self):
		attr_val = 0
		attribute_value_records = ''
		attribute_value_records = self.env['product.attribute.value'].search([])
		for attribute_value in attribute_value_records:
			mapping_rec = self.env['channel.attribute.value.mappings'].search([('odoo_attribute_value_id','=',attribute_value.id),('channel_id.id','=',self.id)])
			if not mapping_rec:
				woocommerce = self.get_woocommerce_connection()
				woocommerce_attribute_id =     self.env['channel.attribute.mappings'].search([('odoo_attribute_id','=',attribute_value.attribute_id.id),('channel_id.id','=',self.id)])
				if woocommerce_attribute_id:
					attribute_id = woocommerce_attribute_id.store_attribute_id
					attribute_value_dict = {
											"name": attribute_value.name,
					}
					return_value_dict = woocommerce.post(
															'products/attributes/'+str(attribute_id)+"/terms",
															attribute_value_dict
														).json()
					if 'message' in return_value_dict:
						raise UserError(_('Error in Creating terms '+str(return_value_dict['message'])))
					attr_val += 1
					mapping_dict={
								'channel_id'				: self.id,
								'store_attribute_value_id'	: return_value_dict['id'],
								'odoo_attribute_value_id'	: attribute_value.id,
								'attribute_value_name'		: attribute_value.id,
								'store_attribute_value_name': attribute_value.name,
							    	'operation'                 : 'export'
					}
					obj = self.env['channel.attribute.value.mappings']
					self._create_mapping(obj, mapping_dict)
					self._cr.commit()
		return attr_val

	@api.multi
	def export_all_woocommerce_attribute_values(self):
		attr = 0
		attr_val = 0
		attribute_value_records = ''
		attribute_records = self.env['product.attribute'].search([])
		for attribute in attribute_records:
			mapping_rec = self.env['channel.attribute.mappings'].search([('odoo_attribute_id','=',attribute.id),('channel_id.id','=',self.id)])
			if not mapping_rec:
				woocommerce = self.get_woocommerce_connection()
				attribute_dict = {
								    "name"			: attribute.name,
									"type"			: "select",
								    "order_by"		: "menu_order",
								    "has_archives"	: True
				}
				return_dict = woocommerce.post('products/attributes',
												attribute_dict
				).json()
				attr += 1
				if 'message' in return_dict:
					raise UserError(_('Error in Creating Attributes :'+str(return_dict['message'])))
				mapping_dict = {
							'channel_id'		: self.id,
							'store_attribute_id': return_dict['id'],
							'odoo_attribute_id' : attribute.id,
							'attribute_name'	: attribute.id,
							'store_attribute_name': attribute.name,
							'operation'           : 'export'
				}
				obj = self.env['channel.attribute.mappings']
				self._create_mapping(obj, mapping_dict)
				attribute_value_records = self.env['product.attribute.value'].search(
												[('attribute_id','=',attribute.id)]
										)
				for attribute_value in attribute_value_records:
					mapping_rec = self.env['channel.attribute.value.mappings'].search(
								[('odoo_attribute_value_id','=',attribute_value.id),('channel_id.id','=',self.id)]
								)
					if not mapping_rec:
						attribute_value_dict = {
												"name": attribute_value.name,
						}
						return_value_dict = woocommerce.post('products/attributes/' + str(return_dict['id']) + "/terms", attribute_value_dict).json()
						if 'message' in return_value_dict:
							raise UserError(_('Error in Creating Attributes Terms :'+str(return_dict['message'])))
						attr_val += 1
						mapping_dict = {
									'channel_id'				: self.id,
									'store_attribute_value_id'	: return_value_dict['id'],
									'odoo_attribute_value_id'	: attribute_value.id,
									'attribute_value_name'		: attribute_value.id,
									'store_attribute_value_name': attribute_value.name,
							        	'operation'                 : 'export'
						}
						obj = self.env['channel.attribute.value.mappings']
						self._create_mapping(obj, mapping_dict)
						self._cr.commit()
		return attr,attr_val

	@api.multi
	def export_woocommerce_attribute_values_by_id(self,attribute):
		attr = 0
		attr_val = 0
		attribute_value_records = ''
		mapping_rec = self.env['channel.attribute.mappings'].search([('odoo_attribute_id','=',attribute.id),('channel_id.id','=',self.id)])
		if not mapping_rec:
			woocommerce = self.get_woocommerce_connection()
			attribute_dict = {
								"name"			: attribute.name,
								"type"			: "select",
								"order_by"		: "menu_order",
								"has_archives"	: True
			}
			return_dict = woocommerce.post('products/attributes',
											attribute_dict
			).json()
			attr += 1
			if 'message' in return_dict:
				raise UserError(_('Error in Creating Attributes :'+str(return_dict['message'])))
			mapping_dict = {
						'channel_id'		: self.id,
						'store_attribute_id': return_dict['id'],
						'odoo_attribute_id' : attribute.id,
						'attribute_name'	: attribute.id,
						'operation'         : 'export'
			}
			obj = self.env['channel.attribute.mappings']
			self._create_mapping(obj, mapping_dict)
			attribute_value_records = self.env['product.attribute.value'].search(
											[('attribute_id','=',attribute.id)]
									)
			for attribute_value in attribute_value_records:
				mapping_rec = self.env['channel.attribute.value.mappings'].search(
							[('odoo_attribute_value_id','=',attribute_value.id),('channel_id.id','=',self.id)]
							)
				if not mapping_rec:
					attribute_value_dict = {
											"name": attribute_value.name,
					}
					return_value_dict = woocommerce.post('products/attributes/' + str(return_dict['id']) + "/terms", attribute_value_dict).json()
					if 'message' in return_value_dict:
						raise UserError(_('Error in Creating Attributes Terms :'+str(return_dict['message'])))
					attr_val += 1
					mapping_dict = {
								'channel_id'				: self.id,
								'store_attribute_value_id'	: return_value_dict['id'],
								'odoo_attribute_value_id'	: attribute_value.id,
								'attribute_value_name'		: attribute_value.id,
							    	'operation'                 : 'export'
					}
					obj = self.env['channel.attribute.value.mappings']
					self._create_mapping(obj, mapping_dict)
					self._cr.commit()
		return attr,attr_val
	#export attribute and value
	@api.multi
	def export_woocommerce_attributes_values(self):
		# self.import_woocommerce_attribute()
		attribute,value = self.export_all_woocommerce_attribute_values()
		value1 = self.export_all_woocommerce_values()
		value = value + value1
		message = str(attribute) + " Attributes have been exported & " + str(value) + " Attribute Terms have been exported"
		return self.display_message(message)
