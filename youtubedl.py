from __future__ import unicode_literals, division, absolute_import
import logging

from flexget import plugin
from flexget.event import event
from flexget.utils.template import RenderError
from flexget.utils.pathscrub import pathscrub


log = logging.getLogger('youtubedl')


class PluginYoutubeDL(object):
    """
    Download videos using YoutubeDL
    (https://github.com/rg3/youtube-dl)

    Example::

      youtubedl:
        username: my_username
        password: my_password
        videopassword: my_videopassword
        format: best
        template: {{ title }}.%(ext)s
        path: ~/downloads/

    All parameters::

      youtubedl:
        username: ...
        password: ...
        videopassword: ...
        format: ...
        template: ...
        path: ...
    """
    #TODO: add more options which will be passed to youtube-dl
    #FIXME: youtube-dl fails when falling back to generic download method
    schema = {
        'type': 'object',
        'properties': {
            'username': {'type': 'string'},
            'password': {'type': 'string'},
            'format': {'type': 'string', 'default': 'best'},
            'template': {'type': 'string', 'default': '%(title)s-%(id)s.%(ext)s'},
            'videopassword': {'type': 'string'},
            'path': {'type': 'string', 'format': 'path'},
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
                raise ExtractorError(message)

            def process_info(self, info_dict):
                self.processed_info_dicts.append(info_dict)
                return super(YoutubeDL, self).process_info(info_dict)
        for entry in task.accepted:
            if task.options.test:
                log.info('Would download %s' % entry['title'])
            else:
                try:
                    outtmpl = entry.render(config['path']) + '/' + pathscrub(entry.render(config['template']) + '.%(ext)s', filename=True)
                    log.info("Output file: %s" % outtmpl)
                except RenderError as e:
                    log.error('Error setting output file: %s' % e)
                    entry.fail('Error setting output file: %s' % e)
                params = {'quiet': True, 'outtmpl': outtmpl}
                if 'username' in config and 'password' in config:
                    params.update({'username': config['username'], 'password': config['password']})
                elif 'username' in config or 'password' in config:
                    log.error('Both username and password is required')
                if 'videopassword' in config:
                    params.update({'videopassword': config['videopassword']})
                if 'title' in config:
                    params.update({'title': config['title']})
                ydl = YoutubeDL(params)
                ydl.add_default_info_extractors()
                log.info('Downloading %s' % entry['title'])
                try:
                    ydl.download([entry['url']])
                except ExtractorError as e:
                    log.error('Youtube-DL was unable to download the video. Error message %s' % e.message)
                    entry.fail('Youtube-DL was unable to download the video. Error message %s' % e.message)
                except Exception as e:
                    log.error('Youtube-DL failed. Error message %s' % e.message)
                    entry.fail('Youtube-DL failed. Error message %s' % e.message)


@event('plugin.register')
def register_plugin():
    plugin.register(PluginYoutubeDL, 'youtubedl', api_ver=2)
