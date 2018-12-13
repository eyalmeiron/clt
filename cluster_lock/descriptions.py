class Descriptions(object):

    info = [
        'Lock is busy, starting watcher',
        'Got an acquire',
        'Got release request',
        'Lock is busy, starting watcher',
        'Lock is busy, but not waiting as no watcher requested',
        'Got peek request',
    ]

    successes = [
        'Lock acquired',
        'Succeeded to set holders. Start function',
        'Lock released successfully',
        'Successfully peek lock',
    ]

    fails = [
        'The timeout of the watcher expired',
        'New max holders differ from the current max holders value',
        'This lock is already acquired by this holder',
        'Attempt to increase remaining holders over the allowed limit',
        'Failed to remove holder from holders list',
        'Got release for unknown lock',
        'Failed peek lock',
    ]
