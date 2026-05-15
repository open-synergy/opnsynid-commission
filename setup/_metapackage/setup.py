import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo11-addons-open-synergy-opnsynid-commission",
    description="Meta package for open-synergy-opnsynid-commission Odoo addons",
    version=version,
    install_requires=[
        'odoo11-addon-commission',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 11.0',
    ]
)
