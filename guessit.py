from __future__ import unicode_literals, division, absolute_import
import logging

from flexget import plugin
from flexget.event import event


log = logging.getLogger('guessit')

#TODO populate more entry fields with guessit fields

class PluginGuessIt(object):
    def on_task_start(self, task, config):
        try:
            import guessit
        except:
            log.debug('Error importing GuessIt: %s' % e)
            raise plugin.DeprecationWarning('guessit', 'guessit',
                    'guessit module required. ImportError: %s' % e)

    def validator(self):
        from flexget import validator
        return validator.factory('boolean')

    @plugin.priority(125)
    def on_task_metainfo(self, task, config):
        import guessit
        if not config:
            return
        for entry in task.entries:
            guess = guessit.guess_file_info(entry['location'], 'autodetect')
            if 'series_id_type' in entry:
                if entry['series_id_type'] == 'sequence':
                    if guess['type'] == 'episode':
                        log.verbose('Found a GuessIt match for %s S%02dE%02d' % (guess['series'], guess['season'], guess['episodeNumber']))
                        entry['series_id'] = 'S%02dE%02d' % (guess['season'], guess['episodeNumber'])
                        entry['series_season'] = guess['season']
                        entry['series_episode'] = guess['episodeNumber']
                        entry['series_episodes'] = guess['episodeNumber']
                        entry['series_id_type'] = 'ep'
                        if 'series_name' not in entry:
                            log.verbose('Added series name name: %s' % (guess['series']))
                            entry['series_name'] =  guess['series']
            if 'series_id_type' not in entry:
                #need to check and properly map out
                #need to add other fields
                if 'season' in guess and 'episode' in guess:
                    entry['series_id'] = 'S%02dE%02d' % (guess['season'], guess['episodeNumber'])
                    entry['series_season'] = guess['season']
                    entry['series_episode'] = guess['episodeNumber']
                    entry['series_episodes'] = guess['episodeNumber']
                    entry['series_id_type'] = 'ep'
                if 'series' in guess:
                    entry['series_name'] =  guess['series']
                if 'screenSize' in guess:
                    entry['quality'].resolution = guess['screenSize']
                if 'format' in guess:
                    entry['quality'].source = guess['format']
                if 'videoCodec' in guess:
                    entry['quality'].codec = guess['videoCodec']
                if 'audioCodec' in guess:
                    entry['quality'].audio = guess['audioCodec']
                    log.verbose(guess)


@event('plugin.register')
def register_plugin():
    plugin.register(PluginGuessIt, 'guessit', api_ver=2)
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
