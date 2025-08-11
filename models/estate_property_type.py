from odoo import models, fields

class EstatePropertyType(models.Model):
    _name = 'estate.property.type'
    _description = 'Estate Property Type'
    
    name = fields.Char(string="Name", required=True)
    
    property_ids = fields.One2many('estate.property', 'property_type_id', string="Properties")
    
    _sql_constraints = [
        ('unique_property_type_name', 'UNIQUE(name)', 'The property type name must be unique.')
    ]