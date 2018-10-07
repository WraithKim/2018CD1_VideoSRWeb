from django.apps import AppConfig


class VideosrConfig(AppConfig):
    name = 'videosr'
    
    def ready(self):
        import videosr.signals
        
