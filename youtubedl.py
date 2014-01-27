from __future__ import unicode_literals, division, absolute_import
import logging

from flexget import plugin
from flexget.event import event


log = logging.getLogger('youtubedl')


class PluginYoutubeDL(object):
    """
    Download videos using YoutubeDL
    (https://github.com/rg3/youtube-dl)

    Example (complete task):
    """

    schema = {
        'type': 'object',
        'properties': {
            'username': {'type': 'string'},
            'password': {'type': 'string'},
            'format': {'type': 'string', 'default': 'best'},
            'template': {'type': 'string', 'default': '%(title)s-%(id)s.%(ext)s'},
            'videopassword': {'type': 'string'},
            'path': {'type': 'string', 'format': 'path'},
            'title': {'type': 'string'},
        },
        'required': ['path']
    }

    def on_task_start(self, task, config):
        try:
            import youtube_dl  # NOQA
        except ImportError as e:
            log.debug('Error importing YoutubeDL: %s' % e)
            raise plugin.DependencyError('youtubedl', 'youtubedl',
                                         'youtubedl module required. ImportError: %s' % e)

    def on_task_output(self, task, config):
        import youtube_dl.YoutubeDL
        from youtube_dl.utils import ExtractorError

        class YoutubeDL(youtube_dl.YoutubeDL):
            def __init__(self, *args, **kwargs):
                self.to_stderr = self.to_screen
                self.processed_info_dicts = []
                super(YoutubeDL, self).__init__(*args, **kwargs)

            def report_warning(self, message):
                # Don't accept warnings during tests
                raise ExtractorError(message)

            def process_info(self, info_dict):
                self.processed_info_dicts.append(info_dict)
                return super(YoutubeDL, self).process_info(info_dict)
        #TODO: evalutate jinja strings
        params = {'quiet': True,
                  'outtmpl': '%s/%s' % (config['path'], config['template'])}
        if 'username' in config and 'password' in config:
            params.update({'username': config['username'],
                           'password': config['password']})
        elif 'username' in config or 'password' in config:
            log.error('Both username and password is required')
        if 'videopassword' in config:
            params.update({'videopassword': config['videopassword']})
        if 'title' in config:
            params.update({'title': config['title']})
        ydl = YoutubeDL(params)
        ydl.add_default_info_extractors()
        log.verbose(params)
        for entry in task.accepted:
            log.verbose([entry['url']])
            if task.option.test:
                log.info('Would download %s and save as %s' % (entry['url'], params['outtmpl']))
            else:
                try:
                    ydl.download([entry['url']])
                except ExtractorError as e:
                    log.error('Youtube-DL was unable to download the video. Error message %s' % e.message)
                except Exception as e:
                    log.error('Youtube-DL failed. Error message %s' % e.message)


@event('plugin.register')
def register_plugin():
    plugin.register(PluginYoutubeDL, 'youtubedl', api_ver=2)
