#raise Exception("edit 'hcp_config.py', modify the account information, and then remove or comment out the first line in that file.")

# the HCP account id - trial accounts typically look like p[0-9]*trial
hcp_account_id = '<your hcp account id, usually ending with "trial">'

# you only need to adapt this part of the URL if you are NOT ON TRIAL but e.g. on PROD
hcp_landscape_host='.hanatrial.ondemand.com'


# hcp_landscape_host='.hana.ondemand.com' # this is used on PROD
# the credentials header for pushing messages to the device; the header
# value can be created using the following command line (in a terminal):
#
#   python -c 'import urllib3 as u;h=u.util.make_headers(basic_auth="user:password");print h["authorization"]'
#
# of course, user and password have to be substituted accordingly using the HCP credentials. Copy/paste the output of
# this command as value of the hcp_authorization_header variable below:

hcp_authorization_header='Basic xxxxxxxxxxxxxxxxxxxx'

# optional network proxy, set if to be used, otherwise set to ''
proxy_url=''
# proxy_url='http://proxy_host:proxy_port'

hcp_device_id = 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
hcp_oauth_credentials = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
hcp_message_type_id_from_device='xxxxxxxxxxxxxxxxxxxx'
hcp_message_type_id_to_device='xxxxxxxxxxxxxxxxxxxx'

# this is the directory where the simulator objects are stored, relative to the current directory
# current user should have read and write permission
default_data_folder = 'simdata'
