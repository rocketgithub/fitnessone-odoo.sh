# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
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
#
#################################################################################
{
  "name"                 :  "Odoo Multi-Channel Sale",
  "summary"              :  "Manage Multiple Marketplace and eCommerce Platform Channel (like CS-Cart, WooCommerce, PrestaShop, Magento, Amazon, eBay, Etsy, Cdiscount  and many more) using a single interface.",
  "category"             :  "Website",
  "version"              :  "0.1.6",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/Odoo-Multi-Channel-Sale.html",
  "description"          :  """https://webkul.com/blog/odoo-multi-channel-sale/,
                              Odoo Multi-Channel Sale Bridge  is the  Odoo Extension to connect  Odoo with multiple marketplace and eCommerce Platform.
                              At present it's provice connector support for these Marketplace and eCommerce Platform:
                                Amazon Connector (Marketplace) ,
                                Ebay Connector (Marketplace),
                                Etsy Connector (Marketplace),
                                WooCommerce Connector (Ecommerce Platform),
                                PrestaShop Connector (Ecommerce Platform),
                                CS-Cart Connector (Ecommerce Platform),
                                Magento1.9 Connector (Magento 1.9 and older) and Magento2.0 Connector (Magento 2.0 and newer) Ecommerce Platform.
                               .""",
  "live_test_url"        :  "",
  "depends"              :  [
                             'account_invoicing',
                             'delivery',
                            ],
  "data"                 :  [
                             'security/security.xml',
                             'security/ir.model.access.csv',
                             'wizard/wizard_view.xml',
                             'wizard/feeds_wizard_view.xml',
                             'views/template.xml',
                             'views/res_config_view.xml',
                             'views/multi_channel_sale_view.xml',
                             'views/channel_syncronization_view.xml',
                             'views/category_skeleton_view.xml',
                             'views/account_skeleton_view.xml',
                             'views/product_skeleton_view.xml',
                             'views/partner_skeleton_view.xml',
                             'views/order_skeleton_view.xml',
                             'views/pricelist_skeleton_view.xml',
                             'wizard/export_products_wizard_view.xml',
                             'wizard/export_templates_wizard_view.xml',
                             'wizard/export_categ_wizard_view.xml',
                             'views/shipping_skeleton_view.xml',
                             'views/inherits.xml',
                             'views/feeds_view.xml',
                             'views/shipping_feed_view.xml',
                             'views/multi_channel_skeleton_view.xml',
                             'views/order_feed_view.xml',
                             'views/attribute_value_skeleton.xml',
                             'views/menu_items.xml',
                             'data/server_action.xml',
                             'data/demo.xml',
                             'data/cron.xml',
                            ],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "price"                :  99,
  "currency"             :  "EUR",
  "pre_init_hook"        :  "pre_init_check",
}
