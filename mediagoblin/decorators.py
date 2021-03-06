# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011, 2012 MediaGoblin contributors.  See AUTHORS.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from functools import wraps

from urlparse import urljoin
from werkzeug.exceptions import Forbidden
from werkzeug.urls import url_quote

from mediagoblin.db.models import MediaEntry, User
from mediagoblin.tools.response import redirect, render_404


def require_active_login(controller):
    """
    Require an active login from the user.
    """
    @wraps(controller)
    def new_controller_func(request, *args, **kwargs):
        if request.user and \
                request.user.get('status') == u'needs_email_verification':
            return redirect(
                request, 'mediagoblin.user_pages.user_home',
                user=request.user.username)
        elif not request.user or request.user.get('status') != u'active':
            next_url = urljoin(
                    request.urlgen('mediagoblin.auth.login',
                        qualified=True),
                    request.url)

            return redirect(request, 'mediagoblin.auth.login',
                            next=url_quote(next_url))

        return controller(request, *args, **kwargs)

    return new_controller_func

def active_user_from_url(controller):
    """Retrieve User() from <user> URL pattern and pass in as url_user=...

    Returns a 404 if no such active user has been found"""
    @wraps(controller)
    def wrapper(request, *args, **kwargs):
        user = User.query.filter_by(username=request.matchdict['user']).first()
        if user is None:
            return render_404(request)

        return controller(request, *args, url_user=user, **kwargs)

    return wrapper


def user_may_delete_media(controller):
    """
    Require user ownership of the MediaEntry to delete.
    """
    @wraps(controller)
    def wrapper(request, *args, **kwargs):
        uploader_id = MediaEntry.query.get(request.matchdict['media']).uploader
        if not (request.user.is_admin or
                request.user.id == uploader_id):
            raise Forbidden()

        return controller(request, *args, **kwargs)

    return wrapper


def user_may_alter_collection(controller):
    """
    Require user ownership of the Collection to modify.
    """
    @wraps(controller)
    def wrapper(request, *args, **kwargs):
        creator_id = request.db.User.find_one(
            {'username': request.matchdict['user']}).id
        if not (request.user.is_admin or
                request.user.id == creator_id):
            raise Forbidden()

        return controller(request, *args, **kwargs)

    return wrapper


def uses_pagination(controller):
    """
    Check request GET 'page' key for wrong values
    """
    @wraps(controller)
    def wrapper(request, *args, **kwargs):
        try:
            page = int(request.GET.get('page', 1))
            if page < 0:
                return render_404(request)
        except ValueError:
            return render_404(request)

        return controller(request, page=page, *args, **kwargs)

    return wrapper


def get_user_media_entry(controller):
    """
    Pass in a MediaEntry based off of a url component
    """
    @wraps(controller)
    def wrapper(request, *args, **kwargs):
        user = request.db.User.find_one(
            {'username': request.matchdict['user']})

        if not user:
            return render_404(request)
        media = request.db.MediaEntry.find_one(
            {'slug': request.matchdict['media'],
             'state': u'processed',
             'uploader': user.id})

        # no media via slug?  Grab it via object id
        if not media:
            media = MediaEntry.query.filter_by(
                    id=request.matchdict['media'],
                    state=u'processed',
                    uploader=user.id).first()
            # Still no media?  Okay, 404.
            if not media:
                return render_404(request)

        return controller(request, media=media, *args, **kwargs)

    return wrapper


def get_user_collection(controller):
    """
    Pass in a Collection based off of a url component
    """
    @wraps(controller)
    def wrapper(request, *args, **kwargs):
        user = request.db.User.find_one(
            {'username': request.matchdict['user']})

        if not user:
            return render_404(request)

        collection = request.db.Collection.find_one(
            {'slug': request.matchdict['collection'],
             'creator': user.id})

        # Still no collection?  Okay, 404.
        if not collection:
            return render_404(request)

        return controller(request, collection=collection, *args, **kwargs)

    return wrapper


def get_user_collection_item(controller):
    """
    Pass in a CollectionItem based off of a url component
    """
    @wraps(controller)
    def wrapper(request, *args, **kwargs):
        user = request.db.User.find_one(
            {'username': request.matchdict['user']})

        if not user:
            return render_404(request)

        collection = request.db.Collection.find_one(
            {'slug': request.matchdict['collection'],
             'creator': user.id})

        collection_item = request.db.CollectionItem.find_one(
            {'id': request.matchdict['collection_item'] })

        # Still no collection item?  Okay, 404.
        if not collection_item:
            return render_404(request)

        return controller(request, collection_item=collection_item, *args, **kwargs)

    return wrapper


def get_media_entry_by_id(controller):
    """
    Pass in a MediaEntry based off of a url component
    """
    @wraps(controller)
    def wrapper(request, *args, **kwargs):
        media = MediaEntry.query.filter_by(
                id=request.matchdict['media'],
                state=u'processed').first()
        # Still no media?  Okay, 404.
        if not media:
            return render_404(request)

        return controller(request, media=media, *args, **kwargs)

    return wrapper
