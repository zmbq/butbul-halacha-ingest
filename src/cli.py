"""Top-level CLI to run pipeline steps.

Usage examples:
  python -m src.cli s01 --filter "הלכה יומית"
  python -m src.cli s04 --limit 10
  python -m src.cli all --limit 100
"""
from argparse import ArgumentParser

from .pipeline.s01_ingest_videos import ingest_videos
from .pipeline.s02_extract_metadata import extract_all_metadata
from .pipeline.s03_transcribe_with_whisper import transcribe_videos
from .pipeline.s04_populate_transcription_segments import populate_segments, clear_segments_table


def main():
    parser = ArgumentParser(prog='butbul', description='Butbul Halacha pipeline CLI')
    subparsers = parser.add_subparsers(dest='cmd', required=True)

    # s01
    p1 = subparsers.add_parser('s01', help='Ingest videos')
    p1.add_argument('--filter', type=str, default='הלכה יומית', help='Playlist name filter')

    # s02
    p2 = subparsers.add_parser('s02', help='Extract metadata')

    # s03
    p3 = subparsers.add_parser('s03', help='Transcribe with Whisper')
    p3.add_argument('--count', '-n', type=int, default=10, help='Max videos')
    p3.add_argument('--parallel', '-p', type=int, default=3, help='Parallel workers (max 5)')
    p3.add_argument('--delay', type=float, default=1.0, help='Delay between queuing videos')

    # s04
    p4 = subparsers.add_parser('s04', help='Populate transcription_segments')
    p4.add_argument('--limit', type=int, default=None, help='Limit number of transcripts to process')
    p4.add_argument('--dry-run', action='store_true', help='Dry run (no DB writes)')
    p4.add_argument('--clear', action='store_true', help='Clear transcription_segments table before importing')

    # all
    pall = subparsers.add_parser('all', help='Run s01..s04 in sequence')
    pall.add_argument('--limit', type=int, default=None, help='Limit number of transcripts for s04')
    pall.add_argument('--dry-run', action='store_true', help='Dry run for s04')

    args = parser.parse_args()

    if args.cmd == 's01':
        ingest_videos(playlist_filter=args.filter)
    elif args.cmd == 's02':
        extract_all_metadata()
    elif args.cmd == 's03':
        transcribe_videos(max_videos=args.count, delay_seconds=args.delay, parallel_workers=args.parallel)
    elif args.cmd == 's04':
        if args.clear and not args.dry_run:
            clear_segments_table()
        populate_segments(limit=args.limit, dry_run=args.dry_run, clear_flag=args.clear)
    elif args.cmd == 'all':
        ingest_videos()
        extract_all_metadata()
        transcribe_videos()
        if args.dry_run:
            print('DRY RUN: would run s04 with limit=', args.limit)
        else:
            if args.limit is not None:
                populate_segments(limit=args.limit)
            else:
                populate_segments()


if __name__ == '__main__':
    main()
