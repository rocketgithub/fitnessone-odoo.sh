#!/usr/bin/env python
# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE file for full copyright and licensing details.
#################################################################################
from odoo import api,fields,models

from odoo.tools.translate import _
from datetime import datetime,timedelta
from odoo.exceptions import UserError
import os
import base64
import logging
_logger	 = logging.getLogger(__name__)
try:
	from woocommerce import API
except ImportError:
	_logger.info('**Please Install Woocommerce Python Api=>(cmd: pip3 install woocommerce)')
class MultiChannelSale(models.Model):
	_inherit = "multi.channel.sale"

	@api.multi
	def export_update_woocommerce_product(self):
		count = 0
		self.export_woocommerce_categories(0)
		self.export_all_woocommerce_attribute_values()
		template_mapping = self.env['channel.template.mappings'].search([('need_sync','=','yes'),('channel_id.id','=',self.id)])
		for check in template_mapping:
			count=len(template_mapping)
			template = check.template_name
			if not template.active: continue
			store_id = check.store_product_id
			woocommerce = self.get_woocommerce_connection()
			try:
				product_dict = woocommerce.get('products/'+str(store_id)).json()
				if 'bundle_layout' in product_dict:
					product_dict.pop('bundle_layout')
				if 'message' in product_dict:
					raise UserError(_("Can't fetch product "+str(product_dict['message'])))
				else:
					if product_dict['type'] == 'simple':
						if len(template.product_variant_ids) == 1 and not template.attribute_line_ids:
							status = self.update_woocommerce_simple_product(template, store_id, product_dict, woocommerce)
							if status:
								message = "Products Updated Successfully , "
						elif len(template.product_variant_ids) == 1 and template.attribute_line_ids and not template.product_variant_ids[0].attribute_value_ids:
							status = self.update_woocommerce_simple_product(template, store_id, product_dict, woocommerce)
							if status:
								message = "Products Updated Successfully , "
						elif len(template.product_variant_ids) >= 1 and template.attribute_line_ids:
							count = self.update_woocommerce_simple2variable_product(template, store_id,  product_dict, woocommerce)
							if count:
								message = str(count)+" Variants added, Product updated Successfully , "
						else:
							raise UserError(_('No Variant'))
					elif product_dict['type'] == 'variable':
						product_map = self.env['channel.product.mappings'].search([('odoo_template_id.id','=',template.id),('channel_id.id','=',self.id)])
						if len(product_map) == len(template.product_variant_ids):
							status = self.update_woocommerce_variable_product(template, product_map, product_dict, woocommerce)
							if status:
								message = "Products Updated!  "
						else:
							status = self.update_create_woocommerce_variable_product(template, product_map, product_dict, woocommerce)
							if status:
								message = "Products Updated!  "
					else:
						raise UserError(_("Product Type Not Supported"))
			except Exception as e:
				raise UserError(_("Can't fetch product"+str(e)))
			check.need_sync = 'no'
		return self.display_message(str(count) + " Products Updated! ")


	@api.multi
	def action_update_woocommerce_products(self):
		template_ids = []
		message = ''
		if 'active_ids' in self._context:
			if self._context['active_model'] == 'product.template':
				template_ids = self._context['active_ids']
			elif self._context['active_model'] == 'product.product':
				product_records = self.env['product.product'].browse(self._context['active_ids'])
				for product in product_records:
					template_ids.append(product.product_tmpl_id.id)
			else:
				raise UserError(_('Context is Empty'))

			for template_id in template_ids:
				check = self.env['channel.template.mappings'].search([('odoo_template_id','=',template_id),('channel_id.id','=',self.id)])
				if not check:
					return self.action_export_woocommerce_products()
				else:
					template = check.template_name
					store_id = check.store_product_id
					woocommerce = self.get_woocommerce_connection()
					try:
						product_dict = woocommerce.get('products/'+str(store_id)).json()
						if 'bundle_layout' in product_dict:
							product_dict.pop('bundle_layout')
						if 'message' in product_dict:
							raise UserError(_("Can't fetch product "+str(product_dict['message'])))
						else:
							if product_dict['type'] == 'simple':
								if len(template.product_variant_ids) == 1 and not template.attribute_line_ids:
									status = self.update_woocommerce_simple_product(template, store_id, product_dict, woocommerce)
									if status:
										message = "Product Updated Successfully , "
								elif len(template.product_variant_ids) == 1 and template.attribute_line_ids and not template.product_variant_ids[0].attribute_value_ids:
									status = self.update_woocommerce_simple_product(template, store_id, product_dict, woocommerce)
									if status:
										message = "Products Updated Successfully , "
								elif len(template.product_variant_ids) >= 1 and template.attribute_line_ids:
									count = self.update_woocommerce_simple2variable_product(template, store_id,  product_dict, woocommerce)
									if count:
										message = str(count)+" Variants added, Product updated Successfully , "
								else:
									raise UserError(_('No Variant'))
							elif product_dict['type'] == 'variable':
								product_map = self.env['channel.product.mappings'].search([('odoo_template_id.id','=',template.id),('channel_id.id','=',self.id)])
								if len(product_map) == len(template.product_variant_ids):
									status = self.update_woocommerce_variable_product(template, product_map, product_dict, woocommerce)
									if status:
										message = "Products Updated!  "
								else:
									status = self.update_create_woocommerce_variable_product(template, product_map, product_dict, woocommerce)
									if status:
										message = "Products Updated!  "
							else:
								raise UserError(_("Product Type Not Supported"))
					except Exception as e:
						raise UserError(_("Can't fetch product , "+str(e)))
				check.need_sync = 'no'
			return self.display_message(message)

	@api.multi
	def update_woocommerce_simple_product(self, template, store_id, product_dict, woocommerce):
		if woocommerce and template:
			product_dict.update({
								'name' 	: template.name,
								'images': self.create_woocommerce_product_image(template),
								'sku' 				: template.default_code or "",
								'regular_price'		: str(template.with_context(pricelist=self.pricelist_name.id).price) or "",
								'attributes'		: self.set_woocommerce_attribute_line(template),
								'categories'		: self.set_woocommerce_product_categories(template),
								'short_description'	: template.description_sale  or "" ,
								'description'		: template.description or "",
								'price'				: template.with_context(pricelist=self.pricelist_name.id).price,
			})
			if template.length or template.width or template.height:
				dimensions = {
								u'width': str(template.width) or "", 
								u'length': str(template.length) or "" , 
								u'unit': str(template.dimensions_uom_id.name) or "", 
								u'height': str(template.height) or "",
							}
				product_dict['dimensions']=dimensions
			if template.weight:
				product_dict['weight']= str(template.weight)  or  ""
			try:
				return_dict = woocommerce.put('products/'+str(store_id),product_dict).json()
				if 'message' in return_dict:
					raise UserError(_("Can't update product , "+str(return_dict['message'])))
			except Exception as e:
				raise UserError(_("Can't update product , "+str(e)))
		return True

	@api.multi
	def update_woocommerce_simple2variable_product(self, template, store_id, product_dict, woocommerce):
		count = 0
		if woocommerce and template:
			product_dict.update({
								'name' 				: template.name,
								'images'			: self.create_woocommerce_product_image(template, True),
								'sku' 				:  "",
								'regular_price'		: str(template.with_context(pricelist=self.pricelist_name.id).price) or "",
								'type'				: 'variable',
								'attributes'		: self.set_woocommerce_attribute_line(template),
								'default_attributes': self.get_woocommerce_attribute_dict(template.product_variant_ids[0]),
								'categories'		: self.set_woocommerce_product_categories(template),
								'short_description'	: template.description_sale  or "" ,
								'description'		: template.description or "",
								'price'				: template.with_context(pricelist=self.pricelist_name.id).price,
			})
			if template.length or template.width or template.height:
				dimensions = {
								u'width': str(template.width) or "", 
								u'length': str(template.length) or "" , 
								u'unit': str(template.dimensions_uom_id.name) or "", 
								u'height': str(template.height) or "",
							}
				product_dict['dimensions']=dimensions
			if template.weight:
				product_dict['weight']= str(template.weight)  or  ""
			try:
				return_dict  = woocommerce.put('products/'+str(store_id),product_dict).json()
				unlink_record = self.env['channel.product.mappings'].search([('odoo_template_id.id','=',template.id),('channel_id.id','=',self.id)])
				unlink_record.unlink()
				if 'message' in return_dict:
					raise UserError(_("Can't update product from simple to variable"+str(return_dict['message'])))
				else:
					image_ids = []
					for image in return_dict['images']:
						if image['position'] != 0:
							image_ids.append(image['id'])
					if image_ids:
						count = self.create_woocommerce_variation(return_dict['id'], template, woocommerce, image_ids)
					else:
						count = self.create_woocommerce_variation(return_dict['id'], template, woocommerce)
					if count:
						return count
			except Exception as e:
				raise UserError(_("Can't update product from simple to variable"))

	def update_woocommerce_variable_product(self, template, product_map, product_dict, woocommerce):
		if woocommerce and template:
			product_dict.update({
								'name' 				: template.name,
								'images'			: self.create_woocommerce_product_image(template, True),
								'sku' 				: "",
								'regular_price'		: str(template.with_context(pricelist=self.pricelist_name.id).price) or "",
								'type'				: 'variable',
								'attributes'		: self.set_woocommerce_attribute_line(template),
								'default_attributes': self.get_woocommerce_attribute_dict(template.product_variant_ids[0]),
								'categories'		: self.set_woocommerce_product_categories(template),
								'short_description'	: template.description_sale  or "" ,
								'description'		: template.description or "",
								'price'				: template.with_context(pricelist=self.pricelist_name.id).price,
			})
			if template.length or template.width or template.height:
				dimensions = {
								u'width': str(template.width) or "", 
								u'length': str(template.length) or "" , 
								u'unit': str(template.dimensions_uom_id.name) or "", 
								u'height': str(template.height) or "",
							}
				product_dict['dimensions']=dimensions
			if template.weight:
				product_dict['weight']= str(template.weight)  or  ""
			try:
				return_dict  = woocommerce.put('products/'+str(product_dict['id']),product_dict).json()
				if 'message' in return_dict:
					raise UserError(_("Can't update product from simple to variable : "+str(return_dict['message'])))
				else:
					image_ids = []
					for image in return_dict['images']:
						if image['position'] != 0:
							image_ids.append(image['id'])
					if image_ids:
						count = self.update_woocommerce_variation(return_dict['id'],template, product_map,woocommerce, image_ids)
					else:
						count = self.update_woocommerce_variation(return_dict['id'], template, product_map,woocommerce)
					if count:
						return count
			except Exception as e:
				raise UserError(_("Can't update  variable product "+str(e)))

	@api.multi
	def update_woocommerce_variation(self, store_product_id, template, product_map, woocommerce, image_ids = False):
		count = 0
		if store_product_id and woocommerce and product_map:
			for product in product_map:
				store_variant_id = product.store_variant_id
				variant = product.product_name
				variant_data = {
								'regular_price'	: str(variant.with_context(pricelist=self.pricelist_name.id).price) or "",
								'visible'		: True,
								'sku'			: variant.default_code or "",
								'description'	: variant.description or "",
								'price'			: variant.with_context(pricelist=self.pricelist_name.id).price,
								'attributes'	: self.get_woocommerce_attribute_dict(variant),
				}
				if variant.length or variant.width or variant.height:
					dimensions = {
								u'width': str(variant.width) or "", 
								u'length': str(variant.length) or "" , 
								u'unit': str(variant.dimensions_uom_id.name) or "", 
								u'height': str(variant.height) or "",
							}
					variant_data['dimensions']=dimensions
				if variant.weight:
					variant_data['weight']= str(variant.weight)  or  ""
				if image_ids:
					variant_data.update({'image': {'id':image_ids[count]}})
				if woocommerce:
					try:
						return_dict = woocommerce.put("products/"+str(store_product_id)+"/variations/"+str(store_variant_id),variant_data).json()
						if 'message' in return_dict:
							raise UserError(_("Can't Update variant "+str(return_dict['message'])))
						count += 1
					except Exception as e:
						raise UserError(_("Can't Update variant "+str(e)))
			return count

	@api.multi
	def update_create_woocommerce_variable_product(self, template, product_map, product_dict, woocommerce):
		if woocommerce and template:
			product_dict.update({
								'name' 				: template.name,
								'images'			: self.create_woocommerce_product_image(template, True),
								'sku' 				: "",
								'regular_price'		: str(template.with_context(pricelist=self.pricelist_name.id).price) or "",
								'type'				: 'variable',
								'attributes'		: self.set_woocommerce_attribute_line(template),
								'default_attributes': self.get_woocommerce_attribute_dict(template.product_variant_ids[0]),
								'categories'		: self.set_woocommerce_product_categories(template),
								'short_description'	: template.description_sale  or "" ,
								'description'		: template.description or "",
								'price'				: template.with_context(pricelist=self.pricelist_name.id).price,
			})
			if template.length or template.width or template.height:
				dimensions = {
								u'width': str(template.width) or "", 
								u'length': str(template.length) or "" , 
								u'unit': str(template.dimensions_uom_id.name) or "", 
								u'height': str(template.height) or "",
							}
				product_dict['dimensions']=dimensions
			if template.weight:
				product_dict['weight']= str(template.weight)  or  ""
			try:
				return_dict  = woocommerce.put('products/'+str(product_dict['id']),product_dict).json()
				if 'message' in return_dict:
					raise UserError(_("Can't update product from simple to variable"+str(return_dict['message'])))
				else:
					image_ids = []
					for image in return_dict['images']:
						if image['position'] != 0:
							image_ids.append(image['id'])
					if image_ids:
						count = self.update_woocommerce_variation(return_dict['id'],template, product_map,woocommerce, image_ids)
					else:
						count = self.update_woocommerce_variation(return_dict['id'], template, product_map,woocommerce)
					if count:
						if image_ids:
							self.create_woocommerce_extra_variation(return_dict['id'], template, woocommerce ,  count, image_ids)
						else:
							self.create_woocommerce_extra_variation(return_dict['id'], template, woocommerce ,  count)
					return count
			except Exception as e:
				raise UserError(_("Can't update product from simple to variable"))

	@api.multi
	def create_woocommerce_extra_variation(self, store_product_id, template,woocommerce , count, image_ids=False):
		if store_product_id and woocommerce:
			if store_product_id and template:
				for variant in template.product_variant_ids:
					match_record = self.env['channel.product.mappings'].search([('erp_product_id','=',variant.id),('channel_id.id','=',self.id)])
					if not match_record:
						qty = variant._product_available()
						quantity = qty[variant.id]['qty_available'] - qty[variant.id]['outgoing_qty']
						variant_data = {
										'regular_price'	: str(variant.with_context(pricelist=self.pricelist_name.id).price) or "",
										'visible'		: True,
										'sku'			: variant.default_code or "",
										'stock_quantity': quantity,
										'description'	: variant.description or "",
										'price'			: variant.with_context(pricelist=self.pricelist_name.id).price,
										'manage_stock'	: True,
										'in_stock'		: True,
										'attributes'	: self.get_woocommerce_attribute_dict(variant),
									}
						if variant.length or variant.width or variant.height:
							dimensions = {
								u'width': str(variant.width) or "", 
								u'length': str(variant.length) or "" , 
								u'unit': str(variant.dimensions_uom_id.name) or "", 
								u'height': str(variant.height) or "",
							}
							variant_data['dimensions']=dimensions
						if variant.weight:
							variant_data['weight']= str(variant.weight)  or  ""
						if image_ids:
							variant_data.update({'image' : {'id':image_ids[count]},})
						if woocommerce:
							try:
								return_dict = woocommerce.post("products/"+str(store_product_id)+"/variations",variant_data).json()
								if 'message' in return_dict:
									raise  UserError("Error in Updation and Creation of variant during update"+str(return_dict['message']))
								count += 1
							except Exception as e:
								raise UserError("Error in Updation and Creation of variant during update"+str(e))
							if 	'id' in return_dict:
								mapping_dict = {
											'channel_id'		: self.id,
											'store_product_id'	: store_product_id,
											'store_variant_id'	: return_dict['id'],
											'odoo_template_id'	: template.id,
											'product_name'		: variant.id,
											'erp_product_id'	: variant.id,
											'default_code'		: variant.default_code or "",
											'operation'             : 'export'
								}
								obj = self.env['channel.product.mappings']
								self._create_mapping(obj, mapping_dict)
							else :
								raise UserError(_('Error in creating variant : '+str(return_dict['message'])))
				return count
			else:
				raise UserError(_('Error in creating variant'))
