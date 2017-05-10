README:

Alex's server
	For the server I used your quiz 3 result to start off with a multi threaded server. Thought it was the best base because it allowed me to build things out evenly and in parts.
	I also used https://gist.github.com/scturtle/1035886 as a guide as to how to setup a server but
	had to customize and implement most of my own stuff.
	
	I currently use local domain and default port for my server and my client uses this to connect to it. 
	
ConfigFile:
	Utilized Config parser to create an easiy to parse configuration file for our server/client.

	
ClientMod:

	This is the client provided by the class that has been modified:
	Some of the major differences is cd is callled with cdw
	
	
	cwd [address] or ['..'] to return to the parent for server
	lcwd [address] or ['..'] to manipulate with local working directions
	
	
Currently missing from the project:

FTP interface that allows you to use a test.txt on it.

verbose mode is always on and cannot be enabled or disabled.

My custom port and data min/max values are currently commented out as my server is setup for local host. A small modication of server and client will be required (changing to custom data) to try it out with the class provided 
ports and min max data.

 
currently not parsing anything from my configuration for the client side
dissect the configfile.py module to see where I'm doing it, did not have time to modify client to parse all my client constants from config folder but 
would take maybe a few minutes or so to setup and test. (Juggling this project with deadlines for a game I'm working on have been killer, sorry.) 
What I'm trying to say here is that I have the feature ready to be implemented I just didn't implement it on the client.

currently not generating any log reports.


ROOT is currently the main project directory.