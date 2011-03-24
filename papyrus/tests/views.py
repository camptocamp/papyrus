# a fake view module for the purpose of the tests

from pyramid.view import view_config

@view_config(route_name='prefix_read_many', renderer='geojson')
def read_many(request):
    """ """

@view_config(route_name='prefix_read_one', renderer='geojson')
def read_one(request):
    """ """

@view_config(route_name='prefix_count', renderer='string')
def count(request):
    """ """

@view_config(route_name='prefix_create', renderer='geojson')
def create(request):
    """ """

@view_config(route_name='prefix_update', renderer='geojson')
def update(request):
    """ """

@view_config(route_name='prefix_delete')
def delete(request):
    """ """
