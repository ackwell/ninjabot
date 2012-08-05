PREFIX = "^"



	
def _execute_command(pfx,args):
	
	#will need to fix this later (most likely)
	cmd = args[1].split()
	
	if len(cmd) > 0:
		try: #to import the module
			mod = __import__(cmd[0].lower())
			if mod.reload:
				mod = reload(mod)
		except:
			pass #NOTIFY user "Could not import module %s" % cmd[0]
			return;
		
		try:
			mod.execute()#ill add in the args later
		except Exception, err:
			pass #NOTIFY err
			return;
	else:
		pass #NOTIFY "No command specified."