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
	def export_all_woocommerce_categories(self):
		message = self.sudo().export_update_woocommerce_categories()
		count = self.sudo().export_woocommerce_categories(0)
		message += str(count)+" Categories have been exported"
		return self.display_message(message)

	@api.multi
	def export_woocommerce_categories(self, count , parent_id = False):
		self.import_woocommerce_categories()
		parent = 0
		category_records = ''
		# if not parent_id and 'active_ids' in self._context:
		# 	if self._context['active_ids'] and self._context['active_model'] == 'product.category':
		# 		category_records=self.env['product.category'].browse(self._context['active_ids'])
		# elif not parent_id:
		category_records = self.env['product.category'].search([])
		if parent_id:
			category_records = self.env['product.category'].browse(parent_id)
		for category in category_records:
			mapping_rec = self.env['channel.category.mappings'].search([('odoo_category_id','=',category.id),('channel_id.id','=',self.id)])
			if mapping_rec and parent_id:
				return mapping_rec.store_category_id
			if not mapping_rec:
				count = count + 1
				if category.parent_id:
					parent = self.export_woocommerce_categories(count, category.parent_id.id)
				woocommerce = self.get_woocommerce_connection()
				category_dict = {
								'name'  : category.name,
				}
				if parent:
					category_dict.update({'parent': parent,})
				return_dict = woocommerce.post('products/categories',category_dict).json()
				if 'message' in return_dict:
					raise UserError(_('Error in Creating Categories : '+str(return_dict['message'])))
				mapping_dict = {
							'channel_id'		: self.id,
							'store_category_id'	: return_dict['id'],
							'odoo_category_id'	: category.id,
							'category_name'		: category.id,
							'operation'             : 'export'
				}
				obj = self.env['channel.category.mappings']
				self._create_mapping(obj, mapping_dict)
				if parent_id:
					return return_dict['id']
		self._cr.commit()
		return count

	@api.multi
	def export_woocommerce_categories_id(self, category):
		parent= False
		if category:
			mapping_rec = self.env['channel.category.mappings'].search([('odoo_category_id','=',category.id),('channel_id.id','=',self.id)])
			if not mapping_rec:
				if category.parent_id:
					parent = self.export_woocommerce_categories(0, category.parent_id.id)
				woocommerce = self.get_woocommerce_connection()
				category_dict = {
								'name' : category.name,
				}
				if parent:
					category_dict.update({'parent': parent,})
				return_dict = woocommerce.post('products/categories',category_dict).json()
				if 'message' in return_dict:
					raise UserError(_('Error in Creating Categories : '+str(return_dict['message'])))
				mapping_dict = {
							'channel_id'		: self.id,
							'store_category_id'	: return_dict['id'],
							'odoo_category_id'	: category.id,
							'category_name'		: category.id,
							'operation'         : 'export'
				}
				obj = self.env['channel.category.mappings']
				self._create_mapping(obj, mapping_dict)
				self._cr.commit()
				return return_dict['id']
		return False