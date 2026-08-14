{
    'name': 'La Casa Nueva',
    'version': '18.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Modificar stock manualmente en productos para usuarios asociados',
    'description': """
        Módulo La Casa Nueva para Odoo 18
        =================================
        Este módulo permite:
        - Modificar el stock de productos manualmente
        - Sincronizar stock con la plantilla del sitio web
        - Restringir operación solo a usuarios asociados
        - Actualización directa desde la ficha del producto
    """,
    'author': 'La Casa Nueva',
    'website': 'https://www.lacasanueva.com',
    'depends': [
        'base',
        'stock',
        'product',
        'website_sale',
        'sale_management',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_users_views.xml',
        'views/product_template_views.xml',
        'views/product_product_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'assets': {
        'web.assets_backend': [],
    },
}