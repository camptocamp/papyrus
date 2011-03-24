# a fake view module for the purpose of the tests

from pyramid.view import view_config

@view_config(renderer='geojson')
def read_many(request):
    """ """

@view_config(renderer='geojson')
def read_one(request):
    """ """

@view_config(renderer='string')
def count(request):
    """ """

@view_config(renderer='geojson')
def create(request):
    """ """

@view_config(renderer='geojson')
def update(request):
    """ """

@view_config()
def delete(request):
    """ """
