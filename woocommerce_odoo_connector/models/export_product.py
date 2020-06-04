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
from urllib import parse as urlparse
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
	def action_export_woocommerce_products(self):
		self.sudo().export_woocommerce_attributes_values()
		self.sudo().export_woocommerce_categories(0)
		woocommerce = self.get_woocommerce_connection()
		count = 0
		template_ids = []
		if 'active_ids' in self._context:
			if self._context['active_model'] == 'product.template':
				template_ids = self._context['active_ids']
			elif self._context['active_model'] == 'product.product':
				product_records = self.env['product.product'].browse(self._context['active_ids'])
				for product in product_records:
					template_ids.append(product.product_tmpl_id.id)
			else:
				raise UserError(_('Context Empty'))
		template_records = self.env['product.template'].browse(template_ids)
		for template in template_records:
			mapping_record = self.env['channel.template.mappings'].search([('odoo_template_id','=',template.id),('channel_id.id','=',self.id)])
			if not mapping_record:
				# if template.attribute_line_ids:
				# 	count += self.create_woocommerce_variable_product(template, woocommerce)
				# else:
				# 	count += self.create_woocommerce_simple_product(template, woocommerce)
				variable = 0
				if len(template.product_variant_ids)>1:
					variable = 1
				elif len(template.product_variant_ids) == 1:
					if template.product_variant_ids[0].attribute_value_ids:
						variable = 1
				if variable:
					count += self.create_woocommerce_variable_product(template, woocommerce)
				else:
					count += self.create_woocommerce_simple_product(template, woocommerce)
		return self.display_message(str(count)+" Products have been exported")

	# @api.multi
	# def set_woocommerce_image_path(self, name, data):
	# 	name = str(name)
	# 	name = name.replace('"','')
	# 	name = name.replace(" ","-")
	# 	base_url = self.env['ir.config_parameter'].get_param('web.base.url')
	# 	direct = os.path.abspath(os.path.join(os.path.realpath(__file__+'/../'), os.pardir))
	# 	f = open(direct+'/static/img/'+name+'.png','wb')
	# 	f.write(base64.decodestring(data))
	# 	f.close
	# 	url = base_url+"/woocommerce_odoo_connector/static/img/"+name+".png"
	# 	return url,name

	@api.multi
	def set_woocommerce_image_path(self, name, product):
		base_url = self.env['ir.config_parameter'].get_param('web.base.url')
		image_url = '/channel/image/product.product/%s/image/492x492.png'%(product.id)
		full_image_url = '%s' % urlparse.urljoin(base_url,image_url)
		return full_image_url,name

	@api.multi
	def create_woocommerce_product_image(self, template, variant = False):
		if template.image:
			image_list = []
			count = 0
			template_url,name = self.set_woocommerce_image_path(template.name, template.product_variant_ids[0])
			image_list.append({
				'src'		: template_url,
				'name'		: name,
				'position'	: 0,
			})
			if variant:
				for variation in template.product_variant_ids:
					count += 1
					variant_url,name = self.set_woocommerce_image_path(variation.name+str(count),variation)
					image_list.append({
						'src'		: variant_url,
						'name'		: name,
						'position'	: count,
					})
			return image_list

	@api.multi
	def get_woocommerce_attribute_dict(self, variant):
		if variant:
			attribute_dict = []
			if variant.attribute_value_ids:
				for attribute_line in variant.attribute_value_ids:
					attr_name,attr_id  = self.get_woocommerce_attribute(attribute_line.attribute_id)
					value_name = attribute_line.name
					attribute_dict.append({
										'id'	: attr_id,
										'name'	: attr_name,
										'option': value_name,
					})
				return attribute_dict

	@api.multi
	def get_woocommerce_attribute_value(self, attribute_line):
		value_list = []
		if attribute_line:
			for value in attribute_line.value_ids:
				value_list.append(value.name)
		return value_list

	@api.multi
	def get_woocommerce_attribute(self, attribute_id):
		if  attribute_id:
			record  =  self.env['channel.attribute.mappings'].search([('odoo_attribute_id','=',attribute_id.id),('channel_id.id','=',self.id)])
			if record:
				return attribute_id.name,record.store_attribute_id
			else:
				return self.export_woocommerce_attribute_values_by_id(attribute_id)

	@api.multi
	def set_woocommerce_attribute_line(self, template):
		attribute_list = []
		attribute_count = 0
		if template.attribute_line_ids:
			for attribute_line in template.attribute_line_ids:
				attr_name,attr_id = self.get_woocommerce_attribute(attribute_line.attribute_id)
				values = self.get_woocommerce_attribute_value(attribute_line)
				attribute_dict = {
								'name'		: attr_name,
								'id'		: attr_id,
								'variation'	: True,
								'visible'	: True,
								'position'	: attribute_count,
								'options'	: values,
				}
				attribute_count += 1
				attribute_list.append(attribute_dict)
		return attribute_list


	@api.multi
	def create_woocommerce_variation(self, woo_product_id, template, woocommerce, image_ids = False):
		count = 0
		if woo_product_id and template:
			for variant in template.product_variant_ids:
				match_record = self.env['channel.product.mappings'].search([('product_name','=',variant.id),('channel_id.id','=',self.id)])
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
										u'width': str(variant.width)  or "", 
										u'length': str(variant.length)  or "", 
										u'unit': str(variant.dimensions_uom_id.name)  or "", 
										u'height': str(variant.height)  or "",
									}
						variant_data['dimensions']=dimensions
					if variant.weight:
						variant_data['weight']= str(variant.weight)  or  ""
					if image_ids:
						variant_data.update({'image': {'id':image_ids[count]}})
					if woocommerce:
						return_dict = woocommerce.post("products/"+str(woo_product_id)+"/variations",variant_data).json()
						count += 1
						if 	'id' in return_dict:
							mapping_dict = {
										'channel_id'		: self.id,
										'store_product_id'	: woo_product_id,
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
							raise UserError(_('Error in creating variant'))
			return count
		else:
			raise UserError(_('Error in creating variant'))

	@api.multi
	def create_woocommerce_variable_product(self, template, woocommerce):
		if template:
			product_dict = {
						'name'				: template.name,
						'sku' 				: "",
						'images'			: self.create_woocommerce_product_image(template,True),
						'type'				: 'variable',
						'categories'		: self.set_woocommerce_product_categories(template),
						'status'			: 'publish',
						'manage_stock'		: False,
						'attributes'		: self.set_woocommerce_attribute_line(template),
						'default_attributes': self.get_woocommerce_attribute_dict(template.product_variant_ids[0]),
						'short_description'	: template.description_sale  or "",
						'description'		: template.description  or "",
			}
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
			if woocommerce:
				return_dict  = woocommerce.post('products',product_dict).json()
				image_ids = []
				if 'images' in return_dict:
					for image in return_dict['images']:
						if image['position'] != 0:
							image_ids.append(image['id'])
				if 'id' in return_dict:
					mapping_dict = {
								'channel_id'		: self.id,
								'store_product_id'	: return_dict['id'],
								'odoo_template_id'	: template.id,
								'template_name'		: template.id,
								'default_code'		: template.default_code or "",
								'operation'             : 'export'
					}
					obj = self.env['channel.template.mappings']
					self._create_mapping(obj, mapping_dict)
					if image_ids:
						count = self.create_woocommerce_variation(return_dict['id'], template, woocommerce, image_ids)
					else:
						count = self.create_woocommerce_variation(return_dict['id'], template, woocommerce)
					if count:
						return count
				else:
					raise UserError(_("Error in Creating Variable product"))

	@api.multi
	def create_woocommerce_simple_product(self, template, woocommerce):
		if template:
			record = self.env['product.product'].search([('product_tmpl_id','=',template.id)])
			qty = record._product_available()
			quantity = qty[template.product_variant_ids[0].id]['qty_available'] - qty[template.product_variant_ids[0].id]['outgoing_qty']
			product_dict = {
						'name'				: template.name,
						'sku' 				: template.default_code or "",
						'regular_price'		: str(template.with_context(pricelist=self.pricelist_name.id).price) or "",
						'type'				: 'simple',
						'categories'		: self.set_woocommerce_product_categories(template),
						'status'			: 'publish',
						'short_description'	: template.description_sale  or "" ,
						'description'		: template.description or "",
						'attributes'		: self.set_woocommerce_attribute_line(template),
						'price'				: template.with_context(pricelist=self.pricelist_name.id).price,
						'manage_stock'		: True,
						'stock_quantity'	: quantity,
						'in_stock'			: True,
			}
			if template.image:
				product_dict['images'] = self.create_woocommerce_product_image(template)
			if template.length or template.width or template.height:
				dimensions = {
								u'width': str(template.width)  or "", 
								u'length': str(template.length)  or "", 
								u'unit': str(template.dimensions_uom_id.name)  or "", 
								u'height': str(template.height)  or "",
							}
				product_dict['dimensions']=dimensions
			if template.weight:
				product_dict['weight']=str(template.weight)
			if woocommerce:
				return_dict  = woocommerce.post('products',product_dict).json()
			if 	'id' in return_dict:
				mapping_dict = {
							'channel_id'		: self.id,
							'store_product_id'	: return_dict['id'],
							'odoo_template_id'	: template.id,
							'template_name'		: template.id,
							'default_code'		: template.default_code or "",
							'operation'             : 'export'
				}
				obj = self.env['channel.template.mappings']
				self._create_mapping(obj, mapping_dict)
				mapping_dict = {
							'channel_id'		: self.id,
							'store_product_id'	: return_dict['id'],
							'odoo_template_id'	: template.id,
							'product_name'		: template.product_variant_ids[0].id,
							'erp_product_id'	: template.product_variant_ids[0].id,
							'default_code'		: template.product_variant_ids[0].default_code or "",
							'operation'             : 'export'
				}
				obj = self.env['channel.product.mappings']
				self._create_mapping(obj, mapping_dict)
				return 1
			else:
				raise UserError(_('Simple Product Creation Failed'))
		raise UserError(_('Simple Product Creation Failed'))

	@api.multi
	def set_woocommerce_product_categories(self, template):
		categ_list = []
		if template.categ_id:
			rec  =  self.env['channel.category.mappings'].search([('odoo_category_id','=',template.categ_id.id),('channel_id.id','=',self.id)])
			if rec:
				categ_list.append({'id':rec.store_category_id})
			else:
				cat_id = self.export_woocommerce_categories_id(template.categ_id)
				categ_list.append({'id':cat_id})
		if template.channel_category_ids:
			for category_channel in template.channel_category_ids:
				if category_channel.instance_id.id == self.id:
					for category in category_channel.extra_category_ids:
						record = self.env['channel.category.mappings'].search([('odoo_category_id','=',category.id),('channel_id.id','=',self.id)])
						if record:
							categ_list.append({'id':record.store_category_id})
						else:
							cat_id = self.export_woocommerce_categories_id(template.categ_id)
							categ_list.append({'id':cat_id})
		# else:	
		# 	if template.categ_id.channel_category_ids:
		# 		for category_channel in template.categ_id.channel_category_ids:
		# 			if category_channel.instance_id.id == self.id:
		# 				for category in category_channel.extra_category_ids:
		# 					record = self.env['channel.category.mappings'].search([('odoo_category_id','=',category.id),('channel_id.id','=',self.id)])
		# 					if record:
		# 						categ_list.append({'id':record.store_category_id})
		return categ_list

	@api.multi
	def export_woocommerce_product(self):
		# self.export_woocommerce_attributes_values()
		# self.export_woocommerce_categories(0)
		# message = self.export_update_woocommerce_product()
		message =""
		woocommerce = self.get_woocommerce_connection()
		count = 0
		template_records =  self.env['product.template'].search([('type','=','product'),('sale_ok','=',True)])
		for template in template_records:
			mapping_record = self.env['channel.template.mappings'].search([('odoo_template_id','=',template.id),('channel_id.id','=',self.id)])
			if not mapping_record:
				variable = 0
				if len(template.product_variant_ids)>1:
					variable = 1
				elif len(template.product_variant_ids) == 1:
					if template.product_variant_ids[0].attribute_value_ids:
						variable = 1
				if variable:
					count += self.create_woocommerce_variable_product(template, woocommerce)
				else:
					count += self.create_woocommerce_simple_product(template, woocommerce)
		message += 	str(count)+" Products have been exported"
		return self.display_message(message)
