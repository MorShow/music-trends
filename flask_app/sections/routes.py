import os
import json

from flask import Blueprint, render_template

sections_bp = Blueprint('sections', __name__, url_prefix='/sections')


@sections_bp.route('/')
def sections():
    return render_template('sections.html')


@sections_bp.route('/spotify')
def spotify():
    figures = []
    for f in os.listdir('static/figures/spotify/'):
        with open('static/figures/spotify/' + f, 'rb') as json_fig:
            figures.append(json.load(json_fig))
    return render_template('spotify.html', graphs=figures)


@sections_bp.route('/itunes')
def itunes():
    figures = []
    for f in os.listdir('static/figures/itunes/'):
        with open('static/figures/itunes/' + f, 'rb') as json_fig:
            figures.append(json.load(json_fig))
    return render_template('itunes.html', graphs=figures)


@sections_bp.route('/apple_music')
def apple_music():
    figures = []
    for f in os.listdir('static/figures/apple_music/'):
        with open('static/figures/apple_music/' + f, 'rb') as json_fig:
            figures.append(json.load(json_fig))
    return render_template('apple_music.html', graphs=figures)


@sections_bp.route('/radio_youtube')
def radio():
    figures = []
    for f in os.listdir('static/figures/radio_youtube/'):
        with open('static/figures/radio_youtube/' + f, 'rb') as json_fig:
            figures.append(json.load(json_fig))
    return render_template('radio_youtube.html', graphs=figures)
