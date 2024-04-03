import imp
import os
from django.core.management.base import BaseCommand
from tweets.models import Media
from moviepy.editor import VideoFileClip
from django.db.models import Q
from django.core.files import File


class Command(BaseCommand):
    help = 'Generate thumbnails for Media objects with null or empty thumbnails'

    def handle(self, *args, **options):
        media_entries = Media.objects.filter(Q(thumbnail__isnull=True) | Q(thumbnail=""))  # Filter for entries with null thumbnails
    
        for media in media_entries:
            print(media.id)
            if media.file.name.endswith('.mp4'):
                video_path = media.file.path
                thumbnail_path = video_path.replace('.mp4', '.jpg')

                try:
                    # Extract a frame at a specific time (e.g., 5 seconds) as a thumbnail
                    clip = VideoFileClip(video_path)
                    clip.save_frame(thumbnail_path, t=0)

                    # Save the generated thumbnail to the media file
                    thumbnail_name = media.file.name.replace(".mp4", ".jpg")
                    media.thumbnail.save(thumbnail_name, File(open(thumbnail_path, 'rb')))

                    # Clean up the temporary frame
                    os.remove(thumbnail_path)

                    self.stdout.write(self.style.SUCCESS(f'Generated thumbnail for Media ID {media.id}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Failed to generate thumbnail for Media ID {media.id}: {str(e)}'))

