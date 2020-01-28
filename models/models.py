# -*- coding: utf-8 -*-
import random

from odoo import models, fields, api, tools
from openerp.exceptions import ValidationError


class player(models.Model):
    _name = 'game.player'
    name = fields.Char()
    imagen = fields.Binary()
    image_small = fields.Binary(string='Imagen', compute='_get_images', store=True)
    casa = fields.Many2one('game.casa')
    reinos = fields.One2many('game.reino', 'jugador')
    reinosk = fields.One2many(related='reinos')  # Per al kanban
    recursos = fields.Many2many('game.recurso', compute='_get_recursos')
    raws = fields.One2many('game.raws', 'jugador')

    dinero = fields.Float(default=1000.0)

    @api.depends('imagen')
    def _get_images(self):
        for i in self:
            imagen = i.imagen
            data = tools.image_get_resized_images(imagen)
            i.image_small = data["image_small"]

    @api.depends('recursos')
    def _get_recursos(self):
        for player in self:
            player.recursos = player.reinos.mapped('recursos')

    @api.multi
    def create_new_reino(self):
        for p in self:
            f_template2 = self.env.ref('game.reino_template1')
            f_template = self.env.ref('game.reino_template' + str(random.randint(1, 9)))
            f = self.env['game.reino'].create({
                'name': f_template.name,
                'imagen': f_template2.imagen,
                'jugador': p.id,
            })
            c_template = self.env.ref('game.cantera')
            c = self.env['game.recurso'].create({
                'name': c_template.name,
                'imagen': c_template.imagen,
                'nivel': 1,
                'reino': f.id,
                'producciones': [(6,0,c_template.producciones.ids)],
            })
            print([(6, 0, c_template.producciones.ids)])
            for i in p.raws:
                i.unlink()
            r = self.env['game.raws'].create({
                'name': 'Piedra',
                'jugador': p.id,
                'raw': self.env.ref('game.piedra').id,
                'cantidad': 100
            })
            r = self.env['game.raws'].create({
                'name': 'Hierro',
                'jugador': p.id,
                'raw': self.env.ref('game.hierro').id,
                'cantidad': 10
            })

class casa(models.Model):
    _name = 'game.casa'
    name = fields.Char()
    imagen = fields.Binary()
    jugador = fields.Many2one('game.player')

class reino(models.Model):
    _name = 'game.reino'
    name = fields.Char()
    tipo = fields.Selection([('1', 'Reino del Norte'), ('2', 'Reino de la Montaña y del Valle'),
                             ('3', 'Reino de las Islas y los Ríos'), ('4', 'Reino de la Roca')
                             , ('5', 'Reino del Dominio'), ('6', 'Reino de las tormentas')
                             , ('7', 'Principado de Dorne'), ('8', 'Guardia de la noche')
                             , ('9', 'Al norte del muro')])
    jugador = fields.Many2one('game.player', ondelete='cascade')
    imagen = fields.Binary()
    image_small = fields.Binary(string='Imagen', compute='_get_images', store=True)
    recursos = fields.One2many('game.recurso','reino')
    personajes = fields.One2many('game.personaje','reino')
    available_resources = fields.Many2many('game.recurso', compute='_get_available_resources')

    @api.depends('imagen')
    def _get_images(self):
        for i in self:
            imagen = i.imagen
            data = tools.image_get_resized_images(imagen)
            i.image_small = data["image_small"]

    @api.multi
    def create_new_character(self):
        for p in self:
                c_template = self.env.ref('game.personaje_template' + str(random.randint(1, 15)))
                c = self.env['game.personaje'].create({
                'name': c_template.name,
                'imagen': c_template.imagen,
                'reino': p.id,
                'ataque': random.randint(1, 20),
                'defensa': random.randint(1, 20),
            })

    @api.multi
    def _get_available_resources(self):
        for f in self:
            print('aaa')
            r = self.env['game.recurso'].search([('template', '=', True)])
            f.available_resources = [(6, 0, r.ids)]

class reino_template(models.Model):
    _name = 'game.reino.template'
    name = fields.Char()
    imagen = fields.Binary()

class personaje(models.Model):
    _name = 'game.personaje'
    name = fields.Char()
    imagen = fields.Binary()
    vida = fields.Float(default=100, readonly=True)
    ataque = fields.Integer()
    defensa = fields.Integer()
    reino = fields.Many2one('game.reino',ondelete='cascade')
    start_date = fields.Date(default=lambda self: fields.Date.today())

    @api.onchange('ataque')
    def check_ataque(self):
        if self.ataque > 20:
            self.ataque = 20
            return{
                'warning':{
                    'title':"Atención!",
                    'message':"No puede tener mas de 20 en ataque!"
                }
            }

    @api.constrains('ataque')
    def _check_ataque(self):
        for record in self:
            if record.ataque > 20:
                raise ValidationError("Your record is too old: %s" % record.ataque)

class personaje_template(models.Model):
    _name = 'game.personaje.template'
    imagen = fields.Binary()
    name = fields.Char()
    casa = fields.Char()

class recurso(models.Model):
    _name = 'game.recurso'
    name = fields.Char()
    imagen = fields.Binary()
    producciones = fields.Many2many('game.raw')
    # o consumeix
    costes = fields.One2many('game.coste', 'recurso')
    duraciones = fields.One2many('game.duracion', 'recurso')
    costes_child = fields.One2many(related='parent.costes')
    duraciones_child = fields.One2many(related='parent.duraciones')
    parent = fields.Many2one('game.recurso', domain="[('template', '=', True)]")
    reino = fields.Many2one('game.reino' , ondelete='cascade')
    nivel = fields.Integer()
    template = fields.Boolean()


    @api.multi
    def build_it(self):

        for r in self:
            reino = self.env['game.reino'].browse(self.env.context['reino'])
            if 10 > len(reino.recursos):
                r.create({'name': r.name, 'imagen': r.imagen, 'reino': self.env.context['reino'],
                          'nivel': 1, 'template': False, 'producciones': [(6,0,r.producciones.ids)],
                          })

class coste(models.Model):
    _name = 'game.coste'
    name = fields.Char()
    recurso = fields.Many2one('game.recurso') # Que recurs
    nivel = fields.Integer() # Cal indicar el que consumeix en cada nivell
    raw = fields.Many2one('game.raw') # Que material
    coste = fields.Float()  #cost total

class duracion(models.Model):
    _name = 'game.duracion'
    name = fields.Char()
    recurso = fields.Many2one('game.recurso') # Que recurs
    nivel = fields.Integer() # Cal indicar el que tarda en cada nivell
    minutos = fields.Integer()  #cost total

class raw(models.Model):
    _name = 'game.raw'
    name = fields.Char()
    imagen = fields.Binary()

class raws(models.Model):
    _name = 'game.raws'
    name = fields.Char()
    jugador = fields.Many2one('game.player')
    raw = fields.Many2one('game.raw')
    cantidad = fields.Float()