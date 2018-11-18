import subprocess
import simplejson
import colorama
import sys

full_time = True

descriptions = [
	'Lock is busy, starting watcher',
	'Got an acquire', 
	'Got release request',
	'Lock is busy, starting watcher',
	'Lock is busy, but not waiting as no watcher requested',
	# 'Failed to release lock',
]

successes = [
	'Lock acquired',
	'Succeeded to set holders. Start function',
	'Lock released successfully',
]

fails = [
	'The timeout of the watcher expired',
	'New max holders differ from the current max holders value',
	'This lock is already acquired by this holder',
	'Attempt to increase remaining holders over the allowed limit',
	'Failed to remove holder from holders list',
	'Got release for unknown lock',
]

# attribute to not display. when dict then ignore only with this value
ignored_more_attributes = [
	'lockName',
	'holders',
	'newHolders',
	'remainingHolders',
	'holderId',
	'maxHolders',
	{'timeout': '0s'},
	'key',
	'stringNewHolders',
	'stringPrevHolders',
	'openWatch',
	{'allowMultipleAcquire': 'true'},
]

colors = [
	'yellow',
	'black', 
	'cyan',
	'magenta',
	'white',
	'reset',
	'blue',
	'red',
	'green',
]

def run_command(command):
    process = subprocess.Popen(['/bin/bash', '-c', command],
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)

    out, err = process.communicate()
    return out, err, process.returncode

def colorize(text, color):
    color = getattr(colorama.Fore, color.upper())
    reset_color = colorama.Fore.BLUE
    return u'{0}{1}{2}'.format(color, text, reset_color)

def colorize_holders(holders):
	if holders == '':
		return ''
	return ''.join([colorize('[', 'RESET'), holders[1:-1], colorize(']', 'RESET')])

def print_lock(lock_name):
	i = 0
	holders_colors = {}
	for holder in locks[lock_name]['holders']:
		holders_colors[holder] = colors[i]
		i = (i + 1) % len(colors)
	max_holders = locks[lock_name]['max_holders']
	if max_holders == -1:
		print '\n{0}'.format(colorize(lock_name, 'white'))
	else:
		print '\n{0} (max holders {1})'.format(colorize(lock_name, 'white'), locks[lock_name]['max_holders'])

	# if not found holders at all to this lock
	if locks[lock_name]['holders'] == set([None]):
		max_len_holder_id = 10
	else:
		max_len_holder_id = max(map(lambda holder_id: len(holder_id), locks[lock_name]['holders']))
	max_len_description = max(map(lambda record: len(record['description']), locks[lock_name]['records']))
	max_len_holders = max(map(lambda record: len(str(record['holders'])), locks[lock_name]['records']))

	for record in locks[lock_name]['records']:

		when = record['when'] if full_time else record['when'][11:-3]
		holder_id = colorize(record['holder_id'], holders_colors[record['holder_id']])
		description = record['description']

		attributes = record['more']
		holders = colorize_holders(record['holders'])

		string_attributes = ''
		for attribute in attributes:
			string_attributes += '{0}{1}{2}{3}'.format(attribute, 
													   colorize('=', 'reset'),
													   attributes[attribute],
													   colorize(' | ', 'reset'))
		attributes = colorize_holders('[{0}]'.format(string_attributes[:-10]))

		# add spaces
		holder_id = '{0}{1}'.format(holder_id, ' ' * (max_len_holder_id - (len(record['holder_id']) if record['holder_id'] is not None else 0)))
		description = '{0}{1}'.format(description, ' ' * (max_len_description - len(description)))
		holders = '{0}{1}'.format(holders, ' ' * (max_len_holders - (len(str(record['holders'])) if record['holders'] is not '' else 0)))

		# colorize description
		if record['description'] in fails:
			description = colorize(description, 'red')
		elif record['description'] in successes:
			description = colorize(description, 'green')

		print '{0}  {1}  {2}  {3}  {4}'.format(when, holder_id, description, holders, attributes)

def save_record(json):
	record = {}
	lock_name = json.get('more').get('lockName')

	if lock_name not in locks:
		locks[lock_name] = {
			'max_holders': None,
			'records': [],
			'holders': set(),
		}

	# holder id
	holder_id = json.get('more').get('holderId', '')
	record['holder_id'] = holder_id
	locks[lock_name]['holders'].add(holder_id)

	# description
	description = json.get('what')
	if description == 'Succeeded to set holders. Start function':
		description = 'Lock acquired'
	elif description == 'Lock is busy, starting watcher':
		description = 'Lock is busy, waiting for update'
	elif description == 'Got an acquire request' and json.get('more', {}).get('openWatch') == 'false':
		description = 'Got an try_acquire request'
	record['description'] = description

	# timestamp
	record['when'] = json.get('when')

	# max_holders
	attributes = json.get('more')
	if locks[lock_name]['max_holders'] == None:
		locks[lock_name]['max_holders'] = attributes.get('actual value', attributes.get('maxHolders'))

	# holders
	holders = ''
	if 'holders' in attributes and 'newHolders' in attributes:
		holders = attributes['newHolders']
	elif 'holders' in attributes:
		holders = attributes['holders']
	record['holders'] = holders

	# more attributes
	for attribute in ignored_more_attributes:
		if type(attribute) == dict:
			if attribute.keys()[0] in attributes and attributes[attribute.keys()[0]] == attribute[attribute.keys()[0]]:
				del attributes[attribute.keys()[0]]
		elif attribute in attributes:
			del attributes[attribute]
	record['more'] = attributes

	return lock_name, record

cmd = 'grep --no-filename "{0}" *debug*.log'.format('\\|'.join(descriptions + fails + successes))
out, err, code = run_command(cmd)
if code == 1:
	print 'No cluster lock found in the logs'
elif code == 2:
	print 'Not found log files'
else:
	lines = out.split('\n')
	locks = {}

	for line in lines:
		if line != '':
			json = simplejson.loads(line)
			if json.get('more') != {}:
				lock_name, record = save_record(json)
				locks[lock_name]['records'].append(record)

	for lock_name in locks:
		if len(sys.argv) == 1 or lock_name in sys.argv:
			print_lock(lock_name)




